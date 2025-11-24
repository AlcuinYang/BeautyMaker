from __future__ import annotations

import logging
from fastapi import Depends, FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from gateway.orchestrator import ServiceOrchestrator
from gateway.schemas import GenerateRequest, GenerateResponse
from gateway.data import APPLICATIONS, APP_TEMPLATES, USER_PROFILES, WORKS, GALLERY_ITEMS
from services.enhancer.service import EnhancementService
from services.generate.service import GenerationService
from services.generate.routes import providers as provider_routes
from services.scoring.aggregator import ScoringAggregator
from services.selector.service import SelectorService
from services.pipeline import (
    Text2ImagePipelineRequest,
    run_text2image_pipeline,
    Image2ImagePipelineRequest,
    run_image2image_pipeline,
)
from services.proxy.proxy_base import router as proxy_router
import os


print("DASHSCOPE_API_KEY (start):", os.getenv("DASHSCOPE_API_KEY"))


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aesthetics Engine",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(provider_routes.router)
app.include_router(proxy_router)


def get_orchestrator() -> ServiceOrchestrator:
    """构建服务编排器，按需注入各子服务。"""
    generation_service = GenerationService()
    scoring_aggregator = ScoringAggregator()
    enhancer = EnhancementService()
    selector = SelectorService()
    return ServiceOrchestrator(
        generation_service=generation_service,
        scoring_aggregator=scoring_aggregator,
        enhancer=enhancer,
        selector=selector,
    )


@app.post("/v1/aesthetic", response_model=GenerateResponse)
async def generate_endpoint(
    payload: GenerateRequest,
    orchestrator: ServiceOrchestrator = Depends(get_orchestrator),
) -> GenerateResponse:
    try:
        return await orchestrator.handle_generate(payload)
    except Exception as exc:  # noqa: BLE001 - top-level guard for API stability
        logger.exception("Failed to handle generate request: %s", exc)
        raise HTTPException(status_code=500, detail="generation_failed") from exc


@app.post("/v1/pipeline/text2image")
async def text2image_pipeline_endpoint(
    payload: Text2ImagePipelineRequest,
) -> dict:
    """曝光免费可用的 Pollinations 管线，便于前端快速串联。"""
    try:
        result = await run_text2image_pipeline(payload)
        if result.get("status") != "success":
            raise HTTPException(status_code=502, detail=result.get("message", "pipeline_failed"))
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - api guard
        logger.exception("Text2Image pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail="pipeline_error") from exc


@app.post("/v1/pipeline/image2image")
async def image2image_pipeline_endpoint(
    payload: Image2ImagePipelineRequest,
) -> dict:
    """图生图“一拍即合”管线入口。"""
    try:
        result = await run_image2image_pipeline(payload)
        if result.get("status") != "success":
            raise HTTPException(status_code=502, detail=result.get("message", "pipeline_failed"))
        return result
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("Image2Image pipeline failed: %s", exc)
        raise HTTPException(status_code=500, detail="pipeline_error") from exc


@app.get("/api/apps")
async def list_apps() -> list[dict]:
    """返回所有可用的应用卡片信息。"""
    return APPLICATIONS


@app.get("/api/apps/{app_id}")
async def get_app_detail(app_id: str = Path(..., description="应用标识")) -> dict:
    """获取指定应用的参数模板和元信息。"""
    if app_id not in APP_TEMPLATES:
        raise HTTPException(status_code=404, detail="app_not_found")

    metadata = next((item for item in APPLICATIONS if item["id"] == app_id), None)
    payload = APP_TEMPLATES[app_id]
    return {
        "meta": metadata,
        "template": payload,
    }


@app.get("/api/works")
async def list_works() -> list[dict]:
    """获取作品市场的最新内容。"""
    return WORKS


@app.get("/api/mock/gallery")
async def list_mock_gallery(page: int = 1, page_size: int = 9) -> dict:
    """返回演示用的美学作品图库，支持简单分页。"""
    if page < 1:
        page = 1
    page_size = max(3, min(page_size, 18))
    start = (page - 1) * page_size
    end = start + page_size
    total = len(GALLERY_ITEMS)
    if total == 0:
        items = []
        has_more = False
    else:
        # 循环复用静态数据以模拟无限滚动
        items = [
            {
                **GALLERY_ITEMS[idx % total],
                "id": f"{GALLERY_ITEMS[idx % total]['id']}-p{page}-i{idx}",
            }
            for idx in range(start, end)
        ]
        has_more = True
    return {
        "page": page,
        "page_size": page_size,
        "has_more": has_more,
        "items": items,
        "total": total,
    }


@app.get("/api/user/{user_id}")
async def get_user_profile(user_id: str) -> dict:
    """返回用户资料及额度信息。"""
    profile = USER_PROFILES.get(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="user_not_found")
    return profile


@app.post("/v1/publish")
async def publish_work(payload: dict) -> JSONResponse:
    """发布作品的占位接口，当前仅回显。"""
    logger.info("Receive publish payload", extra={"payload": payload})
    return JSONResponse({"status": "accepted", "payload": payload})
