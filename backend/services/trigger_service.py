"""
NeXifyAI — Trigger.dev Bridge Service
Python-Client zur Kommunikation mit Trigger.dev Cloud Tasks.
Triggert Tasks, holt Status/Ergebnisse, verwaltet Runs.
"""
import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger("nexifyai.services.trigger")

TRIGGER_API_KEY = os.environ.get("TRIGGER_DEV_API_KEY", "")
TRIGGER_API_URL = os.environ.get("TRIGGER_API_URL", "https://api.trigger.dev")
TRIGGER_PROJECT = os.environ.get("TRIGGER_PROJECT", "nexifyai")

# Task-Definitionen (Mirror der TypeScript-Tasks)
TRIGGER_TASKS = {
    "deep-research": {
        "name": "Deep Research",
        "description": "Multi-Layer Web Research mit rekursiver Query-Expansion",
        "max_duration": 300,
        "payload_schema": {"initialQuery": "str", "depth": "int(1-3)", "breadth": "int(1-5)", "language": "str"},
    },
    "generate-report": {
        "name": "Report generieren",
        "description": "HTML/Markdown-Report aus Research-Daten",
        "max_duration": 120,
        "payload_schema": {"title": "str", "content": "str", "format": "html|markdown", "language": "str"},
    },
    "generate-and-translate-copy": {
        "name": "Copy generieren & übersetzen",
        "description": "Marketing-Copy erstellen, validieren und übersetzen",
        "max_duration": 180,
        "payload_schema": {"brief": "str", "tone": "str", "targetLanguages": "str[]", "maxLength": "int"},
    },
    "analyze-contract": {
        "name": "Vertragsanalyse",
        "description": "AI-Vertragsanalyse mit Risikobewertung und Compliance-Check",
        "max_duration": 180,
        "payload_schema": {"contractText": "str", "contractType": "str", "jurisdiction": "str"},
    },
    "competitor-monitor": {
        "name": "Wettbewerber-Monitoring",
        "description": "Automatisches Release-Tracking und Wettbewerbsanalyse",
        "max_duration": 240,
        "payload_schema": {"competitors": "[{name,url,keywords}]", "lookbackDays": "int"},
    },
    "generate-pdf-and-upload": {
        "name": "PDF generieren & hochladen",
        "description": "HTML → PDF Conversion + Cloud Storage Upload",
        "max_duration": 180,
        "payload_schema": {"title": "str", "content": "str", "template": "report|invoice|contract|proposal"},
    },
}


def is_configured() -> bool:
    return bool(TRIGGER_API_KEY)


async def trigger_task(task_id: str, payload: dict) -> dict:
    """Triggert einen Trigger.dev Task und gibt die Run-ID zurück."""
    if not TRIGGER_API_KEY:
        return {"success": False, "error": "TRIGGER_DEV_API_KEY nicht konfiguriert"}

    if task_id not in TRIGGER_TASKS:
        return {"success": False, "error": f"Unbekannter Task: {task_id}"}

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{TRIGGER_API_URL}/api/v1/tasks/{task_id}/trigger",
                headers={
                    "Authorization": f"Bearer {TRIGGER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={"payload": payload},
            )

            if resp.status_code in (200, 201):
                data = resp.json()
                return {
                    "success": True,
                    "run_id": data.get("id"),
                    "task_id": task_id,
                    "status": data.get("status", "triggered"),
                    "triggered_at": datetime.now(timezone.utc).isoformat(),
                }
            return {
                "success": False,
                "error": f"Trigger.dev API Fehler ({resp.status_code}): {resp.text[:300]}",
            }
    except Exception as e:
        logger.error(f"Trigger.dev trigger error: {e}")
        return {"success": False, "error": str(e)[:500]}


async def get_run_status(run_id: str) -> dict:
    """Holt den Status eines Trigger.dev Runs."""
    if not TRIGGER_API_KEY:
        return {"success": False, "error": "TRIGGER_DEV_API_KEY nicht konfiguriert"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{TRIGGER_API_URL}/api/v1/runs/{run_id}",
                headers={"Authorization": f"Bearer {TRIGGER_API_KEY}"},
            )

            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "run_id": run_id,
                    "status": data.get("status"),
                    "output": data.get("output"),
                    "metadata": data.get("metadata"),
                    "started_at": data.get("startedAt"),
                    "completed_at": data.get("completedAt"),
                    "error": data.get("error"),
                }
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        logger.error(f"Trigger.dev status error: {e}")
        return {"success": False, "error": str(e)[:500]}


async def list_runs(task_id: str = None, limit: int = 20) -> dict:
    """Listet die letzten Runs."""
    if not TRIGGER_API_KEY:
        return {"success": False, "error": "TRIGGER_DEV_API_KEY nicht konfiguriert"}

    try:
        params = {"limit": limit}
        if task_id:
            params["taskIdentifier"] = task_id

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{TRIGGER_API_URL}/api/v1/runs",
                headers={"Authorization": f"Bearer {TRIGGER_API_KEY}"},
                params=params,
            )

            if resp.status_code == 200:
                data = resp.json()
                return {"success": True, "runs": data.get("data", []), "total": data.get("pagination", {}).get("total", 0)}
            return {"success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)[:500]}


async def cancel_run(run_id: str) -> dict:
    """Bricht einen laufenden Run ab."""
    if not TRIGGER_API_KEY:
        return {"success": False, "error": "TRIGGER_DEV_API_KEY nicht konfiguriert"}

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{TRIGGER_API_URL}/api/v1/runs/{run_id}/cancel",
                headers={"Authorization": f"Bearer {TRIGGER_API_KEY}"},
            )
            return {"success": resp.status_code in (200, 204), "run_id": run_id}
    except Exception as e:
        return {"success": False, "error": str(e)[:500]}
