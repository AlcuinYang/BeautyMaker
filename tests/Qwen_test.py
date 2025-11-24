from __future__ import annotations

"""
Standalone CLI to exercise the Qwen image adapter outside the full pipeline.

Usage examples:
  poetry run python tests/qwen_test.py --prompt "Product shot" --mode text2image
  poetry run python tests/qwen_test.py --prompt "重绘产品背景" \
      --mode image2image --reference ./example.png
"""

import argparse
import asyncio
import base64
import json
import logging
import mimetypes
import os
import sys
from pathlib import Path
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.generate.adapters.qwen import QwenProvider
from services.generate.models import GenerateRequestPayload


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hit the Qwen image service directly via the adapter.",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Main textual prompt passed to Qwen.",
    )
    parser.add_argument(
        "--mode",
        choices=("text2image", "image2image"),
        default="image2image",
        help="Select text-to-image or image-to-image flow. Default: image2image.",
    )
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        help="Reference image URL or file path (can be repeated). Required for image2image.",
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        help="Size string such as 1024x1024 (text2image only).",
    )
    parser.add_argument(
        "--style",
        default="<auto>",
        help="Style hint accepted by Qwen text2image API.",
    )
    parser.add_argument(
        "--model",
        help="Override the default model id.",
    )
    parser.add_argument(
        "--num-outputs",
        type=int,
        default=1,
        help="Number of variations to request (clamped to 1-4 by the adapter).",
    )
    parser.add_argument(
        "--endpoint",
        help="Override the submit endpoint used by the adapter.",
    )
    parser.add_argument(
        "--save-dir",
        type=Path,
        help="Optional directory to dump returned images (handles data URLs).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging for the adapter.",
    )
    return parser.parse_args()


def prepare_reference_images(sources: Iterable[str]) -> List[str]:
    prepared: List[str] = []
    for source in sources:
        if not source:
            continue
        if source.startswith(("http://", "https://", "data:")):
            prepared.append(source)
            continue

        path = Path(source).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Reference image not found: {source}")

        mime, _ = mimetypes.guess_type(path.name)
        mime = mime or "image/png"
        encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
        prepared.append(f"data:{mime};base64,{encoded}")
    return prepared


async def run_test(args: argparse.Namespace) -> dict:
    provider = QwenProvider()

    params = {
        "num_outputs": args.num_outputs,
    }
    if args.model:
        params["model"] = args.model
    if args.endpoint:
        params["endpoint"] = args.endpoint

    task = args.mode
    if task == "image2image":
        if not args.reference:
            raise ValueError("Image2image mode requires at least one --reference")
        params["reference_images"] = prepare_reference_images(args.reference)
        size = args.size  # ignored by adapter for i2i
    else:
        params["style"] = args.style
        size = args.size

    payload = GenerateRequestPayload(
        task=task,
        prompt=args.prompt,
        provider=QwenProvider.name,
        size=size,
        params=params,
    )

    result = await provider.generate(payload)
    return result


def save_returned_images(images: Iterable[str], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, image in enumerate(images, start=1):
        if not isinstance(image, str) or not image:
            continue

        if image.startswith("data:"):
            _, _, encoded = image.partition(",")
            header = image.split(";", 1)[0]
            mime = header.split(":", 1)[1] if ":" in header else "image/png"
            ext = mimetypes.guess_extension(mime) or ".png"
            path = output_dir / f"qwen_result_{index}{ext}"
            path.write_bytes(base64.b64decode(encoded))
            logging.info("Saved data URL image to %s", path)
        else:
            path = output_dir / f"qwen_result_{index}.url.txt"
            path.write_text(image, encoding="utf-8")
            logging.info("Recorded image URL to %s", path)


def main() -> int:
    args = parse_arguments()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if not (os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")):
        logging.error("DASHSCOPE_API_KEY (or QWEN_API_KEY) is not set in the environment.")
        return 2

    try:
        result = asyncio.run(run_test(args))
    except Exception as exc:  # noqa: BLE001
        logging.exception("Qwen test run failed: %s", exc)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))

    images = []
    if isinstance(result.get("images"), list):
        images.extend(result["images"])
    if isinstance(result.get("image_url"), str) and result["image_url"]:
        images.append(result["image_url"])

    if args.save_dir and images:
        save_returned_images(images, args.save_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
