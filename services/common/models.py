from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, Field


@dataclass(slots=True)
class GeneratedImage:
    """统一描述生成后的图片对象。"""

    url: str
    provider: str
    prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class GenerationResult:
    """生成阶段的返回结果，包含候选图片集合。"""

    task_id: UUID
    provider: str
    images: List[GeneratedImage]


class ComparativeReview(BaseModel):
    """Comparative review explaining why the best image won."""
    title: str = Field(description="Short title explaining the winning reason (4-8 Chinese characters)")
    analysis: str = Field(description="Detailed comparative analysis (~100 Chinese characters)")
    key_difference: str = Field(description="1-2 key difference keywords")
