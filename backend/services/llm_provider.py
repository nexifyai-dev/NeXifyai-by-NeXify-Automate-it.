"""
LLM-Abstraktionsschicht — Provider-agnostische Kapselung.

Architektur:
  LLMProvider (Interface)
  ├── DeepSeekProvider     (PRIMÄR — Ziel-Architektur)
  └── EmergentGPTProvider  (FALLBACK — nur wenn DeepSeek-Key fehlt)

Kein direkter Provider-Zugriff aus der Fachlogik.
Alle Agenten-Calls gehen über diese Schicht.
"""

import os
import time
import logging
from typing import List, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger("nexifyai.services.llm_provider")


class LLMMessage:
    """Einheitliches Nachrichtenformat."""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class LLMProvider(ABC):
    """Abstrakte Basisklasse für LLM-Provider."""

    @abstractmethod
    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = None,
    ) -> str:
        pass

    @abstractmethod
    async def chat_with_history(
        self,
        session_id: str,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        model: str = None,
    ) -> str:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    def clear_session(self, session_id: str):
        pass

    async def health_check(self) -> dict:
        """Provider-spezifischer Health-Check."""
        return {"status": "unknown"}


# ══════════════════════════════════════════
# DEEPSEEK — PRIMÄRER PROVIDER
# ══════════════════════════════════════════

class DeepSeekProvider(LLMProvider):
    """
    PRIMÄRER Provider: DeepSeek.
    OpenAI-kompatible API mit Retry-Logik und Audit-Trail.
    """

    MODELS = {
        "deepseek-chat": "Standard Chat",
        "deepseek-reasoner": "Reasoning (erweitert)",
    }

    def __init__(self):
        self._api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        self._base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self._default_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self._sessions: Dict[str, list] = {}
        self._metrics = {"calls": 0, "errors": 0, "total_latency_ms": 0}
        self._max_retries = 3
        self._retry_base_delay = 1.0

    async def _call_api(self, messages: list, temperature: float, max_tokens: int, model: str) -> str:
        """API-Call mit Retry-Logik und Metriken."""
        import httpx

        target_model = model or self._default_model
        last_error = None

        for attempt in range(self._max_retries):
            start = time.monotonic()
            try:
                async with httpx.AsyncClient(timeout=90.0) as client:
                    response = await client.post(
                        f"{self._base_url}/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": target_model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        },
                    )
                    latency = int((time.monotonic() - start) * 1000)
                    self._metrics["calls"] += 1
                    self._metrics["total_latency_ms"] += latency

                    if response.status_code == 429:
                        retry_after = float(response.headers.get("retry-after", self._retry_base_delay * (2 ** attempt)))
                        logger.warning(f"DeepSeek rate-limited (429), retry in {retry_after}s (attempt {attempt+1}/{self._max_retries})")
                        import asyncio
                        await asyncio.sleep(retry_after)
                        continue

                    if response.status_code >= 500:
                        logger.warning(f"DeepSeek server error {response.status_code}, retry (attempt {attempt+1}/{self._max_retries})")
                        import asyncio
                        await asyncio.sleep(self._retry_base_delay * (2 ** attempt))
                        continue

                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"DeepSeek OK — model={target_model}, latency={latency}ms, tokens_used={data.get('usage', {}).get('total_tokens', '?')}")
                    return content

            except httpx.TimeoutException:
                latency = int((time.monotonic() - start) * 1000)
                self._metrics["errors"] += 1
                last_error = f"Timeout nach {latency}ms"
                logger.warning(f"DeepSeek timeout (attempt {attempt+1}/{self._max_retries})")
                import asyncio
                await asyncio.sleep(self._retry_base_delay * (2 ** attempt))
            except httpx.HTTPStatusError as e:
                self._metrics["errors"] += 1
                last_error = f"HTTP {e.response.status_code}"
                logger.error(f"DeepSeek HTTP error: {e.response.status_code} — {e.response.text[:200]}")
                if e.response.status_code in (401, 403):
                    return "[DeepSeek Auth-Fehler: API-Key ungültig oder gesperrt]"
                break
            except Exception as e:
                self._metrics["errors"] += 1
                last_error = str(e)[:100]
                logger.error(f"DeepSeek connection error: {e}")
                import asyncio
                await asyncio.sleep(self._retry_base_delay * (2 ** attempt))

        self._metrics["errors"] += 1
        return f"[DeepSeek nicht erreichbar nach {self._max_retries} Versuchen: {last_error}]"

    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = None,
    ) -> str:
        if not self._api_key:
            return "[DeepSeek nicht konfiguriert — DEEPSEEK_API_KEY fehlt]"

        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend([m.to_dict() for m in messages])

        return await self._call_api(api_messages, temperature, max_tokens, model)

    async def chat_with_history(
        self,
        session_id: str,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        model: str = None,
    ) -> str:
        if not self._api_key:
            return "[DeepSeek nicht konfiguriert — DEEPSEEK_API_KEY fehlt]"

        if session_id not in self._sessions:
            self._sessions[session_id] = []
            if system_prompt:
                self._sessions[session_id].append({"role": "system", "content": system_prompt})

        self._sessions[session_id].append({"role": "user", "content": user_message})

        result = await self._call_api(self._sessions[session_id], temperature, 2048, model)
        self._sessions[session_id].append({"role": "assistant", "content": result})

        # Limit history to prevent token overflow (keep system + last 40 messages)
        if len(self._sessions[session_id]) > 42:
            system_msgs = [m for m in self._sessions[session_id] if m["role"] == "system"]
            other_msgs = [m for m in self._sessions[session_id] if m["role"] != "system"]
            self._sessions[session_id] = system_msgs + other_msgs[-40:]

        return result

    def get_provider_name(self) -> str:
        return "deepseek"

    def clear_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    async def health_check(self) -> dict:
        if not self._api_key:
            return {"status": "not_configured", "error": "DEEPSEEK_API_KEY fehlt"}
        try:
            result = await self.chat(
                [LLMMessage(role="user", content="Antworte mit exakt einem Wort: OK")],
                system_prompt="Du bist ein Health-Check-Agent. Antworte nur mit OK.",
                temperature=0.0,
                max_tokens=10,
            )
            ok = "ok" in result.lower() and not result.startswith("[")
            return {
                "status": "healthy" if ok else "degraded",
                "response_sample": result[:50],
                "metrics": {**self._metrics},
            }
        except Exception as e:
            return {"status": "error", "error": str(e)[:100]}

    def get_metrics(self) -> dict:
        avg = (self._metrics["total_latency_ms"] / self._metrics["calls"]) if self._metrics["calls"] else 0
        return {
            **self._metrics,
            "avg_latency_ms": round(avg),
            "error_rate": round(self._metrics["errors"] / max(self._metrics["calls"], 1), 3),
        }


# ══════════════════════════════════════════
# EMERGENT GPT — FALLBACK
# ══════════════════════════════════════════

class EmergentGPTProvider(LLMProvider):
    """
    FALLBACK-Provider: GPT via Emergent LLM Key.
    Aktiv nur wenn DEEPSEEK_API_KEY nicht gesetzt.
    """

    def __init__(self):
        self._sessions = {}
        self._api_key = os.environ.get("EMERGENT_LLM_KEY", "")
        self._metrics = {"calls": 0, "errors": 0}

    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = None,
    ) -> str:
        if not self._api_key:
            return "[LLM nicht verfügbar — kein API-Key konfiguriert]"

        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import secrets

        self._metrics["calls"] += 1
        try:
            session_id = f"chat_{secrets.token_hex(8)}"
            chat = LlmChat(
                api_key=self._api_key,
                session_id=session_id,
                system_message=system_prompt,
            )
            chat.with_model("openai", model or "gpt-4o-mini")

            last_user = ""
            for msg in messages:
                if msg.role == "user":
                    last_user = msg.content

            response = await chat.send_message(UserMessage(text=last_user or ""))
            return response
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Emergent GPT error: {e}")
            return f"[Emergent GPT Fehler: {str(e)[:100]}]"

    async def chat_with_history(
        self,
        session_id: str,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        model: str = None,
    ) -> str:
        if not self._api_key:
            return "[LLM nicht verfügbar — kein API-Key konfiguriert]"

        from emergentintegrations.llm.chat import LlmChat, UserMessage

        self._metrics["calls"] += 1
        try:
            if session_id not in self._sessions:
                chat = LlmChat(
                    api_key=self._api_key,
                    session_id=session_id,
                    system_message=system_prompt,
                )
                chat.with_model("openai", model or "gpt-4o-mini")
                self._sessions[session_id] = chat

            chat = self._sessions[session_id]
            response = await chat.send_message(UserMessage(text=user_message))
            return response
        except Exception as e:
            self._metrics["errors"] += 1
            logger.error(f"Emergent GPT session error: {e}")
            return f"[Emergent GPT Fehler: {str(e)[:100]}]"

    def get_provider_name(self) -> str:
        return "emergent_gpt_fallback"

    def clear_session(self, session_id: str):
        self._sessions.pop(session_id, None)

    async def health_check(self) -> dict:
        if not self._api_key:
            return {"status": "not_configured", "error": "EMERGENT_LLM_KEY fehlt"}
        try:
            result = await self.chat(
                [LLMMessage(role="user", content="Antworte mit exakt einem Wort: OK")],
                system_prompt="Health-Check. Antworte nur mit OK.",
                temperature=0.0,
            )
            ok = "ok" in result.lower() and not result.startswith("[")
            return {"status": "healthy" if ok else "degraded", "response_sample": result[:50]}
        except Exception as e:
            return {"status": "error", "error": str(e)[:100]}


# ══════════════════════════════════════════
# FACTORY
# ══════════════════════════════════════════

def create_llm_provider() -> LLMProvider:
    """
    LLM-Provider basierend auf Konfiguration erstellen.
    Priorität: DeepSeek > Emergent GPT (Fallback).
    """
    provider_name = os.environ.get("LLM_PROVIDER", "auto").lower()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    emergent_key = os.environ.get("EMERGENT_LLM_KEY", "").strip()

    if provider_name == "deepseek" and deepseek_key:
        logger.info("LLM-Provider: DeepSeek (PRIMÄR — Ziel-Architektur)")
        return DeepSeekProvider()

    if provider_name == "auto" and deepseek_key:
        logger.info("LLM-Provider: DeepSeek (auto-detected, PRIMÄR)")
        return DeepSeekProvider()

    if emergent_key:
        logger.info("LLM-Provider: Emergent GPT (FALLBACK — DEEPSEEK_API_KEY nicht gesetzt)")
        return EmergentGPTProvider()

    logger.warning("LLM-Provider: Kein API-Key konfiguriert.")
    return EmergentGPTProvider()


def get_provider_status(provider: LLMProvider) -> dict:
    """Provider-Status für Admin-Dashboard."""
    name = provider.get_provider_name()
    is_deepseek = name == "deepseek"
    deepseek_key = bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())
    emergent_key = bool(os.environ.get("EMERGENT_LLM_KEY", "").strip())

    result = {
        "active_provider": name,
        "is_target_architecture": is_deepseek,
        "providers": {
            "deepseek": {
                "status": "active" if is_deepseek else ("ready" if deepseek_key else "not_configured"),
                "api_key_set": deepseek_key,
                "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                "models": list(DeepSeekProvider.MODELS.keys()),
            },
            "emergent_gpt": {
                "status": "active_fallback" if not is_deepseek and emergent_key else "standby",
                "api_key_set": emergent_key,
                "note": "Fallback — aktiv nur wenn DEEPSEEK_API_KEY fehlt",
            },
        },
        "migration_ready": deepseek_key,
        "env_config": {
            "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "auto"),
            "DEEPSEEK_MODEL": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        },
    }

    if hasattr(provider, 'get_metrics'):
        result["metrics"] = provider.get_metrics()

    return result
