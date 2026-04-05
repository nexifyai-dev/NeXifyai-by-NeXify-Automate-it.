"""
NeXifyAI — Supabase Oracle Bridge Client
Async PostgreSQL connection to the existing Supabase Oracle System.
"""
import os
import logging
import asyncpg
from typing import Optional

logger = logging.getLogger("nexifyai.services.supabase")

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the asyncpg connection pool to Supabase."""
    global _pool
    if _pool is None or _pool._closed:
        dsn = os.environ.get("ALT_SUPABASE_POSTGRESQL", "")
        if not dsn:
            raise RuntimeError("ALT_SUPABASE_POSTGRESQL nicht konfiguriert")
        _pool = await asyncpg.create_pool(dsn, min_size=2, max_size=10, command_timeout=30)
        logger.info("Supabase PostgreSQL Pool erstellt")
    return _pool


async def close_pool():
    """Gracefully close the pool."""
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
        _pool = None
        logger.info("Supabase Pool geschlossen")


async def fetch(query: str, *args, limit: int = 100) -> list:
    """Execute a SELECT and return list of dicts."""
    pool = await get_pool()
    rows = await pool.fetch(query, *args)
    return [dict(r) for r in rows[:limit]]


async def fetchrow(query: str, *args) -> Optional[dict]:
    """Execute a SELECT and return a single dict or None."""
    pool = await get_pool()
    row = await pool.fetchrow(query, *args)
    return dict(row) if row else None


async def fetchval(query: str, *args):
    """Execute a query and return a single value."""
    pool = await get_pool()
    return await pool.fetchval(query, *args)


async def execute(query: str, *args) -> str:
    """Execute an INSERT/UPDATE/DELETE."""
    pool = await get_pool()
    return await pool.execute(query, *args)


# ── High-level Oracle Helpers ──

async def oracle_status() -> dict:
    """Get current Oracle autonomous status."""
    row = await fetchrow("SELECT * FROM oracle_autonomous_status LIMIT 1")
    return row or {}


async def oracle_context() -> dict:
    """Get Oracle full context overview."""
    row = await fetchrow("SELECT * FROM oracle_full_context LIMIT 1")
    return row or {}


async def oracle_tasks(status: str = None, limit: int = 50) -> list:
    """Get Oracle tasks, optionally filtered by status."""
    if status:
        return await fetch(
            "SELECT id, type, priority, status, owner_agent, title, description, created_at, completed_at FROM oracle_tasks WHERE status=$1 ORDER BY priority DESC, created_at DESC LIMIT $2",
            status, limit
        )
    return await fetch(
        "SELECT id, type, priority, status, owner_agent, title, description, created_at, completed_at FROM oracle_tasks ORDER BY created_at DESC LIMIT $1",
        limit
    )


async def oracle_queue(limit: int = 50) -> list:
    """Get Oracle ready queue."""
    return await fetch(
        "SELECT id, type, priority, status, owner_agent, created_by, payload, created_at, due_at, tags FROM oracle_ready_queue WHERE status IN ('pending', 'running') ORDER BY priority DESC, created_at LIMIT $1",
        limit
    )


async def oracle_agents() -> list:
    """Get all Oracle agents."""
    return await fetch(
        "SELECT id, type, capabilities, status, last_heartbeat, current_task FROM oracle_agents ORDER BY id"
    )


async def brain_search(query: str, limit: int = 20) -> list:
    """Full-text search in brain_notes."""
    return await fetch(
        "SELECT id, title, note_type, tags, created_at, LEFT(content, 500) as content_preview FROM brain_notes WHERE fts @@ plainto_tsquery('german', $1) ORDER BY created_at DESC LIMIT $2",
        query, limit
    )


async def knowledge_search(category: str = None, limit: int = 50) -> list:
    """Get knowledge base entries."""
    if category:
        return await fetch(
            "SELECT id, category, content, metadata, created_at FROM knowledge_base WHERE category=$1 ORDER BY created_at DESC LIMIT $2",
            category, limit
        )
    return await fetch(
        "SELECT id, category, content, metadata, created_at FROM knowledge_base ORDER BY created_at DESC LIMIT $1",
        limit
    )


async def memory_entries(category: str = None, limit: int = 50) -> list:
    """Get structured memory entries."""
    if category:
        return await fetch(
            "SELECT id, category, title, LEFT(content, 400) as content_preview, keywords, importance, is_active, created_at FROM memory_entries WHERE category=$1 AND is_active=true ORDER BY importance DESC, created_at DESC LIMIT $2",
            category, limit
        )
    return await fetch(
        "SELECT id, category, title, LEFT(content, 400) as content_preview, keywords, importance, is_active, created_at FROM memory_entries WHERE is_active=true ORDER BY importance DESC, created_at DESC LIMIT $1",
        limit
    )


async def supabase_agents() -> list:
    """Get all AI agents from Supabase."""
    return await fetch(
        "SELECT id, name, description, role, avatar_color, avatar_initials, capabilities, status, is_active, created_at FROM ai_agents WHERE is_active=true ORDER BY created_at"
    )


async def audit_logs(limit: int = 100) -> list:
    """Get recent audit logs."""
    return await fetch(
        "SELECT id, action, resource, status, details, error_message, duration_ms, created_at FROM audit_logs ORDER BY created_at DESC LIMIT $1",
        limit
    )


async def nexify_tasks(status: str = None, limit: int = 50) -> list:
    """Get NeXify tasks."""
    if status:
        return await fetch(
            "SELECT id, priority, task_description, status, assigned_agent, agent_type, review_status, compliance_check, created_at, updated_at FROM nexify_tasks WHERE status=$1 ORDER BY priority DESC, created_at DESC LIMIT $2",
            status, limit
        )
    return await fetch(
        "SELECT id, priority, task_description, status, assigned_agent, agent_type, review_status, compliance_check, created_at, updated_at FROM nexify_tasks ORDER BY priority DESC, created_at DESC LIMIT $1",
        limit
    )


async def insert_oracle_task(task_type: str, title: str, description: str, priority: int = 5, owner_agent: str = "nexify-ai-master", payload: dict = None, tags: list = None) -> str:
    """Insert a new task into oracle_ready_queue."""
    import uuid
    task_id = str(uuid.uuid4())
    await execute(
        """INSERT INTO oracle_ready_queue (id, type, priority, status, owner_agent, created_by, payload, created_at, tags)
           VALUES ($1, $2, $3, 'pending', $4, 'nexify-ai-master', $5::jsonb, NOW(), $6)""",
        task_id, task_type, priority, owner_agent,
        __import__('json').dumps(payload or {"title": title, "description": description}),
        tags or []
    )
    return task_id


async def update_oracle_task_status(task_id: str, status: str, result: dict = None):
    """Update an Oracle task status."""
    import json
    if result:
        await execute(
            "UPDATE oracle_ready_queue SET status=$1, result=$2::jsonb, completed_at=NOW() WHERE id::text=$3",
            status, json.dumps(result), task_id
        )
    else:
        await execute(
            "UPDATE oracle_ready_queue SET status=$1 WHERE id::text=$2",
            status, task_id
        )


async def store_brain_note(title: str, content: str, note_type: str = "operational", tags: list = None, created_by: str = "nexify-ai-master") -> str:
    """Store a new brain note in Supabase."""
    import uuid
    note_id = str(uuid.uuid4())
    await execute(
        """INSERT INTO brain_notes (id, title, content, note_type, tags, created_by, created_at, updated_at, is_global)
           VALUES ($1::uuid, $2, $3, $4, $5, $6, NOW(), NOW(), true)""",
        note_id, title, content, note_type, tags or [], created_by
    )
    return note_id
