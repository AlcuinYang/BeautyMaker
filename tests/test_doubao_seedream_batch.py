"""Manual diagnostic script for Doubao Seedream sequential generation."""

from __future__ import annotations

import argparse
import asyncio
import base64
import mimetypes
import os
import sys
from typing import Iterable, List

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.generate.adapters.doubao_seedream import DoubaoSeedreamProvider
from services.generate.models import GenerateRequestPayload


async def run_seedream_test(
    *,
    prompt: str,
    num_variations: int,
    size: str,
    reference_images: Iterable[str],
) -> None:
    provider = DoubaoSeedreamProvider()
    payload = GenerateRequestPayload(
        task="image2image",
        prompt=prompt,
        provider=provider.name,
        size=size,
        params={
            "reference_images": list(reference_images),
            "sequential_mode": "auto" if num_variations > 1 else "disabled",
            "num_variations": num_variations,
        },
    )

    print("=== Request payload ===")
    print(
        {
            "prompt": payload.prompt,
            "size": payload.size,
            "params": payload.params,
        }
    )

    response = await provider.generate(payload)

    print("=== Raw response keys ===")
    print(list(response.keys()))

    images_raw: List[str] = []
    if isinstance(response.get("images"), list):
        images_raw.extend(str(item) for item in response["images"])
    if response.get("image_url"):
        images_raw.append(response["image_url"])

    unique = list(dict.fromkeys(images_raw))
    print(f"requested={num_variations} delivered={len(images_raw)} unique={len(unique)}")
    for idx, url in enumerate(unique, start=1):
        print(f"[{idx}] {url}")

    if response.get("metadata"):
        print("metadata:", response["metadata"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose Doubao Seedream batch output.")
    parser.add_argument("--prompt", default="为产品生成{num}张高转化电商宣传图", help="Generation prompt.")
    parser.add_argument("--reference", action="append", default=[], help="Reference image URL or data URI.")
    parser.add_argument("--num", type=int, default=4, help="Number of sequential variations.")
    parser.add_argument("--size", default="1728x2304", help="Generation size.")
    parser.add_argument(
        "--group-mode",
        action="store_true",
        help="When set, mark group mode for downstream pipeline (1〜6 sequential images).",
    )
    args = parser.parse_args()

    api_key = os.getenv("ARK_API_KEY") or os.getenv("DOUBAO_API_KEY")
    if not api_key:
        raise SystemExit("请先设置 ARK_API_KEY 或 DOUBAO_API_KEY 环境变量。")

    references: List[str] = []
    for item in args.reference:
        if item.startswith(("http://", "https://", "data:")):
            references.append(item)
            continue
        path = Path(item).expanduser()
        if not path.exists():
            raise SystemExit(f"参考图不存在：{path}")
        mime, _ = mimetypes.guess_type(str(path))
        if not mime:
            mime = "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        references.append(f"data:{mime};base64,{encoded}")

    asyncio.run(
        run_seedream_test(
            prompt=args.prompt,
            num_variations=args.num,
            size=args.size,
            reference_images=references,
        )
    )


if __name__ == "__main__":
    main()
