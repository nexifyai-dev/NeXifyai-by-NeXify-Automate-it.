"""NeXifyAI — Communications Routes"""
import base64
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import S
from routes.shared import (
    get_current_admin,
    _build_customer_memory,
    logger,
)
from domain import (
    Channel, MessageDirection, WhatsAppSessionStatus,
    create_contact, create_conversation, create_message,
    create_timeline_event, create_whatsapp_session,
    utcnow,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["comms"])

@router.get("/api/admin/chat-sessions")
async def admin_chat_sessions(
    limit: int = 30,
    email: str = None,
    current_user: dict = Depends(get_current_admin)
):
    """List chat sessions with optional email filter."""
    query = {}
    if email:
        query["customer_email"] = email.lower()
    
    sessions = []
    async for s in S.db.chat_sessions.find(query, {"_id": 0}).sort("created_at", -1).limit(limit):
        msgs = s.get("messages", [])
        sessions.append({
            "session_id": s["session_id"],
            "customer_email": s.get("customer_email"),
            "qualification": s.get("qualification", {}),
            "message_count": len(msgs),
            "last_message": msgs[-1]["content"][:100] if msgs else "",
            "created_at": str(s.get("created_at", "")),
        })
    return {"sessions": sessions}



@router.get("/api/admin/chat-sessions/{session_id}")
async def admin_chat_session_detail(
    session_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Full chat session with all messages."""
    session = await S.db.chat_sessions.find_one({"session_id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(404, "Session nicht gefunden")
    return session


# --- Admin: Customer Memory ---


@router.get("/api/admin/customer-memory/{email}")
async def admin_customer_memory(
    email: str,
    current_user: dict = Depends(get_current_admin)
):
    """Full customer memory context for admin view."""
    memory = await _build_customer_memory(email)
    
    # Also get all related data separately
    lead = await S.db.leads.find_one({"email": email.lower()}, {"_id": 0})
    quotes = await S.db.quotes.find({"customer.email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(20)
    invoices = await S.db.invoices.find({"customer.email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(20)
    bookings = await S.db.bookings.find({"email": email.lower()}, {"_id": 0}).sort("created_at", -1).to_list(10)
    chat_sessions = await S.db.chat_sessions.find({"customer_email": email.lower()}, {"_id": 0, "messages": {"$slice": -5}}).sort("created_at", -1).to_list(10)
    
    # Unified conversations
    contact = await S.db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    conversations_out = []
    facts_out = []
    if contact:
        cid = contact.get("contact_id")
        async for conv in S.db.conversations.find({"contact_id": cid}, {"_id": 0}).sort("last_message_at", -1).limit(10):
            mc = await S.db.messages.find({"conversation_id": conv["conversation_id"]}, {"_id": 0}).sort("timestamp", -1).limit(3).to_list(3)
            conversations_out.append({
                "conversation_id": conv["conversation_id"],
                "channels": conv.get("channels", []),
                "status": conv.get("status", "open"),
                "message_count": conv.get("message_count", 0),
                "last_message_at": str(conv.get("last_message_at", "")),
                "recent_messages": [{k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in m.items()} for m in mc],
            })
        async for mem in S.db.customer_memory.find({"contact_id": cid}, {"_id": 0}).sort("created_at", -1).limit(20):
            facts_out.append({k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in mem.items()})
    
    return {
        "email": email.lower(),
        "memory_context": memory,
        "lead": lead,
        "quotes": quotes,
        "invoices": invoices,
        "bookings": bookings,
        "chat_sessions": [{
            "session_id": s["session_id"],
            "qualification": s.get("qualification", {}),
            "message_count": len(s.get("messages", [])),
            "recent_messages": s.get("messages", []),
            "created_at": str(s.get("created_at", "")),
        } for s in chat_sessions],
        "conversations": conversations_out,
        "memory_facts": facts_out,
    }



@router.post("/api/admin/customer-memory/{email}/facts")
async def admin_add_memory_fact(
    email: str, data: dict, current_user: dict = Depends(get_current_admin)
):
    """Manually add a memory fact for a customer — mem0-konform."""
    fact_text = data.get("fact", "").strip()
    category = data.get("category", "general")
    if not fact_text:
        raise HTTPException(400, "Fakt darf nicht leer sein")
    contact = await S.db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    contact_id = contact["contact_id"] if contact else None
    if not contact_id:
        contact = create_contact(email, source="admin")
        await S.db.contacts.insert_one(contact)
        contact.pop("_id", None)
        contact_id = contact["contact_id"]
    mem = await S.memory_svc.write(
        contact_id, fact_text, AGENT_IDS["admin"],
        category=category, source="admin", source_ref=current_user["email"],
        verification_status=data.get("verification_status", "verifiziert"),
    )
    evt = create_timeline_event("contact", contact_id, "memory_fact_added",
                                actor=current_user["email"], actor_type="admin",
                                details={"fact": fact_text[:100], "category": category})
    await S.db.timeline_events.insert_one(evt)
    return {"status": "ok", "memory": {k: (str(v) if hasattr(v, 'isoformat') else v) for k, v in mem.items() if k != "_id"}}


# --- Admin: Lead Notes ---


@router.get("/api/admin/conversations")
async def admin_conversations(
    limit: int = 30,
    status: str = None,
    channel: str = None,
    current_user: dict = Depends(get_current_admin)
):
    """List unified conversations across all channels."""
    query = {}
    if status:
        query["status"] = status
    if channel:
        query["channels"] = channel
    
    convos = []
    async for c in S.db.conversations.find(query, {"_id": 0}).sort("last_message_at", -1).limit(limit):
        # Resolve contact
        contact = await S.db.contacts.find_one({"contact_id": c.get("contact_id")}, {"_id": 0, "email": 1, "first_name": 1, "last_name": 1, "company": 1})
        convos.append({
            "conversation_id": c["conversation_id"],
            "contact": contact or {},
            "channels": c.get("channels", []),
            "status": c.get("status", "open"),
            "assigned_to": c.get("assigned_to", "ai"),
            "message_count": c.get("message_count", 0),
            "last_message_at": str(c.get("last_message_at", "")),
            "subject": c.get("subject", ""),
        })
    return {"conversations": convos}



@router.get("/api/admin/conversations/{conversation_id}")
async def admin_conversation_detail(
    conversation_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Full conversation with messages and context."""
    convo = await S.db.conversations.find_one({"conversation_id": conversation_id}, {"_id": 0})
    if not convo:
        raise HTTPException(404, "Konversation nicht gefunden")
    
    # Get messages
    messages = []
    async for m in S.db.messages.find({"conversation_id": conversation_id}, {"_id": 0}).sort("timestamp", 1):
        messages.append(m)
    
    # Get contact
    contact = await S.db.contacts.find_one({"contact_id": convo.get("contact_id")}, {"_id": 0})
    
    return {
        **convo,
        "messages": messages,
        "contact": contact,
    }



@router.post("/api/admin/conversations/{conversation_id}/reply")
async def admin_reply_to_conversation(
    conversation_id: str,
    data: dict,
    current_user: dict = Depends(get_current_admin)
):
    """Admin manually replies to a conversation."""
    convo = await S.db.conversations.find_one({"conversation_id": conversation_id}, {"_id": 0})
    if not convo:
        raise HTTPException(404, "Konversation nicht gefunden")
    
    content = data.get("content", "").strip()
    channel = data.get("channel", convo.get("channel_origin", "chat"))
    if not content:
        raise HTTPException(400, "Nachricht darf nicht leer sein")
    
    msg = create_message(conversation_id, channel, MessageDirection.OUTBOUND.value, content,
                         sender=current_user["email"], ai_generated=False)
    await S.db.messages.insert_one(msg)
    
    await S.db.conversations.update_one(
        {"conversation_id": conversation_id},
        {"$set": {"last_message_at": utcnow(), "updated_at": utcnow()},
         "$inc": {"message_count": 1},
         "$addToSet": {"channels": channel}}
    )
    
    # Log event
    evt = create_timeline_event("conversation", conversation_id, "admin_reply",
                                channel=channel, actor=current_user["email"], actor_type="admin")
    await S.db.timeline_events.insert_one(evt)
    
    return {"status": "ok", "message": {k: v for k, v in msg.items() if k != "_id"}}



# ══════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════
# AUDIT / HEALTH CHECK SYSTEM
# ══════════════════════════════════════════════════════════════


@router.get("/api/admin/whatsapp/status")
async def wa_status(current_user: dict = Depends(get_current_admin)):
    """Get current WhatsApp connector status."""
    session = await S.db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        session = create_whatsapp_session()
        await S.db.whatsapp_sessions.insert_one(session)
        session.pop("_id", None)
    return {
        "session_id": session.get("session_id", ""),
        "status": session.get("status", "unpaired"),
        "phone_number": session.get("phone_number", ""),
        "qr_code": session.get("qr_code"),
        "connected_at": str(session.get("connected_at", "")) if session.get("connected_at") else None,
        "last_activity": str(session.get("last_activity", "")) if session.get("last_activity") else None,
        "error": session.get("error"),
    }



@router.post("/api/admin/whatsapp/pair")
async def wa_pair(current_user: dict = Depends(get_current_admin)):
    """Initiate WhatsApp QR pairing. Generates a QR code placeholder.
    In production, this triggers the actual QR generation via the connector service."""
    session = await S.db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        session = create_whatsapp_session()
        await S.db.whatsapp_sessions.insert_one(session)
    
    # Generate pairing state (In production: triggers connector to generate real QR)
    import base64
    qr_placeholder = f"whatsapp://pair?session={session.get('session_id', '')}&ts={int(datetime.now(timezone.utc).timestamp())}"
    
    await S.db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {
            "status": WhatsAppSessionStatus.PAIRING.value,
            "qr_code": qr_placeholder,
            "qr_generated_at": utcnow(),
            "updated_at": utcnow(),
        }}
    )
    
    evt = create_timeline_event("whatsapp", session["session_id"], "pairing_initiated",
                                actor=current_user["email"], actor_type="admin")
    await S.db.timeline_events.insert_one(evt)
    
    return {
        "status": "pairing",
        "session_id": session["session_id"],
        "qr_code": qr_placeholder,
        "message": "QR-Code bereit. In der Produktivumgebung wird hier der echte WhatsApp-QR angezeigt.",
    }



@router.post("/api/admin/whatsapp/disconnect")
async def wa_disconnect(current_user: dict = Depends(get_current_admin)):
    """Disconnect WhatsApp session."""
    session = await S.db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        raise HTTPException(404, "Keine WhatsApp-Session gefunden")
    
    await S.db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {
            "status": WhatsAppSessionStatus.DISCONNECTED.value,
            "disconnected_at": utcnow(),
            "qr_code": None,
            "updated_at": utcnow(),
        }}
    )
    
    evt = create_timeline_event("whatsapp", session["session_id"], "session_disconnected",
                                actor=current_user["email"], actor_type="admin")
    await S.db.timeline_events.insert_one(evt)
    
    return {"status": "disconnected"}



@router.post("/api/admin/whatsapp/reset")
async def wa_reset(current_user: dict = Depends(get_current_admin)):
    """Reset WhatsApp session completely."""
    new_session = create_whatsapp_session()
    await S.db.whatsapp_sessions.delete_many({})
    await S.db.whatsapp_sessions.insert_one(new_session)
    
    evt = create_timeline_event("whatsapp", new_session["session_id"], "session_reset",
                                actor=current_user["email"], actor_type="admin")
    await S.db.timeline_events.insert_one(evt)
    
    return {"status": "reset", "session_id": new_session["session_id"]}



@router.post("/api/admin/whatsapp/reconnect")
async def wa_reconnect(current_user: dict = Depends(get_current_admin)):
    """Attempt to reconnect a disconnected/failed WhatsApp session."""
    session = await S.db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        raise HTTPException(404, "Keine WhatsApp-Session gefunden")
    if session.get("status") == "connected":
        return {"status": "already_connected"}
    await S.db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {"status": WhatsAppSessionStatus.RECONNECTING.value, "error": None, "updated_at": utcnow()}}
    )
    evt = create_timeline_event("whatsapp", session["session_id"], "reconnect_initiated",
                                actor=current_user["email"], actor_type="admin")
    await S.db.timeline_events.insert_one(evt)
    return {"status": "reconnecting", "session_id": session["session_id"]}



@router.post("/api/admin/whatsapp/simulate-connect")
async def wa_simulate_connect(current_user: dict = Depends(get_current_admin)):
    """DEV ONLY: Simulate a successful WhatsApp connection for testing."""
    session = await S.db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    if not session:
        session = create_whatsapp_session()
        await S.db.whatsapp_sessions.insert_one(session)
    await S.db.whatsapp_sessions.update_one(
        {"session_id": session["session_id"]},
        {"$set": {
            "status": WhatsAppSessionStatus.CONNECTED.value,
            "phone_number": "+31613318856",
            "connected_at": utcnow(),
            "last_activity": utcnow(),
            "qr_code": None,
            "error": None,
            "updated_at": utcnow(),
        }}
    )
    evt = create_timeline_event("whatsapp", session["session_id"], "session_connected",
                                actor=current_user["email"], actor_type="admin",
                                details={"phone": "+31613318856", "mode": "simulated"})
    await S.db.timeline_events.insert_one(evt)
    return {"status": "connected", "session_id": session["session_id"], "phone_number": "+31613318856"}



@router.post("/api/admin/whatsapp/send")
async def wa_send_message(data: dict, current_user: dict = Depends(get_current_admin)):
    """Send a WhatsApp message to a contact (via bridge connector).
    In production, this calls the actual WA connector to deliver the message."""
    to_phone = data.get("to", "").strip()
    content = data.get("content", "").strip()
    conversation_id = data.get("conversation_id", "").strip()
    if not content:
        raise HTTPException(400, "Nachricht darf nicht leer sein")

    # Find or resolve conversation
    convo = None
    if conversation_id:
        convo = await S.db.conversations.find_one({"conversation_id": conversation_id}, {"_id": 0})
    elif to_phone:
        contact = await S.db.contacts.find_one({"$or": [{"phone": to_phone}, {"whatsapp": to_phone}]}, {"_id": 0})
        if not contact:
            contact = create_contact(f"wa_{to_phone}@placeholder.nexifyai.de", phone=to_phone, whatsapp=to_phone, source="whatsapp")
            await S.db.contacts.insert_one(contact)
            contact.pop("_id", None)
        convo = await S.db.conversations.find_one({
            "contact_id": contact["contact_id"], "channels": Channel.WHATSAPP.value,
            "status": {"$in": ["open", "pending"]}
        }, {"_id": 0})
        if not convo:
            convo = create_conversation(contact["contact_id"], Channel.WHATSAPP.value, subject=f"WhatsApp: {to_phone}")
            await S.db.conversations.insert_one(convo)
            convo.pop("_id", None)
    else:
        raise HTTPException(400, "Entweder 'to' (Telefonnummer) oder 'conversation_id' muss angegeben werden")

    msg = create_message(convo["conversation_id"], Channel.WHATSAPP.value,
                         MessageDirection.OUTBOUND.value, content,
                         sender=current_user["email"], ai_generated=False)
    await S.db.messages.insert_one(msg)
    await S.db.conversations.update_one(
        {"conversation_id": convo["conversation_id"]},
        {"$set": {"last_message_at": utcnow(), "updated_at": utcnow()}, "$inc": {"message_count": 1}}
    )
    evt = create_timeline_event("conversation", convo["conversation_id"], "whatsapp_outbound",
                                channel=Channel.WHATSAPP.value, actor=current_user["email"], actor_type="admin",
                                details={"to": to_phone, "content_preview": content[:100]})
    await S.db.timeline_events.insert_one(evt)
    await S.db.whatsapp_sessions.update_one({}, {"$set": {"last_activity": utcnow()}})
    return {"status": "sent", "message_id": msg["message_id"], "conversation_id": convo["conversation_id"]}



@router.get("/api/admin/whatsapp/messages")
async def wa_messages(
    limit: int = 50,
    current_user: dict = Depends(get_current_admin)
):
    """List WhatsApp messages from the unified message store."""
    msgs = []
    async for m in S.db.messages.find({"channel": Channel.WHATSAPP.value}, {"_id": 0}).sort("timestamp", -1).limit(limit):
        convo = await S.db.conversations.find_one({"conversation_id": m.get("conversation_id")}, {"_id": 0, "contact_id": 1})
        contact = None
        if convo:
            contact = await S.db.contacts.find_one({"contact_id": convo.get("contact_id")}, {"_id": 0, "email": 1, "first_name": 1, "last_name": 1, "phone": 1})
        msgs.append({**m, "contact": contact, "timestamp": str(m.get("timestamp", ""))})
    return {"messages": msgs}


# ══════════════════════════════════════════════════════════════
# WEBHOOK: Inbound WhatsApp / Email messages
# ══════════════════════════════════════════════════════════════


@router.post("/api/webhooks/whatsapp/inbound")
async def wa_inbound_webhook(data: dict):
    """Receive inbound WhatsApp messages from connector.
    Creates/updates conversation and routes to AI if needed."""
    phone = data.get("from", "").strip()
    content = data.get("body", "").strip()
    if not phone or not content:
        raise HTTPException(400, "Missing from or body")
    
    # Find or create contact by phone
    contact = await S.db.contacts.find_one({"$or": [{"phone": phone}, {"whatsapp": phone}]}, {"_id": 0})
    if not contact:
        contact = create_contact(f"wa_{phone}@placeholder.nexifyai.de", phone=phone, whatsapp=phone, source="whatsapp")
        await S.db.contacts.insert_one(contact)
        contact.pop("_id", None)
    
    # Find open conversation or create new
    convo = await S.db.conversations.find_one({
        "contact_id": contact["contact_id"],
        "status": {"$in": ["open", "pending"]},
        "channels": Channel.WHATSAPP.value,
    }, {"_id": 0})
    
    if not convo:
        convo = create_conversation(contact["contact_id"], Channel.WHATSAPP.value,
                                     subject=f"WhatsApp: {phone}")
        await S.db.conversations.insert_one(convo)
        convo.pop("_id", None)
    
    # Store message
    msg = create_message(convo["conversation_id"], Channel.WHATSAPP.value,
                         MessageDirection.INBOUND.value, content, sender=phone)
    await S.db.messages.insert_one(msg)
    
    # Update conversation
    await S.db.conversations.update_one(
        {"conversation_id": convo["conversation_id"]},
        {"$set": {"last_message_at": utcnow(), "updated_at": utcnow()},
         "$inc": {"message_count": 1}}
    )
    
    # Log event
    evt = create_timeline_event("conversation", convo["conversation_id"], "whatsapp_inbound",
                                channel=Channel.WHATSAPP.value, actor=phone, actor_type="customer",
                                details={"content_preview": content[:100]})
    await S.db.timeline_events.insert_one(evt)
    
    # Update WhatsApp session activity
    await S.db.whatsapp_sessions.update_one({}, {"$set": {"last_activity": utcnow()}})
    
    return {"status": "received", "message_id": msg["message_id"], "conversation_id": convo["conversation_id"]}


# ══════════════════════════════════════════════════════════════
# WORKER/SCHEDULER MONITORING ENDPOINTS
# ══════════════════════════════════════════════════════════════


@router.get("/api/admin/comms/contacts/{email}")
async def comms_contact_detail(email: str, current_user: dict = Depends(get_current_admin)):
    """Kontakt-Detail mit allen Konversationen."""
    contact = await S.db.contacts.find_one({"email": email.lower()}, {"_id": 0})
    if not contact:
        raise HTTPException(404, "Kontakt nicht gefunden")
    for k in ("created_at", "updated_at"):
        if hasattr(contact.get(k), "isoformat"):
            contact[k] = contact[k].isoformat()
    convs = await S.comms_svc.get_contact_conversations(contact["contact_id"])
    timeline = await S.comms_svc.get_unified_timeline(contact["contact_id"])
    return {"contact": contact, "conversations": convs, "timeline": timeline}



@router.get("/api/admin/comms/conversations/{conv_id}/messages")
async def comms_conversation_messages(conv_id: str, current_user: dict = Depends(get_current_admin)):
    """Kanalübergreifende Nachrichtenhistorie."""
    messages = await S.comms_svc.get_conversation_history(conv_id)
    return {"messages": messages, "count": len(messages)}



@router.post("/api/admin/comms/conversations/{conv_id}/send")
async def comms_send_message(conv_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Nachricht über Kommunikationskern senden."""
    channel = data.get("channel", "email")
    content = data.get("content", "")
    if not content:
        raise HTTPException(400, "Nachricht darf nicht leer sein")
    msg = await S.comms_svc.send_outbound(
        conv_id, channel, content,
        sender=current_user["email"],
        ai_generated=False,
    )
    msg.pop("_id", None)
    if hasattr(msg.get("timestamp"), "isoformat"):
        msg["timestamp"] = msg["timestamp"].isoformat()
    return msg



@router.post("/api/admin/comms/conversations/{conv_id}/assign")
async def comms_assign(conv_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Konversation zuweisen."""
    await S.comms_svc.assign_conversation(conv_id, data.get("assigned_to", "admin"), by=current_user["email"])
    return {"assigned": True}



@router.get("/api/admin/comms/timeline/{contact_id}")
async def comms_timeline(contact_id: str, current_user: dict = Depends(get_current_admin)):
    """Kanalübergreifende Timeline."""
    events = await S.comms_svc.get_unified_timeline(contact_id)
    return {"events": events, "count": len(events)}


# ══════════════════════════════════════════════════════════════
# BILLING SERVICE ENDPOINTS
# ══════════════════════════════════════════════════════════════

