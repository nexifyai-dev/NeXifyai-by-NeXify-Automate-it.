"""NeXifyAI — Outbound Lead Machine Routes"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import S
from routes.shared import (
    get_current_admin,
    logger,
)
from domain import create_contact, create_timeline_event, utcnow
from memory_service import AGENT_IDS

router = APIRouter(tags=["outbound"])

@router.get("/api/admin/outbound/leads")
async def outbound_leads_list(
    status: str = None, min_score: int = 0,
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Outbound-Leads auflisten."""
    leads = await S.outbound_svc.list_outbound_leads(status, min_score, skip, limit)
    return {"leads": leads, "count": len(leads)}



@router.get("/api/admin/outbound/stats")
async def outbound_stats(current_user: dict = Depends(get_current_admin)):
    """Outbound-Pipeline-Statistiken."""
    return await S.outbound_svc.get_outbound_stats()



@router.post("/api/admin/outbound/discover")
async def outbound_discover(data: dict, current_user: dict = Depends(get_current_admin)):
    """Neuen Outbound-Lead erfassen."""
    result = await S.outbound_svc.discover_lead(data, source=data.get("source", "admin"))
    return result



@router.get("/api/admin/outbound/pipeline")
async def outbound_pipeline(current_user: dict = Depends(get_current_admin)):
    """Vollständige Pipeline-Übersicht mit Konversionsraten."""
    stats = await S.outbound_svc.get_outbound_stats()
    stages = [
        ("discovered", "Entdeckt"), ("analyzing", "Analyse"),
        ("qualified", "Qualifiziert"), ("unqualified", "Nicht qualifiziert"),
        ("legal_blocked", "Legal blockiert"), ("outreach_ready", "Outreach-bereit"),
        ("contacted", "Kontaktiert"), ("followup_1", "Follow-up 1"),
        ("followup_2", "Follow-up 2"), ("followup_3", "Follow-up 3"),
        ("responded", "Antwort erhalten"), ("meeting_booked", "Termin gebucht"),
        ("quote_sent", "Angebot gesendet"), ("nurture", "Nurture"),
        ("opt_out", "Opt-Out"), ("suppressed", "Unterdrückt"),
    ]
    by_status = stats.get("by_status", {})
    pipeline = [{"key": k, "label": l, "count": by_status.get(k, 0)} for k, l in stages]
    return {"pipeline": pipeline, "total": stats.get("total", 0), "conversion_rate": stats.get("conversion_rate", 0)}



@router.post("/api/admin/outbound/{lead_id}/prequalify")
async def outbound_prequalify(lead_id: str, current_user: dict = Depends(get_current_admin)):
    """Lead vorqualifizieren."""
    return await S.outbound_svc.prequalify(lead_id)



@router.post("/api/admin/outbound/{lead_id}/analyze")
async def outbound_analyze(lead_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Lead analysieren und scoren."""
    return await S.outbound_svc.analyze_and_score(lead_id, data)



@router.post("/api/admin/outbound/{lead_id}/legal-check")
async def outbound_legal_check(lead_id: str, current_user: dict = Depends(get_current_admin)):
    """Legal Gate prüfen."""
    return await S.outbound_svc.legal_check(lead_id)



@router.post("/api/admin/outbound/{lead_id}/outreach")
async def outbound_create_outreach(lead_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Outreach erstellen."""
    return await S.outbound_svc.create_outreach(lead_id, data)



@router.post("/api/admin/outbound/{lead_id}/outreach/{outreach_id}/send")
async def outbound_send_outreach(lead_id: str, outreach_id: str, current_user: dict = Depends(get_current_admin)):
    """Outreach versenden — mit Legal-Guardian-Gate."""
    lead = await S.db.outbound_leads.find_one({"outbound_lead_id": lead_id}, {"_id": 0})
    if lead and S.legal_svc:
        legal_result = await S.legal_svc.check_outreach({
            "email": lead.get("contact_email", ""),
            "channel": "email",
            "score": lead.get("score", 0),
        })
        if not legal_result.get("approved"):
            return {"error": "Legal-Gate blockiert", "legal_check": legal_result}
    return await S.outbound_svc.send_outreach(lead_id, outreach_id)



@router.post("/api/admin/outbound/{lead_id}/followup")
async def outbound_followup(lead_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Follow-up planen."""
    days = (data or {}).get("days_delay", 3)
    return await S.outbound_svc.schedule_followup(lead_id, days)



@router.post("/api/admin/outbound/opt-out")
async def outbound_opt_out(data: dict, current_user: dict = Depends(get_current_admin)):
    """E-Mail auf Suppression-Liste setzen."""
    email = data.get("email", "")
    if not email:
        raise HTTPException(400, "E-Mail erforderlich")
    return await S.outbound_svc.opt_out(email, data.get("reason", ""))



@router.get("/api/admin/outbound/{lead_id}")
async def outbound_lead_detail(lead_id: str, current_user: dict = Depends(get_current_admin)):
    """Lead-Detail mit vollständiger History."""
    lead = await S.db.outbound_leads.find_one({"outbound_lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    # Timeline
    timeline = []
    async for t in S.db.timeline_events.find({"ref_id": lead_id}, {"_id": 0}).sort("created_at", -1).limit(20):
        if hasattr(t.get("created_at"), "isoformat"):
            t["created_at"] = t["created_at"].isoformat()
        timeline.append(t)
    lead["timeline"] = timeline
    return lead



@router.post("/api/admin/outbound/{lead_id}/respond")
async def outbound_mark_response(lead_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Lead-Antwort erfassen."""
    lead = await S.db.outbound_leads.find_one({"outbound_lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    response_type = data.get("response_type", "positive")
    response_content = data.get("content", "")
    now = utcnow().isoformat()

    new_status = OutboundLeadMachine.__dict__.get("RESPONDED", "responded") if response_type == "positive" else lead.get("status")
    from services.outbound import OutboundStatus
    if response_type == "positive":
        new_status = OutboundStatus.RESPONDED
    elif response_type == "negative":
        new_status = OutboundStatus.NURTURE
    elif response_type == "opt_out":
        new_status = OutboundStatus.OPT_OUT
        await S.outbound_svc.opt_out(lead.get("contact_email", ""), "customer_response_opt_out")

    await S.db.outbound_leads.update_one(
        {"outbound_lead_id": lead_id},
        {"$set": {"status": new_status, "last_response_at": now, "last_response_type": response_type, "updated_at": now},
         "$push": {"responses": {"type": response_type, "content": response_content, "at": now, "by": current_user["email"]}}}
    )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "outbound_lead", lead_id, "outbound_response_received",
        actor=current_user["email"], actor_type="admin",
        details={"response_type": response_type},
    ))
    if S.memory_svc and lead.get("contact_email"):
        await S.memory_svc.write(
            lead["contact_email"], f"Outbound-Antwort: {response_type}",
            agent_id="outbound_agent", category="outbound",
            source="admin", source_ref=lead_id,
        )
    return {"status": new_status, "response_type": response_type}



@router.post("/api/admin/outbound/{lead_id}/handover")
async def outbound_handover(lead_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Lead an Angebot / Termin / Nurture übergeben."""
    lead = await S.db.outbound_leads.find_one({"outbound_lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(404, "Lead nicht gefunden")
    handover_type = data.get("handover_type", "quote")
    from services.outbound import OutboundStatus

    result = {"lead_id": lead_id, "handover_type": handover_type}

    if handover_type == "quote":
        # CRM-Lead erstellen
        crm_lead = {
            "email": lead.get("contact_email", ""),
            "company": lead.get("company_name", ""),
            "name": lead.get("contact_name", ""),
            "phone": lead.get("contact_phone", ""),
            "source": "outbound",
            "notes": f"Outbound-Lead übergeben. Fit-Score: {lead.get('score', 0)}. Fit-Produkte: {', '.join([p['name'] for p in lead.get('fit_products', [])])}",
        }
        existing = await S.db.leads.find_one({"email": crm_lead["email"].lower()})
        if not existing and crm_lead["email"]:
            from domain import create_contact
            # Parse name into first/last name
            name_parts = crm_lead.get("name", "").split(" ", 1)
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            contact = create_contact(
                crm_lead["email"],
                first_name=first_name,
                last_name=last_name,
                phone=crm_lead.get("phone", ""),
                company=crm_lead.get("company", ""),
                source="outbound"
            )
            contact["notes"] = crm_lead.get("notes", "")
            await S.db.leads.insert_one({**contact})
            result["crm_lead_created"] = True
        new_status = OutboundStatus.QUOTE_SENT
    elif handover_type == "meeting":
        new_status = OutboundStatus.MEETING_BOOKED
    elif handover_type == "nurture":
        new_status = OutboundStatus.NURTURE
    else:
        raise HTTPException(400, "handover_type: quote, meeting, oder nurture")

    await S.db.outbound_leads.update_one(
        {"outbound_lead_id": lead_id},
        {"$set": {"status": new_status, "handover_type": handover_type, "handover_at": utcnow().isoformat(), "handover_by": current_user["email"], "updated_at": utcnow().isoformat()}}
    )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "outbound_lead", lead_id, f"outbound_handover_{handover_type}",
        actor=current_user["email"], actor_type="admin",
        details={"handover_type": handover_type},
    ))
    result["status"] = new_status
    return result


# ══════════════════════════════════════════════════════════════
# PROJECT CONTEXT / PROJEKTCHAT ENDPOINTS (P1)
# ══════════════════════════════════════════════════════════════

