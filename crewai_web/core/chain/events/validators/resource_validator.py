"""通用资源校验器"""

from typing import Callable, Dict, Any, List, Optional
from crewai_web.core.chain.events.base_event import ExecutionContext


class ResourceValidator:
    """通用资源校验器
    
    使用声明式配置进行资源校验，避免重复代码。
    
    职责：
    - 校验单个资源是否存在
    - 批量校验资源
    - 校验引用关系
    """
    
    def __init__(self, ctx: ExecutionContext):
        """初始化校验器
        
        Args:
            ctx: 执行上下文
        """
        self.ctx = ctx
    
    def validate_resource(
        self,
        resource_id: str,
        resource_type: str,
        fetch_func: Callable[[str], Any],
        error_context: Optional[str] = None,
    ) -> Any:
        """校验单个资源是否存在
        
        Args:
            resource_id: 资源 ID
            resource_type: 资源类型（用于错误提示，如 "Agent", "Task"）
            fetch_func: 获取资源的函数
            error_context: 错误上下文信息（可选）
            
        Returns:
            资源对象
            
        Raises:
            ValueError: 如果资源不存在
            
        Example:
            >>> validator.validate_resource(
            ...     resource_id="agent1",
            ...     resource_type="Agent",
            ...     fetch_func=agent_service.get_agent,
            ...     error_context="referenced by crew 'my_crew'"
            ... )
        """
        resource = fetch_func(resource_id)
        if not resource:
            error_msg = f"{resource_type} '{resource_id}' not found"
            if error_context:
                error_msg += f" ({error_context})"
            raise ValueError(error_msg)
        return resource
    
    def validate_resources(
        self,
        resource_ids: List[str],
        resource_type: str,
        fetch_func: Callable[[str], Any],
        storage: Dict[str, Any],
        error_context: Optional[str] = None,
    ) -> None:
        """批量校验资源并存储到 context
        
        Args:
            resource_ids: 资源 ID 列表
            resource_type: 资源类型（用于错误提示）
            fetch_func: 获取资源的函数
            storage: 存储资源的字典（通常是 ctx.agent_configs 或 ctx.task_configs）
            error_context: 错误上下文信息（可选）
            
        Example:
            >>> validator.validate_resources(
            ...     resource_ids=["agent1", "agent2"],
            ...     resource_type="Agent",
            ...     fetch_func=agent_service.get_agent,
            ...     storage=ctx.agent_configs,
            ...     error_context="referenced by crew 'my_crew'"
            ... )
        """
        for resource_id in resource_ids:
            resource = self.validate_resource(resource_id, resource_type, fetch_func, error_context)
            storage[resource_id] = resource
        
        self.ctx.log("INFO", f"[Validator] {resource_type}s validated: {len(storage)} items")
    
    def validate_reference(
        self,
        source_id: str,
        target_id: str,
        valid_ids: set,
        error_message: str,
    ) -> None:
        """校验引用关系是否合法
        
        Args:
            source_id: 源资源 ID（用于错误提示，当前未使用）
            target_id: 目标资源 ID
            valid_ids: 合法的 ID 集合
            error_message: 错误提示信息
            
        Raises:
            ValueError: 如果引用不合法
            
        Example:
            >>> validator.validate_reference(
            ...     source_id="task1",
            ...     target_id="agent1",
            ...     valid_ids={"agent1", "agent2"},
            ...     error_message="Task 'task1' references invalid agent 'agent1'"
            ... )
        """
        if target_id not in valid_ids:
            raise ValueError(error_message)
