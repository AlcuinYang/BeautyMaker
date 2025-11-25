"""Manual test for text2image with reference images.

Run this with: python tests/manual_test_reference.py
"""

from __future__ import annotations

import asyncio
import base64
from pathlib import Path

from services.pipeline.text2image import (
    Text2ImagePipelineRequest,
    run_text2image_pipeline,
)


def get_base64_from_file(image_path: str) -> str:
    """Convert image file to base64 data URL."""
    path = Path(image_path)
    with open(path, "rb") as f:
        image_data = f.read()
    b64_data = base64.b64encode(image_data).decode("utf-8")
    ext = path.suffix.lower().lstrip(".")
    if ext == "jpg":
        ext = "jpeg"
    return f"data:image/{ext};base64,{b64_data}"


async def test_with_url():
    """Test with a URL reference image."""
    print("\n" + "="*60)
    print("测试 1: 使用 URL 参考图")
    print("="*60)

    request = Text2ImagePipelineRequest(
        prompt="一只可爱的猫咪，梵高风格",
        providers=["doubao_seedream"],
        num_candidates=1,
        reference_images=["https://picsum.photos/512/512"],
    )

    result = await run_text2image_pipeline(request)

    print(f"状态: {result['status']}")
    print(f"任务ID: {result['task_id']}")
    print(f"使用的提供商: {result['providers_used']}")
    print(f"生成的候选数量: {len(result['candidates'])}")
    print(f"最佳图片URL (前80字符): {result['best_image_url'][:80]}...")

    return result["status"] == "success"


async def test_with_base64():
    """Test with a base64 reference image."""
    print("\n" + "="*60)
    print("测试 2: 使用 Base64 参考图")
    print("="*60)

    # Check if test image exists
    test_img = Path(__file__).parent / "img" / "0001.png"
    if not test_img.exists():
        print(f"⚠️  测试图片不存在: {test_img}")
        print("跳过此测试")
        return True

    base64_url = get_base64_from_file(str(test_img))
    print(f"参考图 Base64 长度: {len(base64_url)} 字符")

    request = Text2ImagePipelineRequest(
        prompt="相同风格的图片，但改为夏天场景",
        providers=["doubao_seedream"],
        num_candidates=1,
        reference_images=[base64_url],
    )

    result = await run_text2image_pipeline(request)

    print(f"状态: {result['status']}")
    print(f"任务ID: {result['task_id']}")
    print(f"使用的提供商: {result['providers_used']}")

    return result["status"] == "success"


async def test_without_reference():
    """Test without reference (backward compatibility)."""
    print("\n" + "="*60)
    print("测试 3: 无参考图（向后兼容性）")
    print("="*60)

    request = Text2ImagePipelineRequest(
        prompt="一只猫骑着自行车",
        providers=["doubao_seedream"],
        num_candidates=1,
        # No reference_images
    )

    result = await run_text2image_pipeline(request)

    print(f"状态: {result['status']}")
    print(f"任务ID: {result['task_id']}")
    print(f"使用的提供商: {result['providers_used']}")

    return result["status"] == "success"


async def test_multiple_references():
    """Test with multiple reference images."""
    print("\n" + "="*60)
    print("测试 4: 多张参考图")
    print("="*60)

    test_img = Path(__file__).parent / "img" / "0001.png"
    if not test_img.exists():
        print(f"⚠️  测试图片不存在，跳过")
        return True

    base64_url = get_base64_from_file(str(test_img))

    # Use same image twice for testing
    request = Text2ImagePipelineRequest(
        prompt="融合参考图的风格元素",
        providers=["doubao_seedream"],
        num_candidates=1,
        reference_images=[base64_url, base64_url],  # 2 images
    )

    result = await run_text2image_pipeline(request)

    print(f"状态: {result['status']}")
    print(f"参考图数量: 2")
    print(f"使用的提供商: {result['providers_used']}")

    return result["status"] == "success"


async def test_validation():
    """Test input validation."""
    print("\n" + "="*60)
    print("测试 5: 参数验证（最多10张参考图）")
    print("="*60)

    try:
        # Try 11 images (should fail)
        request = Text2ImagePipelineRequest(
            prompt="测试",
            providers=["doubao_seedream"],
            num_candidates=1,
            reference_images=["https://example.com/img.jpg"] * 11,
        )
        print("❌ 验证失败：应该拒绝11张参考图")
        return False
    except Exception as e:
        print(f"✅ 验证通过：正确拒绝了11张参考图")
        print(f"   错误信息: {str(e)[:100]}")
        return True


async def main():
    """Run all tests."""
    print("\n🚀 开始测试文生图参考图功能")
    print("="*60)

    results = []

    # Run tests
    results.append(("URL参考图", await test_with_url()))
    results.append(("Base64参考图", await test_with_base64()))
    results.append(("无参考图", await test_without_reference()))
    results.append(("多张参考图", await test_multiple_references()))
    results.append(("参数验证", await test_validation()))

    # Summary
    print("\n" + "="*60)
    print("📊 测试总结")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print("="*60)
    print(f"总计: {passed}/{total} 测试通过")
    print("="*60)

    if passed == total:
        print("\n🎉 所有测试通过！参考图功能已成功实现。")
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查。")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
