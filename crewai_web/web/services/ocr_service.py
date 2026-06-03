"""阿里云 OCR 服务

调用阿里云 OCR API 识别图片中的文字。
使用 alibabacloud_ocr_api20210707 SDK，避免手写签名。
配置从环境变量读取（参见 .env 中的 ALIYUN_OCR_* 变量）。
"""

import io
import logging
from pathlib import Path

from crewai_web.web.config import ALIYUN_OCR_ACCESS_KEY_ID, ALIYUN_OCR_ACCESS_KEY_SECRET, ALIYUN_OCR_ENDPOINT

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    global _client
    if _client is None:
        from alibabacloud_ocr_api20210707.client import Client
        from alibabacloud_tea_openapi import models as open_api_models

        config = open_api_models.Config(
            access_key_id=ALIYUN_OCR_ACCESS_KEY_ID,
            access_key_secret=ALIYUN_OCR_ACCESS_KEY_SECRET,
            endpoint=ALIYUN_OCR_ENDPOINT,
        )
        _client = Client(config)
    return _client


def recognize_image(image_path: str) -> str:
    """识别图片中的文字，返回纯文本内容。

    Args:
        image_path: 本地图片绝对路径

    Returns:
        识别出的文字内容，失败时返回空字符串
    """
    if not ALIYUN_OCR_ACCESS_KEY_ID or not ALIYUN_OCR_ACCESS_KEY_SECRET:
        logger.warning("[OCR] 未配置阿里云 OCR 凭证")
        return ""

    path = Path(image_path)
    if not path.exists():
        logger.error(f"[OCR] 图片文件不存在: {image_path}")
        return ""

    try:
        with open(path, "rb") as f:
            img_bytes = f.read()
    except Exception as e:
        logger.error(f"[OCR] 读取图片失败 {image_path}: {e}")
        return ""

    try:
        from alibabacloud_ocr_api20210707 import models as ocr_models

        client = _get_client()
        req = ocr_models.RecognizeAllTextRequest(
            body=io.BytesIO(img_bytes),
            type="Advanced",
        )
        resp = client.recognize_all_text(req)
        body = resp.body

        if body.data and body.data.content:
            text = body.data.content
            logger.info(f"[OCR] 识别成功，长度={len(text)}")
            return text
        else:
            logger.warning(f"[OCR] 无内容: code={body.code}, message={body.message}")
            return ""

    except Exception as e:
        logger.error(f"[OCR] 调用失败: {e}")
        return ""


def recognize_images(image_paths: list[str]) -> dict[str, str]:
    """批量识别多张图片。

    Returns:
        {image_path: extracted_text} 字典
    """
    results = {}
    for p in image_paths:
        results[p] = recognize_image(p)
    return results
