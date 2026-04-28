from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from crewai_web.web.services import file_service
from crewai_web.web.services.document_service import get_document_service

router = APIRouter(prefix="/files", tags=["files"])


class BrowseRequest(BaseModel):
    path: str


class BrowseResponse(BaseModel):
    current: str
    parent: Optional[str]
    directories: List[dict]
    files: List[dict]


class RootsResponse(BaseModel):
    roots: List[dict]


@router.post("/browse", response_model=BrowseResponse)
def browse_directory(request: BrowseRequest):
    """浏览指定目录内容"""
    try:
        return file_service.browse_directory(request.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/roots", response_model=RootsResponse)
def get_browse_roots():
    """获取默认可浏览的根目录列表"""
    return {"roots": file_service.get_default_browse_roots()}


@router.post("/upload-doc")
async def upload_document(file: UploadFile = File(...)):
    """上传文档文件"""
    return await get_document_service().upload_document(file)


@router.get("/list-docs")
def list_documents():
    """列出已上传的文档文件"""
    return {"files": get_document_service().list_documents()}


@router.get("/read-doc")
def read_document(filename: str):
    """读取已上传文档内容"""
    result = get_document_service().read_document(filename)
    if not result:
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    return result


@router.get("/download-output")
def download_output(filename: str):
    """下载生成的输出文件"""
    path = get_document_service().download_output_path(filename)
    if not path:
        raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
    return FileResponse(path=str(path), filename=filename)


@router.get("/list-outputs")
def list_outputs():
    """列出所有生成的输出文件"""
    return {"files": get_document_service().list_outputs()}
