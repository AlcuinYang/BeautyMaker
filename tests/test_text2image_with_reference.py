"""Test text2image pipeline with reference images.

This test validates the new reference_images parameter in the text2image
pipeline, ensuring it properly passes images to providers that support it.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import pytest

from services.pipeline.text2image import (
    Text2ImagePipelineRequest,
    run_text2image_pipeline,
)


def get_test_image_path() -> Path:
    """Get path to a test image."""
    test_img_dir = Path(__file__).parent / "img"
    test_image = test_img_dir / "0001.png"
    if not test_image.exists():
        pytest.skip(f"Test image not found: {test_image}")
    return test_image


def image_to_base64_url(image_path: Path) -> str:
    """Convert an image file to base64 data URL."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    b64_data = base64.b64encode(image_data).decode("utf-8")
    # Detect format from extension
    ext = image_path.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    return f"data:image/{ext};base64,{b64_data}"


@pytest.mark.asyncio
async def test_text2image_with_reference_url():
    """Test text2image pipeline with a reference image URL."""
    # Use a public test image URL
    reference_url = "https://picsum.photos/512/512"

    request = Text2ImagePipelineRequest(
        prompt="一只可爱的猫咪，梵高风格",
        providers=["doubao_seedream"],  # Seedream supports reference images
        num_candidates=1,
        reference_images=[reference_url],
    )

    result = await run_text2image_pipeline(request)

    assert result["status"] == "success"
    assert "task_id" in result
    assert "best_image_url" in result
    assert len(result["candidates"]) >= 1
    # Provider should have received the request (even if API key is missing)
    assert "doubao_seedream" in result["providers_used"]


@pytest.mark.asyncio
async def test_text2image_with_reference_base64():
    """Test text2image pipeline with a base64 reference image."""
    test_image = get_test_image_path()
    base64_url = image_to_base64_url(test_image)

    request = Text2ImagePipelineRequest(
        prompt="相同风格的图片，但改为夏天场景",
        providers=["doubao_seedream"],
        num_candidates=1,
        reference_images=[base64_url],
    )

    result = await run_text2image_pipeline(request)

    assert result["status"] == "success"
    assert "best_image_url" in result


@pytest.mark.asyncio
async def test_text2image_with_multiple_references():
    """Test text2image pipeline with multiple reference images."""
    test_image = get_test_image_path()
    base64_url = image_to_base64_url(test_image)

    # Use the same image twice for testing (in real use, would be different images)
    request = Text2ImagePipelineRequest(
        prompt="融合两张图片的风格元素",
        providers=["doubao_seedream"],
        num_candidates=1,
        reference_images=[base64_url, base64_url],
    )

    result = await run_text2image_pipeline(request)

    assert result["status"] == "success"
    assert len(result["providers_used"]) > 0


@pytest.mark.asyncio
async def test_text2image_without_reference():
    """Test that text2image still works without reference images (backward compatibility)."""
    request = Text2ImagePipelineRequest(
        prompt="一只猫骑着自行车",
        providers=["doubao_seedream"],
        num_candidates=1,
        # No reference_images provided
    )

    result = await run_text2image_pipeline(request)

    assert result["status"] == "success"
    assert "best_image_url" in result


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.getenv("DASHSCOPE_API_KEY") and not os.getenv("QWEN_API_KEY"),
    reason="Qwen API key not configured",
)
async def test_text2image_qwen_with_reference():
    """Test Qwen provider with reference image (requires API key)."""
    test_image = get_test_image_path()
    base64_url = image_to_base64_url(test_image)

    request = Text2ImagePipelineRequest(
        prompt="类似的图片，但改为冬天场景",
        providers=["qwen"],
        num_candidates=1,
        reference_images=[base64_url],
    )

    result = await run_text2image_pipeline(request)

    assert result["status"] == "success"
    # Should automatically switch to wan2.5-i2i-preview model
    assert "qwen" in result["providers_used"]


@pytest.mark.asyncio
async def test_text2image_reference_validation():
    """Test that reference_images validates max length."""
    # Try to add 11 images (max is 10)
    too_many_refs = ["https://picsum.photos/512/512"] * 11

    with pytest.raises(ValueError, match="max_length"):
        Text2ImagePipelineRequest(
            prompt="测试",
            providers=["doubao_seedream"],
            num_candidates=1,
            reference_images=too_many_refs,
        )


@pytest.mark.asyncio
async def test_text2image_mixed_providers():
    """Test using both reference-supporting and non-supporting providers."""
    test_image = get_test_image_path()
    base64_url = image_to_base64_url(test_image)

    request = Text2ImagePipelineRequest(
        prompt="一只猫咪",
        providers=["doubao_seedream", "pollinations"],  # pollinations doesn't support ref images
        num_candidates=1,
        reference_images=[base64_url],
    )

    result = await run_text2image_pipeline(request)

    # At least one provider should succeed
    assert result["status"] == "success"
    assert len(result["providers_used"]) > 0


if __name__ == "__main__":
    import asyncio

    # Run a simple test
    async def main():
        print("Testing text2image with reference image...")
        request = Text2ImagePipelineRequest(
            prompt="一只可爱的猫咪",
            providers=["doubao_seedream"],
            num_candidates=1,
            reference_images=["https://picsum.photos/512/512"],
        )
        result = await run_text2image_pipeline(request)
        print(f"Result: {result['status']}")
        print(f"Providers used: {result['providers_used']}")
        print(f"Best image: {result['best_image_url'][:80]}...")

    asyncio.run(main())
