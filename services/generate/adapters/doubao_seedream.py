"""豆包 Seedream 图像生成适配器

支持通过火山引擎 Ark 平台 REST API 进行文生图和图生图。
当没有 API 密钥时，适配器会返回占位符图片以保持演示和测试的独立性。
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import uuid4
import httpx

from services.generate.adapters.base import BaseProvider
from services.generate.models import GenerateRequestPayload


logger = logging.getLogger(__name__)


# 占位符图片（1x1 透明 PNG）
# 当 API 密钥缺失或请求失败时返回此图片
_PLACEHOLDER_IMAGE = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAAJElEQVR4Xu3BAQ0AAADCoPdPbQ43oAAAAAAAAAAA"
    "AAAAAAAAAPgPqdcAAT3mKMUAAAAASUVORK5CYII="
)

# 默认使用的模型名称
DEFAULT_MODEL = "doubao-seedream-4-0-250828"
# 默认图像尺寸
DEFAULT_SIZE = "2K"
# 火山引擎 Ark 平台的图像生成 API 端点
ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/images/generations"



class DoubaoSeedreamProvider(BaseProvider):
    """豆包 Seedream 图像生成提供商

    通过火山引擎 Ark 平台调用 Seedream 4.0 模型生成图片。
    支持文生图和图生图两种模式，以及序列化生成（批量生成多张变体）。
    """

    name = "doubao_seedream"

    async def generate(self, request: GenerateRequestPayload) -> Dict[str, Any]:
        """使用豆包 Seedream 生成图片

        如果缺少 API 密钥，会返回一张占位符图片以保持流程正常运行。

        Args:
            request: 生成请求参数（包含 prompt、size、params 等）

        Returns:
            包含生成图片 URL 列表和元数据的字典
        """
        # 尝试从多个环境变量中获取 API 密钥（优先级顺序）
        env_tokens = {
            "ARK_API_KEY": os.getenv("ARK_API_KEY"),
            "DOUBAO_API_KEY": os.getenv("DOUBAO_API_KEY"),
            "HOLISTIC_SCORE_TOKEN": os.getenv("HOLISTIC_SCORE_TOKEN"),
        }
        # 获取第一个非空的 API 密钥
        api_key = next((value for value in env_tokens.values() if value), None)
        # 记录密钥来源
        token_source = next((name for name, value in env_tokens.items() if value), None)
        token_length = len(api_key) if api_key else 0
        # 记录初始化信息（用于调试）
        logger.info(
            "Doubao Seedream init prompt=%s token_source=%s token_present=%s token_length=%s env_snapshot=%s",
            request.prompt[:30] + "..." if request.prompt and len(request.prompt) > 30 else request.prompt,
            token_source,
            bool(api_key),
            token_length,
            {k: bool(v) for k, v in env_tokens.items()},
        )
        # 使用请求中的 prompt，如果为空则使用默认值
        prompt = request.prompt or "Aesthetics Engine prompt"

        # 如果没有 API 密钥，返回占位符响应
        if not api_key:
            logger.warning("Doubao Seedream missing API key, returning placeholder response.")
            return self._placeholder(prompt=prompt, reason="missing_api_key")

        # 构建 API 请求负载
        payload = self._build_payload(request=request, prompt=prompt)

        # 构建请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        try:
            # 发送 HTTP POST 请求到豆包 API（超时 60 秒）
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(ARK_ENDPOINT, json=payload, headers=headers)
            # 检查响应状态码
            response.raise_for_status()
            data = response.json()
            # 从响应中提取图片 URL
            images = self._extract_urls(data)
            if not images:
                raise RuntimeError(f"Doubao response missing images: {data}")

            # 构建元数据
            metadata = {
                "provider": self.name,
                "prompt": prompt,
                "model": data.get("model", payload.get("model")),
                "size": self._extract_size(data) or payload.get("size"),
                "usage": data.get("usage"),  # API 使用情况（token 计数等）
            }

            # 返回成功响应
            return {
                "status": "success",
                "task_id": str(request.task_id or uuid4()),
                "images": images,  # 图片 URL 列表
                "image_url": images[0],  # 第一张图片（向后兼容）
                "metadata": metadata,
            }
        except httpx.HTTPStatusError as exc:
            # HTTP 错误（4xx, 5xx）
            reason = f"{exc.response.status_code} {exc.response.text}"
            logger.error(
                "Doubao request failed status=%s payload=%s body=%s",
                exc.response.status_code,
                payload,
                exc.response.text,
            )
            return self._placeholder(prompt=prompt, reason=reason)
        except Exception as exc:  # noqa: BLE001
            # 其他异常（网络错误、超时等）
            return self._placeholder(prompt=prompt, reason=str(exc))

    def _build_payload(self, *, request: GenerateRequestPayload, prompt: str) -> Dict[str, Any]:
        """从标准化请求构建 Ark API 请求负载

        严格遵循 Seedream 4.0 API 文档规范：
        - 参考图片字段名是 'image'（不是 image_urls）
        - Base64 图片必须包含 data URI 头部（如 data:image/png;base64,）

        Args:
            request: 标准化的生成请求
            prompt: 提示词文本

        Returns:
            符合 Ark API 规范的请求负载字典
        """
        params = request.params or {}
        # 从多个可能的参数名中获取参考图片
        # 支持不同的命名约定以提高兼容性
        references: List[str] = (
            params.get("reference_images")
            or params.get("references")
            or params.get("image_urls")
            or []
        )

        # 确定使用的模型（默认使用 4.0 版本）
        model_name = params.get("model") or "ep-m-20251022222907-9jvsg"

        # 处理图像尺寸
        raw_size = params.get("size") or request.size or DEFAULT_SIZE
        # Seedream 4.0 支持 "1K", "2K" 或 "WxH" 格式，进行归一化
        size = self._normalize_size(raw_size)

        # 构建基础请求负载
        payload: Dict[str, Any] = {
            "model": model_name,
            "prompt": prompt,
            "size": size,
            "response_format": "url",
            "stream": False,
            "watermark": params.get("watermark", False),
            "sequential_image_generation": "disabled",
        }

        # 处理参考图片（如果有）
        if references:
            processed_refs = []
            for ref in references:
                if not isinstance(ref, str):
                    continue

                if ref.startswith("http://") or ref.startswith("https://"):
                    # HTTP(S) URL 格式可以直接使用
                    processed_refs.append(ref)
                elif ref.startswith("data:"):
                    # Data URI 格式（API 要求的格式），直接保留
                    processed_refs.append(ref)
                else:
                    # 原始 base64 字符串，需要添加 data URI 头部
                    # 为安全起见假设为 PNG 格式
                    processed_refs.append(f"data:image/png;base64,{ref}")

            # 重要：API 文档要求字段名为 'image'（不是 'image_urls'）
            payload["image"] = processed_refs

        return payload

    def _extract_urls(self, payload: Dict[str, Any]) -> List[str]:
        """从 Ark API 响应中提取图片 URL

        Args:
            payload: Ark API 返回的响应数据

        Returns:
            图片 URL 列表
        """
        urls: List[str] = []
        data = payload.get("data")
        # 响应中的 data 字段是一个列表，每个元素包含一张图片的信息
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("url"):
                    urls.append(item["url"])
        return urls

    def _extract_size(self, payload: Dict[str, Any]) -> Optional[str]:
        """从 Ark API 响应中提取图像尺寸

        Args:
            payload: Ark API 返回的响应数据

        Returns:
            图像尺寸字符串（如 "1024x1024"），如果未找到则返回 None
        """
        data = payload.get("data")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get("size"):
                    return item["size"]
        return None

    @staticmethod
    def _normalize_size(size: Optional[str]) -> str:
        """归一化图像尺寸字符串

        将各种尺寸表示法统一为标准格式。
        例如：将 "1024×1024" 和 "1024X1024" 都转换为 "1024x1024"

        Args:
            size: 原始尺寸字符串

        Returns:
            归一化后的尺寸字符串
        """
        if not size:
            return DEFAULT_SIZE
        normalized = str(size).strip()
        # 将全角乘号和大写 X 替换为小写 x
        normalized = normalized.replace("×", "x").replace("X", "x")
        return normalized

    def _placeholder(self, *, prompt: str, reason: Optional[str]) -> Dict[str, Any]:
        """返回占位符图片响应

        当 API 密钥缺失或请求失败时，返回一张透明占位符图片。
        这样可以保持流程继续运行而不会完全失败。

        Args:
            prompt: 用户的提示词
            reason: 返回占位符的原因（用于日志记录）

        Returns:
            包含占位符图片的响应字典
        """
        logger.info("Doubao Seedream placeholder emitted reason=%s", reason)
        metadata = {
            "provider": self.name,
            "prompt": prompt,
            "note": f"Doubao placeholder response ({reason or 'unknown'})",
        }
        return {
            "status": "success",
            "task_id": str(uuid4()),
            "images": [_PLACEHOLDER_IMAGE],  # 1x1 透明 PNG
            "image_url": _PLACEHOLDER_IMAGE,
            "metadata": metadata,
        }
