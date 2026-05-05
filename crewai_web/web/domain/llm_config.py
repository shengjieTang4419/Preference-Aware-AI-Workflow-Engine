"""LLM 配置领域模型"""
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ModelTierConfig(BaseModel):
    """单个模型等级配置"""
    model: str
    temperature: float = 0.7
    is_default: bool = False  # 是否为默认模型


class ProviderConfig(BaseModel):
    """LLM 提供商配置"""
    api_key: Optional[str] = None
    base_url: str
    basic: ModelTierConfig
    standard: ModelTierConfig
    advanced: ModelTierConfig
    
    @property
    def default_model(self) -> ModelTierConfig:
        """获取默认模型（is_default=true 的档位）"""
        for tier in [self.basic, self.standard, self.advanced]:
            if tier.is_default:
                return tier
        # 如果没有设置默认，返回中级模型
        return self.standard
    
    def get_tier_by_model(self, model: str) -> Optional[ModelTierConfig]:
        """根据模型名称查找对应的档位配置
        
        Args:
            model: 模型名称
            
        Returns:
            ModelTierConfig: 档位配置，如果找不到返回 None
        """
        for tier in [self.basic, self.standard, self.advanced]:
            if tier.model == model:
                return tier
        return None
    
    def mask_api_key(self) -> str:
        """脱敏后的 API Key"""
        if not self.api_key:
            return "未配置"
        if len(self.api_key) <= 8:
            return "***"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


class LLMConfig(BaseModel):
    """完整的 LLM 配置"""
    default_provider: str = "dashscope"
    dashscope: Optional[ProviderConfig] = None
    claude: Optional[ProviderConfig] = None
    
    @classmethod
    def load(cls) -> "LLMConfig":
        """加载配置（优先级：JSON > .env）"""
        from crewai_web.web.config import STORAGE_DIR
        json_path = STORAGE_DIR / "config" / "llm_settings.json"
        
        if json_path.exists():
            # 优先使用 JSON 配置（运行时配置）
            return cls.from_json(json_path)
        else:
            # 回退到 .env 配置（环境配置）
            return cls.from_env()
    
    @classmethod
    def from_json(cls, path: Path) -> "LLMConfig":
        """从 JSON 文件加载配置"""
        data = json.loads(path.read_text(encoding="utf-8"))
        
        # 构建 ProviderConfig，合并 API Key 和 Base URL（从 .env 读取）
        if "dashscope" in data:
            data["dashscope"] = {
                "api_key": os.getenv("DASHSCOPE_API_KEY"),
                "base_url": os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
                **data["dashscope"]
            }
        
        if "claude" in data:
            data["claude"] = {
                "api_key": os.getenv("CLAUDE_API_KEY"),
                "base_url": os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1"),
                **data["claude"]
            }
        
        return cls(**data)
    
    def save(self, path: Path) -> None:
        """保存到 JSON 文件（不保存敏感信息）"""
        data = {
            "default_provider": self.default_provider
        }
        
        # 只保存模型配置，不保存 API Key 和 Base URL
        if self.dashscope:
            data["dashscope"] = {
                "basic": self.dashscope.basic.model_dump() if self.dashscope.basic else None,
                "standard": self.dashscope.standard.model_dump() if self.dashscope.standard else None,
                "advanced": self.dashscope.advanced.model_dump() if self.dashscope.advanced else None,
            }
        
        if self.claude:
            data["claude"] = {
                "basic": self.claude.basic.model_dump() if self.claude.basic else None,
                "standard": self.claude.standard.model_dump() if self.claude.standard else None,
                "advanced": self.claude.advanced.model_dump() if self.claude.advanced else None,
            }
        
        # 添加更新时间
        data["updated_at"] = datetime.now().isoformat()
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到文件
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """从环境变量加载配置"""
        return cls(
            default_provider=os.getenv("DEFAULT_LLM_PROVIDER", "dashscope"),
            dashscope=cls._load_dashscope(),
            claude=cls._load_claude(),
        )
    
    @classmethod
    def _load_dashscope(cls) -> Optional[ProviderConfig]:
        """加载 DashScope 配置"""
        api_key = os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            return None
        
        # 获取默认模型标识
        default_tier = os.getenv("DASHSCOPE_DEFAULT_TIER", "standard")
        
        return ProviderConfig(
            api_key=api_key,
            base_url=os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
            basic=ModelTierConfig(
                model=os.getenv("DASHSCOPE_MODEL_BASIC", "qwen-turbo"),
                temperature=float(os.getenv("DASHSCOPE_MODEL_BASIC_TEMP", "0.3")),
                is_default=(default_tier == "basic")
            ),
            standard=ModelTierConfig(
                model=os.getenv("DASHSCOPE_MODEL_STANDARD", "qwen-plus"),
                temperature=float(os.getenv("DASHSCOPE_MODEL_STANDARD_TEMP", "0.7")),
                is_default=(default_tier == "standard")
            ),
            advanced=ModelTierConfig(
                model=os.getenv("DASHSCOPE_MODEL_ADVANCED", "qwen-max"),
                temperature=float(os.getenv("DASHSCOPE_MODEL_ADVANCED_TEMP", "0.9")),
                is_default=(default_tier == "advanced")
            ),
        )
    
    @classmethod
    def _load_claude(cls) -> Optional[ProviderConfig]:
        """加载 Claude 配置"""
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            return None
        
        # 获取默认模型标识
        default_tier = os.getenv("CLAUDE_DEFAULT_TIER", "standard")
        
        return ProviderConfig(
            api_key=api_key,
            base_url=os.getenv("CLAUDE_BASE_URL", "https://api.anthropic.com/v1"),
            basic=ModelTierConfig(
                model=os.getenv("CLAUDE_MODEL_BASIC", "claude-3-haiku-20240307"),
                temperature=float(os.getenv("CLAUDE_MODEL_BASIC_TEMP", "0.3")),
                is_default=(default_tier == "basic")
            ),
            standard=ModelTierConfig(
                model=os.getenv("CLAUDE_MODEL_STANDARD", "claude-3-5-sonnet-20241022"),
                temperature=float(os.getenv("CLAUDE_MODEL_STANDARD_TEMP", "0.7")),
                is_default=(default_tier == "standard")
            ),
            advanced=ModelTierConfig(
                model=os.getenv("CLAUDE_MODEL_ADVANCED", "claude-3-opus-20240229"),
                temperature=float(os.getenv("CLAUDE_MODEL_ADVANCED_TEMP", "0.9")),
                is_default=(default_tier == "advanced")
            ),
        )
    
    def to_api_response(self) -> dict:
        """转换为 API 响应格式（API Key 已脱敏，保护安全）"""
        result = {
            "default_provider": self.default_provider
        }
        
        if self.dashscope:
            result["dashscope"] = {
                "api_key": self.dashscope.mask_api_key(),  # ✅ 脱敏后返回
                "base_url": self.dashscope.base_url,
                "basic": self.dashscope.basic.model_dump(),
                "standard": self.dashscope.standard.model_dump(),
                "advanced": self.dashscope.advanced.model_dump(),
            }
        
        if self.claude:
            result["claude"] = {
                "api_key": self.claude.mask_api_key(),  # ✅ 脱敏后返回
                "base_url": self.claude.base_url,
                "basic": self.claude.basic.model_dump(),
                "standard": self.claude.standard.model_dump(),
                "advanced": self.claude.advanced.model_dump(),
            }
        
        return result
