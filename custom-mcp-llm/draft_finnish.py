"""Draft Finnish MCP server.

This module exposes a single MCP tool, ``draft_finnish``, which forwards
incoming prompts to an external vLLM instance. The vLLM endpoint is
configured via environment variables and is expected to implement the
OpenAI-compatible ``/v1/chat/completions`` route.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import os
import httpx
from mcp.server.fastmcp import FastMCP


SERVER_NAME = os.getenv("MCP_SERVER_NAME", "draft-finnish")
SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
mcp = FastMCP(SERVER_NAME, host=SERVER_HOST)

VLLM_ENDPOINT_ENV = "VLLM_ENDPOINT"
VLLM_MODEL_ENV = "VLLM_MODEL"
VLLM_API_KEY_ENV = "VLLM_API_KEY"
DEFAULT_MODEL = os.getenv(VLLM_MODEL_ENV, "meta-llama/Llama-3.1-8B-Instruct")
DEFAULT_SYSTEM_PROMPT = os.getenv(
    "DRAFT_FINNISH_SYSTEM_PROMPT",
    "Olet avulias suomenkielinen avustaja. Vastaa suomeksi, ellei toisin pyydetä.",
)


async def _post_to_vllm(endpoint: str, payload: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, Any]:
    """Send a chat-completion request to the vLLM endpoint."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


def _build_messages(prompt: str, system_prompt: Optional[str]) -> list[Dict[str, str]]:
    messages: list[Dict[str, str]] = []
    system = system_prompt or DEFAULT_SYSTEM_PROMPT
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


@mcp.tool()
async def draft_finnish(
    prompt: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    system_prompt: Optional[str] = None,
) -> str:
    """Forward a prompt to the configured vLLM endpoint and return the response text."""

    endpoint = os.getenv(VLLM_ENDPOINT_ENV)
    if not endpoint:
        return (
            "VLLM endpoint is not configured. Set the environment variable "
            f"{VLLM_ENDPOINT_ENV} to the vLLM /v1/chat/completions URL."
        )

    model = os.getenv(VLLM_MODEL_ENV, DEFAULT_MODEL)
    api_key = os.getenv(VLLM_API_KEY_ENV)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload: Dict[str, Any] = {
        "model": model,
        "messages": _build_messages(prompt, system_prompt),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    try:
        data = await _post_to_vllm(endpoint, payload, headers)
    except httpx.HTTPStatusError as exc:
        return (
            "vLLM returned an error: "
            f"{exc.response.status_code} {exc.response.text}"
        )
    except httpx.RequestError as exc:
        return f"Unable to reach vLLM endpoint at {endpoint}: {exc}"

    try:
        completion = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return f"Unexpected response format from vLLM: {data}"

    return completion.strip()


if __name__ == "__main__":
    mcp.run(transport="sse")
