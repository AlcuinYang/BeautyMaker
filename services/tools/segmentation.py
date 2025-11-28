"""图像分割和背景移除服务

此服务提供：
1. 图像格式转换（确保PNG格式）
2. 背景移除功能（基于RMBG）
"""

import base64
import io
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("Pillow not installed. Image format conversion will be limited.")

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    logger.warning("rembg not installed. Background removal will use pass-through mode.")


class SegmentationService:
    """图像分割服务类"""

    def __init__(self):
        """初始化分割服务"""
        if not PIL_AVAILABLE:
            logger.error("Pillow is required for SegmentationService")

    def ensure_png_format(self, image_data: str) -> str:
        """确保图像为PNG格式

        Args:
            image_data: Base64 data URI (例如: "data:image/jpeg;base64,...")

        Returns:
            PNG格式的base64 data URI

        Raises:
            ValueError: 如果输入格式无效
            RuntimeError: 如果Pillow未安装
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow is required for format conversion")

        # 解析data URI
        match = re.match(r'data:image/(\w+);base64,(.+)', image_data)
        if not match:
            raise ValueError("Invalid data URI format. Expected 'data:image/{type};base64,{data}'")

        image_type, base64_data = match.groups()

        # 如果已经是PNG，直接返回
        if image_type.lower() == 'png':
            return image_data

        # 如果是WebP或其他格式，转换为PNG
        try:
            # 解码base64
            image_bytes = base64.b64decode(base64_data)

            # 用PIL打开图像
            image = Image.open(io.BytesIO(image_bytes))

            # 转换为PNG
            png_buffer = io.BytesIO()
            image.save(png_buffer, format='PNG')
            png_buffer.seek(0)

            # 编码为base64
            png_base64 = base64.b64encode(png_buffer.getvalue()).decode('utf-8')

            logger.info(f"Converted image from {image_type} to PNG")
            return f"data:image/png;base64,{png_base64}"

        except Exception as e:
            logger.error(f"Failed to convert image to PNG: {e}")
            raise ValueError(f"Image conversion failed: {e}") from e

    def remove_background(self, image_data: str) -> bytes:
        """移除图像背景

        Args:
            image_data: Base64 data URI或URL

        Returns:
            移除背景后的PNG图像原始字节

        Raises:
            ValueError: 如果输入格式无效
            RuntimeError: 如果必要的库未安装
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow is required for background removal")

        # 解析并解码图像数据
        try:
            # 如果是data URI，提取base64部分
            if image_data.startswith('data:'):
                match = re.match(r'data:image/\w+;base64,(.+)', image_data)
                if not match:
                    raise ValueError("Invalid data URI format")
                base64_data = match.group(1)
                image_bytes = base64.b64decode(base64_data)
            else:
                # 假设是纯base64字符串
                image_bytes = base64.b64decode(image_data)

            # 打开图像
            input_image = Image.open(io.BytesIO(image_bytes))

        except Exception as e:
            logger.error(f"Failed to decode image data: {e}")
            raise ValueError(f"Image decoding failed: {e}") from e

        # 使用rembg移除背景（如果可用）
        if REMBG_AVAILABLE:
            try:
                logger.info("Removing background using rembg")

                # 将PIL图像转换为字节
                img_buffer = io.BytesIO()
                input_image.save(img_buffer, format='PNG')
                img_buffer.seek(0)

                # 使用rembg移除背景
                output_bytes = remove(img_buffer.read())

                logger.info("Background removed successfully")
                return output_bytes

            except Exception as e:
                logger.error(f"rembg background removal failed: {e}")
                # 降级：返回原始图像
                logger.warning("Falling back to pass-through mode")
        else:
            logger.warning("rembg not available, using pass-through mode")

        # 降级模式：直接返回原始PNG字节
        output_buffer = io.BytesIO()
        input_image.save(output_buffer, format='PNG')
        output_buffer.seek(0)

        return output_buffer.getvalue()

    def remove_background_from_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """从文件移除背景（便捷方法）

        Args:
            file_path: 输入图像文件路径
            output_path: 输出文件路径（可选，默认为输入路径加_nobg后缀）

        Returns:
            输出文件路径

        Raises:
            RuntimeError: 如果必要的库未安装
        """
        if not PIL_AVAILABLE:
            raise RuntimeError("Pillow is required for background removal")

        # 读取输入文件
        with open(file_path, 'rb') as f:
            image_bytes = f.read()

        # 转换为base64 data URI
        base64_data = base64.b64encode(image_bytes).decode('utf-8')

        # 检测图像类型
        image = Image.open(io.BytesIO(image_bytes))
        image_format = image.format.lower() if image.format else 'png'

        data_uri = f"data:image/{image_format};base64,{base64_data}"

        # 移除背景
        output_bytes = self.remove_background(data_uri)

        # 确定输出路径
        if output_path is None:
            from pathlib import Path
            p = Path(file_path)
            output_path = str(p.parent / f"{p.stem}_nobg.png")

        # 写入输出文件
        with open(output_path, 'wb') as f:
            f.write(output_bytes)

        logger.info(f"Saved background-removed image to {output_path}")
        return output_path
