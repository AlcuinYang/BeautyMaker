from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

from services.generate.models import GenerateRequestPayload


class BaseProvider(ABC):
    """模型适配器基类，所有生成服务需继承此类。"""

    name: str

    @abstractmethod
    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        """执行生成任务并返回标准化结构。"""
