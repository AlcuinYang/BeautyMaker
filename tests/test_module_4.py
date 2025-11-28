import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# --- 关键修复: 自动将项目根目录加入路径 ---
# 获取当前脚本所在目录的上一级目录 (即项目根目录)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# -------------------------------------

try:
    from services.reviewer.service import AestheticReviewer
    from services.common.models import GeneratedImage, ComparativeReview
    from services.scoring.aggregator import ImageEvaluation
    print("✅ 成功导入服务模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    print(f"尝试搜索的路径: {sys.path}")
    exit(1)

# ==========================================
# Fixtures (测试数据准备)
# ==========================================

@pytest.fixture
def mock_doubao_client():
    """模拟豆包客户端，避免真实网络请求"""
    client = MagicMock()
    # 设置异步方法的返回值
    client.compare_images = AsyncMock()
    return client

@pytest.fixture
def sample_data():
    """准备测试用的候选图和评分数据"""
    img_a = GeneratedImage(
        url="http://example.com/winner.png",
        provider="doubao",
        prompt="test prompt"
    )
    img_b = GeneratedImage(
        url="http://example.com/loser.png",
        provider="qwen",
        prompt="test prompt"
    )
    
    # 模拟评分：A 是 0.9 分，B 是 0.5 分
    evaluations = {
        img_a.url: ImageEvaluation(
            composite_score=0.9,
            module_scores={
                "clarity_eval": 0.9,
                "quality_score": 0.8,
                "contrast_score": 0.9,
                "noise_eval": 0.9
            }
        ),
        img_b.url: ImageEvaluation(
            composite_score=0.5,
            module_scores={
                "clarity_eval": 0.4,
                "quality_score": 0.5,
                "contrast_score": 0.5,
                "noise_eval": 0.5
            }
        )
    }
    
    return [img_a, img_b], evaluations

# ==========================================
# Test Cases (测试用例)
# ==========================================

@pytest.mark.asyncio
async def test_review_candidates_success(mock_doubao_client, sample_data):
    """测试正常流程：成功生成对比点评"""
    candidates, evaluations = sample_data
    
    # 1. 设置 Mock 的预期返回值
    mock_return_value = {
        "title": "结构更完整",
        "analysis": "图A的手指结构正常，图B扭曲。",
        "key_difference": "结构合理性"
    }
    mock_doubao_client.compare_images.return_value = mock_return_value

    # 2. 初始化服务
    reviewer = AestheticReviewer(client=mock_doubao_client)

    # 3. 执行测试
    result = await reviewer.review_candidates(candidates, evaluations)

    # 4. 验证结果类型
    assert result is not None
    assert isinstance(result, ComparativeReview)
    assert result.title == "结构更完整"
    assert result.key_difference == "结构合理性"

    # 5. 验证是否调用了 API
    mock_doubao_client.compare_images.assert_called_once()
    
    # 6. 验证参数是否正确
    call_args = mock_doubao_client.compare_images.call_args
    kwargs = call_args.kwargs
    
    # 验证图片顺序：应该是 [优胜图, 参照图] -> [0.9分图, 0.5分图]
    assert kwargs['image_urls'] == ["http://example.com/winner.png", "http://example.com/loser.png"]
    
    # 验证 Prompt 是否包含 AIGC 质检关键词
    prompt_text = kwargs['prompt']
    assert "AIGC 质量质检专家" in prompt_text
    assert "结构合理性" in prompt_text
    # 修正：代码会将 0-1 分数 * 10 显示
    assert "9.0/10" in prompt_text  # 优胜图分数 (0.9 * 10)
    # 如果你也想验证参照图分数
    # assert "5.0/10" in prompt_text # 参照图分数 (0.5 * 10)

@pytest.mark.asyncio
async def test_not_enough_candidates(mock_doubao_client, sample_data):
    """测试边界条件：只有一张图时不生成点评"""
    candidates, evaluations = sample_data
    single_candidate = [candidates[0]] # 只取一张
    
    reviewer = AestheticReviewer(client=mock_doubao_client)
    result = await reviewer.review_candidates(single_candidate, evaluations)
    
    assert result is None
    mock_doubao_client.compare_images.assert_not_called()

@pytest.mark.asyncio
async def test_api_failure_graceful_degradation(mock_doubao_client, sample_data):
    """测试异常处理：API 挂了系统不能崩"""
    candidates, evaluations = sample_data
    
    # 模拟 API 抛出异常
    mock_doubao_client.compare_images.side_effect = Exception("API Timeout")
    
    reviewer = AestheticReviewer(client=mock_doubao_client)
    
    # 应该返回 None 而不是抛出异常
    result = await reviewer.review_candidates(candidates, evaluations)
    
    assert result is None

@pytest.mark.asyncio
async def test_missing_evaluations(mock_doubao_client, sample_data):
    """测试数据缺失：有图但没分"""
    candidates, _ = sample_data
    empty_evaluations = {} # 空字典
    
    reviewer = AestheticReviewer(client=mock_doubao_client)
    result = await reviewer.review_candidates(candidates, empty_evaluations)
    
    assert result is None

# 为了方便直接 python test_module_4.py 运行（非 pytest 模式）
if __name__ == "__main__":
    print("⚠️ 请使用 'pytest test_module_4.py' 命令来运行此测试，因为它包含异步函数。")