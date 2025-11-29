#!/usr/bin/env python3
"""Test script for OpenRouter-based image generation providers."""

import asyncio
import os
from uuid import uuid4

from services.generate.adapters.dalle import DalleProvider
from services.generate.adapters.nano_banana import NanoBananaProvider
from services.generate.models import GenerateRequestPayload


async def test_provider(provider_class, prompt: str):
    """Test a single provider with a given prompt."""
    provider = provider_class()
    print(f"\n{'='*60}")
    print(f"Testing: {provider.name}")
    print(f"Model: {provider.model_name}")
    print(f"Prompt: {prompt}")
    print(f"{'='*60}")

    request = GenerateRequestPayload(
        task="text2image",
        task_id=uuid4(),
        prompt=prompt,
        provider=provider.name,
        size="1024x1024",
        params={}
    )

    try:
        result = await provider.generate(request)
        print(f"✓ Status: {result['status']}")
        print(f"✓ Task ID: {result['task_id']}")
        print(f"✓ Images generated: {len(result['images'])}")
        print(f"✓ Provider metadata: {result['metadata']['provider']}")
        print(f"✓ Model used: {result['metadata']['model']}")

        # Print first 100 chars of image URL/data
        if result['images']:
            image_preview = result['images'][0][:100]
            print(f"✓ Image data preview: {image_preview}...")

        return True
    except Exception as e:
        print(f"✗ Error: {type(e).__name__}: {e}")
        return False


async def main():
    """Run tests for all OpenRouter providers."""
    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY environment variable not set!")
        print("Please set it before running this test.")
        return

    print("OpenRouter Providers Test Suite")
    print(f"API Key configured: {api_key[:8]}...{api_key[-4:]}")

    test_prompt = "A serene Japanese garden with cherry blossoms and a koi pond"

    # Test DALL-E (GPT-5 Image)
    dalle_success = await test_provider(DalleProvider, test_prompt)

    # Test Nano Banana (Gemini 3 Pro Image)
    nano_success = await test_provider(NanoBananaProvider, test_prompt)

    # Summary
    print(f"\n{'='*60}")
    print("Test Summary:")
    print(f"  DALL-E (openai/gpt-5-image): {'✓ PASS' if dalle_success else '✗ FAIL'}")
    print(f"  Nano Banana (gemini-3-pro-image): {'✓ PASS' if nano_success else '✗ FAIL'}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())
