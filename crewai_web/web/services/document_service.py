"""
文档管理服务
职责：文档上传、列表、读取、输出文件管理
"""
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile

from crewai_web.web.config import UPLOAD_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)


class DocumentService:

    def __init__(self):
        self.docs_dir = UPLOAD_DIR
        self.output_dir = OUTPUT_DIR

    async def upload_document(self, file: UploadFile) -> dict:
        """上传文档文件"""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        dest = self.docs_dir / file.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Uploaded document: {file.filename} ({dest.stat().st_size} bytes)")
        return {"path": str(dest), "filename": file.filename, "size": dest.stat().st_size}

    def list_documents(self) -> List[dict]:
        """列出已上传的文档"""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        return [
            {"name": f.name, "path": str(f), "size": f.stat().st_size}
            for f in self.docs_dir.iterdir() if f.is_file()
        ]

    def read_document(self, filename: str) -> Optional[dict]:
        """读取文档内容，返回 None 表示不存在"""
        path = self.docs_dir / filename
        if not path.exists():
            return None
        content = path.read_text(encoding="utf-8")
        return {"filename": filename, "content": content, "length": len(content)}

    def download_output_path(self, filename: str) -> Optional[Path]:
        """获取输出文件路径，返回 None 表示不存在"""
        path = self.output_dir / filename
        if not path.exists():
            return None
        return path

    def list_outputs(self) -> List[dict]:
        """列出所有输出文件"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return [
            {"name": f.name, "path": str(f), "size": f.stat().st_size}
            for f in self.output_dir.rglob("*") if f.is_file()
        ]


_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
