"""NeXifyAI — Contract OS Routes"""
import os
import json
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Request
from routes.shared import S
from routes.shared import (
    get_current_admin,
    get_current_customer,
    send_email,
    email_template,
    archive_pdf_to_storage,
    logger,
)
from domain import (
    create_contract, create_contract_appendix, create_contract_evidence,
    create_timeline_event, ContractStatus, utcnow,
    LEGAL_MODULES, APPENDIX_TYPE_LABELS,
)
from commercial import (
    calc_contract, get_next_number, generate_contract_pdf,
    generate_access_token,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["contract"])

def _compute_doc_hash(contract: dict) -> str:
    """Deterministischer Hash über Vertragsinhalt für Evidenzpaket."""
    import hashlib as _hl
    payload = json.dumps({
        "contract_id": contract.get("contract_id"),
        "version": contract.get("version"),
        "tier_key": contract.get("tier_key"),
        "calculation": contract.get("calculation"),
        "appendices": contract.get("appendices", []),
        "customer": contract.get("customer"),
    }, sort_keys=True, default=str)
    return _hl.sha256(payload.encode()).hexdigest()



@router.post("/api/admin/contracts")
async def create_contract_endpoint(data: dict, current_user: dict = Depends(get_current_admin)):
    """Vertrag erstellen (aus Quote oder frei)."""
    customer = data.get("customer", {})
    quote_id = data.get("quote_id", "")
    tier_key = data.get("tier_key", "")
    calc = data.get("calculation", {})

    # Auto-populate from quote if provided
    if quote_id and not customer.get("email"):
        quote = await S.db.quotes.find_one({"quote_id": quote_id}, {"_id": 0})
        if quote:
            customer = customer or quote.get("customer", {})
            if not tier_key:
                tier_key = quote.get("tier", "")
            if not calc:
                calc = quote.get("calculation", {})

    if not customer.get("email"):
        raise HTTPException(400, "customer.email erforderlich")

    contract_type = data.get("contract_type", "standard")
    # Auto-calculate if tier given
    if tier_key and not calc:
        from commercial import calc_contract as cc
        calc = cc(tier_key) or {}
    # Number
    from commercial import get_next_number as gnn
    cnum = await gnn(S.db, "contract")
    contract = create_contract(
        customer, tier_key, contract_type,
        contract_number=cnum,
        quote_id=data.get("quote_id", ""),
        project_id=data.get("project_id", ""),
        calculation=calc,
        notes=data.get("notes", ""),
        valid_until=data.get("valid_until", ""),
        created_by=current_user["email"],
    )
    await S.db.contracts.insert_one({**contract})
    # Timeline
    await S.db.timeline_events.insert_one(create_timeline_event(
        "contract", contract["contract_id"], "contract_created",
        actor=current_user["email"], actor_type="admin",
        details={"number": cnum, "type": contract_type, "tier": tier_key},
    ))
    if S.memory_svc:
        await S.memory_svc.write(
            customer.get("email", ""), f"Vertrag erstellt: {cnum} ({contract_type})",
            agent_id="contract_agent", category="contract",
            source="admin", source_ref=contract["contract_id"],
        )
    contract.pop("_id", None)
    return contract



@router.get("/api/admin/contracts")
async def list_contracts(
    status: str = None, customer_email: str = None,
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Verträge auflisten."""
    query = {}
    if status:
        query["status"] = status
    if customer_email:
        query["customer.email"] = customer_email.lower()
    contracts = []
    async for c in S.db.contracts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit):
        if hasattr(c.get("created_at"), "isoformat"):
            c["created_at"] = c["created_at"].isoformat()
        if hasattr(c.get("updated_at"), "isoformat"):
            c["updated_at"] = c["updated_at"].isoformat()
        contracts.append(c)
    total = await S.db.contracts.count_documents(query)
    return {"contracts": contracts, "total": total}



@router.get("/api/admin/contracts/{contract_id}")
async def get_contract(contract_id: str, current_user: dict = Depends(get_current_admin)):
    """Vertrags-Detail."""
    contract = await S.db.contracts.find_one({"contract_id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    # Load appendices
    appendices = []
    async for a in S.db.contract_appendices.find({"contract_id": contract_id}, {"_id": 0}).sort("created_at", 1):
        if hasattr(a.get("created_at"), "isoformat"):
            a["created_at"] = a["created_at"].isoformat()
        appendices.append(a)
    contract["appendices_detail"] = appendices
    # Evidence
    evidence_list = []
    async for e in S.db.contract_evidence.find({"contract_id": contract_id}, {"_id": 0}).sort("timestamp", -1):
        evidence_list.append(e)
    contract["evidence_list"] = evidence_list
    contract["document_hash"] = _compute_doc_hash(contract)
    contract["legal_module_definitions"] = LEGAL_MODULES
    contract["appendix_type_labels"] = APPENDIX_TYPE_LABELS
    # PDF status
    has_pdf = bool(await S.db.documents.find_one({"ref_id": contract_id, "type": "contract"}, {"_id": 1}))
    contract["has_pdf"] = has_pdf
    contract["pdf_url"] = f"/api/documents/contract/{contract_id}/pdf" if has_pdf else None
    for dt_field in ("created_at", "updated_at"):
        if hasattr(contract.get(dt_field), "isoformat"):
            contract[dt_field] = contract[dt_field].isoformat()
    return contract



@router.patch("/api/admin/contracts/{contract_id}")
async def update_contract(contract_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Vertrag aktualisieren."""
    allowed = {"status", "notes", "valid_until", "tier_key", "calculation", "contract_type", "project_id"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "Keine gültigen Felder")
    updates["updated_at"] = utcnow()
    old = await S.db.contracts.find_one({"contract_id": contract_id}, {"_id": 0, "status": 1, "customer": 1, "version": 1})
    if not old:
        raise HTTPException(404, "Vertrag nicht gefunden")
    # Version increment on status change
    if "status" in updates and updates["status"] != old.get("status"):
        new_version = old.get("version", 1) + 1
        updates["version"] = new_version
        # Save version to history
        await S.db.contracts.update_one(
            {"contract_id": contract_id},
            {"$push": {"versions_history": {"version": old.get("version", 1), "status": old.get("status"), "timestamp": utcnow().isoformat(), "actor": current_user["email"]}}}
        )
        await S.db.timeline_events.insert_one(create_timeline_event(
            "contract", contract_id, "contract_status_changed",
            actor=current_user["email"], actor_type="admin",
            details={"old": old.get("status"), "new": updates["status"], "version": new_version},
        ))
    await S.db.contracts.update_one({"contract_id": contract_id}, {"$set": updates})
    return {"updated": True}



@router.post("/api/admin/contracts/{contract_id}/appendices")
async def add_contract_appendix(contract_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Modulare Anlage hinzufügen."""
    appendix_type = data.get("appendix_type", "")
    title = data.get("title", "")
    content = data.get("content", {})
    if not appendix_type or not title:
        raise HTTPException(400, "appendix_type und title erforderlich")
    contract = await S.db.contracts.find_one({"contract_id": contract_id}, {"_id": 0, "contract_id": 1})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    appendix = create_contract_appendix(
        contract_id, appendix_type, title, content,
        pricing=data.get("pricing", {}),
        status=data.get("status", "draft"),
    )
    await S.db.contract_appendices.insert_one({**appendix})
    # Track in contract
    await S.db.contracts.update_one(
        {"contract_id": contract_id},
        {"$push": {"appendices": appendix["appendix_id"]}, "$set": {"updated_at": utcnow()}}
    )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "contract", contract_id, "appendix_added",
        actor=current_user["email"], actor_type="admin",
        details={"appendix_type": appendix_type, "title": title},
    ))
    appendix.pop("_id", None)
    for dt_field in ("created_at", "updated_at"):
        if hasattr(appendix.get(dt_field), "isoformat"):
            appendix[dt_field] = appendix[dt_field].isoformat()
    return appendix



@router.post("/api/admin/contracts/{contract_id}/send")
async def send_contract(contract_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Vertrag an Kunden senden — mit Legal-Gate."""
    contract = await S.db.contracts.find_one({"contract_id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    email = contract.get("customer", {}).get("email", "")
    if not email:
        raise HTTPException(400, "Keine Kunden-E-Mail")
    # Legal Gate
    if S.legal_svc:
        legal_result = await S.legal_svc.check_contract(contract)
        await S.db.contracts.update_one({"contract_id": contract_id}, {"$set": {"legal_check": legal_result}})
        if legal_result.get("risk_level") in ("high", "critical"):
            return {"sent": False, "gate_blocked": True, "legal_check": legal_result, "message": "Legal-Gate: Vertrag kann aufgrund offener Rechtsrisiken nicht versendet werden."}
    # Update status to sent
    await S.db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {"status": ContractStatus.SENT.value, "updated_at": utcnow(), "sent_at": utcnow().isoformat()}}
    )
    # Magic link for contract access
    from commercial import generate_access_token as gat
    tok = gat(email, "contract")
    await S.db.access_links.insert_one({
        "token_hash": tok["token_hash"], "customer_email": email,
        "contract_id": contract_id, "document_type": "contract",
        "expires_at": tok["expires_at"], "created_at": tok["created_at"],
    })
    base_url = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
    contract_link = f"{base_url}/vertrag?token={tok['token']}&cid={contract_id}"
    # Email
    if S.RESEND_API_KEY:
        try:
            html = email_template(
                "Ihr Vertrag — NeXifyAI",
                f"<p>Guten Tag {contract.get('customer', {}).get('name', '')},</p>"
                f"<p>Ihr Vertrag <strong>{contract.get('contract_number', '')}</strong> liegt zur Prüfung und Annahme bereit.</p>"
                f"<p>Bitte klicken Sie auf den Button, um den Vertrag zu prüfen und digital zu unterschreiben.</p>",
                contract_link,
                "Vertrag prüfen"
            )
            await send_email([email], f"Ihr Vertrag {contract.get('contract_number', '')} — NeXifyAI", html, category="contract", ref_id=contract_id)
        except Exception as e:
            logger.error(f"Contract email error: {e}")
    await S.db.timeline_events.insert_one(create_timeline_event(
        "contract", contract_id, "contract_sent",
        actor=current_user["email"], actor_type="admin",
        details={"email": email, "number": contract.get("contract_number", "")},
    ))
    return {"sent": True, "contract_link": contract_link}



@router.get("/api/admin/contracts/{contract_id}/evidence")
async def get_contract_evidence(contract_id: str, current_user: dict = Depends(get_current_admin)):
    """Evidenzpaket abrufen."""
    evidence_list = []
    async for e in S.db.contract_evidence.find({"contract_id": contract_id}, {"_id": 0}).sort("timestamp", -1):
        evidence_list.append(e)
    return {"evidence": evidence_list, "count": len(evidence_list)}


# Customer contract endpoints


@router.post("/api/admin/contracts/{contract_id}/generate-pdf")
async def admin_generate_contract_pdf(contract_id: str, current_user: dict = Depends(get_current_admin)):
    """Vertrags-PDF generieren und archivieren."""
    contract = await S.db.contracts.find_one({"contract_id": contract_id}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    appendices = []
    async for a in S.db.contract_appendices.find({"contract_id": contract_id}, {"_id": 0}).sort("created_at", 1):
        appendices.append(a)
    evidence = await S.db.contract_evidence.find_one(
        {"contract_id": contract_id, "action": "accepted"}, {"_id": 0}
    )
    try:
        pdf_bytes = generate_contract_pdf(contract, appendices=appendices, evidence=evidence)
        await archive_pdf_to_storage(
            "contract", contract_id, contract.get("contract_number", ""),
            pdf_bytes, version=contract.get("version", 1),
        )
        return {"generated": True, "contract_id": contract_id, "size_bytes": len(pdf_bytes)}
    except Exception as e:
        raise HTTPException(500, f"PDF-Generierung fehlgeschlagen: {str(e)}")



@router.get("/api/customer/contracts")
async def customer_contracts(current_user: dict = Depends(get_current_customer)):
    """Kundenverträge anzeigen."""
    email = current_user["email"]
    contracts = []
    async for c in S.db.contracts.find({"customer.email": email}, {"_id": 0}).sort("created_at", -1):
        for dt_field in ("created_at", "updated_at"):
            if hasattr(c.get(dt_field), "isoformat"):
                c[dt_field] = c[dt_field].isoformat()
        c.pop("versions_history", None)
        contracts.append(c)
    return {"contracts": contracts}



@router.get("/api/customer/contracts/{contract_id}")
async def customer_contract_detail(contract_id: str, current_user: dict = Depends(get_current_customer)):
    """Vertragsdetail für Kunden — inkl. Versionen, Evidenz, Signatur-Vorschau."""
    email = current_user["email"]
    contract = await S.db.contracts.find_one({"contract_id": contract_id, "customer.email": email}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    # Mark as viewed
    if contract.get("status") == ContractStatus.SENT.value:
        await S.db.contracts.update_one({"contract_id": contract_id}, {"$set": {"status": ContractStatus.VIEWED.value, "viewed_at": utcnow().isoformat()}})
        contract["status"] = ContractStatus.VIEWED.value
    # Load appendices
    appendices = []
    async for a in S.db.contract_appendices.find({"contract_id": contract_id}, {"_id": 0}).sort("created_at", 1):
        if hasattr(a.get("created_at"), "isoformat"):
            a["created_at"] = a["created_at"].isoformat()
        appendices.append(a)
    contract["appendices_detail"] = appendices
    contract["document_hash"] = _compute_doc_hash(contract)
    contract["legal_module_definitions"] = LEGAL_MODULES

    # Versions history for customer view
    versions = contract.get("versions_history", [])
    contract["versions"] = [
        {"version": v.get("version", 1), "status": v.get("status", ""), "timestamp": v.get("timestamp", ""), "note": v.get("note", "")}
        for v in versions
    ]
    contract.pop("versions_history", None)

    # Evidence trail (P3: vollständiges Evidenzpaket)
    evidence_list = []
    async for e in S.db.contract_evidence.find({"contract_id": contract_id}, {"_id": 0}).sort("timestamp", -1):
        evidence_list.append({
            "evidence_id": e.get("evidence_id"),
            "action": e.get("action"),
            "timestamp": e.get("timestamp"),
            "ip_address": e.get("ip_address", ""),
            "user_agent": e.get("user_agent", "")[:80],
            "document_hash": e.get("document_hash", ""),
            "contract_version": e.get("contract_version", 1),
            "consent_status": e.get("consent_status", ""),
            "signature_type": e.get("signature_type", ""),
        })
    contract["evidence_trail"] = evidence_list

    # Signature preview (if accepted)
    if contract.get("status") == ContractStatus.ACCEPTED.value and contract.get("signature"):
        acceptance_evidence = await S.db.contract_evidence.find_one(
            {"contract_id": contract_id, "action": "accepted"}, {"_id": 0}
        )
        if acceptance_evidence:
            sig_data = acceptance_evidence.get("signature_data", "")
            contract["signature_preview"] = {
                "type": acceptance_evidence.get("signature_type", ""),
                "data": sig_data[:200] if sig_data.startswith("data:image") else sig_data,
                "is_image": sig_data.startswith("data:image"),
                "timestamp": acceptance_evidence.get("timestamp", ""),
                "customer_name": acceptance_evidence.get("customer_name", ""),
            }

    # Contract PDF availability
    has_pdf = bool(await S.db.documents.find_one({"ref_id": contract_id, "type": "contract"}, {"_id": 1}))
    contract["has_pdf"] = has_pdf
    contract["pdf_url"] = f"/api/documents/contract/{contract_id}/pdf" if has_pdf else None

    # Change request details
    if contract.get("change_request"):
        cr = contract["change_request"]
        contract["change_request_detail"] = {
            "text": cr.get("text", ""),
            "timestamp": cr.get("timestamp", ""),
        }

    for dt_field in ("created_at", "updated_at"):
        if hasattr(contract.get(dt_field), "isoformat"):
            contract[dt_field] = contract[dt_field].isoformat()
    return contract



@router.post("/api/customer/contracts/{contract_id}/accept")
async def customer_accept_contract(contract_id: str, data: dict, request: Request, current_user: dict = Depends(get_current_customer)):
    """Digitale Vertragsannahme mit Evidenzpaket."""
    email = current_user["email"]
    contract = await S.db.contracts.find_one({"contract_id": contract_id, "customer.email": email}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    if contract.get("status") not in (ContractStatus.SENT.value, ContractStatus.VIEWED.value):
        raise HTTPException(400, f"Vertrag kann im Status '{contract.get('status')}' nicht angenommen werden")
    # Signature data
    signature_type = data.get("signature_type", "name")
    signature_data = data.get("signature_data", "")
    if not signature_data:
        raise HTTPException(400, "Signatur erforderlich (signature_data)")
    # Legal modules acceptance
    legal_accepted = data.get("legal_modules_accepted", {})
    for lm in LEGAL_MODULES:
        if lm["required"] and not legal_accepted.get(lm["key"]):
            raise HTTPException(400, f"Pflichtmodul nicht akzeptiert: {lm['label']}")
    # Legal Gate Check (P6: Compliance-Prüfung vor Annahme)
    if S.legal_svc:
        legal_check = await S.legal_svc.check_contract(contract)
        if not legal_check.get("approved") and legal_check.get("risk_level") in ("high", "critical"):
            raise HTTPException(400, f"Compliance-Gate: Vertrag hat offene rechtliche Risiken ({legal_check.get('risk_level')})")
    # Build evidence
    doc_hash = _compute_doc_hash(contract)
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    evidence = create_contract_evidence(
        contract_id, "accepted",
        ip=ip_addr, user_agent=ua, doc_hash=doc_hash,
        contract_version=contract.get("version", 1),
        consent_status="accepted",
        legal_modules_accepted=legal_accepted,
        signature_type=signature_type,
        signature_data=signature_data,
        customer_email=email,
        customer_name=data.get("customer_name", contract.get("customer", {}).get("name", "")),
    )
    await S.db.contract_evidence.insert_one({**evidence})
    # Update contract
    await S.db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {
            "status": ContractStatus.ACCEPTED.value,
            "accepted_at": utcnow().isoformat(),
            "signature": {"type": signature_type, "timestamp": utcnow().isoformat()},
            "evidence": evidence["evidence_id"],
            "legal_modules": {lm["key"]: {"accepted": legal_accepted.get(lm["key"], False), "version": "1.0", "accepted_at": utcnow().isoformat() if legal_accepted.get(lm["key"]) else None} for lm in LEGAL_MODULES},
            "updated_at": utcnow(),
        }}
    )
    # Timeline
    await S.db.timeline_events.insert_one(create_timeline_event(
        "contract", contract_id, "contract_accepted",
        actor=email, actor_type="customer",
        details={"signature_type": signature_type, "evidence_id": evidence["evidence_id"]},
    ))
    # Memory
    if S.memory_svc:
        await S.memory_svc.write(
            email, f"Vertrag {contract.get('contract_number', '')} digital angenommen",
            agent_id="contract_agent", category="contract",
            source="portal", source_ref=contract_id,
            verification_status="verifiziert",
        )
    # PDF-Archivierung (P4: persistente Vertrags-PDF mit Evidenzpaket)
    try:
        appendices = []
        async for a in S.db.contract_appendices.find({"contract_id": contract_id}, {"_id": 0}).sort("created_at", 1):
            appendices.append(a)
        updated_contract = await S.db.contracts.find_one({"contract_id": contract_id}, {"_id": 0})
        pdf_bytes = generate_contract_pdf(updated_contract, appendices=appendices, evidence=evidence)
        await archive_pdf_to_storage(
            "contract", contract_id, contract.get("contract_number", ""),
            pdf_bytes, version=contract.get("version", 1),
            extra_meta={"evidence_id": evidence["evidence_id"]},
        )
        logger.info(f"Contract PDF archived: {contract_id}")
    except Exception as e:
        logger.error(f"Contract PDF generation error: {e}")
    except Exception as e:
        logger.error(f"Contract PDF generation error: {e}")

    evidence.pop("_id", None)
    return {"accepted": True, "evidence_id": evidence["evidence_id"], "status": "accepted"}



@router.post("/api/customer/contracts/{contract_id}/decline")
async def customer_decline_contract(contract_id: str, data: dict, request: Request, current_user: dict = Depends(get_current_customer)):
    """Vertrag ablehnen."""
    email = current_user["email"]
    contract = await S.db.contracts.find_one({"contract_id": contract_id, "customer.email": email}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    reason = data.get("reason", "")
    doc_hash = _compute_doc_hash(contract)
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    evidence = create_contract_evidence(
        contract_id, "declined",
        ip=ip_addr, user_agent=ua, doc_hash=doc_hash,
        contract_version=contract.get("version", 1),
        consent_status="declined",
        customer_email=email,
    )
    await S.db.contract_evidence.insert_one({**evidence})
    await S.db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {"status": ContractStatus.DECLINED.value, "declined_at": utcnow().isoformat(), "decline_reason": reason, "updated_at": utcnow()}}
    )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "contract", contract_id, "contract_declined",
        actor=email, actor_type="customer",
        details={"reason": reason, "evidence_id": evidence["evidence_id"]},
    ))
    evidence.pop("_id", None)
    return {"declined": True, "evidence_id": evidence["evidence_id"]}



@router.post("/api/customer/contracts/{contract_id}/request-change")
async def customer_request_change(contract_id: str, data: dict, request: Request, current_user: dict = Depends(get_current_customer)):
    """Änderungsanfrage zum Vertrag."""
    email = current_user["email"]
    contract = await S.db.contracts.find_one({"contract_id": contract_id, "customer.email": email}, {"_id": 0})
    if not contract:
        raise HTTPException(404, "Vertrag nicht gefunden")
    changes = data.get("requested_changes", "")
    if not changes.strip():
        raise HTTPException(400, "requested_changes erforderlich")
    doc_hash = _compute_doc_hash(contract)
    ip_addr = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "unknown")
    evidence = create_contract_evidence(
        contract_id, "change_requested",
        ip=ip_addr, user_agent=ua, doc_hash=doc_hash,
        contract_version=contract.get("version", 1),
        consent_status="change_requested",
        customer_email=email,
    )
    await S.db.contract_evidence.insert_one({**evidence})
    await S.db.contracts.update_one(
        {"contract_id": contract_id},
        {"$set": {"status": ContractStatus.CHANGE_REQUESTED.value, "change_request": {"text": changes, "timestamp": utcnow().isoformat(), "email": email}, "updated_at": utcnow()}}
    )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "contract", contract_id, "contract_change_requested",
        actor=email, actor_type="customer",
        details={"changes": changes[:200]},
    ))
    evidence.pop("_id", None)
    return {"change_requested": True, "evidence_id": evidence["evidence_id"]}


# ══════════════════════════════════════════════════════════════
# CUSTOMER FINANCE — Portal-Finance-Ansicht (P2)
# ══════════════════════════════════════════════════════════════

