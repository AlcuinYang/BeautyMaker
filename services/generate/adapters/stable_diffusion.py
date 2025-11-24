from __future__ import annotations

from typing import Any, Dict

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


class StableDiffusionProvider(BaseProvider):
    """Stable Diffusion 接入占位实现。"""

    name = "stable_diffusion"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        raise NotImplementedError("Stable Diffusion integration pending.")
