"""
NeXifyAI — Trigger.dev Task Routes
API-Endpoints zum Triggern und Überwachen von Trigger.dev Cloud Tasks.
"""
import os
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional

from routes.shared import S, utcnow, new_id

logger = logging.getLogger("nexifyai.routes.trigger")

router = APIRouter(tags=["Trigger.dev Tasks"])


# ── Auth ──
async def get_admin(request: Request):
    import jwt
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
# TRIGGER.DEV TASK MANAGEMENT
# ════════════════════════════════════════════════════════════

class TriggerTaskRequest(BaseModel):
    task_id: str
    payload: dict = {}


@router.get("/api/admin/trigger/tasks")
async def list_trigger_tasks(admin: dict = Depends(get_admin)):
    """Alle verfügbaren Trigger.dev Tasks auflisten."""
    from services.trigger_service import TRIGGER_TASKS, is_configured
    return {
        "configured": is_configured(),
        "tasks": TRIGGER_TASKS,
        "count": len(TRIGGER_TASKS),
    }


@router.post("/api/admin/trigger/run")
async def trigger_task_endpoint(body: TriggerTaskRequest, admin: dict = Depends(get_admin)):
    """Einen Trigger.dev Task starten."""
    from services.trigger_service import trigger_task, is_configured

    if not is_configured():
        # Fallback: Task lokal über Oracle Engine ausführen
        return await _execute_locally(body.task_id, body.payload, admin)

    result = await trigger_task(body.task_id, body.payload)

    # Run in MongoDB loggen
    if result.get("success"):
        await S.db.trigger_runs.insert_one({
            "run_id": result.get("run_id"),
            "task_id": body.task_id,
            "payload": body.payload,
            "status": "triggered",
            "triggered_at": utcnow().isoformat(),
            "triggered_by": admin.get("email", "admin"),
        })

    return result


@router.get("/api/admin/trigger/runs/{run_id}")
async def get_run_status_endpoint(run_id: str, admin: dict = Depends(get_admin)):
    """Status eines Trigger.dev Runs abrufen."""
    from services.trigger_service import get_run_status, is_configured

    if not is_configured():
        # Lokalen Run-Status aus MongoDB holen
        run = await S.db.trigger_runs.find_one({"run_id": run_id}, {"_id": 0})
        if run:
            return {"success": True, **run}
        raise HTTPException(404, "Run nicht gefunden")

    return await get_run_status(run_id)


@router.get("/api/admin/trigger/runs")
async def list_runs_endpoint(task_id: str = None, limit: int = 20, admin: dict = Depends(get_admin)):
    """Letzte Trigger.dev Runs auflisten."""
    from services.trigger_service import list_runs, is_configured

    if not is_configured():
        query = {}
        if task_id:
            query["task_id"] = task_id
        runs = []
        async for r in S.db.trigger_runs.find(query, {"_id": 0}).sort("triggered_at", -1).limit(limit):
            runs.append(r)
        return {"success": True, "runs": runs, "total": len(runs)}

    return await list_runs(task_id, limit)


@router.post("/api/admin/trigger/runs/{run_id}/cancel")
async def cancel_run_endpoint(run_id: str, admin: dict = Depends(get_admin)):
    """Einen laufenden Run abbrechen."""
    from services.trigger_service import cancel_run
    return await cancel_run(run_id)


@router.get("/api/admin/trigger/status")
async def trigger_status(admin: dict = Depends(get_admin)):
    """Trigger.dev Verbindungsstatus."""
    from services.trigger_service import is_configured, TRIGGER_TASKS

    total_runs = await S.db.trigger_runs.count_documents({})
    recent_runs = await S.db.trigger_runs.count_documents({"status": {"$in": ["triggered", "running"]}})

    return {
        "configured": is_configured(),
        "tasks_available": len(TRIGGER_TASKS),
        "total_runs": total_runs,
        "active_runs": recent_runs,
        "fallback_mode": not is_configured(),
    }


# ════════════════════════════════════════════════════════════
# LOCAL FALLBACK: Oracle Engine Execution
# ════════════════════════════════════════════════════════════

async def _execute_locally(task_id: str, payload: dict, admin: dict) -> dict:
    """Fallback: Task lokal über DeepSeek ausführen wenn Trigger.dev nicht konfiguriert."""
    from services import deepseek_provider as deepseek
    from services.trigger_service import TRIGGER_TASKS

    task_info = TRIGGER_TASKS.get(task_id)
    if not task_info:
        return {"success": False, "error": f"Unbekannter Task: {task_id}"}

    run_id = new_id("trun")

    # Task-spezifische Prompt-Generierung
    task_prompts = {
        "deep-research": f"Führe eine tiefgehende Multi-Layer-Recherche durch zu: {payload.get('initialQuery', '')}. Tiefe: {payload.get('depth', 2)}, Breite: {payload.get('breadth', 3)}. Liefere: Kernerkenntnisse, Detailanalyse, Handlungsempfehlungen, Quellen.",
        "generate-report": f"Erstelle einen professionellen {payload.get('format', 'HTML')}-Report zum Thema: {payload.get('title', '')}. Inhalt: {payload.get('content', '')[:3000]}",
        "generate-and-translate-copy": f"Erstelle Marketing-Copy basierend auf diesem Brief: {payload.get('brief', '')}. Ton: {payload.get('tone', 'professional')}. Übersetze nach: {', '.join(payload.get('targetLanguages', ['en']))}.",
        "analyze-contract": f"Analysiere diesen Vertrag mit Risikobewertung: {payload.get('contractText', '')[:5000]}. Typ: {payload.get('contractType', 'service')}, Jurisdiktion: {payload.get('jurisdiction', 'DE')}.",
        "competitor-monitor": f"Analysiere die Wettbewerber: {json.dumps(payload.get('competitors', []), ensure_ascii=False)[:2000]}. Lookback: {payload.get('lookbackDays', 7)} Tage.",
        "generate-pdf-and-upload": f"Erstelle ein {payload.get('template', 'report')}-Dokument: {payload.get('title', '')}. Inhalt: {payload.get('content', '')[:3000]}",
    }

    prompt = task_prompts.get(task_id, f"Führe folgenden Task aus: {task_id}. Payload: {json.dumps(payload, ensure_ascii=False)[:3000]}")

    try:
        result = await deepseek.chat_completion(
            messages=[
                {"role": "system", "content": f"Du bist ein spezialisierter NeXifyAI-Agent für '{task_info['name']}'. {task_info['description']}. Sprache: Deutsch. Liefere strukturierte, professionelle Ergebnisse."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=4000,
        )

        # Run loggen
        run_data = {
            "run_id": run_id,
            "task_id": task_id,
            "payload": payload,
            "status": "completed" if "error" not in result else "failed",
            "result": result.get("content", ""),
            "model": result.get("model", "deepseek-chat"),
            "fallback": True,
            "triggered_at": utcnow().isoformat(),
            "completed_at": utcnow().isoformat(),
            "triggered_by": admin.get("email", "admin"),
        }
        await S.db.trigger_runs.insert_one(run_data)
        run_data.pop("_id", None)

        return {
            "success": "error" not in result,
            "run_id": run_id,
            "task_id": task_id,
            "status": "completed",
            "result": result.get("content", ""),
            "fallback": True,
            "model": result.get("model", ""),
        }
    except Exception as e:
        logger.error(f"Local execution error: {e}")
        return {"success": False, "error": str(e)[:500], "fallback": True}
