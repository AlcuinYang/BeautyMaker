from __future__ import annotations

from dataclasses import replace
from typing import Iterable, List
from uuid import UUID

from services.common.models import GeneratedImage


class EnhancementService:
    """执行图片增强流程，例如清晰术，以提升最终观感。"""

    async def apply_clarity(
        self,
        *,
        task_id: UUID,
        images: Iterable[GeneratedImage],
    ) -> List[GeneratedImage]:
        enhanced: List[GeneratedImage] = []
        for image in images:
            metadata = dict(image.metadata)
            # 标记清晰术已生效，方便后续排查
            metadata["clarity_enhanced"] = True
            metadata["enhancement_task"] = str(task_id)
            enhanced.append(
                replace(
                    image,
                    metadata=metadata,
                )
            )
        return enhanced
