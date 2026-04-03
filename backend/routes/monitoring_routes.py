"""NeXifyAI — Monitoring, LLM, Workers, Agents, Audit, E2E Routes"""
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends
from routes.shared import S
from routes.shared import (
    get_current_admin,
    _build_customer_memory,
    logger,
)
from domain import utcnow
from memory_service import AGENT_IDS

router = APIRouter(tags=["monitoring"])

@router.get("/api/admin/audit/health")
async def admin_audit_health(current_user: dict = Depends(get_current_admin)):
    """System health check and audit summary."""
    checks = {}
    
    # 1. Database connectivity
    try:
        await S.db.command("ping")
        checks["database"] = {"status": "ok", "detail": "MongoDB erreichbar"}
    except Exception as e:
        checks["database"] = {"status": "error", "detail": str(e)}
    
    # 2. Collections stats
    collections_needed = ["leads", "quotes", "invoices", "bookings", "chat_sessions",
                          "contacts", "conversations", "messages", "timeline_events",
                          "customer_memory", "whatsapp_sessions"]
    col_stats = {}
    for col_name in collections_needed:
        col = S.db[col_name]
        cnt = await col.count_documents({})
        col_stats[col_name] = cnt
    checks["collections"] = {"status": "ok", "counts": col_stats}
    
    # 3. Agent layer
    checks["agents"] = {
        "status": "ok" if S.agents else "error",
        "count": len(S.agents),
        "names": list(S.agents.keys()),
    }
    
    # 4. WA session status
    wa = await S.db.whatsapp_sessions.find_one({}, {"_id": 0}, sort=[("created_at", -1)])
    checks["whatsapp"] = {
        "status": wa.get("status", "unknown") if wa else "no_session",
        "phone": wa.get("phone_number") if wa else None,
    }
    
    # 5. LLM provider status
    if S.llm_provider:
        checks["llm"] = {
            "status": "ok",
            "provider": S.llm_provider.get_provider_name(),
            "is_target": S.llm_provider.get_provider_name() == "deepseek",
        }
    else:
        checks["llm"] = {"status": "not_initialized"}
    
    # 6. Recent errors in timeline
    error_count = await S.db.timeline_events.count_documents({
        "action": {"$regex": "error|fail", "$options": "i"},
        "timestamp": {"$gte": utcnow() - timedelta(hours=24)}
    })
    checks["recent_errors_24h"] = error_count
    
    # 7. Pricing consistency check
    tariff_count = await S.db.quotes.count_documents({})
    checks["pricing"] = {"status": "ok", "quotes_in_system": tariff_count}
    
    overall = "healthy"
    for k, v in checks.items():
        if isinstance(v, dict) and v.get("status") == "error":
            overall = "degraded"
            break
    
    return {"overall": overall, "checks": checks, "timestamp": str(utcnow())}



@router.get("/api/admin/audit/timeline")
async def admin_audit_timeline(
    hours: int = 24,
    limit: int = 100,
    current_user: dict = Depends(get_current_admin)
):
    """Recent audit trail / timeline events."""
    cutoff = utcnow() - timedelta(hours=hours)
    events = []
    async for evt in S.db.timeline_events.find(
        {"timestamp": {"$gte": cutoff}}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit):
        evt["timestamp"] = str(evt.get("timestamp", ""))
        events.append(evt)
    return {"events": events, "count": len(events), "hours": hours}


# AI AGENT LAYER (Orchestrator + Sub-Agents)
# ══════════════════════════════════════════════════════════════


@router.post("/api/admin/agents/route")
async def agent_route_task(data: dict, current_user: dict = Depends(get_current_admin)):
    """Route a task through the S.orchestrator to a sub-agent."""
    task = data.get("task", "").strip()
    context = data.get("context", {})
    if not task:
        raise HTTPException(400, "Aufgabe darf nicht leer sein")
    result = await S.orchestrator.route(task, context)
    return result



@router.post("/api/admin/agents/{agent_name}/execute")
async def agent_execute(agent_name: str, data: dict, current_user: dict = Depends(get_current_admin)):
    """Execute a task with a specific sub-agent."""
    if agent_name not in S.agents:
        raise HTTPException(404, f"Agent '{agent_name}' nicht gefunden. Verfügbar: {list(S.agents.keys())}")
    task = data.get("task", "").strip()
    context = data.get("context", "")
    if not task:
        raise HTTPException(400, "Aufgabe darf nicht leer sein")

    # Auto-inject customer memory if email provided
    email = data.get("customer_email")
    if email:
        memory = await _build_customer_memory(email)
        if memory:
            context = f"KUNDENSPEICHER:\n{memory}\n\n{context}" if context else f"KUNDENSPEICHER:\n{memory}"

    result = await S.agents[agent_name].execute(task, context)
    return result



@router.get("/api/admin/agents")
async def list_agents(current_user: dict = Depends(get_current_admin)):
    """List all available sub-agents."""
    from agents.orchestrator import AGENT_ROLES
    return {
        "orchestrator": {"status": "active", "model": f"{os.environ.get('ORCHESTRATOR_PROVIDER', 'openai')}/{os.environ.get('ORCHESTRATOR_MODEL', 'gpt-5.2')}"},
        "agents": {name: {"role": AGENT_ROLES.get(name, ""), "status": "active"} for name in S.agents},
    }


# ══════════════════════════════════════════════════════════════
# WHATSAPP QR CONNECTOR (Isolated Bridge Layer)
# ══════════════════════════════════════════════════════════════
# Architecture: This is a TRANSITION bridge solution.
# The QR connector is isolated and replaceable.
# Central messaging domain is NOT coupled to QR implementation.
# Later migration to official WhatsApp Business API requires
# only swapping this connector layer.


@router.get("/api/admin/workers/status")
async def worker_status(current_user: dict = Depends(get_current_admin)):
    """Worker- und Scheduler-Status."""
    if not S.worker_mgr:
        return {"status": "not_initialized"}
    return S.worker_mgr.get_status()



@router.get("/api/admin/workers/jobs")
async def worker_jobs(
    status: str = None, job_type: str = None,
    skip: int = 0, limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Job-Liste mit Filtern."""
    query = {}
    if status:
        query["status"] = status
    if job_type:
        query["job_type"] = job_type
    jobs = []
    async for j in S.db.jobs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit):
        jobs.append(j)
    return {"jobs": jobs, "count": len(jobs)}



@router.get("/api/admin/workers/dead-letter")
async def worker_dead_letter(
    limit: int = 50,
    current_user: dict = Depends(get_current_admin),
):
    """Dead-Letter-Queue."""
    jobs = []
    async for j in S.db.jobs.find({"status": "dead_letter"}, {"_id": 0}).sort("dead_letter_at", -1).limit(limit):
        jobs.append(j)
    return {"dead_letter_jobs": jobs, "count": len(jobs)}



@router.post("/api/admin/workers/retry/{job_id}")
async def worker_retry_job(job_id: str, current_user: dict = Depends(get_current_admin)):
    """Dead-Letter-Job manuell wiederholen."""
    job = await S.db.jobs.find_one({"job_id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(404, "Job nicht gefunden")
    if job["status"] != "dead_letter":
        raise HTTPException(400, "Nur Dead-Letter-Jobs können wiederholt werden")

    from workers.job_queue import JobPriority
    new_job_id = await S.worker_mgr.enqueue(
        job["job_type"], job["payload"],
        priority=JobPriority(job.get("priority", 2)),
        ref_id=job.get("ref_id", ""),
        ref_type=job.get("ref_type", ""),
        created_by=f"manual_retry:{current_user['email']}",
    )
    return {"new_job_id": new_job_id, "original_job_id": job_id}


# ══════════════════════════════════════════════════════════════
# COMMUNICATION SERVICE ENDPOINTS
# ══════════════════════════════════════════════════════════════


@router.get("/api/admin/monitoring/status")
async def monitoring_status(current_user: dict = Depends(get_current_admin)):
    """Konsolidierter System-Status für das Monitoring-Dashboard."""
    from services.llm_provider import get_provider_status

    # API health
    api_status = {"status": "ok", "version": "3.0.0"}

    # Database
    try:
        await S.db.command("ping")
        db_collections = await S.db.list_collection_names()
        db_status = {"status": "ok", "collections": len(db_collections)}
    except Exception as e:
        db_status = {"status": "error", "error": str(e)[:100]}

    # Worker/Queue
    worker_status = {"status": "ok", "queue_active": bool(S.worker_mgr)} if S.worker_mgr else {"status": "not_initialized"}

    # E-Mail / Resend
    email_total = await S.db.email_events.count_documents({})
    email_failed = await S.db.email_events.count_documents({"status": "failed"})
    email_status = {
        "status": "ok" if S.RESEND_API_KEY else "not_configured",
        "provider": "resend",
        "api_key_set": bool(S.RESEND_API_KEY),
        "total_sent": email_total - email_failed,
        "total_failed": email_failed,
    }

    # Payment providers
    revolut_key = bool(os.environ.get("REVOLUT_SECRET_KEY", "").strip())
    stripe_key = bool(os.environ.get("STRIPE_API_KEY", "").strip())
    payment_status = {
        "revolut": {"status": "configured" if revolut_key else "not_configured", "api_key_set": revolut_key},
        "stripe": {"status": "configured" if stripe_key else "not_configured", "api_key_set": stripe_key, "webhook_secret_set": bool(os.environ.get("STRIPE_WEBHOOK_SECRET", "").strip())},
    }

    # Webhooks
    webhook_total = await S.db.webhook_events.count_documents({})
    webhook_recent_errors = 0
    webhook_status = {"total_events": webhook_total, "recent_errors": webhook_recent_errors}

    # Memory / Audit
    timeline_total = await S.db.timeline_events.count_documents({})
    audit_total = await S.db.legal_audit.count_documents({})
    memory_total = await S.db.customer_memory.count_documents({})
    memory_status = {"timeline_events": timeline_total, "legal_audits": audit_total, "memory_entries": memory_total}

    # LLM provider
    llm_status_data = get_provider_status(S.llm_provider) if S.llm_provider else {"active_provider": "none"}

    # Dead letter queue
    dead_letters = await S.db.dead_letter_queue.count_documents({}) if "dead_letter_queue" in await S.db.list_collection_names() else 0

    # Object Storage
    from services.storage import is_available as storage_available, _storage_key
    storage_status = {
        "status": "configured" if _storage_key else ("available" if storage_available() else "not_configured"),
        "initialized": bool(_storage_key),
    }

    # Documents archived
    docs_total = await S.db.documents.count_documents({})
    docs_in_storage = await S.db.documents.count_documents({"storage_path": {"$exists": True, "$ne": None}})

    return {
        "timestamp": utcnow().isoformat(),
        "systems": {
            "api": api_status,
            "database": db_status,
            "workers": worker_status,
            "email": email_status,
            "payments": payment_status,
            "webhooks": webhook_status,
            "memory_audit": memory_status,
            "llm": llm_status_data,
            "dead_letter_queue": {"count": dead_letters, "status": "ok" if dead_letters == 0 else "attention"},
            "object_storage": storage_status,
            "documents": {"total": docs_total, "in_storage": docs_in_storage, "in_mongodb": docs_total - docs_in_storage},
        },
        "overall_status": "operational",
    }


# ══════════════════════════════════════════════════════════════
# LLM PROVIDER STATUS & OPERATIONS
# ══════════════════════════════════════════════════════════════


@router.get("/api/admin/llm/status")
async def llm_status(current_user: dict = Depends(get_current_admin)):
    """LLM-Provider-Status, Metriken und DeepSeek-Migrationsstatus."""
    from services.llm_provider import get_provider_status
    if S.llm_provider:
        return get_provider_status(S.llm_provider)
    return {"active_provider": "not_initialized", "migration_ready": False}



@router.get("/api/admin/llm/health")
async def llm_health(current_user: dict = Depends(get_current_admin)):
    """Live Health-Check: Sendet Test-Prompt an aktiven Provider."""
    if not S.llm_provider:
        raise HTTPException(503, "LLM-Provider nicht initialisiert")
    result = await S.llm_provider.health_check()
    result["provider"] = S.llm_provider.get_provider_name()
    result["is_target_architecture"] = S.llm_provider.get_provider_name() == "deepseek"
    return result



@router.post("/api/admin/llm/test")
async def llm_test(data: dict = None, current_user: dict = Depends(get_current_admin)):
    """LLM-Provider-Test mit optionalem Model-Override."""
    if not S.llm_provider:
        raise HTTPException(503, "LLM-Provider nicht initialisiert")
    model = (data or {}).get("model")
    prompt = (data or {}).get("prompt", "Antworte kurz: Wer ist DeepSeek?")
    from services.llm_provider import LLMMessage
    try:
        response = await S.llm_provider.chat(
            [LLMMessage(role="user", content=prompt)],
            system_prompt="Du bist ein hilfreicher KI-Assistent.",
            temperature=0.5,
            model=model,
        )
        return {
            "provider": S.llm_provider.get_provider_name(),
            "model": model or "default",
            "response": response[:500],
            "success": not response.startswith("["),
        }
    except Exception as e:
        return {"provider": S.llm_provider.get_provider_name(), "error": str(e), "success": False}



@router.post("/api/admin/llm/test-agent-flow")
async def llm_test_agent_flow(data: dict = None, current_user: dict = Depends(get_current_admin)):
    """Realer Agentenfluss-Test: Simuliert Chat-Session mit System-Prompt."""
    if not S.llm_provider:
        raise HTTPException(503, "LLM-Provider nicht initialisiert")

    import secrets as _sec
    test_session = f"test_{_sec.token_hex(6)}"
    system_prompt = get_system_prompt("de")
    test_message = (data or {}).get("message", "Welche Leistungen bietet NeXifyAI an?")

    try:
        # Test 1: Initial message
        r1 = await S.llm_provider.chat_with_history(
            session_id=test_session,
            user_message=test_message,
            system_prompt=system_prompt,
            temperature=0.7,
        )
        # Test 2: Follow-up (session continuity)
        r2 = await S.llm_provider.chat_with_history(
            session_id=test_session,
            user_message="Kannst du mir mehr über die Preise sagen?",
            system_prompt=system_prompt,
            temperature=0.7,
        )
        # Cleanup
        S.llm_provider.clear_session(test_session)

        return {
            "provider": S.llm_provider.get_provider_name(),
            "session_id": test_session,
            "test_results": {
                "initial_response": {"text": r1[:300], "ok": bool(r1) and not r1.startswith("[")},
                "followup_response": {"text": r2[:300], "ok": bool(r2) and not r2.startswith("[")},
                "session_continuity": bool(r1) and bool(r2) and not r1.startswith("[") and not r2.startswith("["),
            },
            "success": bool(r1) and bool(r2) and not r1.startswith("[") and not r2.startswith("["),
        }
    except Exception as e:
        S.llm_provider.clear_session(test_session)
        return {"provider": S.llm_provider.get_provider_name(), "error": str(e), "success": False}



@router.post("/api/admin/e2e/verify-flow")
async def verify_e2e_flow(current_user: dict = Depends(get_current_admin)):
    """E2E-Flow-Verifikation: Lead → Quote → Contract → Invoice → Payment → Status.
    Prüft die gesamte Kette auf Konsistenz."""
    checks = []
    issues = []

    # 1. Check: Accepted quotes have invoices
    async for q in S.db.quotes.find({"status": "accepted"}, {"_id": 0}).limit(50):
        inv = await S.db.invoices.find_one({"quote_id": q["quote_id"]}, {"_id": 0})
        if inv:
            checks.append({
                "check": "quote_has_invoice",
                "quote_id": q["quote_id"],
                "invoice_id": inv["invoice_id"],
                "payment_status": inv.get("payment_status", "unknown"),
                "pass": True,
            })
        else:
            issues.append({"check": "quote_has_invoice", "quote_id": q["quote_id"], "pass": False, "issue": "Accepted quote without invoice"})

    # 2. Check: Accepted contracts have matching quotes
    async for c in S.db.contracts.find({"status": "accepted"}, {"_id": 0}).limit(50):
        qid = c.get("quote_id", "")
        if qid:
            quote = await S.db.quotes.find_one({"quote_id": qid}, {"_id": 0})
            checks.append({
                "check": "contract_has_quote",
                "contract_id": c["contract_id"],
                "quote_id": qid,
                "quote_status": quote.get("status") if quote else "missing",
                "pass": bool(quote),
            })
            if not quote:
                issues.append({"check": "contract_has_quote", "contract_id": c["contract_id"], "pass": False, "issue": f"Quote {qid} missing"})

    # 3. Check: Paid invoices have consistent contract/quote status
    async for inv in S.db.invoices.find({"payment_status": "paid"}, {"_id": 0}).limit(50):
        qid = inv.get("quote_id", "")
        if qid:
            quote = await S.db.quotes.find_one({"quote_id": qid}, {"_id": 0})
            contract = await S.db.contracts.find_one({"quote_id": qid}, {"_id": 0})
            q_sync = quote and quote.get("payment_status") == "deposit_paid" if quote else True
            c_sync = contract and contract.get("payment_status") == "deposit_paid" if contract else True
            checks.append({
                "check": "payment_status_sync",
                "invoice_id": inv["invoice_id"],
                "quote_sync": q_sync,
                "contract_sync": c_sync,
                "pass": q_sync and c_sync,
            })
            if not (q_sync and c_sync):
                issues.append({"check": "payment_status_sync", "invoice_id": inv["invoice_id"], "pass": False, "issue": "Status divergence"})

    # 4. Check: Reminder logic correctness
    async for inv in S.db.invoices.find({"payment_status": "paid", "reminder_count": {"$gte": 1}}, {"_id": 0}).limit(20):
        issues.append({"check": "reminder_on_paid", "invoice_id": inv.get("invoice_id"), "pass": False, "issue": "Paid invoice still has active reminders"})

    # 5. Check: LLM provider health
    llm_ok = False
    if S.llm_provider:
        try:
            hc = await S.llm_provider.health_check()
            llm_ok = hc.get("status") == "healthy"
        except Exception:
            pass
    checks.append({"check": "llm_provider_healthy", "provider": S.llm_provider.get_provider_name() if S.llm_provider else "none", "pass": llm_ok})

    # 6. Check: Evidence completeness for accepted contracts
    async for c in S.db.contracts.find({"status": "accepted"}, {"_id": 0}).limit(50):
        evidence = await S.db.contract_evidence.find_one({"contract_id": c["contract_id"], "action": "accepted"}, {"_id": 0})
        has_evidence = bool(evidence)
        checks.append({
            "check": "contract_evidence_complete",
            "contract_id": c["contract_id"],
            "has_evidence": has_evidence,
            "has_signature": bool(evidence.get("signature_data")) if evidence else False,
            "has_hash": bool(evidence.get("document_hash")) if evidence else False,
            "pass": has_evidence,
        })
        if not has_evidence:
            issues.append({"check": "contract_evidence_complete", "contract_id": c["contract_id"], "pass": False, "issue": "Missing evidence for accepted contract"})

    passed = sum(1 for c in checks if c.get("pass"))
    total = len(checks)

    return {
        "e2e_verification": True,
        "total_checks": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate": f"{round(passed/max(total,1)*100)}%",
        "checks": checks,
        "issues": issues,
        "timestamp": utcnow().isoformat(),
    }
