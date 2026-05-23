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
ARTIFACTS_DIR = STORAGE_DIR / "artifacts"

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

# ── 数据库配置 ─────────────────────────────────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "crewai_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ── JWT 配置 ───────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "72"))
