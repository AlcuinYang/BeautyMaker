from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from services.common.models import GeneratedImage


class ScoreService(ABC):
    """美学评分微服务约定，子类需实现具体的打分逻辑。"""

    module_name: str

    @abstractmethod
    async def score(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
    ) -> float:
        """返回当前模块的评分结果，范围约定为 0~1。"""
