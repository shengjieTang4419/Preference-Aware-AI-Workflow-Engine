from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from crewai_web.core.llm.factory import llm_factory
from crewai_web.web.services.config_service import get_config_service

router = APIRouter(prefix="/llm", tags=["LLM Settings"])


class ModelTierConfig(BaseModel):
    """单个模型等级配置"""
    model: str
    temperature: float = 0.7
    is_default: bool = False  # 是否为默认模型


class LLMProviderConfig(BaseModel):
    """LLM 提供商配置"""
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    basic: Optional[ModelTierConfig] = None      # 初级模型
    standard: Optional[ModelTierConfig] = None   # 中级模型
    advanced: Optional[ModelTierConfig] = None   # 高级模型


class LLMSettings(BaseModel):
    """完整的 LLM 配置"""
    default_provider: str
    dashscope: Optional[LLMProviderConfig] = None
    claude: Optional[LLMProviderConfig] = None


@router.get("/providers")
async def list_providers():
    """获取可用的 LLM 提供商列表"""
    return {"providers": llm_factory.list_providers(), "default_provider": llm_factory.default_provider}


@router.get("/settings")
async def get_llm_settings():
    """获取当前 LLM 配置"""
    return get_config_service().get_llm_settings()


@router.put("/settings")
async def update_llm_settings(settings: LLMSettings):
    """更新 LLM 配置"""
    get_config_service().update_llm_settings(settings)
    return {"message": "LLM settings updated. Please restart for changes to take effect."}


@router.post("/test/{provider}")
async def test_provider_connection(provider: str, model: Optional[str] = None):
    """测试 LLM 提供商连接"""
    try:
        llm_provider = llm_factory.get_provider(provider)
        if not llm_provider.validate_config():
            raise HTTPException(status_code=400, detail=f"Provider '{provider}' not configured. Check API key.")
        test_model = model or llm_provider.get_default_model()
        llm_provider.create_llm(test_model)
        return {"success": True, "provider": provider, "model": test_model, "message": f"Connected to {provider}/{test_model}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
