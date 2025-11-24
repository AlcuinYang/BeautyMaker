from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Optional
from urllib.parse import quote_plus

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proxy", tags=["proxy"])


# Provider metadata for automatic defaults.
ProviderConfig = Dict[str, Any]

PROVIDERS: Dict[str, ProviderConfig] = {
    "openai": {
        "default_endpoint": "https://api.openai.com/v1/images/generations",
        "auth_header": "Authorization",
        "env_key": "OPENAI_API_KEY",
        "response_type": "json",
    },
    "gemini": {
        "default_endpoint": (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-pro:generateContent"
        ),
        "auth_header": "x-goog-api-key",
        "env_key": "GEMINI_API_KEY",
        "response_type": "json",
    },
    "stability": {
        "default_endpoint": (
            "https://api.stability.ai/v1/generation/"
            "stable-diffusion-xl-1024x1024/text-to-image"
        ),
        "auth_header": "Authorization",
        "env_key": "STABILITY_API_KEY",
        "auth_prefix": "Bearer ",
        "response_type": "image",
    },
    "qwen": {
        "default_endpoint": (
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/"
            "generation"
        ),
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "env_key": "DASHSCOPE_API_KEY",
        "response_type": "json",
    },
    "pollinations": {
        "default_endpoint": "https://pollinations.ai/prompt",
        "response_type": "image",
    },
}

# Default timeout (seconds) for outbound calls.
DEFAULT_TIMEOUT = 30.0


def _resolve_endpoint(provider: str, endpoint: Optional[str], payload: Dict[str, Any]) -> str:
    if endpoint:
        return endpoint

    config = PROVIDERS.get(provider)
    if not config:
        raise HTTPException(status_code=400, detail="unknown_provider")

    base = config.get("default_endpoint")
    if provider == "pollinations":
        prompt = payload.get("prompt")
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt_required_for_pollinations")
        prompt_encoded = quote_plus(prompt)
        params = {
            "model": payload.get("model", "flux"),
            "width": payload.get("width", 1024),
            "height": payload.get("height", 1024),
            "seed": payload.get("seed"),
            "referrer": payload.get("referrer", "proxy.aesthetic-engine"),
        }
        query = httpx.QueryParams({k: v for k, v in params.items() if v is not None}).to_str()
        return f"{base}/{prompt_encoded}?{query}" if query else f"{base}/{prompt_encoded}"

    if provider == "qwen":
        # If the incoming payload already includes the DashScope request body, use
        # the default endpoint; no special URL rewriting needed.
        return base

    if not base:
        raise HTTPException(status_code=400, detail="endpoint_required")
    return base


def _inject_auth_headers(provider: str, headers: Dict[str, str]) -> Dict[str, str]:
    config = PROVIDERS.get(provider)
    if not config:
        return headers

    env_key = config.get("env_key")
    if not env_key:
        return headers

    api_key = os.getenv(env_key)
    if not api_key:
        logger.warning("API key missing for provider '%s' (env %s)", provider, env_key)
        return headers

    header_name = config.get("auth_header", "Authorization")
    prefix = config.get("auth_prefix", "Bearer " if header_name.lower() == "authorization" else "")

    headers = dict(headers)  # copy to avoid mutating caller data
    headers.setdefault(header_name, f"{prefix}{api_key}")
    return headers


@router.post("/{provider}")
async def proxy_request(provider: str, request: Request) -> Response:
    payload = await request.json()
    endpoint = payload.get("endpoint")
    headers: Dict[str, str] = payload.get("headers") or {}
    body: Dict[str, Any] = payload.get("payload") or {}

    try:
        target_url = _resolve_endpoint(provider, endpoint, body)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to resolve endpoint for %s: %s", provider, exc)
        raise HTTPException(status_code=400, detail="invalid_endpoint") from exc

    headers = _inject_auth_headers(provider, headers)

    timeout = httpx.Timeout(DEFAULT_TIMEOUT)
    proxies = os.getenv("GLOBAL_HTTP_PROXY") or None

    logger.info(
        "Proxying request -> provider=%s endpoint=%s via=%s",
        provider,
        target_url,
        "proxy" if proxies else "direct",
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(target_url, headers=headers, json=body)

        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=content_type,
                headers={"x-proxy-provider": provider},
            )

        if resp.status_code >= 400:
            message = resp.text or resp.reason_phrase
            logger.warning("Proxy request failed [%s] %s", resp.status_code, message)
            return Response(
                content=json.dumps({"status": "failed", "reason": message}),
                status_code=resp.status_code,
                media_type="application/json",
            )

        if "image" in content_type or PROVIDERS.get(provider, {}).get("response_type") == "image":
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=content_type or "image/png",
                headers={"x-proxy-provider": provider},
            )

        return Response(
            content=json.dumps(
                {
                    "status": "unknown_response",
                    "content_type": content_type,
                    "text": resp.text,
                }
            ),
            status_code=resp.status_code,
            media_type="application/json",
        )
    except httpx.HTTPError as exc:
        logger.exception("Proxy request HTTP error for %s: %s", provider, exc)
        return Response(
            content=json.dumps({"status": "failed", "reason": str(exc)}),
            status_code=502,
            media_type="application/json",
        )
