"""NeXifyAI — Agent Routes (NeXify AI Master Agent Admin Endpoints)"""
from datetime import datetime, timezone
from typing import Optional, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from routes.shared import get_current_admin, log_audit, logger, S

router = APIRouter(tags=["agent"])


# ══════════════════════════════════════════════════════════════
# REQUEST MODELS
# ══════════════════════════════════════════════════════════════

class AgentChatRequest(BaseModel):
    session_id: str
    message: str
    auto_brain: bool = True


class AgentCodeRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: int = Field(default=30, le=60)


class AgentApiCallRequest(BaseModel):
    url: str
    method: str = "GET"
    headers: Optional[dict] = None
    body: Optional[Any] = None
    timeout: int = Field(default=30, le=60)


class AgentBrainStoreRequest(BaseModel):
    content: str
    metadata: Optional[dict] = None
    memory_layer: str = "KNOWLEDGE"


class AgentBrainSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=10, le=50)


# ══════════════════════════════════════════════════════════════
# AGENT CHAT
# ══════════════════════════════════════════════════════════════

@router.post("/api/admin/agent/chat")
async def admin_agent_chat(req: AgentChatRequest, user=Depends(get_current_admin)):
    """Chat with the NeXify AI Master Agent."""
    from agent import agent_chat
    try:
        result = await agent_chat(
            session_id=req.session_id,
            message=req.message,
            db=S.db,
            auto_brain=req.auto_brain,
        )
        await log_audit("agent_chat", user["email"], {
            "session_id": req.session_id,
            "message_preview": req.message[:100],
        })
        return result
    except Exception as e:
        logger.error(f"Agent chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent-Fehler: {str(e)}")


# ══════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ══════════════════════════════════════════════════════════════

@router.get("/api/admin/agent/sessions")
async def admin_agent_sessions(user=Depends(get_current_admin)):
    """List all agent sessions."""
    from agent import agent_sessions
    sessions = []
    for sid, msgs in agent_sessions.items():
        sessions.append({
            "session_id": sid,
            "message_count": len(msgs),
            "last_message": msgs[-1]["content"][:100] if msgs else "",
            "last_role": msgs[-1]["role"] if msgs else "",
        })
    return {"sessions": sessions}


@router.get("/api/admin/agent/sessions/{session_id}")
async def admin_agent_session_detail(session_id: str, user=Depends(get_current_admin)):
    """Get full session history."""
    from agent import agent_sessions
    if session_id not in agent_sessions:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")
    messages = agent_sessions[session_id]
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": m["role"],
                "content": m["content"][:5000],
                "timestamp": m.get("timestamp"),
            }
            for m in messages
            if m["role"] != "system"
        ],
    }


@router.delete("/api/admin/agent/sessions/{session_id}")
async def admin_agent_session_delete(session_id: str, user=Depends(get_current_admin)):
    """Delete an agent session."""
    from agent import agent_sessions
    if session_id in agent_sessions:
        del agent_sessions[session_id]
    await log_audit("agent_session_deleted", user["email"], {"session_id": session_id})
    return {"success": True}


# ══════════════════════════════════════════════════════════════
# BRAIN (mem0) MANAGEMENT
# ══════════════════════════════════════════════════════════════

@router.post("/api/admin/agent/brain/store")
async def admin_agent_brain_store(req: AgentBrainStoreRequest, user=Depends(get_current_admin)):
    """Store a memory in the agent's brain (mem0)."""
    from agent import mem0_store
    messages = [{"role": "user", "content": req.content}]
    metadata = req.metadata or {
        "tenant": "nexify-automate",
        "scope": "global_company_knowledge",
        "memory_layer": req.memory_layer,
        "trust_level": "official_internal_source",
        "stored_by": user["email"],
        "stored_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await mem0_store(messages, metadata)
    await log_audit("agent_brain_store", user["email"], {
        "content_preview": req.content[:100],
        "memory_layer": req.memory_layer,
    })
    return result


@router.post("/api/admin/agent/brain/search")
async def admin_agent_brain_search(req: AgentBrainSearchRequest, user=Depends(get_current_admin)):
    """Search the agent's brain (mem0)."""
    from agent import mem0_search
    return await mem0_search(req.query, top_k=req.top_k)


@router.get("/api/admin/agent/brain/memories")
async def admin_agent_brain_list(user=Depends(get_current_admin)):
    """List all memories in the agent's brain."""
    from agent import mem0_get_all
    return await mem0_get_all()


@router.delete("/api/admin/agent/brain/{memory_id}")
async def admin_agent_brain_delete(memory_id: str, user=Depends(get_current_admin)):
    """Delete a specific memory from the brain."""
    from agent import mem0_delete
    result = await mem0_delete(memory_id)
    await log_audit("agent_brain_delete", user["email"], {"memory_id": memory_id})
    return result


# ══════════════════════════════════════════════════════════════
# CODE EXECUTION
# ══════════════════════════════════════════════════════════════

@router.post("/api/admin/agent/execute")
async def admin_agent_execute(req: AgentCodeRequest, user=Depends(get_current_admin)):
    """Execute code in a sandboxed environment."""
    from agent import execute_code
    result = await execute_code(req.code, language=req.language, timeout=req.timeout)
    await log_audit("agent_code_exec", user["email"], {
        "language": req.language,
        "code_preview": req.code[:100],
        "returncode": result.get("returncode"),
    })
    return result


# ══════════════════════════════════════════════════════════════
# EXTERNAL API PROXY
# ══════════════════════════════════════════════════════════════

@router.post("/api/admin/agent/api-call")
async def admin_agent_api_call(req: AgentApiCallRequest, user=Depends(get_current_admin)):
    """Proxy an external API call through the agent."""
    from agent import call_external_api

    # Additional private network blocking
    from urllib.parse import urlparse
    parsed = urlparse(req.url)
    if parsed.hostname:
        hostname = parsed.hostname
        blocked = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
        if hostname in blocked or hostname.startswith("10.") or hostname.startswith("192.168."):
            raise HTTPException(status_code=403, detail="Interne/private Adressen sind nicht erlaubt")

    result = await call_external_api(
        url=req.url,
        method=req.method,
        headers=req.headers,
        body=req.body,
        timeout=req.timeout,
    )
    await log_audit("agent_api_call", user["email"], {
        "url": req.url,
        "method": req.method,
        "status": result.get("status"),
    })
    return result


# ══════════════════════════════════════════════════════════════
# AGENT STATUS
# ══════════════════════════════════════════════════════════════

@router.get("/api/admin/agent/status")
async def admin_agent_status(user=Depends(get_current_admin)):
    """Get current agent status and capabilities."""
    from agent import agent_sessions, MEM0_API_KEY, LLM_PROVIDERS
    import agent as agent_module

    available_providers = []
    for p in LLM_PROVIDERS:
        key = agent_module._get_api_key(p)
        available_providers.append({
            "name": p["name"],
            "model": p["model"],
            "available": bool(key),
        })

    return {
        "status": "active",
        "brain_connected": bool(MEM0_API_KEY),
        "llm_providers": available_providers,
        "active_sessions": len(agent_sessions),
        "capabilities": ["chat", "brain", "code_execution", "api_calls"],
        "version": "1.0.0",
    }
