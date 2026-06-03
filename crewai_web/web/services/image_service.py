"""图片上传服务

处理图片文件保存 + 自动 OCR 识别。
"""

import shutil
from pathlib import Path

from crewai_web.web.config import UPLOAD_IMAGES_DIR
from crewai_web.web.services.ocr_service import recognize_image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tiff", ".tif"}


def upload_image(filename: str, file_obj) -> dict:
    """保存图片文件，自动调用 OCR。

    Args:
        filename: 原始文件名
        file_obj: 文件对象（支持 shutil.copyfileobj）

    Returns:
        {filename, path, size, ocr_text, ocr_success}
    """
    UPLOAD_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPLOAD_IMAGES_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file_obj, f)

    suffix = Path(filename or "").suffix.lower()
    ocr_text = ""
    ocr_success = False
    if suffix in IMAGE_EXTENSIONS:
        ocr_text = recognize_image(str(dest))
        ocr_success = bool(ocr_text.strip())

    return {
        "filename": filename,
        "path": str(dest),
        "size": dest.stat().st_size,
        "ocr_text": ocr_text,
        "ocr_success": ocr_success,
    }
