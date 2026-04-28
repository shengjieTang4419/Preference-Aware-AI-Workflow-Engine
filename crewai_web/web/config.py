from pathlib import Path
import os

# 项目根目录 (crewai_web 的父目录，即项目根)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# 存储目录配置
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", PROJECT_ROOT / "storage"))
AGENTS_DIR = STORAGE_DIR / "agents"
TASKS_DIR = STORAGE_DIR / "tasks"
CREWS_DIR = STORAGE_DIR / "crews"
EXECUTIONS_DIR = STORAGE_DIR / "executions"

# 文件目录配置
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", PROJECT_ROOT / "upload"))
OUTPUT_DIR = STORAGE_DIR / "results"

# 环境变量文件
ENV_FILE = PROJECT_ROOT / ".env"

# 确保目录存在
def ensure_storage_dirs():
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    CREWS_DIR.mkdir(parents=True, exist_ok=True)
    EXECUTIONS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件浏览根目录 (安全限制)
ALLOWED_BROWSE_ROOTS = [
    STORAGE_DIR,
    Path("/tmp"),
    Path.home() / "workspace",
]
