"""NeXifyAI — Admin CRM Routes"""
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from routes.shared import S
from routes.shared import (
    get_current_admin,
    log_audit,
    send_email,
    email_template,
    logger,
)
from domain import create_contact, create_timeline_event, utcnow
from memory_service import AGENT_IDS

router = APIRouter(tags=["admin"])

from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    vorname: Optional[str] = None
    nachname: Optional[str] = None
    email: Optional[str] = None
    unternehmen: Optional[str] = None
    telefon: Optional[str] = None
    source: Optional[str] = None
    nachricht: Optional[str] = None

class BookingUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None

class BlockedSlot(BaseModel):
    date: str
    time: Optional[str] = None
    reason: Optional[str] = None
    all_day: bool = False

@router.get("/api/admin/stats")
async def admin_stats(user = Depends(get_current_admin)):
    now = datetime.now(timezone.utc)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    
    total = await S.db.leads.count_documents({})
    today_count = await S.db.leads.count_documents({"created_at": {"$gte": today}})
    week_count = await S.db.leads.count_documents({"created_at": {"$gte": week_ago}})
    upcoming = await S.db.bookings.count_documents({"date": {"$gte": today.strftime("%Y-%m-%d")}, "status": "confirmed"})
    
    status_agg = await S.db.leads.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}]).to_list(20)
    
    return {
        "total_leads": total,
        "new_leads_today": today_count,
        "new_leads_week": week_count,
        "upcoming_bookings": upcoming,
        "by_status": {s["_id"]: s["count"] for s in status_agg if s["_id"]}
    }


@router.get("/api/admin/leads")
async def admin_leads(user = Depends(get_current_admin), status: str = None, search: str = None, skip: int = 0, limit: int = 50):
    query = {}
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"vorname": {"$regex": search, "$options": "i"}},
            {"nachname": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"unternehmen": {"$regex": search, "$options": "i"}}
        ]
    
    total = await S.db.leads.count_documents(query)
    leads = await S.db.leads.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {"total": total, "leads": leads}



@router.post("/api/admin/leads")
async def admin_create_lead(data: dict, current_user: dict = Depends(get_current_admin)):
    """Manuell einen Lead anlegen."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    existing = await S.db.leads.find_one({"email": email})
    if existing:
        raise HTTPException(409, "Ein Lead mit dieser E-Mail existiert bereits")
    lead = {
        "lead_id": new_id("lead"),
        "vorname": data.get("vorname", "").strip(),
        "nachname": data.get("nachname", "").strip(),
        "email": email,
        "unternehmen": data.get("unternehmen", "").strip(),
        "telefon": data.get("telefon", "").strip(),
        "nachricht": data.get("nachricht", "").strip(),
        "source": data.get("source", "admin"),
        "status": "new",
        "notes": [],
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    await S.db.leads.insert_one(lead)
    lead.pop("_id", None)
    # Also create a unified contact
    contact = create_contact(email, first_name=data.get("vorname",""), last_name=data.get("nachname",""),
                             phone=data.get("telefon",""), company=data.get("unternehmen",""), source="admin")
    await S.db.contacts.update_one({"email": email}, {"$setOnInsert": contact}, upsert=True)
    evt = create_timeline_event("lead", lead["lead_id"], "lead_created_manually",
                                actor=current_user["email"], actor_type="admin",
                                details={"email": email, "source": "admin"})
    await S.db.timeline_events.insert_one(evt)
    return lead




@router.get("/api/admin/leads/{lead_id}")
async def admin_lead_detail(lead_id: str, user = Depends(get_current_admin)):
    lead = await S.db.leads.find_one({"lead_id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead nicht gefunden")
    
    bookings = await S.db.bookings.find({"lead_id": lead_id}, {"_id": 0}).to_list(10)
    chat = await S.db.chat_sessions.find_one({"lead_id": lead_id}, {"_id": 0})
    
    return {"lead": lead, "bookings": bookings, "chat": chat}


@router.patch("/api/admin/leads/{lead_id}")
async def admin_update_lead(lead_id: str, update: LeadUpdate, user = Depends(get_current_admin)):
    updates = {"updated_at": datetime.now(timezone.utc)}
    for field in ["status", "vorname", "nachname", "email", "unternehmen", "telefon", "source", "nachricht"]:
        val = getattr(update, field, None)
        if val is not None:
            updates[field] = val
    
    if update.notes:
        await S.db.leads.update_one(
            {"lead_id": lead_id},
            {"$set": updates, "$push": {"notes": {"text": update.notes, "by": user["email"], "at": datetime.now(timezone.utc).isoformat()}}}
        )
    else:
        await S.db.leads.update_one({"lead_id": lead_id}, {"$set": updates})
    
    await log_audit("lead_updated", user["email"], {"lead_id": lead_id, "updates": {k: v for k, v in updates.items() if k != "updated_at"}})
    
    # mem0 Memory
    if S.memory_svc:
        contact = await S.db.contacts.find_one({"email": (update.email or "").lower() or (await S.db.leads.find_one({"lead_id": lead_id}))["email"]})
        if contact:
            changed = ", ".join(f"{k}={v}" for k, v in updates.items() if k != "updated_at")
            await S.memory_svc.write(contact["contact_id"], f"Lead {lead_id} bearbeitet: {changed}", AGENT_IDS["admin"],
                                   category="context", source="admin", source_ref=user["email"], verification_status="verifiziert")
    
    return {"success": True}


@router.get("/api/admin/bookings")
async def admin_bookings(user = Depends(get_current_admin), status: str = None, date_from: str = None, date_to: str = None, skip: int = 0, limit: int = 100):
    query = {}
    if status:
        query["status"] = status
    if date_from:
        query.setdefault("date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("date", {})["$lte"] = date_to
    total = await S.db.bookings.count_documents(query)
    bookings = await S.db.bookings.find(query, {"_id": 0}).sort("date", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "bookings": bookings}


@router.get("/api/admin/bookings/{booking_id}")
async def admin_booking_detail(booking_id: str, user = Depends(get_current_admin)):
    booking = await S.db.bookings.find_one({"booking_id": booking_id}, {"_id": 0})
    if not booking:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    return booking


@router.patch("/api/admin/bookings/{booking_id}")
async def admin_update_booking(booking_id: str, update: BookingUpdate, user = Depends(get_current_admin)):
    booking = await S.db.bookings.find_one({"booking_id": booking_id})
    if not booking:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    updates = {"updated_at": datetime.now(timezone.utc)}
    if update.status:
        updates["status"] = update.status
    if update.date:
        updates["date"] = update.date
    if update.time:
        updates["time"] = update.time
    if update.notes is not None:
        await S.db.bookings.update_one(
            {"booking_id": booking_id},
            {"$set": updates, "$push": {"notes": {"text": update.notes, "by": user["email"], "at": datetime.now(timezone.utc).isoformat()}}}
        )
    else:
        await S.db.bookings.update_one({"booking_id": booking_id}, {"$set": updates})
    await log_audit("booking_updated", user["email"], {"booking_id": booking_id, "updates": {k: v for k, v in updates.items() if k != "updated_at"}})
    return {"success": True}


@router.delete("/api/admin/bookings/{booking_id}")
async def admin_delete_booking(booking_id: str, user = Depends(get_current_admin)):
    result = await S.db.bookings.delete_one({"booking_id": booking_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Buchung nicht gefunden")
    await log_audit("booking_deleted", user["email"], {"booking_id": booking_id})
    return {"success": True}

# ============== BLOCKED SLOTS ==============


@router.get("/api/admin/blocked-slots")
async def admin_get_blocked_slots(user = Depends(get_current_admin), date_from: str = None, date_to: str = None):
    query = {}
    if date_from:
        query.setdefault("date", {})["$gte"] = date_from
    if date_to:
        query.setdefault("date", {})["$lte"] = date_to
    slots = await S.db.blocked_slots.find(query, {"_id": 0}).sort("date", 1).to_list(200)
    return {"slots": slots}


@router.post("/api/admin/blocked-slots")
async def admin_create_blocked_slot(slot: BlockedSlot, user = Depends(get_current_admin)):
    slot_id = f"BLK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    doc = {
        "slot_id": slot_id,
        "date": slot.date,
        "time": slot.time,
        "all_day": slot.all_day,
        "reason": slot.reason or "",
        "created_by": user["email"],
        "created_at": datetime.now(timezone.utc)
    }
    await S.db.blocked_slots.insert_one(doc)
    await log_audit("slot_blocked", user["email"], {"slot_id": slot_id, "date": slot.date})
    del doc["_id"]
    return doc


@router.delete("/api/admin/blocked-slots/{slot_id}")
async def admin_delete_blocked_slot(slot_id: str, user = Depends(get_current_admin)):
    result = await S.db.blocked_slots.delete_one({"slot_id": slot_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Slot nicht gefunden")
    await log_audit("slot_unblocked", user["email"], {"slot_id": slot_id})
    return {"success": True}

# ============== CUSTOMER MANAGEMENT ==============


@router.get("/api/admin/customers")
async def admin_customers(user = Depends(get_current_admin), search: str = None):
    pipeline = [
        {"$group": {
            "_id": "$email",
            "vorname": {"$first": "$vorname"},
            "nachname": {"$first": "$nachname"},
            "unternehmen": {"$first": "$unternehmen"},
            "telefon": {"$first": "$telefon"},
            "total_leads": {"$sum": 1},
            "first_contact": {"$min": "$created_at"},
            "last_contact": {"$max": "$created_at"},
            "statuses": {"$push": "$status"}
        }},
        {"$sort": {"last_contact": -1}}
    ]
    if search:
        pipeline.insert(0, {"$match": {"$or": [
            {"vorname": {"$regex": search, "$options": "i"}},
            {"nachname": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"unternehmen": {"$regex": search, "$options": "i"}}
        ]}})
    customers = await S.db.leads.aggregate(pipeline).to_list(200)
    for c in customers:
        c["email"] = c.pop("_id")
        booking_count = await S.db.bookings.count_documents({"email": c["email"]})
        c["total_bookings"] = booking_count
        if c.get("first_contact"):
            c["first_contact"] = c["first_contact"].isoformat()
        if c.get("last_contact"):
            c["last_contact"] = c["last_contact"].isoformat()
    return {"customers": customers}


@router.post("/api/admin/customers")
async def admin_create_customer(data: dict, user = Depends(get_current_admin)):
    """Manuell einen Kunden anlegen — erstellt Lead + Contact + Memory-Eintrag."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    vorname = data.get("vorname", "").strip()
    nachname = data.get("nachname", "").strip()
    unternehmen = data.get("unternehmen", "").strip()
    telefon = data.get("telefon", "").strip()
    branche = data.get("branche", "").strip()
    
    # Upsert lead record
    existing_lead = await S.db.leads.find_one({"email": email})
    now = datetime.now(timezone.utc)
    if existing_lead:
        await S.db.leads.update_one(
            {"email": email},
            {"$set": {
                "vorname": vorname or existing_lead.get("vorname", ""),
                "nachname": nachname or existing_lead.get("nachname", ""),
                "unternehmen": unternehmen or existing_lead.get("unternehmen", ""),
                "telefon": telefon or existing_lead.get("telefon", ""),
                "branche": branche or existing_lead.get("branche", ""),
                "updated_at": now,
            }}
        )
    else:
        lead_id = new_id("ld")
        await S.db.leads.insert_one({
            "lead_id": lead_id,
            "email": email,
            "vorname": vorname,
            "nachname": nachname,
            "unternehmen": unternehmen,
            "telefon": telefon,
            "branche": branche,
            "source": "admin_manual",
            "status": "qualified",
            "notes": [],
            "created_at": now,
            "updated_at": now,
        })
    
    # Upsert unified contact
    existing_contact = await S.db.contacts.find_one({"email": email})
    if existing_contact:
        await S.db.contacts.update_one(
            {"email": email},
            {"$set": {
                "first_name": vorname or existing_contact.get("first_name", ""),
                "last_name": nachname or existing_contact.get("last_name", ""),
                "company": unternehmen or existing_contact.get("company", ""),
                "phone": telefon or existing_contact.get("phone", ""),
                "industry": branche or existing_contact.get("industry", ""),
                "updated_at": now,
            },
            "$addToSet": {"channels_used": "admin"}}
        )
        contact_id = existing_contact["contact_id"]
    else:
        contact = create_contact(email, first_name=vorname, last_name=nachname,
                                  company=unternehmen, phone=telefon, industry=branche,
                                  source="admin_manual")
        await S.db.contacts.insert_one(contact)
        contact.pop("_id", None)
        contact_id = contact["contact_id"]
    
    # Memory-Eintrag: Manuell erstellter Kunde (mem0-konform)
    await S.memory_svc.write(contact_id, f"Kunde manuell angelegt von Admin ({user['email']}). {vorname} {nachname}, {unternehmen}, Branche: {branche}",
                           AGENT_IDS["admin"], category="context", source="admin", source_ref=user["email"],
                           verification_status="verifiziert")
    
    # Timeline
    evt = create_timeline_event("contact", contact_id, "customer_created_manual",
                                actor=user["email"], actor_type="admin",
                                details={"email": email, "vorname": vorname, "nachname": nachname, "unternehmen": unternehmen})
    await S.db.timeline_events.insert_one(evt)
    
    return {"status": "ok", "email": email, "contact_id": contact_id}



@router.post("/api/admin/customers/portal-access")
async def admin_create_portal_access(data: dict, user = Depends(get_current_admin)):
    """Portalzugang für einen Kunden erstellen — Magic Link generieren."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    # Ensure contact exists
    contact = await S.db.contacts.find_one({"email": email})
    if not contact:
        raise HTTPException(404, "Kein Kontakt für diese E-Mail gefunden. Bitte erst Kunden anlegen.")
    
    token_data = generate_access_token(email, "portal")
    await S.db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": email,
        "document_type": "portal",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": user["email"],
    })
    
    base_url = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
    portal_url = f"{base_url}/portal/{token_data['token']}"
    
    # Memory-Eintrag (mem0-konform)
    await S.memory_svc.write(contact["contact_id"], f"Portalzugang erstellt von {user['email']}",
                           AGENT_IDS["admin"], category="context", source="admin", source_ref=user["email"],
                           verification_status="verifiziert")
    
    # Timeline
    evt = create_timeline_event("contact", contact["contact_id"], "portal_access_created",
                                actor=user["email"], actor_type="admin",
                                details={"email": email, "expires_at": token_data["expires_at"]})
    await S.db.timeline_events.insert_one(evt)
    
    return {"status": "ok", "portal_url": portal_url, "expires_at": token_data["expires_at"]}



@router.get("/api/admin/customers/{email}")
async def admin_customer_detail(email: str, user = Depends(get_current_admin)):
    leads = await S.db.leads.find({"email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(50)
    bookings = await S.db.bookings.find({"email": email.lower()}, {"_id": 0}).sort("date", -1).to_list(50)
    chats = await S.db.chat_sessions.find(
        {"$or": [{"email": email.lower()}, {"qualification.email": email.lower()}]},
        {"_id": 0, "messages": {"$slice": -10}}
    ).sort("updated_at", -1).to_list(10)
    return {"leads": leads, "bookings": bookings, "chats": chats}



@router.patch("/api/admin/customers/{email}")
async def admin_update_customer(email: str, data: dict, user = Depends(get_current_admin)):
    """Kunden-/Kontaktdaten bearbeiten."""
    email = email.lower()
    contact = await S.db.contacts.find_one({"email": email})
    if not contact:
        raise HTTPException(404, "Kontakt nicht gefunden")
    
    updates = {"updated_at": datetime.now(timezone.utc)}
    field_map = {"vorname": "first_name", "nachname": "last_name", "unternehmen": "company", "telefon": "phone", "branche": "industry"}
    for de_key, en_key in field_map.items():
        if de_key in data and data[de_key]:
            updates[en_key] = data[de_key].strip()
    
    if len(updates) > 1:
        await S.db.contacts.update_one({"email": email}, {"$set": updates})
    
    # Auch Lead-Daten synchronisieren
    lead_updates = {}
    lead_map = {"vorname": "vorname", "nachname": "nachname", "unternehmen": "unternehmen", "telefon": "telefon", "branche": "branche"}
    for key in lead_map:
        if key in data and data[key]:
            lead_updates[key] = data[key].strip()
    if lead_updates:
        lead_updates["updated_at"] = datetime.now(timezone.utc)
        await S.db.leads.update_many({"email": email}, {"$set": lead_updates})
    
    await log_audit("customer_updated", user["email"], {"email": email, "fields": list(updates.keys())})
    
    if S.memory_svc:
        changed = ", ".join(f"{k}={v}" for k, v in updates.items() if k != "updated_at")
        await S.memory_svc.write(contact["contact_id"], f"Kundendaten bearbeitet: {changed}", AGENT_IDS["admin"],
                               category="context", source="admin", source_ref=user["email"], verification_status="verifiziert")
    
    return {"success": True}



@router.post("/api/admin/bookings")
async def admin_create_booking(data: dict, user = Depends(get_current_admin)):
    """Termin manuell anlegen."""
    required = ["vorname", "email", "date", "time"]
    for f in required:
        if not data.get(f, "").strip():
            raise HTTPException(400, f"{f} ist Pflichtfeld")
    
    booking_id = f"BK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{secrets.token_hex(3).upper()}"
    doc = {
        "booking_id": booking_id,
        "vorname": data.get("vorname", "").strip(),
        "nachname": data.get("nachname", "").strip(),
        "email": data.get("email", "").strip().lower(),
        "telefon": data.get("telefon", ""),
        "unternehmen": data.get("unternehmen", ""),
        "thema": data.get("thema", ""),
        "date": data.get("date"),
        "time": data.get("time"),
        "status": "confirmed",
        "source": "admin_manual",
        "notes": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    await S.db.bookings.insert_one(doc)
    doc.pop("_id", None)
    
    await log_audit("booking_created_manual", user["email"], {"booking_id": booking_id})
    evt = create_timeline_event("booking", booking_id, "booking_created",
                                actor=user["email"], actor_type="admin",
                                details={"email": doc["email"], "date": doc["date"], "time": doc["time"]})
    await S.db.timeline_events.insert_one(evt)
    
    return {"success": True, "booking_id": booking_id}


# ============== ENHANCED STATS ==============


@router.get("/api/admin/calendar-data")
async def admin_calendar_data(user = Depends(get_current_admin), month: str = None):
    """Get bookings and blocked slots for a month (format: YYYY-MM)"""
    if not month:
        month = datetime.now(timezone.utc).strftime("%Y-%m")
    date_from = f"{month}-01"
    year, mon = int(month.split("-")[0]), int(month.split("-")[1])
    if mon == 12:
        date_to = f"{year + 1}-01-01"
    else:
        date_to = f"{year}-{mon + 1:02d}-01"
    
    bookings = await S.db.bookings.find(
        {"date": {"$gte": date_from, "$lt": date_to}},
        {"_id": 0}
    ).sort("date", 1).to_list(200)
    
    blocked = await S.db.blocked_slots.find(
        {"date": {"$gte": date_from, "$lt": date_to}},
        {"_id": 0}
    ).sort("date", 1).to_list(200)
    
    return {"bookings": bookings, "blocked_slots": blocked, "month": month}



# ═══════════════════════════════════════════════════════════════════
# COMMERCIAL ENGINE v2.0 — Source of Truth: commercial.py
# ═══════════════════════════════════════════════════════════════════

@router.get("/api/admin/timeline")
async def admin_timeline(
    limit: int = 50,
    email: str = None,
    current_user: dict = Depends(get_current_admin)
):
    """Unified timeline across all entities for a customer or global."""
    events = []
    
    # Audit log events
    query = {}
    if email:
        query["$or"] = [{"details.email": email.lower()}, {"actor": email.lower()}]
    async for ev in S.db.audit_log.find(query, {"_id": 0}).sort("timestamp", -1).limit(limit):
        events.append({
            "type": "audit",
            "event": ev.get("event_type", ev.get("event", "")),
            "ref_id": ev.get("ref_id", ""),
            "actor": ev.get("user", ev.get("actor", "")),
            "timestamp": ev.get("timestamp", ""),
            "details": ev.get("details", {}),
        })
    
    # Commercial events fallback
    async for ev in S.db.commercial_events.find(query if email else {}, {"_id": 0}).sort("timestamp", -1).limit(limit):
        events.append({
            "type": "commercial",
            "event": ev.get("event", ""),
            "ref_id": ev.get("ref_id", ""),
            "actor": ev.get("actor", ""),
            "timestamp": ev.get("timestamp", ""),
            "details": ev.get("details", {}),
        })
    
    # Sort combined by timestamp desc
    events.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)
    return {"events": events[:limit]}


# --- mem0 Memory API (Pflicht-Layer) ---


@router.post("/api/admin/leads/{lead_id}/notes")
async def admin_add_lead_note(
    lead_id: str,
    data: dict,
    current_user: dict = Depends(get_current_admin)
):
    """Add a note to a lead."""
    note = {
        "text": data.get("text", ""),
        "author": current_user["email"],
        "date": datetime.now(timezone.utc).isoformat(),
    }
    result = await S.db.leads.update_one(
        {"lead_id": lead_id},
        {"$push": {"notes": note}, "$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Lead nicht gefunden")
    return {"status": "ok", "note": note}


# --- Customer Portal: Enhanced ---

