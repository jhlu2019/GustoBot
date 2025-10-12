"""
基础Agent类
所有Agent的基类，定义通用接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, name: str, description: str):
        """
        初始化Agent

        Args:
            name: Agent名称
            description: Agent描述
        """
        self.name = name
        self.description = description
        logger.info(f"Initialized agent: {name}")

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理输入数据

        Args:
            input_data: 输入数据

        Returns:
            处理结果
        """
        pass

    def get_info(self) -> Dict[str, str]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "description": self.description,
        }

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        验证输入数据

        Args:
            input_data: 输入数据

        Returns:
            是否有效
        """
        return True

    async def log_action(self, action: str, details: Optional[Dict] = None):
        """记录Agent动作"""
        log_msg = f"[{self.name}] {action}"
        if details:
            log_msg += f" - {details}"
        logger.info(log_msg)
