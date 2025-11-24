import pytest
from httpx import AsyncClient, ASGITransport

from gateway.main import app


@pytest.mark.asyncio
async def test_image2image_pipeline_returns_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/v1/pipeline/image2image",
            json={
                "prompt": "为产品生成驻足的电商展示图",
                "reference_images": [
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
                ],
                "providers": ["doubao_seedream"],
                "size": "1024x1024",
                "params": {
                    "num_variations": 1,
                    "image_size": "1024x1024",
                },
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "results" in data and len(data["results"]) >= 1
