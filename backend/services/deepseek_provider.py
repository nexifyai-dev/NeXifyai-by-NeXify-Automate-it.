"""
NeXifyAI — DeepSeek LLM Provider
Alle Sub-Agenten nutzen DeepSeek. Der Master bleibt auf Arcee AI.
"""
import os
import json
import logging
from typing import Optional, AsyncGenerator

import httpx

logger = logging.getLogger("nexifyai.services.deepseek")

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")


def is_configured() -> bool:
    return bool(DEEPSEEK_API_KEY)


async def chat_completion(
    messages: list,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    stream: bool = False
) -> dict:
    """Non-streaming chat completion via DeepSeek."""
    if not DEEPSEEK_API_KEY:
        return {"error": "DEEPSEEK_API_KEY nicht konfiguriert"}

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model or DEEPSEEK_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                return {"content": content, "usage": usage, "model": model or DEEPSEEK_MODEL}
            logger.error(f"DeepSeek error {resp.status_code}: {resp.text[:300]}")
            return {"error": f"DeepSeek API Fehler ({resp.status_code})"}
    except Exception as e:
        logger.error(f"DeepSeek exception: {e}")
        return {"error": str(e)}


async def stream_completion(
    messages: list,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> AsyncGenerator[str, None]:
    """Streaming chat completion via DeepSeek. Yields content chunks."""
    if not DEEPSEEK_API_KEY:
        yield json.dumps({"error": "DEEPSEEK_API_KEY nicht konfiguriert"})
        return

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model or DEEPSEEK_MODEL,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                }
            ) as resp:
                if resp.status_code != 200:
                    error_body = await resp.aread()
                    yield json.dumps({"error": f"DeepSeek ({resp.status_code}): {error_body.decode()[:300]}"})
                    return
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"DeepSeek stream error: {e}")
        yield json.dumps({"error": str(e)})


async def invoke_agent(
    agent_name: str,
    agent_role: str,
    system_prompt: str,
    user_message: str,
    context: str = "",
    model: str = None,
    temperature: float = 0.5
) -> dict:
    """Invoke a sub-agent with DeepSeek. Returns the agent's response."""
    full_system = f"""Du bist {agent_name}, ein spezialisierter KI-Agent im NeXifyAI-Team.
Rolle: {agent_role}
Arbeitssprache: Deutsch
Qualitätsstandard: Professionell, präzise, handlungsorientiert.

{system_prompt}"""

    messages = [{"role": "system", "content": full_system}]
    if context:
        messages.append({"role": "system", "content": f"[KONTEXT]\n{context}\n[/KONTEXT]"})
    messages.append({"role": "user", "content": user_message})

    result = await chat_completion(messages, model=model, temperature=temperature, max_tokens=6000)
    if "error" in result:
        return {"agent": agent_name, "error": result["error"]}
    return {
        "agent": agent_name,
        "role": agent_role,
        "response": result["content"],
        "model": result.get("model", DEEPSEEK_MODEL),
        "usage": result.get("usage", {})
    }
