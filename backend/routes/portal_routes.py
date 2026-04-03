"""NeXifyAI — Portal Routes"""
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from routes.shared import S
from routes.shared import (
    get_current_admin,
    get_current_customer,
    log_audit,
    _log_event,
    send_email,
    email_template,
    _build_customer_memory,
    logger,
)
from domain import create_timeline_event, utcnow
from commercial import COMPANY_DATA as COMM_COMPANY, verify_access_token

router = APIRouter(tags=["portal"])

PAYMENT_STATUS_MAP = {
    "pending": {"label": "Ausstehend", "severity": "warning"},
    "paid": {"label": "Bezahlt", "severity": "success"},
    "overdue": {"label": "Überfällig", "severity": "error"},
    "partial": {"label": "Teilbezahlt", "severity": "warning"},
    "cancelled": {"label": "Storniert", "severity": "neutral"},
    "refunded": {"label": "Erstattet", "severity": "neutral"},
}

REMINDER_LEVEL_MAP = {
    0: "Keine",
    1: "Zahlungserinnerung",
    2: "1. Mahnung",
    3: "2. Mahnung",
}

@router.get("/api/customer/dashboard")
async def customer_dashboard(user = Depends(get_current_customer)):
    """Kunden-Dashboard — alle Daten JWT-authentifiziert."""
    email = user["email"]
    
    # Quotes
    quotes = []
    async for q in S.db.quotes.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        quotes.append({
            "quote_id": q["quote_id"],
            "quote_number": q.get("quote_number", ""),
            "status": q.get("status", ""),
            "tier": q.get("tier", ""),
            "calculation": q.get("calculation", {}),
            "discount": q.get("discount", {}),
            "special_items": q.get("special_items", []),
            "created_at": str(q.get("created_at", "")),
        })
    
    # Invoices
    invoices = []
    async for inv in S.db.invoices.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        invoices.append({
            "invoice_id": inv["invoice_id"],
            "invoice_number": inv.get("invoice_number", ""),
            "status": inv.get("status", ""),
            "payment_status": inv.get("payment_status", ""),
            "total_eur": inv.get("totals", {}).get("gross", 0),
            "created_at": str(inv.get("created_at", "")),
        })
    
    # Bookings
    bookings = []
    async for bk in S.db.bookings.find({"email": email}, {"_id": 0}).sort("created_at", -1).limit(10):
        bookings.append({
            "booking_id": bk.get("booking_id", ""),
            "date": bk.get("date", ""),
            "time": bk.get("time", ""),
            "status": bk.get("status", ""),
            "thema": bk.get("thema", ""),
        })
    
    # Communication
    chat_summaries = []
    async for sess in S.db.chat_sessions.find({"customer_email": email}, {"_id": 0, "messages": {"$slice": -3}}).sort("created_at", -1).limit(5):
        msgs = sess.get("messages", [])
        chat_summaries.append({
            "type": "chat", "date": str(sess.get("created_at", "")),
            "messages": [{"role": m["role"], "content": m["content"][:150]} for m in msgs],
        })
    
    unified_convos = []
    contact = user["contact"]
    if contact:
        cid = contact.get("contact_id")
        async for conv in S.db.conversations.find({"contact_id": cid}, {"_id": 0}).sort("last_message_at", -1).limit(10):
            last_msgs = []
            async for m in S.db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0}).sort("timestamp", -1).limit(3):
                last_msgs.append({
                    "direction": m.get("direction"), "channel": m.get("channel"),
                    "content": m.get("content", "")[:200], "timestamp": str(m.get("timestamp", "")),
                })
            unified_convos.append({
                "type": "conversation", "channels": conv.get("channels", []),
                "status": conv.get("status"), "message_count": conv.get("message_count", 0),
                "date": str(conv.get("last_message_at", "")), "messages": last_msgs,
            })
    
    # Timeline
    timeline_items = []
    async for evt in S.db.timeline_events.find(
        {"$or": [{"actor": email}, {"details.email": email}, {"details.customer_email": email}]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20):
        timeline_items.append({
            "event_type": evt.get("event_type"), "action": evt.get("action"),
            "channel": evt.get("channel"), "timestamp": str(evt.get("timestamp", "")),
            "details": {k: v for k, v in evt.get("details", {}).items() if k not in ("_id",)},
        })
    
    return {
        "email": email,
        "customer_name": f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
        "quotes": quotes,
        "invoices": invoices,
        "bookings": bookings,
        "communications": chat_summaries + unified_convos,
        "timeline": timeline_items,
    }


@router.get("/api/portal/quote/{quote_id}")
async def portal_get_quote(quote_id: str, token: str):
    """Customer access: view quote via magic link"""
    link = await S.db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link:
        raise HTTPException(403, "Zugangslink ungültig")
    if not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink abgelaufen")

    quote = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0, "history": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")

    await _log_event(S.db, "offer_opened", quote_id, link.get("customer_email", "customer"))
    await S.db.quotes.update_one(
        {"quote_id": quote_id, "status": "sent"},
        {"$set": {"status": "opened"},
         "$push": {"history": {"action": "opened", "at": datetime.now(timezone.utc).isoformat(), "by": "customer"}}},
    )

    return {
        "quote": quote,
        "company": {
            "name": COMM_COMPANY["name"],
            "brand": COMM_COMPANY["brand"],
            "phone": COMM_COMPANY["phone"],
            "email": COMM_COMPANY["email"],
        },
    }



@router.post("/api/portal/quote/{quote_id}/accept")
async def portal_accept_quote(quote_id: str, token: str, request: Request):
    """Customer accepts the quote — triggers invoice + payment"""
    link = await S.db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")

    quote = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    if quote.get("status") in ("accepted", "declined"):
        raise HTTPException(400, f"Angebot bereits {quote['status']}")

    now = datetime.now(timezone.utc)
    calc = quote.get("calculation", {})

    audit = {
        "action": "offer_accepted",
        "quote_id": quote_id,
        "quote_number": quote.get("quote_number"),
        "customer_email": quote["customer"]["email"],
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "timestamp": now.isoformat(),
    }
    await S.db.audit_log.insert_one(audit)

    invoice_number = await get_next_number(S.db, "invoice")
    due_date = (now + timedelta(days=14)).strftime("%d.%m.%Y")
    upfront_net = calc.get("upfront_eur", 0)
    vat = round(upfront_net * VAT_RATE / 100, 2)
    gross = round(upfront_net + vat, 2)

    tariff = get_tariff(calc.get("tier", "starter"))
    payment_product = tariff.get("payment_products", {}).get("activation", {})

    invoice = {
        "invoice_id": f"inv_{secrets.token_hex(8)}",
        "invoice_number": invoice_number,
        "type": "deposit",
        "product_code": payment_product.get("product_code", ""),
        "status": "created",
        "quote_id": quote_id,
        "customer": quote["customer"],
        "items": [{
            "description": payment_product.get("description", f"Aktivierungsanzahlung (30 %) — {calc.get('tier_name', '')}"),
            "amount_net": upfront_net,
        }],
        "totals": {
            "net": upfront_net,
            "vat_rate": VAT_RATE,
            "vat": vat,
            "gross": gross,
        },
        "date": now.strftime("%d.%m.%Y"),
        "due_date": due_date,
        "payment_reference": invoice_number,
        "payment_status": "pending",
        "revolut_order_id": None,
        "created_at": now.isoformat(),
        "history": [{"action": "created", "at": now.isoformat(), "by": "customer_acceptance"}],
    }

    pdf_bytes = generate_invoice_pdf(invoice)
    await S.db.invoices.insert_one(invoice)
    invoice.pop("_id", None)

    await S.db.documents.insert_one({
        "doc_id": f"doc_{secrets.token_hex(8)}",
        "type": "invoice",
        "ref_id": invoice["invoice_id"],
        "number": invoice_number,
        "pdf_data": pdf_bytes,
        "created_at": now.isoformat(),
    })

    await S.db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "accepted", "accepted_at": now.isoformat(), "invoice_id": invoice["invoice_id"]},
         "$push": {"history": {"action": "accepted", "at": now.isoformat(), "by": "customer"}}},
    )

    amount_cents = int(gross * 100)
    revolut_result = await create_revolut_order(
        amount_cents=amount_cents,
        currency="EUR",
        customer_email=quote["customer"]["email"],
        description=f"NeXifyAI Aktivierungsanzahlung — {calc.get('tier_name', '')} ({invoice_number})",
        merchant_order_id=invoice["invoice_id"],
    )

    checkout_url = None
    if revolut_result.get("order_id"):
        checkout_url = revolut_result.get("checkout_url")
        await S.db.invoices.update_one(
            {"invoice_id": invoice["invoice_id"]},
            {"$set": {
                "revolut_order_id": revolut_result["order_id"],
                "revolut_token": revolut_result.get("token"),
                "checkout_url": checkout_url,
            }},
        )

    if S.RESEND_API_KEY:
        try:
            import base64
            pdf_b64 = base64.b64encode(pdf_bytes).decode()
            payment_cta = ""
            if checkout_url:
                payment_cta = f'<a href="{checkout_url}" style="display:inline-block;background:#ffb599;color:#5a1c00;padding:14px 28px;font-weight:700;text-decoration:none;margin:24px 0;">Jetzt online bezahlen</a>'

            import asyncio
            asyncio.create_task(send_email(
                [quote["customer"]["email"]],
                f"Angebotsannahme bestätigt — Ihre Anzahlungsrechnung {invoice_number}",
                email_template(
                    "Angebotsannahme bestätigt",
                    f'''<h1 style="color:#fff;font-size:22px;margin:0 0 16px;">Vielen Dank für Ihre Beauftragung</h1>
                    <p>Ihr Angebot <strong>{quote.get("quote_number", "")}</strong> wurde angenommen.</p>
                    <div style="background:#252a32;padding:20px;margin:20px 0;border-left:3px solid #ffb599;">
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">RECHNUNG</p>
                    <p style="margin:0 0 8px;color:#fff;font-weight:600;">{invoice_number}</p>
                    <p style="margin:0 0 4px;font-size:12px;color:#8f9095;">BETRAG (BRUTTO)</p>
                    <p style="margin:0;color:#ffb599;font-weight:600;">{gross:,.2f} EUR</p>
                    </div>
                    {payment_cta}
                    <p>Alternativ per Banküberweisung:<br/>
                    IBAN: {COMM_COMPANY["bank"]["iban"]}<br/>
                    BIC: {COMM_COMPANY["bank"]["bic"]}<br/>
                    Verwendungszweck: {invoice_number}</p>''',
                ),
                category="invoice",
                ref_id=invoice_number,
            ))
        except Exception as e:
            logger.error(f"Acceptance email error: {e}")

    await _log_event(S.db, "offer_accepted", quote_id, quote["customer"]["email"])

    return {
        "accepted": True,
        "invoice_number": invoice_number,
        "amount_gross": gross,
        "due_date": due_date,
        "checkout_url": checkout_url,
        "bank_transfer": {
            "iban": COMM_COMPANY["bank"]["iban"],
            "bic": COMM_COMPANY["bank"]["bic"],
            "reference": invoice_number,
        },
    }



@router.post("/api/portal/quote/{quote_id}/decline")
async def portal_decline_quote(quote_id: str, token: str, request: Request):
    """Customer declines the quote"""
    link = await S.db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    reason = body.get("reason", "")

    await S.db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "declined", "declined_at": now.isoformat(), "decline_reason": reason},
         "$push": {"history": {"action": "declined", "at": now.isoformat(), "by": "customer", "reason": reason}}},
    )
    await _log_event(S.db, "offer_declined", quote_id, "customer")
    return {"declined": True}



@router.post("/api/portal/quote/{quote_id}/revision")
async def portal_request_revision(quote_id: str, token: str, request: Request):
    """Customer requests a revision"""
    link = await S.db.access_links.find_one({
        "token_hash": hashlib.sha256(token.encode()).hexdigest(),
        "quote_id": quote_id,
    })
    if not link or not verify_access_token(token, link["token_hash"], link["expires_at"]):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    now = datetime.now(timezone.utc)
    feedback = body.get("feedback", "")

    await S.db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "revision_requested", "revision_feedback": feedback},
         "$push": {"history": {"action": "revision_requested", "at": now.isoformat(), "by": "customer", "feedback": feedback}}},
    )
    await _log_event(S.db, "offer_revision_requested", quote_id, "customer")

    if S.RESEND_API_KEY:
        quote = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
        if quote:
            import asyncio
            asyncio.create_task(send_email(
                S.NOTIFICATION_EMAILS,
                f"[NeXifyAI] Änderungswunsch: {quote.get('quote_number', '')}",
                email_template("Änderungswunsch",
                    f'''<h1 style="color:#fff;font-size:20px;">Änderungswunsch zum Angebot</h1>
                    <p>Angebot: {quote.get("quote_number","")}</p>
                    <p>Kunde: {quote["customer"].get("name","")}</p>
                    <div style="background:#252a32;padding:16px;margin:16px 0;color:#c5c6cb;white-space:pre-wrap;">{feedback}</div>'''
                ),
            ))

    return {"revision_requested": True}


# --- AI Chat Discovery → Offer Generation ---


@router.get("/api/portal/customer/{token}")
async def customer_portal(token: str):
    """Customer portal via magic link token — shows all customer data."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await S.db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    
    email = link.get("customer_email", "").lower()
    if not email:
        raise HTTPException(400, "Kein Kundenkonto verknüpft")
    
    # Quotes
    quotes = []
    async for q in S.db.quotes.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        quotes.append({
            "quote_id": q["quote_id"],
            "quote_number": q.get("quote_number", ""),
            "status": q.get("status", ""),
            "tier": q.get("tier", ""),
            "calculation": q.get("calculation", {}),
            "created_at": str(q.get("created_at", "")),
        })
    
    # Invoices
    invoices = []
    async for inv in S.db.invoices.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        invoices.append({
            "invoice_id": inv["invoice_id"],
            "invoice_number": inv.get("invoice_number", ""),
            "status": inv.get("status", ""),
            "payment_status": inv.get("payment_status", ""),
            "total_eur": inv.get("totals", {}).get("gross", 0),
            "created_at": str(inv.get("created_at", "")),
        })
    
    # Bookings
    bookings = []
    async for bk in S.db.bookings.find({"email": email}, {"_id": 0}).sort("created_at", -1).limit(10):
        bookings.append({
            "booking_id": bk.get("booking_id", ""),
            "date": bk.get("date", ""),
            "time": bk.get("time", ""),
            "status": bk.get("status", ""),
        })
    
    # Communication history (recent chat summaries + unified conversations)
    chat_summaries = []
    async for sess in S.db.chat_sessions.find({"customer_email": email}, {"_id": 0, "messages": {"$slice": -3}}).sort("created_at", -1).limit(5):
        msgs = sess.get("messages", [])
        chat_summaries.append({
            "type": "chat",
            "date": str(sess.get("created_at", "")),
            "messages": [{"role": m["role"], "content": m["content"][:150]} for m in msgs],
        })
    
    # Unified conversations (WhatsApp, Email, Portal)
    contact = await S.db.contacts.find_one({"email": email}, {"_id": 0})
    unified_convos = []
    if contact:
        cid = contact.get("contact_id")
        async for conv in S.db.conversations.find({"contact_id": cid}, {"_id": 0}).sort("last_message_at", -1).limit(10):
            last_msgs = []
            async for m in S.db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0}).sort("timestamp", -1).limit(3):
                last_msgs.append({
                    "direction": m.get("direction"),
                    "channel": m.get("channel"),
                    "content": m.get("content", "")[:200],
                    "timestamp": str(m.get("timestamp", "")),
                })
            unified_convos.append({
                "type": "conversation",
                "channels": conv.get("channels", []),
                "status": conv.get("status"),
                "message_count": conv.get("message_count", 0),
                "date": str(conv.get("last_message_at", "")),
                "messages": last_msgs,
            })
    
    # Timeline events for this customer
    timeline_items = []
    async for evt in S.db.timeline_events.find(
        {"$or": [{"actor": email}, {"details.email": email}, {"details.customer_email": email}]},
        {"_id": 0}
    ).sort("timestamp", -1).limit(20):
        timeline_items.append({
            "event_type": evt.get("event_type"),
            "action": evt.get("action"),
            "channel": evt.get("channel"),
            "timestamp": str(evt.get("timestamp", "")),
            "details": {k: v for k, v in evt.get("details", {}).items() if k not in ("_id",)},
        })
    
    return {
        "email": email,
        "customer_name": link.get("customer_name", ""),
        "quotes": quotes,
        "invoices": invoices,
        "bookings": bookings,
        "communications": chat_summaries + unified_convos,
        "timeline": timeline_items,
    }



@router.post("/api/portal/quote/{quote_id}/accept")
async def portal_accept_quote(quote_id: str, token: str = None):
    """Customer accepts a quote via portal."""
    if not token:
        raise HTTPException(401, "Zugangstoken fehlt")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await S.db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    email = link.get("customer_email", "").lower()
    quote = await S.db.quotes.find_one({"quote_id": quote_id, "customer.email": email}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    if quote.get("status") not in ("sent", "opened"):
        raise HTTPException(400, f"Angebot kann im Status '{quote.get('status')}' nicht angenommen werden")
    await S.db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "accepted", "accepted_at": utcnow(), "updated_at": utcnow()}}
    )
    evt = create_timeline_event("quote", quote_id, "quote_accepted",
                                actor=email, actor_type="customer",
                                details={"quote_number": quote.get("quote_number")})
    await S.db.timeline_events.insert_one(evt)
    return {"status": "accepted", "quote_id": quote_id}



@router.post("/api/portal/quote/{quote_id}/decline")
async def portal_decline_quote(quote_id: str, data: dict = None, token: str = None):
    """Customer declines a quote via portal."""
    if not token:
        raise HTTPException(401, "Zugangstoken fehlt")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await S.db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    email = link.get("customer_email", "").lower()
    quote = await S.db.quotes.find_one({"quote_id": quote_id, "customer.email": email}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    reason = (data or {}).get("reason", "")
    await S.db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "declined", "decline_reason": reason, "updated_at": utcnow()}}
    )
    evt = create_timeline_event("quote", quote_id, "quote_declined",
                                actor=email, actor_type="customer",
                                details={"quote_number": quote.get("quote_number"), "reason": reason[:200]})
    await S.db.timeline_events.insert_one(evt)
    return {"status": "declined", "quote_id": quote_id}



@router.post("/api/portal/quote/{quote_id}/revision")
async def portal_request_revision(quote_id: str, data: dict, token: str = None):
    """Customer requests a quote revision via portal."""
    if not token:
        raise HTTPException(401, "Zugangstoken fehlt")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await S.db.access_links.find_one({"token_hash": token_hash}, {"_id": 0})
    if not link or link.get("expires_at", datetime.min.replace(tzinfo=timezone.utc)) < datetime.now(timezone.utc):
        raise HTTPException(403, "Zugangslink ungültig oder abgelaufen")
    email = link.get("customer_email", "").lower()
    quote = await S.db.quotes.find_one({"quote_id": quote_id, "customer.email": email}, {"_id": 0})
    if not quote:
        raise HTTPException(404, "Angebot nicht gefunden")
    notes = data.get("notes", "")
    await S.db.quotes.update_one(
        {"quote_id": quote_id},
        {"$set": {"status": "revision_requested", "revision_notes": notes, "updated_at": utcnow()}}
    )
    evt = create_timeline_event("quote", quote_id, "revision_requested",
                                actor=email, actor_type="customer",
                                details={"notes": notes[:200]})
    await S.db.timeline_events.insert_one(evt)
    return {"status": "revision_requested", "quote_id": quote_id}


# ══════════════════════════════════════════════════════════════
# UNIFIED COMMUNICATION API
# ══════════════════════════════════════════════════════════════


@router.get("/api/customer/finance")
async def customer_finance(current_user: dict = Depends(get_current_customer)):
    """Vollständige Finance-Ansicht: Rechnungen, Zahlungsstatus, Verträge, Angebote, Statuslogik."""
    email = current_user["email"]
    now = utcnow()

    # --- Invoices (full detail) ---
    invoices = []
    total_outstanding = 0
    total_paid = 0
    async for inv in S.db.invoices.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1):
        totals = inv.get("totals", {})
        gross = totals.get("gross", inv.get("total_eur", 0))
        net = totals.get("net", inv.get("amount_netto_eur", 0))
        vat = totals.get("vat", inv.get("tax_eur", 0))
        ps = inv.get("payment_status", "pending")
        reminder_count = inv.get("reminder_count", 0)

        # Check overdue
        due_str = inv.get("due_date", "")
        is_overdue = False
        if due_str and ps not in ("paid", "cancelled", "refunded"):
            try:
                due_dt = datetime.strptime(due_str, "%d.%m.%Y").replace(tzinfo=timezone.utc)
                is_overdue = now > due_dt
            except Exception:
                pass

        effective_status = "overdue" if is_overdue and ps == "pending" else ps
        status_info = PAYMENT_STATUS_MAP.get(effective_status, {"label": ps, "severity": "neutral"})

        if effective_status in ("pending", "overdue"):
            total_outstanding += gross
        elif effective_status == "paid":
            total_paid += gross

        has_pdf = bool(await S.db.documents.find_one({"ref_id": inv.get("invoice_id"), "type": "invoice"}, {"_id": 1}))

        inv_data = {
            "invoice_id": inv.get("invoice_id"),
            "invoice_number": inv.get("invoice_number", ""),
            "type": inv.get("type", "standard"),
            "status": inv.get("status", ""),
            "payment_status": effective_status,
            "payment_status_label": status_info["label"],
            "payment_status_severity": status_info["severity"],
            "amount_net": net,
            "amount_vat": vat,
            "amount_gross": gross,
            "vat_rate": totals.get("vat_rate", inv.get("tax_rate", 19)),
            "date": inv.get("date", ""),
            "due_date": due_str,
            "is_overdue": is_overdue,
            "description": inv.get("description", ""),
            "items": inv.get("items", []),
            "payment_reference": inv.get("payment_reference", inv.get("invoice_number", "")),
            "checkout_url": inv.get("checkout_url"),
            "revolut_order_id": inv.get("revolut_order_id"),
            "reminder_count": reminder_count,
            "reminder_level": REMINDER_LEVEL_MAP.get(min(reminder_count, 3), f"Stufe {reminder_count}"),
            "last_reminder_at": inv.get("last_reminder_at"),
            "quote_id": inv.get("quote_id", ""),
            "has_pdf": has_pdf,
            "pdf_url": f"/api/documents/invoice/{inv.get('invoice_id')}/pdf" if has_pdf else None,
            "created_at": str(inv.get("created_at", "")),
        }
        invoices.append(inv_data)

    # --- Quotes (summary for finance context) ---
    quotes_summary = []
    async for q in S.db.quotes.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1).limit(20):
        calc = q.get("calculation", {})
        quotes_summary.append({
            "quote_id": q.get("quote_id"),
            "quote_number": q.get("quote_number", ""),
            "status": q.get("status", ""),
            "tier": q.get("tier", ""),
            "tier_name": calc.get("tier_name", ""),
            "total_contract_eur": calc.get("total_contract_eur", 0),
            "upfront_eur": calc.get("upfront_eur", 0),
            "monthly_eur": calc.get("monthly_eur", 0),
            "created_at": str(q.get("created_at", "")),
        })

    # --- Contracts (finance-relevant fields) ---
    contracts_summary = []
    async for c in S.db.contracts.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1):
        contracts_summary.append({
            "contract_id": c.get("contract_id"),
            "contract_number": c.get("contract_number", ""),
            "status": c.get("status", ""),
            "contract_type": c.get("contract_type", ""),
            "tier": c.get("tier", ""),
            "total_value": c.get("total_value", 0),
            "monthly_value": c.get("monthly_value", 0),
            "created_at": str(c.get("created_at", "")),
            "accepted_at": str(c.get("accepted_at", "")) if c.get("accepted_at") else None,
        })

    # --- Bank transfer info ---
    bank_info = {
        "iban": COMM_COMPANY.get("bank", {}).get("iban", ""),
        "bic": COMM_COMPANY.get("bank", {}).get("bic", ""),
        "bank_name": COMM_COMPANY.get("bank", {}).get("bank", ""),
        "account_holder": COMM_COMPANY.get("name", "NeXify Automate"),
    }

    return {
        "summary": {
            "total_invoices": len(invoices),
            "total_outstanding_eur": round(total_outstanding, 2),
            "total_paid_eur": round(total_paid, 2),
            "open_invoices": sum(1 for i in invoices if i["payment_status"] in ("pending", "overdue")),
            "overdue_invoices": sum(1 for i in invoices if i["is_overdue"]),
        },
        "invoices": invoices,
        "quotes": quotes_summary,
        "contracts": contracts_summary,
        "bank_transfer_info": bank_info,
    }




# ══════════════════════════════════════════════════════════════
# MONITORING / SYSTEM STATUS (P7)
# ══════════════════════════════════════════════════════════════

