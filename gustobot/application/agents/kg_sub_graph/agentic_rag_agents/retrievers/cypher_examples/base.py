from abc import ABC, abstractmethod
from typing import Any
from pydantic import BaseModel, ConfigDict
import re

class BaseCypherExampleRetriever(BaseModel, ABC):
    """
    Abstract base class for an example retriever.
    Subclasses must implement the `get_examples` method.
    """

    model_config: ConfigDict = ConfigDict(**{"arbitrary_types_allowed": True})  # type: ignore[misc]

    @abstractmethod
    def get_examples(self, query: str, k: int = 5) -> str:
        """
        根据用户查询返回相关的Cypher查询示例
        
        Parameters
        ----------
        query : str
            用户的自然语言查询
        k : int, optional
            返回的示例数量, by default 5
            
        Returns
        -------
        str
            格式化的示例字符串，每个示例包含问题和对应的Cypher查询
        """
        pass
