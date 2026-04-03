"""
Object Storage Service — Emergent Object Storage für PDF-/Dokumenten-Archivierung.
Kapselt Upload/Download und Storage-Key-Management.
"""

import os
import logging
import requests

logger = logging.getLogger("nexifyai.services.storage")

STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
APP_NAME = "nexifyai"

_storage_key = None


def init_storage():
    """Storage-Key einmalig beim Start initialisieren."""
    global _storage_key
    if _storage_key:
        return _storage_key
    emergent_key = os.environ.get("EMERGENT_LLM_KEY", "")
    if not emergent_key:
        logger.warning("Object Storage nicht verfügbar — EMERGENT_LLM_KEY fehlt")
        return None
    try:
        resp = requests.post(f"{STORAGE_URL}/init", json={"emergent_key": emergent_key}, timeout=30)
        resp.raise_for_status()
        _storage_key = resp.json()["storage_key"]
        logger.info("Object Storage initialisiert")
        return _storage_key
    except Exception as e:
        logger.error(f"Object Storage Init-Fehler: {e}")
        return None


def put_object(path: str, data: bytes, content_type: str = "application/pdf") -> dict:
    """Datei in Object Storage hochladen."""
    key = init_storage()
    if not key:
        raise RuntimeError("Object Storage nicht initialisiert")
    resp = requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data,
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()


def get_object(path: str) -> tuple:
    """Datei aus Object Storage herunterladen. Returns (bytes, content_type)."""
    key = init_storage()
    if not key:
        raise RuntimeError("Object Storage nicht initialisiert")
    resp = requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")


def is_available() -> bool:
    """Prüfe ob Object Storage verfügbar ist."""
    return _storage_key is not None or bool(os.environ.get("EMERGENT_LLM_KEY", ""))
