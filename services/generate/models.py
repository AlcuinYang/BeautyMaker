from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from uuid import UUID


@dataclass(slots=True)
class EnhancementOptions:
    apply_clarity: bool = False
    apply_aesthetic: bool = False


@dataclass(slots=True)
class GenerateRequestPayload:
    """统一的适配器输入数据结构。"""

    task: str
    prompt: str
    provider: str
    size: str
    params: Dict[str, Any] = field(default_factory=dict)
    enhancement: EnhancementOptions = field(default_factory=EnhancementOptions)
    image_url: Optional[str] = None
    task_id: Optional[UUID] = None


def from_gateway_request(
    *,
    task_id: UUID,
    request,
) -> GenerateRequestPayload:
    """将 gateway.schemas.GenerateRequest 转换为适配器 payload。"""
    enhancement = EnhancementOptions(
        apply_clarity=getattr(request.enhancement, "apply_clarity", False),
        apply_aesthetic=getattr(request.enhancement, "apply_aesthetic", False),
    )

    payload = GenerateRequestPayload(
        task=request.task,
        prompt=request.prompt,
        provider=request.provider,
        size=request.size,
        params=request.params or {},
        enhancement=enhancement,
        image_url=getattr(request, "image_url", None),
        task_id=task_id,
    )
    return payload
