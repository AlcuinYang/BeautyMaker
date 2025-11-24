from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class EnhancementOptions(BaseModel):
    """增强选项，仅在需要时控制图片优化行为。"""

    apply_clarity: bool = Field(default=False, description="是否启用清晰术增强")


class GenerateRequest(BaseModel):
    """统一入口请求体，描述一次生成与美学评估任务。"""

    task: str = Field(pattern="^(text2image|image2image)$", description="任务类型")
    prompt: str = Field(description="生成提示词")
    provider: str = Field(description="外部生成服务提供商")
    size: str = Field(default="512x512", description="生成图像尺寸")
    use_modules: List[str] = Field(default_factory=list, description="需要启用的评估模块列表")
    params: Dict[str, Any] = Field(default_factory=dict, description="生成或模型参数")
    enhancement: EnhancementOptions = Field(
        default_factory=EnhancementOptions, description="增强配置"
    )


class GenerateResponse(BaseModel):
    """统一出口响应体，返回最佳图片与美学结果。"""

    status: str = Field(description="执行状态")
    task_id: UUID = Field(default_factory=uuid4, description="任务标识")
    image_url: str = Field(description="首选输出图像")
    modules_used: List[str] = Field(default_factory=list, description="实际启用的模块")
    scores: Dict[str, float] = Field(default_factory=dict, description="各模块得分")
    composite_score: Optional[float] = Field(
        default=None, description="美感评分（0-1）"
    )
    best_candidate: Optional[str] = Field(
        default=None, description="最佳候选图像地址"
    )
    detail: Optional[str] = Field(default=None, description="失败时的详细描述")
