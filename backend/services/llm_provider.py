"""
LLM-Abstraktionsschicht — Provider-agnostische Kapselung.

Ziel: DeepSeek als primärer Provider.
Temporär: GPT-5.2 via Emergent LLM Key.

Architektur:
  LLMProvider (Interface)
  ├── EmergentGPTProvider  (TEMPORÄR — aktiv)
  └── DeepSeekProvider     (ZIEL — vorbereitet)

Kein direkter Provider-Zugriff aus der Fachlogik.
Alle Agenten-Calls gehen über diese Schicht.
"""

import os
import logging
from typing import List, Dict, Optional, Any
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
        """Einzelne Chat-Completion."""
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
        """Chat mit Session-basiertem History-Management."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass


class EmergentGPTProvider(LLMProvider):
    """
    TEMPORÄRER Provider: GPT-5.2 via Emergent LLM Key.
    Wird durch DeepSeekProvider ersetzt.
    """

    def __init__(self):
        self._sessions = {}
        self._api_key = os.environ.get("EMERGENT_LLM_KEY", "")

    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = None,
    ) -> str:
        if not self._api_key:
            return "LLM nicht verfügbar (Key fehlt)"

        from emergentintegrations.llm.chat import LlmChat, UserMessage
        import secrets

        # LlmChat requires session_id, not model/temperature in __init__
        session_id = f"chat_{secrets.token_hex(8)}"
        chat = LlmChat(
            api_key=self._api_key,
            session_id=session_id,
            system_message=system_prompt,
        )
        # Set model via with_model method
        chat.with_model("openai", model or "gpt-4o-mini")

        # Nur letzte User-Message senden (Emergent-API-Pattern)
        last_user = ""
        for msg in messages:
            if msg.role == "user":
                last_user = msg.content

        response = await chat.send_message(UserMessage(text=last_user or ""))
        return response

    async def chat_with_history(
        self,
        session_id: str,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        model: str = None,
    ) -> str:
        if not self._api_key:
            return "LLM nicht verfügbar (Key fehlt)"

        from emergentintegrations.llm.chat import LlmChat, UserMessage

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

    def get_provider_name(self) -> str:
        return "emergent_gpt52_temporary"

    def clear_session(self, session_id: str):
        """Session-Cache leeren."""
        self._sessions.pop(session_id, None)


class DeepSeekProvider(LLMProvider):
    """
    ZIEL-Provider: DeepSeek.
    Unterstützte Modelle:
      - deepseek-chat (Standard-Chat)
      - deepseek-reasoner (erweiterte Reasoning-Fähigkeiten)

    Aktivierung:
    1. DEEPSEEK_API_KEY in .env setzen
    2. LLM_PROVIDER=deepseek in .env setzen (oder auto)
    """

    MODELS = {
        "deepseek-chat": "Standard Chat",
        "deepseek-reasoner": "Reasoning (erweitert)",
    }

    def __init__(self):
        self._api_key = os.environ.get("DEEPSEEK_API_KEY", "")
        self._base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self._default_model = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")
        self._sessions: Dict[str, list] = {}

    async def chat(
        self,
        messages: List[LLMMessage],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: str = None,
    ) -> str:
        if not self._api_key:
            return "DeepSeek nicht konfiguriert (DEEPSEEK_API_KEY fehlt). Bitte in .env hinterlegen."

        import httpx

        api_messages = []
        if system_prompt:
            api_messages.append({"role": "system", "content": system_prompt})
        api_messages.extend([m.to_dict() for m in messages])

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self._base_url}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model or self._default_model,
                        "messages": api_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"DeepSeek API error: {e.response.status_code} — {e.response.text[:200]}")
            return f"DeepSeek API-Fehler: {e.response.status_code}"
        except Exception as e:
            logger.error(f"DeepSeek connection error: {e}")
            return f"DeepSeek Verbindungsfehler: {str(e)[:100]}"

    async def chat_with_history(
        self,
        session_id: str,
        user_message: str,
        system_prompt: str = "",
        temperature: float = 0.7,
        model: str = None,
    ) -> str:
        if session_id not in self._sessions:
            self._sessions[session_id] = []
            if system_prompt:
                self._sessions[session_id].append({"role": "system", "content": system_prompt})

        self._sessions[session_id].append({"role": "user", "content": user_message})

        messages = [LLMMessage(**m) for m in self._sessions[session_id] if m["role"] != "system"]
        system = system_prompt or next(
            (m["content"] for m in self._sessions[session_id] if m["role"] == "system"), ""
        )

        response = await self.chat(messages, system, temperature, model=model)
        self._sessions[session_id].append({"role": "assistant", "content": response})

        return response

    def get_provider_name(self) -> str:
        return "deepseek"

    def clear_session(self, session_id: str):
        self._sessions.pop(session_id, None)


# ══════════════════════════════════════════
# FACTORY
# ══════════════════════════════════════════

def create_llm_provider() -> LLMProvider:
    """
    LLM-Provider basierend auf Konfiguration erstellen.
    Prüft: LLM_PROVIDER env var:
      - 'deepseek' → DeepSeek direkt
      - 'emergent' → Emergent GPT-5.2 (Fallback)
      - 'auto' (default) → DeepSeek wenn Key vorhanden, sonst Emergent
    """
    provider_name = os.environ.get("LLM_PROVIDER", "auto").lower()
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    emergent_key = os.environ.get("EMERGENT_LLM_KEY", "").strip()

    if provider_name == "deepseek" and deepseek_key:
        logger.info("LLM-Provider: DeepSeek (Ziel-Architektur)")
        return DeepSeekProvider()

    if provider_name == "auto" and deepseek_key:
        logger.info("LLM-Provider: DeepSeek (auto-detected)")
        return DeepSeekProvider()

    if emergent_key:
        logger.info("LLM-Provider: Emergent GPT-5.2 (TEMPORÄR — Fallback bis DeepSeek-Key gesetzt)")
        return EmergentGPTProvider()

    logger.warning("LLM-Provider: Kein API-Key konfiguriert. Emergent-Fallback ohne Key.")
    return EmergentGPTProvider()


def get_provider_status(provider: LLMProvider) -> dict:
    """Provider-Status für Admin-Dashboard."""
    name = provider.get_provider_name()
    is_deepseek = name == "deepseek"
    deepseek_key = bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())
    emergent_key = bool(os.environ.get("EMERGENT_LLM_KEY", "").strip())

    return {
        "active_provider": name,
        "is_target_architecture": is_deepseek,
        "providers": {
            "deepseek": {
                "status": "active" if is_deepseek else ("ready" if deepseek_key else "not_configured"),
                "api_key_set": deepseek_key,
                "base_url": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                "models": list(DeepSeekProvider.MODELS.keys()) if is_deepseek else [],
            },
            "emergent_gpt52": {
                "status": "active" if not is_deepseek else "fallback",
                "api_key_set": emergent_key,
                "note": "Temporärer Fallback — wird durch DeepSeek ersetzt",
            },
        },
        "migration_ready": deepseek_key,
        "env_config": {
            "LLM_PROVIDER": os.environ.get("LLM_PROVIDER", "auto"),
            "DEEPSEEK_MODEL": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
        },
    }
