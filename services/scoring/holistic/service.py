from __future__ import annotations

import base64
import logging
import os
from typing import Optional, Tuple
from urllib.parse import urlparse
from uuid import UUID

import httpx

from services.common.models import GeneratedImage
from services.scoring.base import ScoreService


logger = logging.getLogger(__name__)


class HolisticScoreService(ScoreService):
    """调用外部 MNet 接口获取整体美学分数。"""

    module_name = "holistic"

    def __init__(
        self,
        *,
        api_url: Optional[str] = None,
        timeout: float = 10.0,
        api_token: Optional[str] = None,
    ) -> None:
        self._api_url = (
            api_url
            or os.getenv("HOLISTIC_SCORE_URL")
            or os.getenv("MNET_SCORE_URL")
            or "http://10.112.201.86:8099/api/mnet"
        )
        self._timeout = timeout
        self._api_token = api_token or os.getenv("HOLISTIC_SCORE_TOKEN") or os.getenv("MNET_SCORE_TOKEN")

    async def score(
        self,
        *,
        task_id: UUID,
        image: GeneratedImage,
    ) -> float:
        try:
            payload = await self._build_payload(image.url)
            if payload is None:
                raise ValueError("无法获取图片内容")

            headers = {}
            if self._api_token:
                headers["Authorization"] = f"Bearer {self._api_token}"

            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    self._api_url,
                    files={"file": payload},
                    headers=headers or None,
                )
            response.raise_for_status()
            score = self._extract_score(response.json())
            if score is None:
                raise ValueError("响应中缺少可用的分数字段")
            return self._clamp_score(score)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Holistic 美学评分失败: %s",
                exc,
                extra={"task_id": str(task_id), "image": image.url},
            )
            return 0.0

    async def _build_payload(self, image_url: str) -> Optional[Tuple[str, bytes, str]]:
        content_type = "application/octet-stream"
        if image_url.startswith("data:"):
            content_type, data = self._decode_data_url(image_url)
            filename = "image"
            return (filename, data, content_type)

        parsed = urlparse(image_url)
        if not parsed.scheme or not parsed.netloc:
            return None

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.get(image_url)
        response.raise_for_status()
        filename = os.path.basename(parsed.path) or "image"
        return (filename, response.content, response.headers.get("content-type", content_type))

    def _decode_data_url(self, data_url: str) -> Tuple[str, bytes]:
        header, _, encoded = data_url.partition(",")
        content_type = "image/png"
        if ";" in header:
            meta, *_ = header.split(";", 1)
            if meta.startswith("data:"):
                content_type = meta[5:] or content_type
        data = base64.b64decode(encoded)
        return content_type, data

    def _extract_score(self, payload: object) -> Optional[float]:
        def coerce(value: object) -> Optional[float]:
            if value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return None
            if isinstance(value, dict):
                for key in (
                    "holistic",
                    "holistic_score",
                    "holisticScore",
                    "score",
                    "value",
                ):
                    if key in value:
                        numeric = coerce(value[key])
                        if numeric is not None:
                            return numeric
                nested_candidates = [
                    value.get("data"),
                    value.get("scores"),
                    value.get("result"),
                    value.get("results"),
                    value.get("payload"),
                ]
                for candidate in nested_candidates:
                    numeric = coerce(candidate)
                    if numeric is not None:
                        return numeric
                if "items" in value:
                    numeric = coerce(value["items"])
                    if numeric is not None:
                        return numeric
                return None
            if isinstance(value, list):
                for item in value:
                    numeric = coerce(item)
                    if numeric is not None:
                        return numeric
                return None
            return None

        return coerce(payload)

    def _clamp_score(self, value: float) -> float:
        if value < 0.0:
            return 0.0

        # MNet 默认返回 0-1，小数过低时在视觉上显得过小。
        # 这里将其线性放大到 1-10 区间后再归一化回 0-1，避免兜底分显著低于豆包分。
        if value <= 1.0:
            boosted = 1.0 + max(0.0, min(1.0, value)) * 9.0  # 0 -> 1，1 -> 10
            return round(boosted / 10.0, 3)

        if value <= 10.0:
            return round(value / 10.0, 3)
        if value <= 100.0:
            return round(value / 100.0, 3)
        return 1.0
