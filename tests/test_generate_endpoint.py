import pytest
from httpx import AsyncClient, ASGITransport

from gateway.main import app


@pytest.mark.asyncio
async def test_generate_endpoint_returns_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/aesthetic",
            json={
                "task": "text2image",
                "prompt": "一只猫骑着自行车",
                "provider": "pollinations",
                "size": "512x512",
                "use_modules": [
                    "holistic",
                    "color_score",
                    "contrast_score",
                    "clarity_eval",
                ],
                "params": {},
                "enhancement": {
                    "apply_clarity": True,
                },
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "image_url" in data
    assert data["best_candidate"] == data["image_url"]
    assert set(data["modules_used"]) == {
        "holistic",
        "color_score",
        "contrast_score",
        "clarity_eval",
    }
    assert "scores" in data and data["scores"]
    assert data["composite_score"] is not None
