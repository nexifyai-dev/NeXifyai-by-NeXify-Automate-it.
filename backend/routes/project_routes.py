"""NeXifyAI — Project Routes"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import S
from routes.shared import (
    get_current_admin,
    get_current_customer,
    logger,
)
from domain import (
    create_project, create_project_section, create_project_chat_message,
    create_project_version, create_timeline_event,
    PROJECT_SECTIONS, PROJECT_SECTION_LABELS,
    utcnow,
)
from memory_service import AGENT_IDS

router = APIRouter(tags=["project"])

@router.post("/api/admin/projects")
async def create_project_endpoint(data: dict, current_user: dict = Depends(get_current_admin)):
    """Neues Projekt anlegen."""
    email = data.get("customer_email", "")
    title = data.get("title", "")
    if not email or not title:
        raise HTTPException(400, "customer_email und title erforderlich")
    project = create_project(
        email, title,
        tier=data.get("tier", ""),
        quote_id=data.get("quote_id", ""),
        classification=data.get("classification", ""),
        tags=data.get("tags", []),
        created_by=current_user["email"],
        assigned_to=data.get("assigned_to", current_user["email"]),
        contact_id=data.get("contact_id", ""),
    )
    await S.db.projects.insert_one({**project})
    # Timeline
    await S.db.timeline_events.insert_one(create_timeline_event(
        "project", project["project_id"], "project_created",
        actor=current_user["email"], actor_type="admin",
        details={"title": title, "customer": email},
    ))
    # Memory
    if S.memory_svc:
        await S.memory_svc.write(
            project.get("contact_id", email), f"Projekt erstellt: {title}",
            agent_id="planning_agent", category="project",
            source="admin", source_ref=project["project_id"],
        )
    project.pop("_id", None)
    return project



@router.get("/api/admin/projects")
async def list_projects(
    status: str = None, customer_email: str = None,
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Projekte auflisten."""
    query = {}
    if status:
        query["status"] = status
    if customer_email:
        query["customer_email"] = customer_email.lower()
    projects = []
    async for p in S.db.projects.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit):
        # Completeness
        sections_status = p.get("sections_status", {})
        total = len(PROJECT_SECTIONS)
        done = sum(1 for v in sections_status.values() if v in ("freigegeben", "review"))
        p["completeness"] = round(done / total * 100) if total else 0
        projects.append(p)
    total_count = await S.db.projects.count_documents(query)
    return {"projects": projects, "total": total_count}



@router.get("/api/admin/projects/{project_id}")
async def get_project(project_id: str, current_user: dict = Depends(get_current_admin)):
    """Projekt-Detail mit allen Sektionen."""
    project = await S.db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    # Load sections
    sections = []
    async for s in S.db.project_sections.find({"project_id": project_id}, {"_id": 0}).sort("created_at", 1):
        sections.append(s)
    # Load latest chat messages
    chat = []
    async for m in S.db.project_chat.find({"project_id": project_id}, {"_id": 0}).sort("timestamp", -1).limit(30):
        chat.append(m)
    chat.reverse()
    # Latest version
    latest_version = await S.db.project_versions.find_one(
        {"project_id": project_id}, {"_id": 0}, sort=[("version", -1)]
    )
    project["sections"] = sections
    project["chat"] = chat
    project["latest_version"] = latest_version
    project["section_definitions"] = PROJECT_SECTION_LABELS

    # P5: Projektstatus aus echten Entitäten ableiten
    derived_status = {}
    qid = project.get("quote_id")
    cid = project.get("contract_id")
    customer_email = project.get("customer", {}).get("email", "")
    if qid:
        quote = await S.db.quotes.find_one({"quote_id": qid}, {"_id": 0, "status": 1, "payment_status": 1, "quote_number": 1})
        if quote:
            derived_status["quote"] = {"id": qid, "number": quote.get("quote_number"), "status": quote.get("status"), "payment_status": quote.get("payment_status")}
    if cid:
        contract = await S.db.contracts.find_one({"contract_id": cid}, {"_id": 0, "status": 1, "contract_number": 1, "accepted_at": 1})
        if contract:
            derived_status["contract"] = {"id": cid, "number": contract.get("contract_number"), "status": contract.get("status"), "accepted_at": str(contract.get("accepted_at", "")) if contract.get("accepted_at") else None}
    if qid:
        inv = await S.db.invoices.find_one({"quote_id": qid}, {"_id": 0, "invoice_id": 1, "invoice_number": 1, "payment_status": 1})
        if inv:
            derived_status["invoice"] = {"id": inv["invoice_id"], "number": inv.get("invoice_number"), "payment_status": inv.get("payment_status")}
    if customer_email:
        inv_count = await S.db.invoices.count_documents({"customer.email": customer_email, "payment_status": "paid"})
        derived_status["payments_completed"] = inv_count

    # Derive build readiness
    is_build_ready = (
        derived_status.get("contract", {}).get("status") == "accepted"
        and derived_status.get("invoice", {}).get("payment_status") == "paid"
    )
    derived_status["build_ready"] = is_build_ready
    derived_status["phase"] = (
        "build_ready" if is_build_ready
        else "payment_pending" if derived_status.get("contract", {}).get("status") == "accepted"
        else "contract_pending" if derived_status.get("quote", {}).get("status") == "accepted"
        else "quote_pending" if qid
        else "discovery"
    )
    project["derived_status"] = derived_status

    return project



@router.patch("/api/admin/projects/{project_id}")
async def update_project(project_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Projekt-Metadaten aktualisieren."""
    allowed = {"title", "status", "tier", "quote_id", "contract_id", "classification", "tags", "assigned_to", "risks"}
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        raise HTTPException(400, "Keine gültigen Felder")
    updates["updated_at"] = utcnow()
    old = await S.db.projects.find_one({"project_id": project_id}, {"_id": 0, "status": 1, "customer_email": 1, "contact_id": 1})
    if not old:
        raise HTTPException(404, "Projekt nicht gefunden")
    await S.db.projects.update_one({"project_id": project_id}, {"$set": updates})
    # Status change → Timeline
    if "status" in updates and updates["status"] != old.get("status"):
        await S.db.timeline_events.insert_one(create_timeline_event(
            "project", project_id, "project_status_changed",
            actor=current_user["email"], actor_type="admin",
            details={"old": old.get("status"), "new": updates["status"]},
        ))
        if S.memory_svc:
            await S.memory_svc.write(
                old.get("contact_id", old.get("customer_email", "")),
                f"Projektstatus: {old.get('status')} → {updates['status']}",
                agent_id="planning_agent", category="project",
                source="admin", source_ref=project_id,
            )
    return {"updated": True}



@router.post("/api/admin/projects/{project_id}/sections")
async def upsert_project_section(project_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Sektion erstellen oder aktualisieren (versioniert)."""
    section_key = data.get("section_key", "")
    content = data.get("content", "")
    if not section_key or section_key not in PROJECT_SECTIONS:
        raise HTTPException(400, f"Ungültige section_key. Erlaubt: {', '.join(PROJECT_SECTIONS)}")
    if not content.strip():
        raise HTTPException(400, "content darf nicht leer sein")
    project = await S.db.projects.find_one({"project_id": project_id}, {"_id": 0, "project_id": 1})
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    # Check existing
    existing = await S.db.project_sections.find_one(
        {"project_id": project_id, "section_key": section_key}, {"_id": 0}
    )
    if existing:
        new_version = existing.get("version", 1) + 1
        await S.db.project_sections.update_one(
            {"project_id": project_id, "section_key": section_key},
            {"$set": {
                "content": content,
                "version": new_version,
                "status": data.get("status", "entwurf"),
                "author": current_user["email"],
                "updated_at": utcnow(),
            }}
        )
        section_id = existing["section_id"]
    else:
        section = create_project_section(
            project_id, section_key, content,
            author=current_user["email"],
            status=data.get("status", "entwurf"),
        )
        await S.db.project_sections.insert_one({**section})
        section_id = section["section_id"]
        new_version = 1
    # Update sections_status on project
    sec_status = data.get("status", "entwurf")
    await S.db.projects.update_one(
        {"project_id": project_id},
        {"$set": {f"sections_status.{section_key}": sec_status, "updated_at": utcnow()}}
    )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "project", project_id, "section_updated",
        actor=current_user["email"], actor_type="admin",
        details={"section": section_key, "version": new_version, "status": sec_status},
    ))
    return {"section_id": section_id, "version": new_version, "status": sec_status}



@router.get("/api/admin/projects/{project_id}/sections")
async def list_project_sections(project_id: str, current_user: dict = Depends(get_current_admin)):
    """Alle Sektionen eines Projekts."""
    sections = []
    async for s in S.db.project_sections.find({"project_id": project_id}, {"_id": 0}).sort("created_at", 1):
        sections.append(s)
    return {"sections": sections, "definitions": PROJECT_SECTION_LABELS}



@router.post("/api/admin/projects/{project_id}/sections/{section_key}/review")
async def review_project_section(project_id: str, section_key: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Review-Kommentar zu einer Sektion hinzufügen."""
    comment = data.get("comment", "")
    new_status = data.get("status", "")
    if not comment:
        raise HTTPException(400, "comment erforderlich")
    existing = await S.db.project_sections.find_one(
        {"project_id": project_id, "section_key": section_key}, {"_id": 0}
    )
    if not existing:
        raise HTTPException(404, "Sektion nicht gefunden")
    review_entry = {
        "review_id": new_id("rev"),
        "comment": comment,
        "author": current_user["email"],
        "timestamp": utcnow().isoformat(),
        "status": new_status or existing.get("status", "entwurf"),
    }
    update_set = {"updated_at": utcnow()}
    if new_status:
        update_set["status"] = new_status
    await S.db.project_sections.update_one(
        {"project_id": project_id, "section_key": section_key},
        {"$push": {"review_comments": review_entry}, "$set": update_set}
    )
    if new_status:
        await S.db.projects.update_one(
            {"project_id": project_id},
            {"$set": {f"sections_status.{section_key}": new_status, "updated_at": utcnow()}}
        )
    return {"review_id": review_entry["review_id"], "added": True}



@router.post("/api/admin/projects/{project_id}/chat")
async def add_project_chat(project_id: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Nachricht im Projektchat senden."""
    content = data.get("content", "")
    if not content.strip():
        raise HTTPException(400, "content erforderlich")
    project = await S.db.projects.find_one({"project_id": project_id}, {"_id": 0, "project_id": 1})
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    msg = create_project_chat_message(
        project_id, current_user["email"], content,
        sender_type="admin",
        metadata=data.get("metadata", {}),
    )
    await S.db.project_chat.insert_one({**msg})
    msg.pop("_id", None)
    if hasattr(msg.get("timestamp"), "isoformat"):
        msg["timestamp"] = msg["timestamp"].isoformat()
    return msg



@router.get("/api/admin/projects/{project_id}/chat")
async def get_project_chat(project_id: str, limit: int = 50, current_user: dict = Depends(get_current_admin)):
    """Projektchat-Verlauf."""
    messages = []
    async for m in S.db.project_chat.find({"project_id": project_id}, {"_id": 0}).sort("timestamp", -1).limit(limit):
        if hasattr(m.get("timestamp"), "isoformat"):
            m["timestamp"] = m["timestamp"].isoformat()
        messages.append(m)
    messages.reverse()
    return {"messages": messages, "count": len(messages)}



@router.post("/api/admin/projects/{project_id}/build-handover")
async def generate_build_handover(project_id: str, data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Build-Ready-Markdown generieren und versionieren."""
    project = await S.db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    # Collect all sections
    sections = {}
    async for s in S.db.project_sections.find({"project_id": project_id}, {"_id": 0}).sort("created_at", 1):
        sections[s["section_key"]] = s
    # Build markdown
    md_parts = [f"# Build-Handover: {project.get('title', 'Projekt')}"]
    md_parts.append(f"\n**Kunde:** {project.get('customer_email', '')}")
    md_parts.append(f"**Tarif:** {project.get('tier', '-')}")
    md_parts.append(f"**Status:** {project.get('status', 'draft')}")
    md_parts.append(f"**Erstellt:** {project.get('created_at', '')}")
    md_parts.append(f"**Version:** {project.get('build_handover_version', 0) + 1}")
    md_parts.append("")
    for sk in PROJECT_SECTIONS:
        label = PROJECT_SECTION_LABELS.get(sk, sk)
        sec = sections.get(sk)
        if sk == "startprompt_emergent":
            continue  # Geheim — nicht im Handover-Dokument
        if sec:
            md_parts.append(f"## {label}")
            md_parts.append(f"*Status: {sec.get('status', 'entwurf')} | Version: {sec.get('version', 1)}*")
            md_parts.append("")
            md_parts.append(sec.get("content", ""))
            md_parts.append("")
        else:
            md_parts.append(f"## {label}")
            md_parts.append("*— ausstehend —*")
            md_parts.append("")
    markdown = "\n".join(md_parts)
    # Generate start prompt from real context
    start_prompt_parts = [f"Projektkontext: {project.get('title', '')}"]
    for sk in ["projektsteckbrief", "scope_dokument", "systemarchitektur_integrationsplan", "work_packages", "build_ready_markdown"]:
        sec = sections.get(sk)
        if sec:
            start_prompt_parts.append(f"\n### {PROJECT_SECTION_LABELS.get(sk, sk)}\n{sec.get('content', '')}")
    start_prompt = "\n".join(start_prompt_parts)
    # Version
    new_ver = project.get("build_handover_version", 0) + 1
    version_doc = create_project_version(
        project_id, new_ver, markdown,
        start_prompt=start_prompt,
        changelog=(data or {}).get("changelog", f"Version {new_ver}"),
        author=current_user["email"],
    )
    await S.db.project_versions.insert_one({**version_doc})
    await S.db.projects.update_one(
        {"project_id": project_id},
        {"$set": {"build_handover_version": new_ver, "updated_at": utcnow()}}
    )
    await S.db.timeline_events.insert_one(create_timeline_event(
        "project", project_id, "build_handover_generated",
        actor=current_user["email"], actor_type="admin",
        details={"version": new_ver},
    ))
    version_doc.pop("_id", None)
    if hasattr(version_doc.get("created_at"), "isoformat"):
        version_doc["created_at"] = version_doc["created_at"].isoformat()
    return version_doc



@router.get("/api/admin/projects/{project_id}/versions")
async def list_project_versions(project_id: str, current_user: dict = Depends(get_current_admin)):
    """Versionsverlauf des Build-Handovers."""
    versions = []
    async for v in S.db.project_versions.find({"project_id": project_id}, {"_id": 0}).sort("version", -1):
        if hasattr(v.get("created_at"), "isoformat"):
            v["created_at"] = v["created_at"].isoformat()
        versions.append(v)
    return {"versions": versions, "count": len(versions)}



@router.get("/api/admin/projects/{project_id}/download-handover")
async def download_handover(project_id: str, version: int = None, current_user: dict = Depends(get_current_admin)):
    """Build-Ready-Markdown als Datei herunterladen."""
    from fastapi.responses import Response
    query = {"project_id": project_id}
    if version:
        query["version"] = version
    doc = await S.db.project_versions.find_one(query, {"_id": 0}, sort=[("version", -1)])
    if not doc:
        raise HTTPException(404, "Keine Handover-Version gefunden")
    project = await S.db.projects.find_one({"project_id": project_id}, {"_id": 0, "title": 1})
    title = (project or {}).get("title", "project").replace(" ", "_").lower()[:30]
    filename = f"build-handover_{title}_v{doc.get('version', 1)}.md"
    return Response(
        content=doc.get("markdown", ""),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )



@router.get("/api/admin/projects/{project_id}/start-prompt")
async def get_start_prompt(project_id: str, current_user: dict = Depends(get_current_admin)):
    """Startprompt aus dem neuesten Build-Handover (nur Admin, geheim)."""
    doc = await S.db.project_versions.find_one({"project_id": project_id}, {"_id": 0}, sort=[("version", -1)])
    if not doc:
        raise HTTPException(404, "Keine Handover-Version")
    return {"start_prompt": doc.get("start_prompt", ""), "version": doc.get("version", 1)}



@router.get("/api/admin/projects/{project_id}/completeness")
async def project_completeness(project_id: str, current_user: dict = Depends(get_current_admin)):
    """Planungsvollständigkeit prüfen."""
    project = await S.db.projects.find_one({"project_id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    sections_status = project.get("sections_status", {})
    result = []
    for sk in PROJECT_SECTIONS:
        st = sections_status.get(sk, "leer")
        result.append({
            "section_key": sk,
            "label": PROJECT_SECTION_LABELS.get(sk, sk),
            "status": st,
            "complete": st in ("freigegeben", "review"),
        })
    total = len(PROJECT_SECTIONS)
    done = sum(1 for r in result if r["complete"])
    missing = [r["label"] for r in result if not r["complete"]]
    return {
        "total": total,
        "done": done,
        "percent": round(done / total * 100) if total else 0,
        "sections": result,
        "missing": missing,
        "ready_for_build": done == total,
    }


# Customer-facing project endpoints

@router.get("/api/customer/projects")
async def customer_projects(current_user: dict = Depends(get_current_customer)):
    """Kundenprojekte anzeigen."""
    email = current_user["email"]
    projects = []
    async for p in S.db.projects.find({"customer_email": email}, {"_id": 0}).sort("created_at", -1):
        sections_status = p.get("sections_status", {})
        total = len(PROJECT_SECTIONS)
        done = sum(1 for v in sections_status.values() if v in ("freigegeben", "review"))
        p["completeness"] = round(done / total * 100) if total else 0
        # Remove internal sections from customer view
        p.pop("sections_status", None)
        projects.append(p)
    return {"projects": projects}



@router.get("/api/customer/projects/{project_id}")
async def customer_project_detail(project_id: str, current_user: dict = Depends(get_current_customer)):
    """Projekt-Detail für Kunden (ohne interne Sektionen)."""
    email = current_user["email"]
    project = await S.db.projects.find_one({"project_id": project_id, "customer_email": email}, {"_id": 0})
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    # Load non-internal sections
    hidden_sections = {"startprompt_emergent"}
    sections = []
    async for s in S.db.project_sections.find({"project_id": project_id}, {"_id": 0}).sort("created_at", 1):
        if s.get("section_key") not in hidden_sections:
            sections.append(s)
    # Chat (only customer-visible)
    chat = []
    async for m in S.db.project_chat.find(
        {"project_id": project_id, "sender_type": {"$ne": "internal"}},
        {"_id": 0}
    ).sort("timestamp", -1).limit(30):
        if hasattr(m.get("timestamp"), "isoformat"):
            m["timestamp"] = m["timestamp"].isoformat()
        chat.append(m)
    chat.reverse()
    latest_version = await S.db.project_versions.find_one(
        {"project_id": project_id}, {"_id": 0, "start_prompt": 0}, sort=[("version", -1)]
    )
    if latest_version and hasattr(latest_version.get("created_at"), "isoformat"):
        latest_version["created_at"] = latest_version["created_at"].isoformat()
    project["sections"] = sections
    project["chat"] = chat
    project["latest_version"] = latest_version
    sections_status = project.get("sections_status", {})
    total = len(PROJECT_SECTIONS)
    done = sum(1 for v in sections_status.values() if v in ("freigegeben", "review"))
    project["completeness"] = round(done / total * 100) if total else 0
    project.pop("sections_status", None)

    # P5: Projektstatus für Kunden aus echten Entitäten
    derived = {}
    qid = project.get("quote_id")
    cid = project.get("contract_id")
    if qid:
        quote = await S.db.quotes.find_one({"quote_id": qid}, {"_id": 0, "status": 1, "payment_status": 1})
        if quote:
            derived["quote_status"] = quote.get("status")
    if cid:
        contract = await S.db.contracts.find_one({"contract_id": cid}, {"_id": 0, "status": 1, "accepted_at": 1})
        if contract:
            derived["contract_status"] = contract.get("status")
    if qid:
        inv = await S.db.invoices.find_one({"quote_id": qid}, {"_id": 0, "payment_status": 1})
        if inv:
            derived["payment_status"] = inv.get("payment_status")
    is_build_ready = (derived.get("contract_status") == "accepted" and derived.get("payment_status") == "paid")
    derived["phase"] = (
        "build_ready" if is_build_ready
        else "payment_pending" if derived.get("contract_status") == "accepted"
        else "contract_pending" if derived.get("quote_status") == "accepted"
        else "quote_pending" if qid
        else "discovery"
    )
    phase_labels = {
        "discovery": "Bedarfsanalyse",
        "quote_pending": "Angebot in Prüfung",
        "contract_pending": "Vertrag ausstehend",
        "payment_pending": "Zahlung ausstehend",
        "build_ready": "Build-Phase bereit",
    }
    derived["phase_label"] = phase_labels.get(derived["phase"], derived["phase"])
    project["project_phase"] = derived

    return project



@router.post("/api/customer/projects/{project_id}/chat")
async def customer_project_chat(project_id: str, data: dict, current_user: dict = Depends(get_current_customer)):
    """Kunden-Nachricht im Projektchat."""
    email = current_user["email"]
    project = await S.db.projects.find_one({"project_id": project_id, "customer_email": email}, {"_id": 0, "project_id": 1})
    if not project:
        raise HTTPException(404, "Projekt nicht gefunden")
    content = data.get("content", "")
    if not content.strip():
        raise HTTPException(400, "content erforderlich")
    msg = create_project_chat_message(
        project_id, email, content,
        sender_type="customer",
    )
    await S.db.project_chat.insert_one({**msg})
    msg.pop("_id", None)
    if hasattr(msg.get("timestamp"), "isoformat"):
        msg["timestamp"] = msg["timestamp"].isoformat()
    return msg


# ══════════════════════════════════════════════════════════════
# CONTRACT OPERATING SYSTEM (P2)
# ══════════════════════════════════════════════════════════════

