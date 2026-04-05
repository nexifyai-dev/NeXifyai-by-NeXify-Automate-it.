"""
NeXifyAI — Oracle System Routes
Live-Daten aus dem Supabase Oracle-System: Tasks, Queue, Agenten, Brain, Knowledge.
Bidirektionale Brücke zwischen MongoDB (CRM) und Supabase (Oracle).
"""
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from routes.shared import S, utcnow, new_id
from services import supabase_client as supa
from services import deepseek_provider as deepseek

logger = logging.getLogger("nexifyai.routes.oracle")

router = APIRouter(tags=["Oracle System"])


# ── Auth ──
async def get_admin(request: Request):
    import jwt, os
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Nicht authentifiziert")
    token = auth[7:]
    try:
        payload = jwt.decode(token, os.environ.get("SECRET_KEY", ""), algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(401, "Ungültiger Token")
        user = await S.db.admin_users.find_one({"email": email}, {"_id": 0})
        if not user:
            raise HTTPException(401, "Admin nicht gefunden")
        return user
    except Exception:
        raise HTTPException(401, "Nicht authentifiziert")


# ════════════════════════════════════════════════════════════
# ORACLE DASHBOARD — Aggregated live data
# ════════════════════════════════════════════════════════════

@router.get("/api/admin/oracle/dashboard")
async def oracle_dashboard(admin: dict = Depends(get_admin)):
    """Komplettes Oracle-Dashboard: Status, Queue, Agenten, Brain-Stats."""
    try:
        status = await supa.oracle_status()
        context = await supa.oracle_context()
        agents = await supa.oracle_agents()
        queue = await supa.oracle_queue(limit=20)

        # Counts
        brain_count = await supa.fetchval("SELECT count(*) FROM brain_notes")
        knowledge_count = await supa.fetchval("SELECT count(*) FROM knowledge_base")
        memory_count = await supa.fetchval("SELECT count(*) FROM memory_entries WHERE is_active=true")
        ai_agents_count = await supa.fetchval("SELECT count(*) FROM ai_agents WHERE is_active=true")
        audit_count = await supa.fetchval("SELECT count(*) FROM audit_logs")
        tasks_total = await supa.fetchval("SELECT count(*) FROM oracle_tasks")
        tasks_pending = await supa.fetchval("SELECT count(*) FROM oracle_ready_queue WHERE status='pending'")
        tasks_running = await supa.fetchval("SELECT count(*) FROM oracle_ready_queue WHERE status='running'")

        return {
            "oracle_status": _serialize(status),
            "oracle_context": _serialize(context),
            "oracle_agents": [_serialize(a) for a in agents],
            "queue": [_serialize(q) for q in queue],
            "queue_pending": tasks_pending,
            "queue_running": tasks_running,
            "counts": {
                "brain_notes": brain_count,
                "knowledge_entries": knowledge_count,
                "memory_entries": memory_count,
                "ai_agents": ai_agents_count,
                "audit_logs": audit_count,
                "oracle_tasks_total": tasks_total,
            },
            "timestamp": utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Oracle dashboard error: {e}")
        raise HTTPException(500, f"Oracle-Fehler: {str(e)}")


# ════════════════════════════════════════════════════════════
# ORACLE TASKS
# ════════════════════════════════════════════════════════════

@router.get("/api/admin/oracle/tasks")
async def list_oracle_tasks(status: str = None, limit: int = 50, admin: dict = Depends(get_admin)):
    """Oracle-Tasks auflisten."""
    try:
        tasks = await supa.oracle_tasks(status=status, limit=limit)
        return {"tasks": [_serialize(t) for t in tasks], "count": len(tasks)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/api/admin/oracle/queue")
async def get_oracle_queue(limit: int = 50, admin: dict = Depends(get_admin)):
    """Oracle Ready-Queue."""
    try:
        queue = await supa.oracle_queue(limit=limit)
        return {"queue": [_serialize(q) for q in queue], "count": len(queue)}
    except Exception as e:
        raise HTTPException(500, str(e))


class CreateTaskRequest(BaseModel):
    title: str
    description: str = ""
    task_type: str = "general"
    priority: int = 5
    owner_agent: str = "nexify-ai-master"
    tags: list = []


VALID_ORACLE_TASK_TYPES = [
    'infrastructure', 'security', 'migration', 'verification', 'optimization',
    'response', 'escalation', 'intake', 'observation', 'user_request',
    'agent_task', 'improvement', 'monitoring', 'agent', 'data', 'general',
    'deployment', 'configuration', 'project_task', 'system_task',
    'email', 'telegram', 'llm', 'kpi', 'crm'
]


@router.post("/api/admin/oracle/tasks")
async def create_oracle_task(body: CreateTaskRequest, admin: dict = Depends(get_admin)):
    """Neuen Oracle-Task erstellen."""
    try:
        task_type = body.task_type if body.task_type in VALID_ORACLE_TASK_TYPES else "general"
        task_id = await supa.insert_oracle_task(
            task_type=task_type,
            title=body.title,
            description=body.description,
            priority=body.priority,
            owner_agent=body.owner_agent,
            tags=body.tags
        )
        return {"task_id": task_id, "status": "pending", "type": task_type, "created": True}
    except Exception as e:
        raise HTTPException(500, str(e))


# ════════════════════════════════════════════════════════════
# ORACLE AGENTS (Supabase)
# ════════════════════════════════════════════════════════════

@router.get("/api/admin/oracle/agents")
async def list_oracle_agents(admin: dict = Depends(get_admin)):
    """Alle Agenten aus Supabase (Oracle-Registry + AI-Agents)."""
    try:
        registry = await supa.oracle_agents()
        ai_agents = await supa.supabase_agents()
        return {
            "oracle_agents": [_serialize(a) for a in registry],
            "ai_agents": [_serialize(a) for a in ai_agents],
            "total": len(registry) + len(ai_agents)
        }
    except Exception as e:
        raise HTTPException(500, str(e))


# ════════════════════════════════════════════════════════════
# BRAIN & KNOWLEDGE (Supabase)
# ════════════════════════════════════════════════════════════

@router.get("/api/admin/oracle/brain")
async def search_brain(q: str = "", limit: int = 20, admin: dict = Depends(get_admin)):
    """Brain-Notes durchsuchen."""
    try:
        if q:
            notes = await supa.brain_search(q, limit=limit)
        else:
            notes = await supa.fetch(
                "SELECT id, title, note_type, tags, created_at, LEFT(content, 500) as content_preview FROM brain_notes ORDER BY created_at DESC LIMIT $1",
                limit
            )
        return {"notes": [_serialize(n) for n in notes], "count": len(notes)}
    except Exception as e:
        raise HTTPException(500, str(e))


class BrainNoteRequest(BaseModel):
    title: str
    content: str
    note_type: str = "operational"
    tags: list = []


@router.post("/api/admin/oracle/brain")
async def create_brain_note(body: BrainNoteRequest, admin: dict = Depends(get_admin)):
    """Brain-Note in Supabase speichern."""
    try:
        note_id = await supa.store_brain_note(
            title=body.title,
            content=body.content,
            note_type=body.note_type,
            tags=body.tags,
            created_by=admin.get("email", "admin")
        )
        return {"note_id": note_id, "stored": True}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/api/admin/oracle/knowledge")
async def list_knowledge(category: str = None, limit: int = 50, admin: dict = Depends(get_admin)):
    """Knowledge-Base auflisten."""
    try:
        entries = await supa.knowledge_search(category=category, limit=limit)
        return {"entries": [_serialize(e) for e in entries], "count": len(entries)}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/api/admin/oracle/memory")
async def list_memory(category: str = None, limit: int = 50, admin: dict = Depends(get_admin)):
    """Memory-Entries auflisten."""
    try:
        entries = await supa.memory_entries(category=category, limit=limit)
        return {"entries": [_serialize(e) for e in entries], "count": len(entries)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ════════════════════════════════════════════════════════════
# AGENT ORCHESTRATION — DeepSeek Sub-Agent Invocation
# ════════════════════════════════════════════════════════════

class AgentInvokeRequest(BaseModel):
    agent_name: str
    message: str
    context: str = ""
    use_brain: bool = True


@router.post("/api/admin/oracle/invoke-agent")
async def invoke_deepseek_agent(body: AgentInvokeRequest, admin: dict = Depends(get_admin)):
    """Fachagenten über DeepSeek aufrufen (nicht Master)."""
    if not deepseek.is_configured():
        raise HTTPException(500, "DeepSeek API nicht konfiguriert")

    # Look up agent in Supabase first, then MongoDB
    agent_info = None
    try:
        agents = await supa.fetch(
            "SELECT name, role, description, capabilities FROM ai_agents WHERE name ILIKE $1 AND is_active=true LIMIT 1",
            f"%{body.agent_name}%"
        )
        if agents:
            agent_info = agents[0]
    except Exception:
        pass

    if not agent_info:
        # Fallback to MongoDB
        mongo_agent = await S.db.ai_agents.find_one(
            {"name": {"$regex": body.agent_name, "$options": "i"}, "status": "active"},
            {"_id": 0}
        )
        if mongo_agent:
            agent_info = {
                "name": mongo_agent.get("name", body.agent_name),
                "role": mongo_agent.get("role", "specialist"),
                "description": mongo_agent.get("system_prompt", ""),
                "capabilities": mongo_agent.get("tools", [])
            }

    if not agent_info:
        raise HTTPException(404, f"Agent '{body.agent_name}' nicht gefunden")

    # Brain context
    brain_context = ""
    if body.use_brain:
        try:
            brain_notes = await supa.brain_search(body.message, limit=5)
            if brain_notes:
                brain_texts = [f"- {n.get('title', '')}: {n.get('content_preview', '')}" for n in brain_notes]
                brain_context = "\n[BRAIN]\n" + "\n".join(brain_texts[:5]) + "\n[/BRAIN]"
        except Exception:
            pass

    result = await deepseek.invoke_agent(
        agent_name=agent_info.get("name", body.agent_name),
        agent_role=str(agent_info.get("role", "specialist")),
        system_prompt=str(agent_info.get("description", "")),
        user_message=body.message,
        context=(body.context + brain_context).strip()
    )

    # Log to Oracle audit
    try:
        await supa.execute(
            """INSERT INTO audit_logs (id, action, resource, status, details, created_at)
               VALUES ($1, 'agent_invoke', $2, $3, $4::jsonb, NOW())""",
            new_id("aud"), body.agent_name,
            "SUCCESS" if "error" not in result else "ERROR",
            json.dumps({"message": body.message[:200], "model": result.get("model", ""), "agent": body.agent_name}, ensure_ascii=False)
        )
    except Exception:
        pass

    return result


# ════════════════════════════════════════════════════════════
# AUDIT LOGS (Supabase)
# ════════════════════════════════════════════════════════════

@router.get("/api/admin/oracle/audit")
async def list_audit_logs(limit: int = 100, admin: dict = Depends(get_admin)):
    """Supabase Audit-Logs."""
    try:
        logs = await supa.audit_logs(limit=limit)
        return {"logs": [_serialize(l) for l in logs], "count": len(logs)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ════════════════════════════════════════════════════════════
# NEXIFY TASKS (Supabase Legacy)
# ════════════════════════════════════════════════════════════

@router.get("/api/admin/oracle/nexify-tasks")
async def list_nexify_tasks(status: str = None, limit: int = 50, admin: dict = Depends(get_admin)):
    """NeXify-Tasks aus Supabase."""
    try:
        tasks = await supa.nexify_tasks(status=status, limit=limit)
        return {"tasks": [_serialize(t) for t in tasks], "count": len(tasks)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ════════════════════════════════════════════════════════════
# HEALTH CHECK — Supabase + DeepSeek connectivity
# ════════════════════════════════════════════════════════════

@router.get("/api/admin/oracle/health")
async def oracle_health(admin: dict = Depends(get_admin)):
    """Prüfe Supabase und DeepSeek Konnektivität."""
    result = {
        "supabase": {"connected": False, "error": None},
        "deepseek": {"configured": deepseek.is_configured(), "connected": False, "model": deepseek.DEEPSEEK_MODEL, "error": None},
        "timestamp": utcnow().isoformat()
    }

    # Supabase check
    try:
        val = await supa.fetchval("SELECT 1")
        result["supabase"]["connected"] = val == 1
    except Exception as e:
        result["supabase"]["error"] = str(e)[:100]

    # DeepSeek check
    if deepseek.is_configured():
        try:
            resp = await deepseek.chat_completion(
                [{"role": "user", "content": "ping"}],
                max_tokens=5, temperature=0
            )
            result["deepseek"]["connected"] = "error" not in resp
            if "error" in resp:
                result["deepseek"]["error"] = resp["error"][:100]
        except Exception as e:
            result["deepseek"]["error"] = str(e)[:100]

    return result


# ── Serialization helper ──
def _serialize(obj):
    """Convert asyncpg Record / datetime to JSON-safe dict."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, '__str__') and not isinstance(obj, (str, int, float, bool)):
        return str(obj)
    return obj
