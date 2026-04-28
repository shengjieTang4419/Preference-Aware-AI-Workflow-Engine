"""
责任链基类 - BaseEvent 和 ExecutionContext

所有事件（内置标准事件 + 业务动态事件）的抽象基类。
通过 ExecutionContext 在 chain 中传递状态。
"""

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """事件类型"""
    STANDARD = "standard"   # 内置标准事件（PreHandle, Finish, Touch）
    BUSINESS = "business"   # 业务动态事件（Crew 中的 Agent/Task 执行）


@dataclass
class ExecutionContext:
    """
    执行上下文 - 在 chain 中传递的共享状态
    
    每个 Event 可以读取和写入 context，下一个 Event 可以看到上一个的修改。
    类似 Java 中的 ServletContext / PipelineContext。
    """
    # 输入参数
    crew_id: str = ""
    requirement: str = ""
    inputs: dict = field(default_factory=dict)
    exec_id: str = ""
    output_dir: str = ""
    input_folder: Optional[str] = None
    
    # 中间状态
    crew_config: Any = None
    agent_configs: dict = field(default_factory=dict)
    task_configs: dict = field(default_factory=dict)
    crew_instance: Any = None  # 构建好的 CrewAI Crew 对象
    
    # 执行结果
    result: Optional[str] = None
    success: bool = False
    error: Optional[str] = None
    
    # 指标
    metrics: dict = field(default_factory=lambda: {
        "task_started": 0,
        "task_completed": 0,
        "task_failed": 0,
        "start_time": None,
        "end_time": None,
    })
    
    # 日志
    logs: list = field(default_factory=list)
    
    # 扩展数据（业务自定义）
    extras: dict = field(default_factory=dict)
    
    def log(self, level: str, message: str) -> None:
        """记录日志"""
        self.logs.append(f"[{level}] {message}")
        getattr(logger, level.lower(), logger.info)(message)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """执行时长"""
        start = self.metrics.get("start_time")
        end = self.metrics.get("end_time")
        if start and end:
            return (end - start).total_seconds()
        return None


class BaseEvent(ABC):
    """
    事件基类 - 责任链中的一个节点
    
    类似 Java 的:
        public abstract class BaseEvent {
            protected EventType eventType;
            public abstract ExecutionContext handle(ExecutionContext ctx);
        }
    """
    
    def __init__(self, event_type: EventType):
        self.event_type = event_type
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def handle(self, ctx: ExecutionContext) -> ExecutionContext:
        """
        处理事件，返回更新后的 context
        
        Args:
            ctx: 执行上下文
            
        Returns:
            更新后的执行上下文
            
        Raises:
            任何异常都会中断 chain
        """
        pass
    
    @property
    def name(self) -> str:
        return self.__class__.__name__
