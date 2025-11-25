import pytest
from httpx import AsyncClient, ASGITransport

from gateway.main import app


@pytest.mark.asyncio
async def test_text2image_pipeline_returns_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/pipeline/text2image",
            json={
                "prompt": "清晨薄雾中的城市天际线",
                "providers": ["doubao_seedream"],
                "num_candidates": 2,
                "params": {
                    "ratio": "1:1",
                    "expand_prompt": False,
                },
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["best_image_url"]
    assert "candidates" in data and len(data["candidates"]) >= 1
