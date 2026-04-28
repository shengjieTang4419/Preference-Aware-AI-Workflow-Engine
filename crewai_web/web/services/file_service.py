import os
from pathlib import Path
from typing import List, Dict
from crewai_web.web.config import ALLOWED_BROWSE_ROOTS, STORAGE_DIR


def is_safe_path(path: Path) -> bool:
    """检查路径是否在允许的浏览范围内"""
    try:
        resolved = path.resolve()
        for root in ALLOWED_BROWSE_ROOTS:
            try:
                if resolved.is_relative_to(root.resolve()):
                    return True
            except:
                # is_relative_to 可能不存在于旧版本
                pass
        # 兜底检查
        return str(resolved).startswith(str(STORAGE_DIR.resolve()))
    except:
        return False


def browse_directory(path: str) -> Dict:
    """浏览指定目录，返回子目录和文件列表"""
    target = Path(path).expanduser()
    
    if not target.exists():
        raise ValueError(f"Path does not exist: {path}")
    
    if not target.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    if not is_safe_path(target):
        raise PermissionError(f"Access denied: {path}")
    
    dirs = []
    files = []
    
    for item in sorted(target.iterdir()):
        try:
            stat = item.stat()
            info = {
                "name": item.name,
                "path": str(item),
                "size": stat.st_size if item.is_file() else 0,
                "modified": stat.st_mtime,
            }
            if item.is_dir():
                dirs.append(info)
            else:
                files.append(info)
        except:
            continue  # 跳过无权限访问的项
    
    return {
        "current": str(target),
        "parent": str(target.parent) if target.parent != target else None,
        "directories": dirs,
        "files": files,
    }


def get_default_browse_roots() -> List[Dict]:
    """获取默认可浏览的根目录列表"""
    results = []
    for root in ALLOWED_BROWSE_ROOTS:
        if root.exists():
            results.append({
                "name": root.name or str(root),
                "path": str(root),
            })
    return results


def ensure_directory(path: str) -> Path:
    """确保目录存在，不存在则创建"""
    target = Path(path).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    return target
