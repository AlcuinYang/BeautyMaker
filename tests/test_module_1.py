import sys
import os

# --- 关键修复: 自动将项目根目录加入路径 ---
# 获取当前脚本所在目录的上一级目录 (即项目根目录)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# -------------------------------------

try:
    from services.pipeline.image2image import Image2ImagePipelineParams, ProductCategory
    from services.tools.segmentation import SegmentationService
    print("✅ 成功导入新模块")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    # 打印当前的 sys.path 方便调试
    print(f"当前搜索路径: {sys.path}")
    exit(1)

def test_data_models():
    print("\n--- 测试数据模型 ---")
    try:
        # 测试默认值
        params = Image2ImagePipelineParams()
        assert params.category == "other", f"默认品类错误: {params.category}"
        assert params.use_auto_segmentation is True, "默认去底开关错误"
        print("1. 默认参数: 通过")

        # 测试枚举赋值
        params_standing = Image2ImagePipelineParams(category=ProductCategory.STANDING)
        assert params_standing.category == ProductCategory.STANDING
        print("2. 枚举赋值: 通过")
        print("✅ 数据模型验证成功")
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")

def test_segmentation_service():
    print("\n--- 测试图像处理服务 ---")
    service = SegmentationService()
    
    # 模拟一个 1x1 像素的红色 PNG Base64
    dummy_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    
    try:
        # 测试 1: 格式清洗 (PNG 应该原样返回)
        cleaned = service.ensure_png_format(dummy_png)
        assert cleaned.startswith("data:image/png;base64,"), "格式头丢失"
        print("1. 格式标准化 (PNG): 通过")

        # 测试 2: 去底功能 (检查返回类型是否为 bytes)
        # 注意：如果你安装了 rembg，这里会真跑；没安装会跑 mock 逻辑
        result_bytes = service.remove_background(dummy_png)
        assert isinstance(result_bytes, bytes), f"去底返回类型错误: {type(result_bytes)}"
        print("2. 去底服务调用: 通过")
        print("✅ 图像服务验证成功")
        
    except Exception as e:
        print(f"❌ 图像服务测试失败: {e}")

if __name__ == "__main__":
    test_data_models()
    test_segmentation_service()