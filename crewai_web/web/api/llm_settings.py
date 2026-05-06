from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from crewai_web.core.llm.provider_registry import provider_registry
from crewai_web.web.services.config_service import get_config_service
from crewai_web.core.llm.config_loader import config_loader

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
    basic: Optional[ModelTierConfig] = None  # 初级模型
    standard: Optional[ModelTierConfig] = None  # 中级模型
    advanced: Optional[ModelTierConfig] = None  # 高级模型


class LLMSettings(BaseModel):
    """完整的 LLM 配置"""

    default_provider: str
    dashscope: Optional[LLMProviderConfig] = None
    claude: Optional[LLMProviderConfig] = None


@router.get("/providers")
async def list_providers():
    """获取可用的 LLM 提供商列表"""
    return {"providers": provider_registry.list_providers(), "default_provider": provider_registry.default_provider}


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
    """测试 LLM 提供商连接 - 通过实际 API 调用验证"""
    try:
        llm_provider = provider_registry.get_provider(provider)
        if not llm_provider.validate_config():
            raise HTTPException(status_code=400, detail=f"Provider '{provider}' not configured. Check API key.")

        # 创建 LLM 实例（使用指定模型或默认模型）
        if model:
            llm = llm_provider.create_llm(model)
            test_model = model
        else:
            llm = llm_provider.get_default_llm()
            # 获取默认模型名称用于返回
            default_tier = config_loader.get_default_tier(llm_provider.platform)
            test_model = default_tier.model

        # 实际调用 AI provider 进行测试
        test_prompt = "Hello"
        response = llm.call(test_prompt)

        return {
            "success": True,
            "provider": provider,
            "model": test_model,
            "message": f"Successfully connected to {provider}/{test_model}",
            "test_response": response[:100] if len(response) > 100 else response,  # 返回前100个字符作为验证
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")
