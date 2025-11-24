from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import httpx
from fastapi import APIRouter

from services.generate import list_providers
from services.generate.routes.provider_info import PROVIDER_META


router = APIRouter()


async def _check_provider_status(endpoint: str | None) -> bool:
    if not endpoint:
        return False
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(endpoint)
            return response.status_code in {200, 401, 403, 404}
    except Exception:
        return False


def _bundle_provider(name: str, is_active: bool) -> Dict[str, Any]:
    meta = PROVIDER_META.get(name, {})
    return {
        "id": name,
        "display_name": meta.get("display_name", name),
        "description": meta.get("description", ""),
        "category": meta.get("category", "general"),
        "is_free": meta.get("is_free", False),
        "is_active": is_active,
        "icon": meta.get("icon"),
        "endpoint": meta.get("endpoint"),
        "latency_ms": None,
    }


@router.get("/api/providers")
async def list_registered_providers() -> Dict[str, Any]:
    provider_names: List[str] = list_providers()
    status_checks = await asyncio.gather(
        *(_check_provider_status(PROVIDER_META.get(name, {}).get("endpoint"))
          for name in provider_names)
    )

    providers = [_bundle_provider(name, status) for name, status in zip(provider_names, status_checks)]

    providers.sort(
        key=lambda item: (
            not item["is_free"],
            not item["is_active"],
            item["id"].startswith("lab_"),
            item["display_name"],
        )
    )

    return {
        "status": "success",
        "providers": providers,
    }
