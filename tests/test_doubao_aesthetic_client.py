"""豆包视觉理解接口调试脚本（参数已固定）。"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Dict

import httpx

# 固定参数
ARK_ENDPOINT = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
ARK_MODEL = "doubao-seed-1-6-vision-250815"
ARK_TOKEN = os.environ.get("ARK_API_KEY")
ARK_PROMPT_PATH = Path("prompts/doubao_aesthetic.prompt")
IMAGE_SOURCE = "tests/img/0001.png"  # 可替换为任意本地路径或网络 URL
QUESTION = "请直接输出JSON结果"
SYSTEM_PROMPT = ARK_PROMPT_PATH.read_text(encoding="utf-8").strip()

def _load_image_payload(image: str) -> Dict[str, Dict[str, str]]:
    if image.startswith("http://") or image.startswith("https://"):
        return {"type": "image_url", "image_url": {"url": image}}

    file_path = Path(image).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"找不到图片文件: {file_path}")

    mime, _ = mimetypes.guess_type(str(file_path))
    if mime is None:
        mime = "image/png"

    encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime};base64,{encoded}",
        },
    }


def main() -> None:
    if not ARK_TOKEN:
        raise RuntimeError("请先通过环境变量 ARK_API_KEY 或 HOLISTIC_SCORE_TOKEN 提供豆包 Token。")

    # payload = {
    #     "model": ARK_MODEL,
    #     "messages": [
    #         {
    #             "role": "user",
    #             "content": [
    #                 _load_image_payload(IMAGE_SOURCE),
    #                 {"type": "text", "text": QUESTION},
    #             ],
    #         }
    #     ],
    # }
    payload = {
    "model": ARK_MODEL,
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},      # 关键：发送系统提示
        {
            "role": "user",
            "content": [
                _load_image_payload(IMAGE_SOURCE),
                {"type": "text", "text": QUESTION},
            ],
        },
    ],
}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ARK_TOKEN}",
    }

    print("===== Request =====")
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    try:
        response = httpx.post(ARK_ENDPOINT, headers=headers, json=payload, timeout=60.0)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(f"请求失败：{exc.response.status_code} {exc.response.text}")
        return
    except httpx.RequestError as exc:
        print(f"网络异常：{exc}")
        return

    print("===== Response =====")
    try:
        parsed = response.json()
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    except json.JSONDecodeError:
        print(response.text)


if __name__ == "__main__":
    main()
