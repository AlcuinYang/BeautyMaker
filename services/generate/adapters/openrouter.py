from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload

logger = logging.getLogger(__name__)


class OpenRouterImageProvider(BaseProvider):
    """Shared logic for OpenRouter-backed image models."""

    endpoint = "https://openrouter.ai/api/v1/chat/completions"
    timeout_seconds = 120.0
    model_name: str = ""
    default_modalities: Optional[List[str]] = None

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        payload = self._build_payload(request)
        headers = self._build_headers()
        transport = _build_transport()

        timeout = httpx.Timeout(self.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
            try:
                response = await client.post(
                    self.endpoint,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text if exc.response is not None else str(exc)
                logger.error(
                    "OpenRouter request failed status=%s detail=%s provider=%s",
                    exc.response.status_code if exc.response is not None else "n/a",
                    detail,
                    self.name,
                )
                raise RuntimeError(f"OpenRouter request failed: {detail}") from exc
            except httpx.HTTPError as exc:
                raise RuntimeError(f"OpenRouter network error: {exc}") from exc

        body = response.json()
        images = self._extract_images(body)
        if not images:
            raise RuntimeError(f"OpenRouter response missing images: {body}")

        metadata = {
            "provider": self.name,
            "model": payload.get("model"),
            "mode": request.task,
            "request_id": body.get("id"),
            "usage": body.get("usage"),
            "endpoint": self.endpoint,
        }

        return {
            "status": "success",
            "task_id": str(request.task_id or uuid4()),
            "images": images,
            "image_url": images[0],
            "metadata": metadata,
        }

    def _build_payload(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        params = dict(request.params or {})
        model_name = params.pop("model", self.model_name)
        if not model_name:
            raise ValueError("OpenRouter provider requires a model name.")

        references = self._collect_references(request, params)
        messages = params.pop("messages", None)
        if not messages:
            messages = [self._build_default_message(request.prompt, references)]
        elif not isinstance(messages, list):
            raise ValueError("OpenRouter payload 'messages' must be a list.")

        payload: Dict[str, Any] = {
            "model": model_name,
            "messages": messages,
        }

        modalities = params.pop("modalities", None) or self.default_modalities
        if modalities:
            payload["modalities"] = modalities

        # Include gateway-level size hints if they are meaningful to the model.
        if request.size and "size" not in params:
            payload["size"] = request.size

        payload.update(params)
        return payload

    def _collect_references(
        self,
        request: GenerateRequestPayload,
        params: Dict[str, Any],
    ) -> List[str]:
        references: List[str] = []
        primary_image = request.image_url or params.pop("image_url", None)
        if primary_image:
            references.append(primary_image)

        extra_refs: Iterable[str] = (
            params.pop("reference_images", None)
            or params.pop("image_urls", None)
            or []
        )
        for ref in extra_refs:
            if isinstance(ref, str):
                references.append(ref)
        return references

    def _build_default_message(
        self,
        prompt: Optional[str],
        references: List[str],
    ) -> Dict[str, Any]:
        if not prompt and not references:
            raise ValueError("Prompt or reference image is required for OpenRouter.")

        content: List[Dict[str, Any]] = []
        if prompt:
            content.append({"type": "text", "text": prompt})

        for ref in references:
            normalized = _normalize_image_reference(ref)
            content.append({"type": "image_url", "image_url": {"url": normalized}})

        return {"role": "user", "content": content}

    def _build_headers(self) -> Dict[str, str]:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for this provider.")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        referer = os.getenv("OPENROUTER_SITE_URL")
        if referer:
            headers["HTTP-Referer"] = referer
        title = os.getenv("OPENROUTER_SITE_NAME")
        if title:
            headers["X-Title"] = title
        return headers

    def _extract_images(self, body: Dict[str, Any]) -> List[str]:
        images: List[str] = []
        choices = body.get("choices") or []
        for choice in choices:
            message = choice.get("message") or {}
            images.extend(_extract_images_from_message(message))

        # Some providers may return images directly on the root object.
        if not images:
            images.extend(_extract_images_from_message(body))

        # Deduplicate while preserving order.
        seen = set()
        unique = []
        for image in images:
            if image and image not in seen:
                seen.add(image)
                unique.append(image)
        return unique


def _extract_images_from_message(message: Dict[str, Any]) -> List[str]:
    found: List[str] = []
    images_section = message.get("images") or []
    content_section = message.get("content")

    for entry in images_section:
        url = _extract_url(entry)
        if url:
            found.append(url)

    if isinstance(content_section, list):
        for item in content_section:
            if not isinstance(item, dict):
                continue
            if item.get("type") in {"output_image", "input_image", "image_url"}:
                urls = item.get("images") or [item.get("image_url")]
                for url_entry in urls:
                    url = _extract_url(url_entry)
                    if url:
                        found.append(url)
            elif item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str) and text.startswith("data:image"):
                    found.append(text)
    elif isinstance(content_section, str) and content_section.startswith("data:image"):
        found.append(content_section)

    return found


def _extract_url(entry: Any) -> Optional[str]:
    if isinstance(entry, str):
        return entry

    if not isinstance(entry, dict):
        return None

    if "url" in entry and isinstance(entry["url"], str):
        return entry["url"]

    image_url = entry.get("image_url")
    if isinstance(image_url, dict):
        url = image_url.get("url")
        if isinstance(url, str):
            return url
    elif isinstance(image_url, str):
        return image_url

    data_field = entry.get("b64_json")
    if isinstance(data_field, str):
        return f"data:image/png;base64,{data_field}"
    return None


def _normalize_image_reference(raw: str) -> str:
    if raw.startswith(("http://", "https://", "data:")):
        return raw
    return f"data:image/png;base64,{raw}"


def _resolve_proxy() -> Optional[str]:
    proxy = os.getenv("OPENROUTER_PROXY_URL")
    if proxy is None:
        proxy = "http://127.0.0.1:7897"
    proxy = proxy.strip()
    if not proxy or proxy.lower() in {"none", "false", "no"}:
        return None
    return proxy


def _build_transport() -> Optional[httpx.AsyncHTTPTransport]:
    proxy = _resolve_proxy()
    if not proxy:
        return None
    return httpx.AsyncHTTPTransport(proxy=proxy)
