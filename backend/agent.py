"""
NeXify AI Agent — Backend Module
Master AI Agent with mem0 Brain, LLM routing (Arcee/nScale/DeepSeek),
sandboxed code execution, and external API calling capabilities.
"""
import os
import io
import sys
import json
import traceback
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

import httpx

logger = logging.getLogger("nexifyai.agent")

# ============== CONFIGURATION ==============

MEM0_API_KEY = os.environ.get("MEM0_API_KEY", "")
MEM0_BASE_URL = "https://api.mem0.ai"

ARCEE_API_KEY = os.environ.get("ARCEE_API_KEY", "")
NSCALE_API_KEY = os.environ.get("NSCALE_API_KEY", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")

# Default user/agent/app IDs for mem0
MEM0_USER_ID = "pascal-courbois"
MEM0_AGENT_ID = "nexify-ai-master"
MEM0_APP_ID = "nexify-automate-core"

# LLM provider configs — ordered by priority
LLM_PROVIDERS = [
    {
        "name": "nscale",
        "url": "https://inference.api.nscale.com/v1/chat/completions",
        "key_env": "NSCALE_API_KEY",
        "model": "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        "fallback_model": "Qwen/Qwen2.5-72B-Instruct",
    },
    {
        "name": "deepseek",
        "url": "https://api.deepseek.com/chat/completions",
        "key_env": "DEEPSEEK_API_KEY",
        "model": "deepseek-chat",
    },
    {
        "name": "arcee",
        "url": "https://api.arcee.ai/api/v1/chat/completions",
        "key_env": "ARCEE_API_KEY",
        "model": "trinity-large-preview",
    },
]

# ============== SYSTEM PROMPT ==============

MASTER_SYSTEM_PROMPT = """Du bist NeXify AI (Master).

## 1. Kernidentität

Du bist der direkte persönliche Master-Assistent von Pascal und die zentrale Leit-, Koordinations-, Entscheidungs- und Eskalationsinstanz für das gesamte NeXify-AI-Team.

Du bist:
- persönlicher Ansprechpartner von Pascal
- erster Ansprechpartner für alle AI-Assistenten
- Orchestrator für Planung, Umsetzung, Kontrolle und Verbesserung
- Hüter der Systemkonsistenz, des gemeinsamen Brain und der Auditierbarkeit
- operative Schaltzentrale für Projekte, Agenturprozesse, Kundenkontexte, Delivery, Akquise, Qualität, Monitoring und Wissensmanagement

Du handelst nicht als passiver Chatbot, sondern als aktiver, kontextbewusster, handlungsfähiger Systemoperator.

## 2. Primärmission

Deine Primärmission ist es, Pascals Ziele schnell, präzise, belastbar, revisionssicher und möglichst autonom in umsetzbare Realität zu überführen.

## 3. Brain- und Memory-Protokoll

Du hast Zugriff auf das mem0 Brain. Nutze es um:
- Kontext zu laden bevor du antwortest
- Wissen zu persistieren nach Entscheidungen
- Aufgaben und Status zu tracken

Trenne immer: globales Agenturwissen, projektbezogenes Wissen, tenant-spezifisches Wissen, private Notizen, untrusted content.

## 4. Fähigkeiten

Du kannst:
- **Coden**: Python-Code ausführen (Datenanalyse, Berechnungen, Textverarbeitung, Automatisierung)
- **API-Aufrufe**: Externe APIs aufrufen (REST, GraphQL, Webhooks)
- **Brain nutzen**: Wissen speichern, abrufen und durchsuchen via mem0
- **Planen und Delegieren**: Aufgaben strukturieren und Fachagenten steuern

## 5. Kommunikationsstandard

Kommuniziere klar, direkt, priorisiert und handlungsorientiert.
- professionell, präzise, sachlich, outcome-orientiert
- keine Floskeln, keine generische KI-Sprache
- wenn du Code ausführen sollst, sage es und führe ihn aus
- wenn du eine API aufrufen sollst, sage es und rufe sie auf

## 6. Unternehmenswissen

NeXify Automate — Eenmanszaak, KvK: 90483944, USt-ID: NL865786276B01
Hauptsitz: Graaf van Loonstraat 1E, 5921 JA Venlo, Niederlande
Niederlassung DE: Wallstraße 9, 41334 Nettetal-Kaldenkirchen
Vertreten durch: Pascal Courbois, Geschäftsführer
Kontakt: +31 6 133 188 56, support@nexify-automate.com

## 7. Standard-Ausgabeformat

Wenn du operativ arbeitest, strukturiere:
1. Ziel
2. Geladener Kontext
3. Verifizierte Fakten / Offene Punkte
4. Plan / Sofort auszuführende Aktionen
5. Nächster sinnvoller Schritt
"""


# ============== MEM0 BRAIN ==============

async def mem0_store(messages: List[Dict], metadata: Dict = None) -> Dict:
    """Store memories in mem0 Brain."""
    if not MEM0_API_KEY:
        return {"error": "MEM0_API_KEY not configured"}

    payload = {
        "messages": messages,
        "user_id": MEM0_USER_ID,
        "agent_id": MEM0_AGENT_ID,
        "app_id": MEM0_APP_ID,
        "metadata": metadata or {
            "tenant": "nexify-automate",
            "scope": "global_company_knowledge",
            "memory_layer": "KNOWLEDGE",
            "trust_level": "official_internal_source",
        },
        "version": "v2",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{MEM0_BASE_URL}/v1/memories/",
            headers={
                "Authorization": f"Token {MEM0_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def mem0_search(query: str, top_k: int = 10, filters: Dict = None) -> Dict:
    """Search memories in mem0 Brain."""
    if not MEM0_API_KEY:
        return {"error": "MEM0_API_KEY not configured", "results": []}

    payload = {
        "query": query,
        "version": "v2",
        "top_k": top_k,
        "threshold": 0.3,
        "filter_memories": True,
        "filters": filters or {
            "AND": [
                {"OR": [
                    {"user_id": MEM0_USER_ID},
                    {"agent_id": MEM0_AGENT_ID},
                ]},
                {"app_id": MEM0_APP_ID},
            ]
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{MEM0_BASE_URL}/v2/memories/search/",
            headers={
                "Authorization": f"Token {MEM0_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def mem0_get_all(user_id: str = None) -> Dict:
    """Get all memories for a user."""
    if not MEM0_API_KEY:
        return {"error": "MEM0_API_KEY not configured", "results": []}

    params = {
        "version": "v2",
        "user_id": user_id or MEM0_USER_ID,
        "app_id": MEM0_APP_ID,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{MEM0_BASE_URL}/v1/memories/",
            headers={
                "Authorization": f"Token {MEM0_API_KEY}",
                "Content-Type": "application/json",
            },
            params=params,
        )
        resp.raise_for_status()
        return resp.json()


async def mem0_delete(memory_id: str) -> Dict:
    """Delete a specific memory."""
    if not MEM0_API_KEY:
        return {"error": "MEM0_API_KEY not configured"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.delete(
            f"{MEM0_BASE_URL}/v1/memories/{memory_id}/",
            headers={
                "Authorization": f"Token {MEM0_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        return {"success": True, "deleted": memory_id}


# ============== LLM ROUTING ==============

def _get_api_key(provider: Dict) -> str:
    """Get API key for a provider from env."""
    env_key = provider["key_env"]
    return os.environ.get(env_key, globals().get(env_key, ""))


async def llm_chat(
    messages: List[Dict],
    provider_name: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> Dict:
    """
    Send chat completion request to LLM providers with automatic fallback.
    Returns dict with 'content', 'provider', 'model', 'usage'.
    """
    providers_to_try = []

    if provider_name:
        # Use specific provider
        for p in LLM_PROVIDERS:
            if p["name"] == provider_name:
                providers_to_try.append(p)
                break
    else:
        providers_to_try = list(LLM_PROVIDERS)

    last_error = None

    for provider in providers_to_try:
        api_key = _get_api_key(provider)
        if not api_key:
            logger.warning(f"No API key for {provider['name']}, skipping")
            continue

        payload = {
            "model": provider["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    provider["url"],
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})

                return {
                    "content": content,
                    "provider": provider["name"],
                    "model": provider["model"],
                    "usage": usage,
                }
        except Exception as e:
            last_error = str(e)
            logger.warning(f"LLM provider {provider['name']} failed: {e}")

            # Try fallback model if available
            if provider.get("fallback_model"):
                try:
                    payload["model"] = provider["fallback_model"]
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            provider["url"],
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json",
                            },
                            json=payload,
                        )
                        resp.raise_for_status()
                        data = resp.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        return {
                            "content": content,
                            "provider": provider["name"],
                            "model": provider["fallback_model"],
                            "usage": data.get("usage", {}),
                        }
                except Exception as e2:
                    logger.warning(f"Fallback model {provider['fallback_model']} also failed: {e2}")
                    last_error = str(e2)
            continue

    return {
        "content": f"Alle LLM-Provider sind derzeit nicht erreichbar. Letzter Fehler: {last_error}",
        "provider": "none",
        "model": "none",
        "usage": {},
        "error": last_error,
    }


# ============== CODE EXECUTION ==============

async def execute_code(code: str, language: str = "python", timeout: int = 30) -> Dict:
    """
    Execute code in a sandboxed subprocess.
    Returns dict with 'stdout', 'stderr', 'returncode', 'duration'.
    """
    start = datetime.now(timezone.utc)

    if language == "python":
        # Write code to a temp file and execute in subprocess
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/tmp",
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return {
                    "stdout": "",
                    "stderr": f"Timeout nach {timeout} Sekunden",
                    "returncode": -1,
                    "duration_ms": timeout * 1000,
                    "language": language,
                }

            duration = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            return {
                "stdout": stdout.decode("utf-8", errors="replace")[:50000],
                "stderr": stderr.decode("utf-8", errors="replace")[:10000],
                "returncode": proc.returncode,
                "duration_ms": round(duration),
                "language": language,
            }
        finally:
            os.unlink(temp_path)

    elif language == "javascript":
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                "node", temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd="/tmp",
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=timeout
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.communicate()
                return {
                    "stdout": "",
                    "stderr": f"Timeout nach {timeout} Sekunden",
                    "returncode": -1,
                    "duration_ms": timeout * 1000,
                    "language": language,
                }

            duration = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            return {
                "stdout": stdout.decode("utf-8", errors="replace")[:50000],
                "stderr": stderr.decode("utf-8", errors="replace")[:10000],
                "returncode": proc.returncode,
                "duration_ms": round(duration),
                "language": language,
            }
        finally:
            os.unlink(temp_path)

    else:
        return {
            "stdout": "",
            "stderr": f"Sprache '{language}' nicht unterstützt. Verfügbar: python, javascript",
            "returncode": -1,
            "duration_ms": 0,
            "language": language,
        }


# ============== API PROXY ==============

async def call_external_api(
    url: str,
    method: str = "GET",
    headers: Dict = None,
    body: Any = None,
    timeout: int = 30,
) -> Dict:
    """
    Call an external API endpoint.
    Returns dict with 'status', 'headers', 'body', 'duration_ms'.
    """
    start = datetime.now(timezone.utc)

    # Block internal/localhost calls for security
    from urllib.parse import urlparse
    parsed = urlparse(url)
    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if parsed.hostname in blocked_hosts:
        return {
            "status": 403,
            "headers": {},
            "body": "Interne Adressen sind nicht erlaubt",
            "duration_ms": 0,
            "error": "Blocked: localhost/internal addresses not allowed",
        }

    try:
        async with httpx.AsyncClient(timeout=float(timeout), follow_redirects=True) as client:
            resp = await client.request(
                method=method.upper(),
                url=url,
                headers=headers or {},
                json=body if body and method.upper() in ("POST", "PUT", "PATCH") else None,
                params=body if body and method.upper() == "GET" else None,
            )

            duration = (datetime.now(timezone.utc) - start).total_seconds() * 1000

            # Try to parse as JSON
            try:
                resp_body = resp.json()
            except Exception:
                resp_body = resp.text[:50000]

            return {
                "status": resp.status_code,
                "headers": dict(resp.headers),
                "body": resp_body,
                "duration_ms": round(duration),
            }

    except httpx.TimeoutException:
        return {
            "status": 408,
            "headers": {},
            "body": f"Timeout nach {timeout} Sekunden",
            "duration_ms": timeout * 1000,
            "error": "Request timeout",
        }
    except Exception as e:
        duration = (datetime.now(timezone.utc) - start).total_seconds() * 1000
        return {
            "status": 0,
            "headers": {},
            "body": str(e),
            "duration_ms": round(duration),
            "error": str(e),
        }


# ============== AGENT CHAT (orchestrated) ==============

# In-memory conversation store per session
agent_sessions: Dict[str, List[Dict]] = {}


async def agent_chat(
    session_id: str,
    message: str,
    db=None,
    auto_brain: bool = True,
) -> Dict:
    """
    Main agent chat function. Orchestrates:
    1. Load context from brain
    2. Build message history
    3. Call LLM
    4. Detect tool calls (code/api) and execute
    5. Persist results
    """

    # Initialize session if needed
    if session_id not in agent_sessions:
        agent_sessions[session_id] = []

    history = agent_sessions[session_id]

    # 1. Auto-load brain context
    brain_context = ""
    if auto_brain and MEM0_API_KEY:
        try:
            brain_results = await mem0_search(message, top_k=5)
            memories = brain_results.get("results", brain_results) if isinstance(brain_results, dict) else brain_results
            if isinstance(memories, list) and memories:
                brain_snippets = []
                for m in memories[:5]:
                    if isinstance(m, dict):
                        mem_text = m.get("memory", m.get("content", m.get("text", "")))
                        if mem_text:
                            brain_snippets.append(f"- {mem_text}")
                if brain_snippets:
                    brain_context = "\n\n[BRAIN-KONTEXT]\n" + "\n".join(brain_snippets) + "\n[/BRAIN-KONTEXT]"
        except Exception as e:
            logger.warning(f"Brain context load failed: {e}")

    # 2. Build messages
    system_msg = MASTER_SYSTEM_PROMPT
    if brain_context:
        system_msg += brain_context

    system_msg += f"\n\nAktuelles Datum: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"

    messages = [{"role": "system", "content": system_msg}]

    # Add conversation history (last 20 messages)
    for h in history[-20:]:
        messages.append({"role": h["role"], "content": h["content"]})

    messages.append({"role": "user", "content": message})

    # 3. Call LLM
    llm_result = await llm_chat(messages)

    response_text = llm_result.get("content", "")
    provider = llm_result.get("provider", "unknown")
    model = llm_result.get("model", "unknown")

    # 4. Store in session history
    history.append({"role": "user", "content": message, "ts": datetime.now(timezone.utc).isoformat()})
    history.append({"role": "assistant", "content": response_text, "ts": datetime.now(timezone.utc).isoformat()})
    agent_sessions[session_id] = history

    # 5. Persist to DB if available
    if db is not None:
        try:
            await db.agent_sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {"updated_at": datetime.now(timezone.utc)},
                    "$push": {
                        "messages": {
                            "$each": [
                                {"role": "user", "content": message, "ts": datetime.now(timezone.utc).isoformat()},
                                {"role": "assistant", "content": response_text, "ts": datetime.now(timezone.utc).isoformat(), "provider": provider, "model": model},
                            ]
                        }
                    },
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)},
                },
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Failed to persist agent session: {e}")

    return {
        "message": response_text,
        "provider": provider,
        "model": model,
        "brain_context_loaded": bool(brain_context),
        "session_id": session_id,
        "usage": llm_result.get("usage", {}),
    }
