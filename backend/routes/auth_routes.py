"""NeXifyAI — Auth Routes"""
import os
import hashlib
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from routes.shared import S
from routes.shared import (
    create_access_token,
    get_current_admin,
    get_current_customer,
    verify_password,
    check_rate_limit,
    log_audit,
    send_email,
    email_template,
    logger,
)
from domain import create_contact, create_timeline_event, utcnow
from memory_service import AGENT_IDS
from commercial import generate_access_token, verify_access_token

router = APIRouter(tags=["auth"])

@router.post("/api/admin/login")
async def admin_login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None):
    if request:
        await check_rate_limit(request, limit=20, window=300)
    
    user = await S.db.admin_users.find_one({"email": form_data.username.lower()})
    if not user or not verify_password(form_data.password, user["password_hash"]):
        await log_audit("login_failed", form_data.username)
        raise HTTPException(status_code=401, detail="Ungültige Anmeldedaten")
    
    token = create_access_token({"sub": user["email"], "role": "admin"})
    await log_audit("login_success", user["email"])
    
    return {"access_token": token, "token_type": "bearer"}


# ============== UNIFIED AUTH (Admin + Kunde) ==============


@router.post("/api/auth/check-email")
async def auth_check_email(data: dict):
    """Prüfe ob E-Mail ein Admin oder Kunde ist."""
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    admin = await S.db.admin_users.find_one({"email": email})
    if admin:
        return {"role": "admin", "needs_password": True}
    
    contact = await S.db.contacts.find_one({"email": email})
    lead = await S.db.leads.find_one({"email": email})
    if contact or lead:
        return {"role": "customer", "needs_magic_link": True}
    
    return {"role": "unknown"}



@router.post("/api/auth/request-magic-link")
async def auth_request_magic_link(data: dict, request: Request):
    """Magic Link per E-Mail an Kunden senden."""
    if request:
        await check_rate_limit(request, limit=5, window=300)
    
    email = data.get("email", "").strip().lower()
    if not email:
        raise HTTPException(400, "E-Mail ist Pflichtfeld")
    
    # Prüfe ob Kontakt/Lead existiert
    contact = await S.db.contacts.find_one({"email": email})
    lead = await S.db.leads.find_one({"email": email})
    if not contact and not lead:
        raise HTTPException(404, "Kein Konto für diese E-Mail gefunden")
    
    # Erstelle Portal-Zugangstoken
    token_data = generate_access_token(email, "portal")
    await S.db.access_links.insert_one({
        "token_hash": token_data["token_hash"],
        "customer_email": email,
        "customer_name": (contact or {}).get("first_name", (lead or {}).get("vorname", "")) + " " + (contact or {}).get("last_name", (lead or {}).get("nachname", "")),
        "document_type": "portal",
        "expires_at": token_data["expires_at"],
        "created_at": token_data["created_at"],
        "created_by": "system_magic_link",
    })
    
    base_url = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
    magic_link = f"{base_url}/login/verify?token={token_data['token']}"
    
    # E-Mail senden
    if S.RESEND_API_KEY:
        try:
            html = email_template(
                "Ihr Portalzugang — NeXifyAI",
                "<p>Hallo,</p>"
                "<p>Sie haben einen Zugangslink für Ihr NeXifyAI-Kundenportal angefordert.</p>"
                "<p>Klicken Sie auf den Button, um sich einzuloggen. Der Link ist 24 Stunden gültig.</p>",
                magic_link,
                "Zum Portal"
            )
            await send_email([email], "Ihr Portalzugang — NeXifyAI", html, category="portal_access", ref_id=email)
        except Exception as e:
            logger.error(f"Magic Link E-Mail Fehler: {e}")
    
    await log_audit("magic_link_requested", email)
    
    return {"status": "ok", "message": "Magic Link wurde per E-Mail gesendet"}



@router.post("/api/auth/verify-token")
async def auth_verify_token(data: dict):
    """Magic Link Token verifizieren → JWT mit role=customer zurückgeben."""
    token = data.get("token", "").strip()
    if not token:
        raise HTTPException(400, "Token fehlt")
    
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    link = await S.db.access_links.find_one({"token_hash": token_hash})
    if not link:
        raise HTTPException(403, "Zugangslink ungültig")
    
    expires = link.get("expires_at")
    if expires:
        if isinstance(expires, str):
            from dateutil.parser import parse as dateparse
            expires = dateparse(expires)
        if expires < datetime.now(timezone.utc):
            raise HTTPException(403, "Zugangslink abgelaufen")
    
    email = link.get("customer_email", "").lower()
    if not email:
        raise HTTPException(400, "Kein Kundenkonto verknüpft")
    
    # JWT mit role=customer erstellen
    jwt_token = create_access_token(
        {"sub": email, "role": "customer"},
        expires_delta=timedelta(hours=24)
    )
    
    await log_audit("customer_login_magic_link", email)
    
    # mem0 Memory Write
    if S.memory_svc:
        contact = await S.db.contacts.find_one({"email": email})
        if contact:
            await S.memory_svc.write(contact["contact_id"], "Kunde hat sich über Magic Link eingeloggt",
                                   AGENT_IDS["system"], category="context", source="auth",
                                   verification_status="verifiziert")
    
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "role": "customer",
        "email": email,
        "customer_name": link.get("customer_name", "")
    }


# ============== CUSTOMER PORTAL JWT-AUTH ENDPOINTS ==============


@router.get("/api/customer/me")
async def customer_me(user = Depends(get_current_customer)):
    """Kundenprofil — JWT-authentifiziert."""
    return {
        "email": user["email"],
        "role": "customer",
        "contact": {k: v for k, v in user["contact"].items() if k not in ("_id",)}
    }



@router.get("/api/admin/me")
async def admin_me(user = Depends(get_current_admin)):
    return {"email": user["email"], "role": user.get("role", "admin")}


@router.get("/api/admin/memory/agents")
async def admin_memory_agents(current_user: dict = Depends(get_current_admin)):
    """Liste aller bekannten Agent-IDs für mem0."""
    return {"agents": AGENT_IDS}


@router.get("/api/admin/memory/by-agent/{agent_id}")
async def admin_memory_by_agent(agent_id: str, limit: int = 30, current_user: dict = Depends(get_current_admin)):
    """Alle Memory-Einträge eines bestimmten Agenten."""
    entries = await S.memory_svc.get_agent_history(agent_id, limit)
    for e in entries:
        for k, v in list(e.items()):
            if hasattr(v, 'isoformat'):
                e[k] = str(v)
    return {"agent_id": agent_id, "entries": entries, "count": len(entries)}


@router.get("/api/admin/memory/search")
async def admin_memory_search(q: str, contact_id: str = None, limit: int = 20, current_user: dict = Depends(get_current_admin)):
    """Text-Suche über alle Memory-Einträge."""
    results = await S.memory_svc.search(q, contact_id, limit)
    for r in results:
        for k, v in list(r.items()):
            if hasattr(v, 'isoformat'):
                r[k] = str(v)
    return {"query": q, "results": results, "count": len(results)}



# --- Admin: Chat Sessions ---

