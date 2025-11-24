from __future__ import annotations

from uuid import UUID

from gateway.schemas import GenerateRequest
from services.common.models import GenerationResult
from services.generate import get_provider
from services.generate.models import from_gateway_request


class GenerationService:
    """统一外部生成提供商的调用入口，屏蔽差异化细节。"""

    async def generate(
        self,
        *,
        task_id: UUID,
        request: GenerateRequest,
    ) -> GenerationResult:
        provider = get_provider(request.provider)
        payload = from_gateway_request(task_id=task_id, request=request)
        provider_response = await provider.generate(payload)

        images = _normalize_images(
            provider_response,
            provider_name=provider.name,
            prompt=payload.prompt,
        )

        return GenerationResult(task_id=task_id, provider=provider.name, images=images)


def _normalize_images(response: dict, *, provider_name: str, prompt: str):
    from services.common.models import GeneratedImage

    metadata = response.get("metadata") or {}
    urls = []
    if isinstance(response.get("images"), list):
        urls.extend(response["images"])
    if response.get("image_url"):
        urls.append(response["image_url"])

    urls = [url for url in urls if isinstance(url, str) and url]

    if not urls:
        # 返回至少一个占位图，避免后续流程中断
        return [
            GeneratedImage(
                url="",
                provider=provider_name,
                prompt=prompt,
                metadata={**metadata, "status": response.get("status")},
            )
        ]

    images = [
        GeneratedImage(
            url=url,
            provider=provider_name,
            prompt=prompt,
            metadata=metadata,
        )
        for url in urls
    ]
    return images
