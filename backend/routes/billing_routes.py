"""NeXifyAI — Billing Routes"""
import os
import json
import hashlib
import secrets
import asyncio
from datetime import datetime, timezone, timedelta
from io import BytesIO
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from routes.shared import S
from routes.shared import (
    get_current_admin,
    get_current_customer,
    check_rate_limit,
    log_audit,
    _log_event,
    send_email,
    email_template,
    archive_pdf_to_storage,
    logger,
)
from domain import (
    create_timeline_event, OfferStatus, utcnow,
)
from commercial import (
    COMPANY_DATA as COMM_COMPANY, TARIFF_CONFIG,
    calc_contract, get_tariff, get_next_number,
    generate_quote_pdf, generate_invoice_pdf, generate_contract_pdf,
    generate_access_token, verify_access_token,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["billing"])

class QuoteRequest(BaseModel):
    tier: str
    customer_name: str
    customer_email: EmailStr
    customer_company: Optional[str] = ""
    customer_phone: Optional[str] = ""
    customer_country: Optional[str] = "DE"
    customer_industry: Optional[str] = ""
    use_case: Optional[str] = ""
    notes: Optional[str] = ""
    discount_percent: Optional[float] = 0
    discount_reason: Optional[str] = ""
    special_items: Optional[list] = []

class OfferDiscoveryRequest(BaseModel):
    tier: str
    customer_name: str
    customer_email: EmailStr
    customer_company: Optional[str] = ""
    customer_phone: Optional[str] = ""
    customer_country: Optional[str] = "DE"
    customer_industry: Optional[str] = ""
    session_id: Optional[str] = ""
    use_case: Optional[str] = ""
    target_systems: Optional[str] = ""
    automations: Optional[str] = ""
    channels: Optional[str] = ""
    gdpr_relevant: Optional[bool] = True
    timeline: Optional[str] = ""
    special_requirements: Optional[str] = ""


@router.patch("/api/admin/quotes/{quote_id}")
async def admin_update_quote(quote_id: str, data: dict, user = Depends(get_current_admin)):
    """Angebot bearbeiten — Status, Notizen, Rabatt, Sonderpositionen."""
    quote = await S.db.quotes.find_one({"quote_id": quote_id})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    
    updates = {"updated_at": datetime.now(timezone.utc)}
    
    if "status" in data:
        old_status = quote.get("status", "draft")
        updates["status"] = data["status"]
        # Timeline Event für Statusänderung
        evt = create_timeline_event("quote", quote_id, f"quote_status_{data['status']}",
                                    actor=user["email"], actor_type="admin",
                                    details={"old_status": old_status, "new_status": data["status"]})
        await S.db.timeline_events.insert_one(evt)
    
    if "notes" in data:
        updates["notes"] = data["notes"]
    
    if "use_case" in data:
        updates["use_case"] = data["use_case"]
    
    if "customer_name" in data:
        updates["customer.name"] = data["customer_name"]
    if "customer_email" in data:
        updates["customer.email"] = data["customer_email"]
    if "customer_company" in data:
        updates["customer.company"] = data["customer_company"]
    
    if "discount_percent" in data:
        dp = float(data["discount_percent"] or 0)
        updates["discount.percent"] = dp
        updates["discount.reason"] = data.get("discount_reason", "")
        # Neuberechnung
        from commercial import TARIFF_CONFIG
        tier = quote.get("tier", "starter")
        tariff = TARIFF_CONFIG.get(tier, TARIFF_CONFIG["starter"])
        net = tariff.get("total_contract_eur", 11976.00)  # Use total_contract_eur as net base
        discount_amount = round(net * dp / 100, 2)
        net_after = net - discount_amount
        # Special items
        sp_items = data.get("special_items", quote.get("special_items", []))
        sp_total = sum(si.get("amount_eur", 0) * (1 if si.get("type") == "add" else -1) for si in sp_items)
        net_final = net_after + sp_total
        updates["calculation.discount_amount_eur"] = discount_amount
        updates["calculation.special_items_total_eur"] = sp_total
        updates["calculation.total_contract_eur"] = round(net_final * 1.19, 2)
        updates["calculation.total_contract_net_eur"] = net_final
        updates["special_items"] = sp_items
    
    await S.db.quotes.update_one({"quote_id": quote_id}, {"$set": updates})
    await log_audit("quote_updated", user["email"], {"quote_id": quote_id, "fields": list(updates.keys())})
    
    return {"success": True}



@router.patch("/api/admin/invoices/{invoice_id}")
async def admin_update_invoice(invoice_id: str, data: dict, user = Depends(get_current_admin)):
    """Rechnung bearbeiten — Status, Zahlungsstatus, Notizen."""
    invoice = await S.db.invoices.find_one({"invoice_id": invoice_id})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    
    updates = {"updated_at": datetime.now(timezone.utc)}
    
    if "status" in data:
        updates["status"] = data["status"]
    if "payment_status" in data:
        updates["payment_status"] = data["payment_status"]
    if "notes" in data:
        updates["notes"] = data["notes"]
    
    await S.db.invoices.update_one({"invoice_id": invoice_id}, {"$set": updates})
    await log_audit("invoice_updated", user["email"], {"invoice_id": invoice_id, "fields": list(updates.keys())})
    
    evt = create_timeline_event("invoice", invoice_id, "invoice_updated",
                                actor=user["email"], actor_type="admin",
                                details={"updates": {k: v for k, v in updates.items() if k != "updated_at"}})
    await S.db.timeline_events.insert_one(evt)
    
    return {"success": True}



@router.post("/api/admin/quotes")
async def create_quote(req: QuoteRequest, current_user: dict = Depends(get_current_admin)):
    """Angebot manuell erstellen — mit Tarifvorauswahl, Rabatt und Sonderpositionen."""
    calc = calc_contract(req.tier)
    if not calc:
        raise HTTPException(400, "Ungültiger Tarif")

    quote_number = await get_next_number(S.db, "quote")
    now = datetime.now(timezone.utc)
    tariff = get_tariff(req.tier)

    # Apply discount
    discount = {}
    if req.discount_percent > 0:
        discount = {
            "percent": min(req.discount_percent, 25.0),  # Max 25% Rabatt
            "reason": req.discount_reason or "Kein Grund angegeben",
            "applied_by": current_user["email"],
        }
        calc["discount_percent"] = discount["percent"]
        calc["discount_reason"] = discount["reason"]
        calc["total_contract_eur_before_discount"] = calc.get("total_contract_eur", 0)
        calc["total_contract_eur"] = round(calc["total_contract_eur"] * (1 - discount["percent"] / 100), 2)
        calc["activation_fee_eur"] = round(calc["total_contract_eur"] * 0.3, 2)

    # Apply special items
    special_items = []
    special_total = 0
    for item in (req.special_items or []):
        desc = item.get("description", "").strip()
        amount = float(item.get("amount_eur", 0))
        item_type = item.get("type", "add")
        if desc and amount > 0:
            special_items.append({"description": desc, "amount_eur": amount, "type": item_type})
            special_total += amount if item_type == "add" else -amount

    quote = {
        "quote_id": f"q_{secrets.token_hex(8)}",
        "quote_number": quote_number,
        "status": "draft",
        "tier": req.tier,
        "tariff_number": tariff.get("tariff_number", ""),
        "customer": {
            "name": req.customer_name,
            "email": req.customer_email,
            "company": req.customer_company,
            "phone": req.customer_phone,
            "country": req.customer_country,
            "industry": req.customer_industry,
        },
        "use_case": req.use_case,
        "calculation": calc,
        "discount": discount,
        "special_items": special_items,
        "special_items_total_eur": special_total,
        "notes": req.notes,
        "date": now.strftime("%d.%m.%Y"),
        "valid_until": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "created_by": current_user["email"],
        "history": [{"action": "erstellt", "at": now.isoformat(), "by": current_user["email"]}],
    }

    await S.db.quotes.insert_one(quote)
    quote.pop("_id", None)

    pdf_bytes = generate_quote_pdf(quote)
    await S.db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "quote",
        "ref_id": quote["quote_id"],
        "number": quote_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })

    await _log_event(S.db, "offer_generated", quote["quote_id"], current_user["email"])
    return {"quote": quote, "pdf_available": True}



@router.get("/api/admin/quotes")
async def list_quotes(current_user: dict = Depends(get_current_admin)):
    quotes = await S.db.quotes.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).to_list(200)
    return {"quotes": quotes}



@router.get("/api/admin/quotes/{quote_id}")
async def get_quote_detail(quote_id: str, current_user: dict = Depends(get_current_admin)):
    quote = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    return quote



@router.post("/api/admin/quotes/{quote_id}/send")
async def send_quote(quote_id: str, current_user: dict = Depends(get_current_admin)):
    """Send quote to customer via email with magic link"""
    quote = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")

    doc = await S.db.documents.find_one({"ref_id": quote_id, "type": "quote"})
    if not doc:
        raise HTTPException(404, "PDF nicht gefunden")

    now = datetime.now(timezone.utc)
    customer_email = quote["customer"]["email"]
    customer_name = quote["customer"].get("name", "")
    calc = quote.get("calculation", {})

    token_data = generate_access_token(customer_email, "quote")
    await S.db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": customer_email,
        "quote_id": quote_id,
        "document_type": "quote",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": "system",
    })

    frontend_url = os.environ.get("FRONTEND_URL", "https://nexifyai.de")
    portal_link = f"{frontend_url}/angebot?token={token_data['token']}&qid={quote_id}"

    if S.RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(doc["pdf_data"]).decode()
            resend.Emails.send({
                "from": f"NeXifyAI <{S.SENDER_EMAIL}>",
                "to": customer_email,
                "subject": f"Ihr Angebot von NeXifyAI — {calc.get('tier_name', '')}",
                "html": email_template(
                    "Ihr Angebot",
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Ihr persoenliches Angebot</h1>
                    <p>Sehr geehrte/r {customer_name},</p>
                    <p>vielen Dank für Ihr Interesse an <strong style="color:#ffb599;">NeXifyAI</strong>.</p>
                    <p>Anbei erhalten Sie Ihr Angebot für <strong>{calc.get("tier_name", "")}</strong>:</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 8px;font-size:13px;color:#8f9095;">ANGEBOT</p>
                    <p style="margin:0 0 4px;color:#fff;font-weight:600;">{quote.get("quote_number", "")}</p>
                    <p style="margin:8px 0 0;font-size:13px;color:#8f9095;">GESAMTVERTRAGSWERT</p>
                    <p style="margin:0;color:#ffb599;font-weight:600;">{calc.get("total_contract_eur", 0):,.2f} EUR (netto)</p>
                    </div>
                    <p>Öffnen Sie das Angebot über den sicheren Link:</p>''',
                    portal_link,
                    "Angebot öffnen"
                ),
                "attachments": [{
                    "filename": f"Angebot_{quote['quote_number'].replace('.', '_')}.pdf",
                    "content": pdf_b64,
                    "content_type": "application/pdf",
                }],
            })
            logger.info(f"Quote {quote_id} sent to {customer_email}")
        except Exception as e:
            logger.error(f"Email send error: {e}")
            raise HTTPException(500, f"E-Mail-Versand fehlgeschlagen: {str(e)}")

    await S.db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "sent", "sent_at": now.isoformat()},
         "$push": {"history": {"action": "sent", "at": now.isoformat(), "by": current_user["email"]}}},
    )
    await _log_event(S.db, "offer_sent", quote_id, current_user["email"])
    return {"sent": True, "to": customer_email}



@router.post("/api/admin/quotes/{quote_id}/copy")
async def copy_quote(quote_id: str, current_user: dict = Depends(get_current_admin)):
    """Angebot kopieren / versionieren."""
    orig = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not orig:
        raise HTTPException(404, "Angebot nicht gefunden")
    new_id_val = f"q_{secrets.token_hex(8)}"
    new_number = await get_next_number(S.db, "quote")
    now = datetime.now(timezone.utc)
    copy = {**orig,
        "quote_id": new_id_val,
        "quote_number": new_number,
        "status": "draft",
        "date": now.strftime("%d.%m.%Y"),
        "valid_until": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "created_by": current_user["email"],
        "history": [
            {"action": "kopiert", "at": now.isoformat(), "by": current_user["email"], "from": quote_id},
        ],
    }
    await S.db.quotes.insert_one(copy)
    copy.pop("_id", None)
    # Regenerate PDF
    from commercial import generate_quote_pdf
    pdf_bytes = generate_quote_pdf(copy)
    await S.db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "quote",
        "ref_id": new_id_val,
        "number": new_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })
    await _log_event(S.db, "offer_copied", new_id_val, current_user["email"])
    return {"quote": copy, "copied_from": quote_id}



@router.post("/api/admin/invoices")
async def admin_create_invoice(data: dict, current_user: dict = Depends(get_current_admin)):
    """Rechnung manuell erstellen (aus Angebot oder frei)."""
    quote_id = data.get("quote_id")
    now = datetime.now(timezone.utc)
    inv_number = await get_next_number(S.db, "invoice")

    if quote_id:
        quote = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
        if not quote:
            raise HTTPException(404, "Angebot nicht gefunden")
        calc = quote.get("calculation", {})
        inv_type = data.get("type", "activation")
        if inv_type == "activation":
            amount = data.get("amount_eur") or calc.get("upfront_eur") or calc.get("activation_fee_eur", 0)
            desc = f"Aktivierungsanzahlung {calc.get('tier_name', '')}"
        elif inv_type == "recurring":
            amount = data.get("amount_eur") or calc.get("recurring_eur", 0)
            desc = f"Monatliche Rate {calc.get('tier_name', '')}"
        else:
            amount = data.get("amount_eur", 0)
            desc = data.get("description", "")
        customer = quote.get("customer", {})
    else:
        amount = data.get("amount_eur", 0)
        customer = {
            "name": data.get("customer_name", ""),
            "email": data.get("customer_email", ""),
            "company": data.get("customer_company", ""),
        }

    tax_rate = data.get("tax_rate", 0.19)
    netto = round(float(amount), 2)
    ust = round(netto * tax_rate, 2)
    brutto = round(netto + ust, 2)

    invoice = {
        "invoice_id": f"inv_{secrets.token_hex(8)}",
        "invoice_number": inv_number,
        "quote_id": quote_id or "",
        "status": "draft",
        "customer": customer,
        "amount_netto_eur": netto,
        "tax_rate": tax_rate,
        "tax_eur": ust,
        "total_eur": brutto,
        "description": data.get("description") or (desc if quote_id else ""),
        "date": now.strftime("%d.%m.%Y"),
        "due_date": (now + timedelta(days=14)).strftime("%d.%m.%Y"),
        "created_at": now.isoformat(),
        "created_by": current_user["email"],
        "history": [{"action": "erstellt", "at": now.isoformat(), "by": current_user["email"]}],
    }
    await S.db.invoices.insert_one(invoice)
    invoice.pop("_id", None)
    evt = create_timeline_event("invoice", invoice["invoice_id"], "invoice_created",
                                actor=current_user["email"], actor_type="admin",
                                details={"invoice_number": inv_number, "total_eur": brutto})
    await S.db.timeline_events.insert_one(evt)
    return invoice



# --- Customer-Facing Offer Portal ---


@router.post("/api/chat/generate-offer")
async def chat_generate_offer(data: OfferDiscoveryRequest, request: Request):
    """Generate an offer from chat discovery data"""
    await check_rate_limit(request, limit=5, window=60)

    calc = calc_contract(data.tier)
    if not calc:
        raise HTTPException(400, "Ungültiger Tarif")

    quote_number = await get_next_number(S.db, "quote")
    now = datetime.now(timezone.utc)
    tariff = get_tariff(data.tier)

    quote = {
        "quote_id": f"q_{secrets.token_hex(8)}",
        "quote_number": quote_number,
        "status": "generated",
        "tier": data.tier,
        "tariff_number": tariff.get("tariff_number", ""),
        "customer": {
            "name": data.customer_name,
            "email": data.customer_email,
            "company": data.customer_company,
            "phone": data.customer_phone,
            "country": data.customer_country,
            "industry": data.customer_industry,
        },
        "discovery": {
            "session_id": data.session_id,
            "use_case": data.use_case,
            "target_systems": data.target_systems,
            "automations": data.automations,
            "channels": data.channels,
            "gdpr_relevant": data.gdpr_relevant,
            "timeline": data.timeline,
            "special_requirements": data.special_requirements,
        },
        "calculation": calc,
        "date": now.strftime("%d.%m.%Y"),
        "valid_until": (now + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat(),
        "created_by": "ai_advisor",
        "history": [{"action": "generated_from_chat", "at": now.isoformat(), "by": "ai_advisor", "session": data.session_id}],
    }

    await S.db.quotes.insert_one(quote)
    quote.pop("_id", None)

    pdf_bytes = generate_quote_pdf(quote)
    await S.db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "quote",
        "ref_id": quote["quote_id"],
        "number": quote_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })

    await _log_event(S.db, "offer_generated", quote["quote_id"], "ai_advisor")

    token_data = generate_access_token(data.customer_email, "quote")
    await S.db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": data.customer_email,
        "quote_id": quote["quote_id"],
        "document_type": "quote",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": "ai_advisor",
    })

    frontend_url = os.environ.get("FRONTEND_URL", "https://nexifyai.de")
    portal_link = f"{frontend_url}/angebot?token={token_data['token']}&qid={quote['quote_id']}"

    if S.RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            import asyncio
            asyncio.create_task(send_email(
                [data.customer_email],
                f"Ihr Angebot von NeXifyAI — {calc.get('tier_name', '')}",
                email_template("Ihr Angebot",
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Ihr persoenliches Angebot</h1>
                    <p>Sehr geehrte/r {data.customer_name},</p>
                    <p>basierend auf unserem Gespraech haben wir Ihr individuelles Angebot erstellt.</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">TARIF</p>
                    <p style="margin:0 0 8px;color:#ffb599;font-weight:600;">{calc.get("tier_name","")}</p>
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">GESAMTVERTRAGSWERT</p>
                    <p style="margin:0;color:#fff;font-weight:600;">{calc.get("total_contract_eur",0):,.2f} EUR</p>
                    </div>''',
                    portal_link,
                    "Angebot öffnen"
                ),
            ))
        except Exception as e:
            logger.error(f"Chat offer email error: {e}")

    return {
        "quote_id": quote["quote_id"],
        "quote_number": quote_number,
        "tier_name": calc.get("tier_name", ""),
        "total_contract_eur": calc.get("total_contract_eur", 0),
        "upfront_gross": calc.get("upfront_gross", 0),
        "pdf_download_url": f"/api/documents/quote/{quote['quote_id']}/pdf",
        "portal_link": portal_link,
        "sent_to": data.customer_email,
    }


# --- Invoice Management (Admin) ---


@router.get("/api/admin/invoices")
async def list_invoices(current_user: dict = Depends(get_current_admin)):
    invoices = await S.db.invoices.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).to_list(200)
    return {"invoices": invoices}



@router.get("/api/admin/invoices/{invoice_id}")
async def get_invoice_detail(invoice_id: str, current_user: dict = Depends(get_current_admin)):
    invoice = await S.db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    return invoice



@router.post("/api/admin/invoices/{invoice_id}/send")
async def send_invoice(invoice_id: str, current_user: dict = Depends(get_current_admin)):
    """Send invoice to customer via email"""
    invoice = await S.db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")

    doc = await S.db.documents.find_one({"ref_id": invoice_id, "type": "invoice"})
    if not doc:
        raise HTTPException(404, "PDF nicht gefunden")

    now = datetime.now(timezone.utc)
    customer_email = invoice["customer"]["email"]
    customer_name = invoice["customer"].get("name", "")

    type_labels = {"deposit": "Aktivierungsanzahlung", "monthly": "Monatsrechnung", "final": "Schlussrechnung"}
    inv_label = type_labels.get(invoice.get("type", "deposit"), "Rechnung")

    if S.RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(doc["pdf_data"]).decode()
            checkout_url = invoice.get("checkout_url", "")
            payment_html = ""
            if checkout_url:
                payment_html = f'<a href="{checkout_url}" style="display:inline-block;padding:12px 24px;background:#ffb599;color:#0c1117;text-decoration:none;font-weight:bold;border-radius:6px;">Jetzt online bezahlen</a>'

            totals = invoice.get("totals", {})
            gross_val = totals.get("gross", 0)
            gross_str = f"{gross_val:,.2f} EUR" if isinstance(gross_val, (int, float)) else str(gross_val)

            resend.Emails.send({
                "from": f"NeXifyAI <{S.SENDER_EMAIL}>",
                "to": customer_email,
                "subject": f"{inv_label} {invoice['invoice_number']} — NeXifyAI",
                "html": email_template(
                    inv_label,
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">{inv_label}</h1>
                    <p>Sehr geehrte/r {customer_name},</p>
                    <p>anbei erhalten Sie Ihre {inv_label} Nr. {invoice["invoice_number"]}.</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">BETRAG (BRUTTO)</p>
                    <p style="margin:0 0 8px;color:#ffb599;font-weight:600;">{gross_str}</p>
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">FAELLIG AM</p>
                    <p style="margin:0;color:#fff;">{invoice.get("due_date","---")}</p>
                    </div>
                    {payment_html}
                    <p>Alternativ per Banküberweisung:<br/>
                    IBAN: {COMM_COMPANY["bank"]["iban"]}<br/>
                    BIC: {COMM_COMPANY["bank"]["bic"]}<br/>
                    Verwendungszweck: {invoice["invoice_number"]}</p>''',
                ),
                "attachments": [{
                    "filename": f"Rechnung_{invoice['invoice_number'].replace('.', '_')}.pdf",
                    "content": pdf_b64,
                    "content_type": "application/pdf",
                }],
            })
        except Exception as e:
            logger.error(f"Invoice email error: {e}")
            raise HTTPException(500, f"E-Mail-Versand fehlgeschlagen: {str(e)}")

    await S.db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {"status": "sent", "sent_at": now.isoformat()},
         "$push": {"history": {"action": "sent", "at": now.isoformat(), "by": current_user["email"]}}},
    )
    await _log_event(S.db, "invoice_sent", invoice_id, current_user["email"])
    return {"sent": True, "to": customer_email}


# --- Document Downloads ---


@router.get("/api/documents/{doc_type}/{ref_id}/pdf")
async def download_document(doc_type: str, ref_id: str, token: str = None):
    """Download document PDF — Object Storage primär, MongoDB-Fallback."""
    doc = await S.db.documents.find_one({"ref_id": ref_id, "type": doc_type})
    if not doc:
        raise HTTPException(404, "Dokument nicht gefunden")

    if token:
        link = await S.db.access_links.find_one({"token_hash": hashlib.sha256(token.encode()).hexdigest()})
        if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
            raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
        await _log_event(S.db, "document_accessed", ref_id, "magic_link")

    filename = f"{doc_type}_{doc.get('number', ref_id).replace('.', '_')}.pdf"

    # Object Storage primär
    storage_path = doc.get("storage_path")
    if storage_path:
        try:
            from services.storage import get_object
            pdf_data, _ = get_object(storage_path)
            return StreamingResponse(
                BytesIO(pdf_data),
                media_type="application/pdf",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
        except Exception as e:
            logger.warning(f"Object Storage download fallback: {e}")

    # MongoDB-Fallback
    if doc.get("pdf_data"):
        return StreamingResponse(
            BytesIO(doc["pdf_data"]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    raise HTTPException(404, "PDF-Daten nicht verfügbar")


# --- Customer Magic Link Access ---


@router.post("/api/admin/access-link")
async def create_access_link(customer_email: str = "", current_user: dict = Depends(get_current_admin)):
    token_data = generate_access_token(customer_email)
    await S.db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": customer_email,
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": current_user["email"],
    })
    return {"magic_link_token": token_data["token"], "expires_at": token_data["expires_at"]}


# --- Revolut Webhook ---


@router.post("/api/webhooks/revolut")
async def revolut_webhook(request: Request):
    """Handle Revolut payment webhooks — idempotent, signaturverifiziert, synchronisiert."""
    body = await request.body()
    raw_body = body.decode("utf-8")

    # Signatur-Verifikation (wenn Secret konfiguriert)
    revolut_signing_secret = os.environ.get("REVOLUT_WEBHOOK_SECRET", "").strip()
    if revolut_signing_secret:
        sig = request.headers.get("revolut-signature", "")
        timestamp = request.headers.get("revolut-request-timestamp", "")
        if sig and timestamp:
            from commercial import verify_revolut_webhook
            if not verify_revolut_webhook(revolut_signing_secret, timestamp, raw_body, sig):
                logger.warning(f"Revolut webhook signature mismatch")
                raise HTTPException(401, "Invalid webhook signature")

    try:
        data = json.loads(raw_body)
    except Exception:
        raise HTTPException(400, "Invalid JSON")

    event = data.get("event", "")
    order_id = data.get("order_id", "")

    logger.info(f"Revolut webhook: {event} for order {order_id}")

    # Idempotenz-Check
    existing = await S.db.webhook_events.find_one({"order_id": order_id, "event": event})
    if existing:
        return {"status": "already_processed"}

    await S.db.webhook_events.insert_one({
        "order_id": order_id,
        "event": event,
        "data": data,
        "provider": "revolut",
        "processed_at": datetime.now(timezone.utc).isoformat(),
    })
    await _log_event(S.db, "webhook_received", order_id, "revolut")

    if S.billing_svc:
        result = await S.billing_svc.process_payment_webhook("revolut", {
            "order_id": order_id, "event": event,
            "amount": data.get("amount", 0),
        })
        # Contract sync
        if event == "ORDER_COMPLETED":
            invoice = await S.db.invoices.find_one({"revolut_order_id": order_id}, {"_id": 0})
            if invoice and invoice.get("quote_id"):
                contract = await S.db.contracts.find_one({"quote_id": invoice["quote_id"]}, {"_id": 0})
                if contract and contract.get("status") in ("sent", "viewed", "accepted"):
                    await S.db.contracts.update_one(
                        {"contract_id": contract["contract_id"]},
                        {"$set": {"payment_status": "deposit_paid", "updated_at": utcnow()}}
                    )
                    await S.db.timeline_events.insert_one(create_timeline_event(
                        "contract", contract["contract_id"], "contract_payment_received",
                        actor="webhook:revolut", actor_type="system",
                        details={"order_id": order_id, "invoice_id": invoice.get("invoice_id", "")},
                    ))
    else:
        # Fallback (ohne BillingService)
        if event == "ORDER_COMPLETED":
            invoice = await S.db.invoices.find_one({"revolut_order_id": order_id})
            if invoice:
                now = datetime.now(timezone.utc)
                await S.db.invoices.update_one(
                    {"invoice_id": invoice["invoice_id"]},
                    {"$set": {"payment_status": "paid", "paid_at": now.isoformat(), "status": "payment_completed"},
                     "$push": {"history": {"action": "payment_received_revolut", "at": now.isoformat(), "by": "system"}}},
                )
                if invoice.get("quote_id"):
                    await S.db.quotes.update_one(
                        {"quote_id": invoice["quote_id"]},
                        {"$set": {"payment_status": "deposit_paid"},
                         "$push": {"history": {"action": "deposit_paid_revolut", "at": now.isoformat(), "by": "system"}}},
                    )
                await _log_event(S.db, "payment_completed", invoice["invoice_id"], "revolut_webhook")

        elif event == "ORDER_PAYMENT_FAILED":
            invoice = await S.db.invoices.find_one({"revolut_order_id": order_id})
            if invoice:
                await S.db.invoices.update_one(
                    {"invoice_id": invoice["invoice_id"]},
                    {"$set": {"payment_status": "failed"},
                     "$push": {"history": {"action": "payment_failed", "at": datetime.now(timezone.utc).isoformat(), "by": "system"}}},
                )
                await _log_event(S.db, "payment_failed", invoice["invoice_id"], "revolut_webhook")

    await _log_event(S.db, "webhook_processed", order_id, "system")
    return {"status": "ok"}


# --- Stripe Webhook ---


@router.post("/api/admin/invoices/{invoice_id}/create-stripe-checkout")
async def create_stripe_checkout(invoice_id: str, request: Request, current_user: dict = Depends(get_current_admin)):
    """Stripe Checkout Session für eine Rechnung erstellen."""
    if not S.STRIPE_API_KEY:
        raise HTTPException(503, "Stripe nicht konfiguriert")
    invoice = await S.db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    if invoice.get("payment_status") == "paid":
        raise HTTPException(400, "Rechnung bereits bezahlt")

    totals = invoice.get("totals", {})
    gross = float(totals.get("gross", invoice.get("total_eur", 0)))
    host_url = str(request.base_url).rstrip("/")

    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest
        webhook_url = f"{host_url}api/webhooks/stripe"
        stripe_checkout = StripeCheckout(api_key=S.STRIPE_API_KEY, webhook_url=webhook_url)

        checkout_req = CheckoutSessionRequest(
            amount=gross,
            currency="eur",
            success_url=f"{host_url}portal?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{host_url}portal?payment=cancelled",
            metadata={"invoice_id": invoice_id, "invoice_number": invoice.get("invoice_number", "")},
        )
        session = await stripe_checkout.create_checkout_session(checkout_req)

        # payment_transactions Collection
        await S.db.payment_transactions.insert_one({
            "session_id": session.session_id,
            "invoice_id": invoice_id,
            "invoice_number": invoice.get("invoice_number", ""),
            "amount": gross,
            "currency": "eur",
            "provider": "stripe",
            "payment_status": "initiated",
            "customer_email": invoice.get("customer", {}).get("email", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        await S.db.invoices.update_one(
            {"invoice_id": invoice_id},
            {"$set": {
                "stripe_checkout_session_id": session.session_id,
                "checkout_url": session.url,
            }},
        )
        await _log_event(S.db, "stripe_checkout_created", invoice_id, "billing")
        return {"checkout_url": session.url, "session_id": session.session_id}
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(500, f"Stripe Checkout-Fehler: {str(e)[:200]}")



@router.get("/api/payments/checkout/status/{session_id}")
async def checkout_status(session_id: str):
    """Stripe Checkout Status abfragen — für Frontend-Polling."""
    if not S.STRIPE_API_KEY:
        raise HTTPException(503, "Stripe nicht konfiguriert")
    try:
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        stripe_checkout = StripeCheckout(api_key=S.STRIPE_API_KEY, webhook_url="")
        status = await stripe_checkout.get_checkout_status(session_id)

        # Update payment_transactions
        if status.payment_status == "paid":
            existing = await S.db.payment_transactions.find_one({"session_id": session_id, "payment_status": "paid"})
            if not existing:
                await S.db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}},
                )
                # Update invoice
                tx = await S.db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
                if tx and tx.get("invoice_id"):
                    now = datetime.now(timezone.utc)
                    await S.db.invoices.update_one(
                        {"invoice_id": tx["invoice_id"]},
                        {"$set": {"payment_status": "paid", "paid_at": now.isoformat(), "status": "payment_completed"},
                         "$push": {"history": {"action": "payment_received_stripe", "at": now.isoformat(), "by": "system"}}},
                    )
                    invoice = await S.db.invoices.find_one({"invoice_id": tx["invoice_id"]}, {"_id": 0})
                    if invoice and invoice.get("quote_id"):
                        await S.db.quotes.update_one(
                            {"quote_id": invoice["quote_id"]},
                            {"$set": {"payment_status": "deposit_paid"},
                             "$push": {"history": {"action": "deposit_paid_stripe", "at": now.isoformat(), "by": "system"}}},
                        )
                    await _log_event(S.db, "payment_confirmed_stripe", tx["invoice_id"], "billing")

        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "metadata": status.metadata,
        }
    except Exception as e:
        logger.error(f"Stripe status check error: {e}")
        raise HTTPException(500, f"Status-Abfrage fehlgeschlagen: {str(e)[:100]}")



@router.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe payment webhooks — idempotent, signaturverifiziert, dasselbe Statusmodell wie Revolut."""
    body = await request.body()
    raw_body = body.decode("utf-8")

    # Handle via emergentintegrations if available
    if S.STRIPE_API_KEY:
        try:
            from emergentintegrations.payments.stripe.checkout import StripeCheckout
            stripe_checkout = StripeCheckout(api_key=S.STRIPE_API_KEY, webhook_url="")
            sig_header = request.headers.get("Stripe-Signature", "")
            webhook_response = await stripe_checkout.handle_webhook(body, sig_header)
            if webhook_response:
                event_type = webhook_response.event_type
                event_id = webhook_response.event_id
                session_id = webhook_response.session_id
                payment_status = webhook_response.payment_status
                metadata = webhook_response.metadata or {}
            else:
                data = json.loads(raw_body)
                event_type = data.get("type", "")
                event_id = data.get("id", "")
                session_id = ""
                payment_status = ""
                metadata = {}
        except Exception as e:
            logger.warning(f"Stripe webhook handle error: {e}, falling back to raw parse")
            data = json.loads(raw_body)
            event_type = data.get("type", "")
            event_id = data.get("id", "")
            session_id = ""
            payment_status = ""
            metadata = {}
    else:
        try:
            data = json.loads(raw_body)
        except Exception:
            raise HTTPException(400, "Invalid JSON")
        event_type = data.get("type", "")
        event_id = data.get("id", "")
        session_id = ""
        payment_status = ""
        metadata = {}

    invoice_id_ref = metadata.get("invoice_id", "")

    logger.info(f"Stripe webhook: {event_type} event_id={event_id} session={session_id}")

    # Idempotenz-Check
    existing = await S.db.webhook_events.find_one({"order_id": event_id, "event": event_type, "provider": "stripe"})
    if existing:
        return {"status": "already_processed"}

    await S.db.webhook_events.insert_one({
        "order_id": event_id,
        "event": event_type,
        "provider": "stripe",
        "session_id": session_id,
        "payment_status": payment_status,
        "metadata": metadata,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    })
    await _log_event(S.db, "webhook_received", event_id, "stripe")

    # Update payment transaction and invoice
    if payment_status == "paid" and session_id:
        existing_paid = await S.db.payment_transactions.find_one({"session_id": session_id, "payment_status": "paid"})
        if not existing_paid:
            await S.db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {"payment_status": "paid", "paid_at": datetime.now(timezone.utc).isoformat()}},
            )
            tx = await S.db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
            if tx and tx.get("invoice_id"):
                now_ts = datetime.now(timezone.utc)
                await S.db.invoices.update_one(
                    {"invoice_id": tx["invoice_id"]},
                    {"$set": {"payment_status": "paid", "paid_at": now_ts.isoformat(), "status": "payment_completed"},
                     "$push": {"history": {"action": "payment_received_stripe_webhook", "at": now_ts.isoformat(), "by": "system"}}},
                )
                inv = await S.db.invoices.find_one({"invoice_id": tx["invoice_id"]}, {"_id": 0})
                if inv and inv.get("quote_id"):
                    await S.db.quotes.update_one(
                        {"quote_id": inv["quote_id"]},
                        {"$set": {"payment_status": "deposit_paid"},
                         "$push": {"history": {"action": "deposit_paid_stripe_webhook", "at": now_ts.isoformat(), "by": "system"}}},
                    )
    elif invoice_id_ref and event_type in ("payment_intent.succeeded",):
        if S.billing_svc:
            await S.billing_svc.process_payment_webhook("stripe", {
                "order_id": invoice_id_ref,
                "event": event_type,
                "amount": 0,
            })

    await _log_event(S.db, "webhook_processed", event_id, "stripe")
    return {"status": "ok"}


# --- Manuelle Zahlung / Banküberweisung ---


@router.post("/api/admin/invoices/{invoice_id}/mark-paid")
async def mark_invoice_paid(invoice_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Manuelle Zahlungsbestätigung (Banküberweisung, Bar, etc.)."""
    invoice = await S.db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    if invoice.get("payment_status") == "paid":
        return {"already_paid": True}

    now = utcnow()
    method = (data or {}).get("method", "bank_transfer")
    reference = (data or {}).get("reference", "")
    notes = (data or {}).get("notes", "")

    await S.db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "payment_status": "paid", "paid_at": now.isoformat(),
            "status": "payment_completed",
            "payment_method": method,
            "payment_reference_manual": reference,
        },
         "$push": {"history": {"action": f"manual_paid_{method}", "at": now.isoformat(), "by": current_user["email"], "notes": notes}}},
    )
    # Sync Quote
    if invoice.get("quote_id"):
        await S.db.quotes.update_one(
            {"quote_id": invoice["quote_id"]},
            {"$set": {"payment_status": "deposit_paid"},
             "$push": {"history": {"action": f"deposit_paid_{method}", "at": now.isoformat(), "by": current_user["email"]}}},
        )
    # Sync Contract
    contract = await S.db.contracts.find_one({"quote_id": invoice.get("quote_id", "---")}, {"_id": 0})
    if contract:
        await S.db.contracts.update_one(
            {"contract_id": contract["contract_id"]},
            {"$set": {"payment_status": "deposit_paid", "updated_at": now}}
        )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "invoice", invoice_id, "manual_payment_confirmed",
        actor=current_user["email"], actor_type="admin",
        details={"method": method, "reference": reference, "amount": invoice.get("totals", {}).get("gross", 0)},
    ))
    if S.memory_svc:
        email = invoice.get("customer", {}).get("email", "")
        if email:
            await S.memory_svc.write(
                email, f"Zahlung bestätigt: {invoice.get('invoice_number', '')} via {method}",
                agent_id="finance_agent", category="payment",
                source="admin", source_ref=invoice_id,
                verification_status="verifiziert",
            )
    return {"marked_paid": True, "method": method}


# --- Reminder/Mahnlogik ---


@router.post("/api/admin/invoices/{invoice_id}/send-reminder")
async def send_invoice_reminder(invoice_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Zahlungserinnerung senden. Eskalation: Erinnerung → 1. Mahnung → 2. Mahnung."""
    invoice = await S.db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    if invoice.get("payment_status") == "paid":
        return {"error": "Rechnung ist bereits bezahlt"}

    reminder_count = invoice.get("reminder_count", 0) + 1
    reminder_type = "erinnerung"
    if reminder_count == 2:
        reminder_type = "1_mahnung"
    elif reminder_count >= 3:
        reminder_type = "2_mahnung"

    now = utcnow()
    await S.db.invoices.update_one(
        {"invoice_id": invoice_id},
        {"$set": {
            "reminder_count": reminder_count,
            "last_reminder_at": now.isoformat(),
            "last_reminder_type": reminder_type,
        },
         "$push": {"history": {"action": f"reminder_{reminder_type}", "at": now.isoformat(), "by": current_user["email"]}}},
    )
    # Email
    email = invoice.get("customer", {}).get("email", "")
    if email and S.RESEND_API_KEY:
        subjects = {
            "erinnerung": f"Zahlungserinnerung — Rechnung {invoice.get('invoice_number', '')}",
            "1_mahnung": f"1. Mahnung — Rechnung {invoice.get('invoice_number', '')}",
            "2_mahnung": f"2. Mahnung — Rechnung {invoice.get('invoice_number', '')}",
        }
        bodies = {
            "erinnerung": "dies ist eine freundliche Erinnerung an die ausstehende Zahlung.",
            "1_mahnung": "leider konnten wir bisher keinen Zahlungseingang feststellen. Wir bitten Sie, die offene Rechnung umgehend zu begleichen.",
            "2_mahnung": "trotz unserer vorherigen Erinnerungen steht die Zahlung weiterhin aus. Wir bitten um sofortige Begleichung.",
        }
        try:
            html = email_template(
                subjects.get(reminder_type, "Zahlungserinnerung"),
                f'''<h1 style="color:#fff;font-size:20px;margin:0 0 16px;">{subjects.get(reminder_type, "")}</h1>
                <p>Guten Tag,</p>
                <p>{bodies.get(reminder_type, "")}</p>
                <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">RECHNUNG</p>
                <p style="margin:0 0 8px;color:#fff;font-weight:600;">{invoice.get("invoice_number", "")}</p>
                <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">OFFENER BETRAG</p>
                <p style="margin:0;color:#ffb599;font-weight:600;">{invoice.get("totals", {}).get("gross", 0):,.2f} EUR</p></div>
                <p>IBAN: {COMM_COMPANY["bank"]["iban"]}<br/>BIC: {COMM_COMPANY["bank"]["bic"]}<br/>Verwendungszweck: {invoice.get("invoice_number", "")}</p>'''
            )
            await send_email([email], subjects.get(reminder_type, ""), html, category="reminder", ref_id=invoice_id)
        except Exception as e:
            logger.error(f"Reminder email error: {e}")

    await S.db.timeline_events.insert_one(create_timeline_event(
        "invoice", invoice_id, f"reminder_{reminder_type}",
        actor=current_user["email"], actor_type="admin",
        details={"reminder_count": reminder_count, "type": reminder_type},
    ))
    return {"reminder_sent": True, "type": reminder_type, "count": reminder_count}


# --- Billing Status Dashboard ---


@router.get("/api/admin/billing/status")
async def admin_billing_status(customer_email: str = None, current_user: dict = Depends(get_current_admin)):
    """Einheitliche Billing-Statusübersicht. Gleiche Quelle für Portal/Admin/Timeline."""
    if customer_email and S.billing_svc:
        return await S.billing_svc.get_billing_status(customer_email)

    # Global overview
    total_quotes = await S.db.quotes.count_documents({})
    accepted_quotes = await S.db.quotes.count_documents({"status": "accepted"})
    total_invoices = await S.db.invoices.count_documents({})
    paid_invoices = await S.db.invoices.count_documents({"payment_status": "paid"})
    pending_invoices = await S.db.invoices.count_documents({"payment_status": {"$in": ["pending", "unpaid"]}})
    overdue_invoices = await S.db.invoices.count_documents({"payment_status": {"$nin": ["paid"]}, "reminder_count": {"$gte": 1}})
    total_contracts = await S.db.contracts.count_documents({})
    active_contracts = await S.db.contracts.count_documents({"status": "accepted"})

    pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$totals.gross"}}},
    ]
    revenue_agg = await S.db.invoices.aggregate(pipeline).to_list(1)
    total_revenue = revenue_agg[0]["total"] if revenue_agg else 0

    pipeline_open = [
        {"$match": {"payment_status": {"$nin": ["paid"]}}},
        {"$group": {"_id": None, "total": {"$sum": "$totals.gross"}}},
    ]
    open_agg = await S.db.invoices.aggregate(pipeline_open).to_list(1)
    total_open = open_agg[0]["total"] if open_agg else 0

    return {
        "quotes": {"total": total_quotes, "accepted": accepted_quotes},
        "invoices": {"total": total_invoices, "paid": paid_invoices, "pending": pending_invoices, "overdue": overdue_invoices},
        "contracts": {"total": total_contracts, "active": active_contracts},
        "revenue": {"total_gross": round(total_revenue, 2), "total_open": round(total_open, 2), "currency": "EUR"},
    }


# ══════════════════════════════════════════════════════════════
# RECONCILIATION (P4: Keine divergierenden Wahrheitsquellen)
# ══════════════════════════════════════════════════════════════


@router.post("/api/admin/billing/reconcile")
async def billing_reconcile(current_user: dict = Depends(get_current_admin)):
    """Reconciliation: Quote ↔ Contract ↔ Invoice ↔ Payment Status abgleichen."""
    fixed = []
    issues = []

    # 1. Invoices mit payment_status=paid → Quote + Contract sync
    async for inv in S.db.invoices.find({"payment_status": "paid"}, {"_id": 0}):
        qid = inv.get("quote_id", "")
        if qid:
            quote = await S.db.quotes.find_one({"quote_id": qid}, {"_id": 0})
            if quote and quote.get("payment_status") != "deposit_paid":
                await S.db.quotes.update_one(
                    {"quote_id": qid},
                    {"$set": {"payment_status": "deposit_paid"},
                     "$push": {"history": {"action": "reconciled_deposit_paid", "at": utcnow().isoformat(), "by": "reconciliation"}}},
                )
                fixed.append(f"Quote {qid}: payment_status → deposit_paid")

            contract = await S.db.contracts.find_one({"quote_id": qid}, {"_id": 0})
            if contract and contract.get("payment_status") != "deposit_paid":
                await S.db.contracts.update_one(
                    {"contract_id": contract["contract_id"]},
                    {"$set": {"payment_status": "deposit_paid", "updated_at": utcnow()}}
                )
                fixed.append(f"Contract {contract['contract_id']}: payment_status → deposit_paid")

    # 2. Contracts accepted but no invoice
    async for c in S.db.contracts.find({"status": "accepted"}, {"_id": 0}):
        if c.get("quote_id"):
            inv = await S.db.invoices.find_one({"quote_id": c["quote_id"]}, {"_id": 0})
            if not inv:
                issues.append(f"Contract {c['contract_id']} accepted but no invoice for quote {c['quote_id']}")

    # 3. Invoices with reminder but paid
    async for inv in S.db.invoices.find({"payment_status": "paid", "reminder_count": {"$gte": 1}}, {"_id": 0}):
        issues.append(f"Invoice {inv.get('invoice_id')} is paid but has reminder_count={inv.get('reminder_count')}")

    await S.db.timeline_events.insert_one(create_timeline_event(
        "system", "reconciliation", "billing_reconciliation",
        actor=current_user["email"], actor_type="admin",
        details={"fixed": len(fixed), "issues": len(issues)},
    ))

    return {
        "reconciled": True,
        "fixed": fixed,
        "issues": issues,
        "timestamp": utcnow().isoformat(),
    }


# ══════════════════════════════════════════════════════════════
# E-MAIL / RESEND MONITORING (P3)
# ══════════════════════════════════════════════════════════════


@router.get("/api/admin/email/stats")
async def email_stats(current_user: dict = Depends(get_current_admin)):
    """E-Mail-Versand-Statistiken und History."""
    total = await S.db.email_events.count_documents({})
    sent = await S.db.email_events.count_documents({"status": "sent"})
    failed = await S.db.email_events.count_documents({"status": "failed"})

    recent = []
    async for e in S.db.email_events.find({}, {"_id": 0}).sort("sent_at", -1).limit(30):
        recent.append(e)

    return {
        "total": total,
        "sent": sent,
        "failed": failed,
        "success_rate": f"{round(sent / max(total, 1) * 100)}%",
        "resend_configured": bool(S.RESEND_API_KEY),
        "sender": S.SENDER_EMAIL,
        "recent_events": recent,
    }



@router.post("/api/admin/email/test")
async def email_test(data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Test-E-Mail an Admin senden."""
    to_email = (data or {}).get("to", current_user["email"])
    result = await send_email(
        [to_email],
        "NeXifyAI — E-Mail-Systemtest",
        email_template(
            "Systemtest erfolgreich",
            f"<p>Diese E-Mail bestätigt die funktionierende E-Mail-Zustellung über Resend.</p>"
            f"<p style='color:#6b7b8d;font-size:12px;'>Gesendet: {datetime.now(timezone.utc).strftime('%d.%m.%Y %H:%M UTC')}</p>",
        ),
        category="test",
        ref_id="email_test",
    )
    return {
        "sent": result is not None,
        "to": to_email,
        "provider": "resend",
        "resend_id": result.get("id") if isinstance(result, dict) else str(result) if result else None,
    }




@router.get("/api/admin/webhooks/history")
async def webhook_history(provider: str = None, limit: int = 50, current_user: dict = Depends(get_current_admin)):
    """Webhook-Events-Historie für Audit."""
    query = {}
    if provider:
        query["provider"] = provider
    events = []
    async for e in S.db.webhook_events.find(query, {"_id": 0}).sort("processed_at", -1).limit(limit):
        events.append(e)
    return {"events": events, "count": len(events)}



# ══════════════════════════════════════════════════════════════
# LEGAL & COMPLIANCE GUARDIAN (P4)
# ══════════════════════════════════════════════════════════════


@router.post("/api/admin/legal/check-outreach")
async def legal_check_outreach(data: dict, current_user: dict = Depends(get_current_admin)):
    """Legal-Gate: Outreach-Prüfung vor Erstansprache."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    return await S.legal_svc.check_outreach(data)



@router.post("/api/admin/legal/check-contract/{contract_id}")
async def legal_check_contract(contract_id: str, current_user: dict = Depends(get_current_admin)):
    """Legal-Gate: Vertragsprüfung vor Versand."""
    contract = await S.db.contracts.find_one({"contract_id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    result = await S.legal_svc.check_contract(contract)
    # Attach result to contract
    await S.db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {"legal_check": result, "updated_at": utcnow()}}
    )
    return result



@router.post("/api/admin/legal/check-communication")
async def legal_check_communication(data: dict, current_user: dict = Depends(get_current_admin)):
    """Legal-Gate: Kommunikationsprüfung."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    return await S.legal_svc.check_communication(data)



@router.post("/api/admin/legal/check-billing/{invoice_id}")
async def legal_check_billing(invoice_id: str, current_user: dict = Depends(get_current_admin)):
    """Legal-Gate: Rechnungsprüfung."""
    invoice = await S.db.invoices.find_one({"invoice_id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(404, "Rechnung nicht gefunden")
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    return await S.legal_svc.check_billing(invoice)



@router.post("/api/admin/legal/risks")
async def add_legal_risk(data: dict, current_user: dict = Depends(get_current_admin)):
    """Risiko hinzufügen."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    entity_type = data.get("entity_type", "")
    entity_id = data.get("entity_id", "")
    risk = data.get("risk", {})
    if not entity_type or not entity_id:
        raise HTTPException(400, "entity_type und entity_id erforderlich")
    return await S.legal_svc.add_risk(entity_type, entity_id, risk, actor=current_user["email"])



@router.patch("/api/admin/legal/risks/{risk_id}/resolve")
async def resolve_legal_risk(risk_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Risiko als gelöst markieren."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    return await S.legal_svc.resolve_risk(risk_id, data.get("resolution", ""), actor=current_user["email"])



@router.get("/api/admin/legal/risks")
async def list_legal_risks(entity_type: str = None, entity_id: str = None, resolved: str = None, current_user: dict = Depends(get_current_admin)):
    """Risiken anzeigen."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    resolved_bool = None
    if resolved == "true":
        resolved_bool = True
    elif resolved == "false":
        resolved_bool = False
    return {"risks": await S.legal_svc.get_risks(entity_type, entity_id, resolved_bool)}



@router.get("/api/admin/legal/audit")
async def legal_audit_log(entity_type: str = None, limit: int = 50, current_user: dict = Depends(get_current_admin)):
    """Legal-Audit-Log."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    return {"audit_log": await S.legal_svc.get_audit_log(entity_type, limit)}



@router.get("/api/admin/legal/compliance")
async def compliance_summary(current_user: dict = Depends(get_current_admin)):
    """Compliance-Gesamtübersicht."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    return await S.legal_svc.compliance_summary()



@router.post("/api/admin/legal/opt-out")
async def register_opt_out(data: dict, current_user: dict = Depends(get_current_admin)):
    """Opt-Out registrieren (Admin)."""
    if not S.legal_svc:
        raise HTTPException(503, "Legal Guardian nicht initialisiert")
    email = data.get("email", "")
    if not email:
        raise HTTPException(400, "email erforderlich")
    return await S.legal_svc.opt_out(email, data.get("reason", "admin_registered"), actor=current_user["email"])



@router.get("/api/admin/commercial/stats")
async def commercial_stats(current_user: dict = Depends(get_current_admin)):
    """Commercial dashboard stats"""
    total_quotes = await S.db.quotes.count_documents({})
    sent_quotes = await S.db.quotes.count_documents({"status": "sent"})
    accepted_quotes = await S.db.quotes.count_documents({"status": "accepted"})
    declined_quotes = await S.db.quotes.count_documents({"status": "declined"})
    total_invoices = await S.db.invoices.count_documents({})
    paid_invoices = await S.db.invoices.count_documents({"payment_status": "paid"})
    pending_invoices = await S.db.invoices.count_documents({"payment_status": "pending"})

    pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$totals.gross"}}},
    ]
    revenue_agg = await S.db.invoices.aggregate(pipeline).to_list(1)
    total_revenue = revenue_agg[0]["total"] if revenue_agg else 0

    return {
        "quotes": {"total": total_quotes, "sent": sent_quotes, "accepted": accepted_quotes, "declined": declined_quotes},
        "invoices": {"total": total_invoices, "paid": paid_invoices, "pending": pending_invoices},
        "revenue": {"total_gross": total_revenue, "currency": "EUR"},
    }


# --- Billing Overview Dashboard ---


@router.get("/api/admin/billing/overview")
async def billing_overview(current_user: dict = Depends(get_current_admin)):
    """Konsolidierte Billing-Übersicht: Quotes + Invoices + Contracts + Revenue."""
    now = utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    total_quotes = await S.db.quotes.count_documents({})
    open_quotes = await S.db.quotes.count_documents({"status": {"$in": ["draft", "sent", "generated"]}})
    accepted_quotes = await S.db.quotes.count_documents({"status": "accepted"})

    total_invoices = await S.db.invoices.count_documents({})
    paid_invoices = await S.db.invoices.count_documents({"payment_status": "paid"})
    pending_invoices = await S.db.invoices.count_documents({"payment_status": {"$in": ["pending", "unpaid", None]}})
    overdue_invoices = await S.db.invoices.count_documents({
        "payment_status": {"$nin": ["paid"]},
        "reminder_count": {"$gte": 1}
    })

    total_contracts = await S.db.contracts.count_documents({})
    active_contracts = await S.db.contracts.count_documents({"status": "accepted"})

    # Revenue aggregation
    rev_pipeline = [{"$match": {"payment_status": "paid"}}, {"$group": {"_id": None, "total": {"$sum": "$total_eur"}}}]
    rev_agg = await S.db.invoices.aggregate(rev_pipeline).to_list(1)
    total_revenue = rev_agg[0]["total"] if rev_agg else 0

    open_pipeline = [{"$match": {"payment_status": {"$nin": ["paid"]}}}, {"$group": {"_id": None, "total": {"$sum": "$total_eur"}}}]
    open_agg = await S.db.invoices.aggregate(open_pipeline).to_list(1)
    open_revenue = open_agg[0]["total"] if open_agg else 0

    # Monthly revenue
    month_rev_pipeline = [
        {"$match": {"payment_status": "paid", "paid_at": {"$gte": month_start.isoformat()}}},
        {"$group": {"_id": None, "total": {"$sum": "$total_eur"}}},
    ]
    month_agg = await S.db.invoices.aggregate(month_rev_pipeline).to_list(1)
    monthly_revenue = month_agg[0]["total"] if month_agg else 0

    # Recent activity
    recent_quotes = []
    async for q in S.db.quotes.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).limit(5):
        recent_quotes.append({
            "quote_id": q.get("quote_id"),
            "quote_number": q.get("quote_number"),
            "tier": q.get("tier"),
            "status": q.get("status"),
            "customer": q.get("customer", {}).get("name", ""),
            "total": q.get("calculation", {}).get("total_contract_eur", 0),
        })

    recent_invoices = []
    async for inv in S.db.invoices.find({}, {"_id": 0, "history": 0}).sort("created_at", -1).limit(5):
        recent_invoices.append({
            "invoice_id": inv.get("invoice_id"),
            "invoice_number": inv.get("invoice_number"),
            "status": inv.get("status"),
            "payment_status": inv.get("payment_status"),
            "total_eur": inv.get("total_eur", 0),
            "customer": inv.get("customer", {}).get("name", ""),
        })

    return {
        "summary": {
            "quotes": {"total": total_quotes, "open": open_quotes, "accepted": accepted_quotes},
            "invoices": {"total": total_invoices, "paid": paid_invoices, "pending": pending_invoices, "overdue": overdue_invoices},
            "contracts": {"total": total_contracts, "active": active_contracts},
        },
        "revenue": {
            "total_paid_eur": round(total_revenue, 2),
            "total_open_eur": round(open_revenue, 2),
            "monthly_eur": round(monthly_revenue, 2),
            "currency": "EUR",
        },
        "recent_quotes": recent_quotes,
        "recent_invoices": recent_invoices,
        "timestamp": now.isoformat(),
    }


# --- Admin: Activity Timeline ---


@router.get("/api/admin/billing/status/{email}")
async def billing_status(email: str, current_user: dict = Depends(get_current_admin)):
    """Gesamter Billing-Status für einen Kontakt."""
    result = await S.billing_svc.get_billing_status(email)
    return result



@router.post("/api/admin/billing/sync-quote/{quote_id}")
async def billing_sync_quote(quote_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Quote-Status synchronisieren."""
    new_status = data.get("status", "")
    if not new_status:
        raise HTTPException(400, "Status erforderlich")
    result = await S.billing_svc.sync_quote_status(quote_id, new_status, by=current_user["email"])
    return result



@router.post("/api/admin/billing/sync-invoice/{invoice_id}")
async def billing_sync_invoice(invoice_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Invoice-Status synchronisieren."""
    new_status = data.get("status", "")
    if not new_status:
        raise HTTPException(400, "Status erforderlich")
    result = await S.billing_svc.sync_invoice_status(invoice_id, new_status, by=current_user["email"])
    return result


# ══════════════════════════════════════════════════════════════
# OUTBOUND LEAD MACHINE ENDPOINTS
# ══════════════════════════════════════════════════════════════

