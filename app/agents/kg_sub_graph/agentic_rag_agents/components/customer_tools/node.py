from typing import Any, Callable, Coroutine, Dict, List
import asyncio
import os
from pathlib import Path
from pydantic import BaseModel, Field

# 导入GraphRAG相关模块
import app.graphrag.graphrag.api as api
from app.graphrag.graphrag.config.load_config import load_config
from app.graphrag.graphrag.callbacks.noop_query_callbacks import NoopQueryCallbacks
from app.graphrag.graphrag.utils.storage import load_table_from_storage
from app.graphrag.graphrag.storage.file_pipeline_storage import FilePipelineStorage

# 导入配置
from app.core.config import settings

# 定义GraphRAG查询的输入状态类型
class GraphRAGQueryInputState(BaseModel):
    task: str
    query: str
    steps: List[str]

# 定义GraphRAG查询的输出状态类型
class GraphRAGQueryOutputState(BaseModel):
    task: str
    query: str
    errors: List[str]
    records: Dict[str, Any]
    steps: List[str]

# 定义GraphRAG API包装器
class GraphRAGAPI:
    def __init__(self, project_dir: str = None, 
                 data_dir_name: str = None,
                 query_type: str = None,
                 response_type: str = None,
                 community_level: int = None,
                 dynamic_community_selection: bool = None):
        # 从环境变量获取配置，如果提供了参数则使用参数值
        self.project_dir = project_dir or settings.GRAPHRAG_PROJECT_DIR
        self.data_dir_name = data_dir_name or settings.GRAPHRAG_DATA_DIR
        self.query_type = query_type or settings.GRAPHRAG_QUERY_TYPE
        self.response_type = response_type or settings.GRAPHRAG_RESPONSE_TYPE
        self.community_level = community_level or settings.GRAPHRAG_COMMUNITY_LEVEL
        self.dynamic_community_selection = dynamic_community_selection if dynamic_community_selection is not None else settings.GRAPHRAG_DYNAMIC_COMMUNITY
        self.config = None
        self.storage = None
        self.entities = None
        self.text_units = None
        self.communities = None
        self.community_reports = None
        self.relationships = None
        self.covariates = None
        self.initialized = False
    
    async def initialize(self):
        """初始化GraphRAG API，加载必要的数据"""
        if self.initialized:
            return
            
        # 构建完整项目路径
        project_directory = os.path.join(self.project_dir, self.data_dir_name)
        
        # 加载配置
        self.config = load_config(Path(project_directory), None, None)
        
        # 创建存储路径
        output_dir = Path(self.config.output.base_dir)
        if not output_dir.is_absolute():
            output_dir = Path(project_directory) / output_dir
        
        # 创建FilePipelineStorage对象
        self.storage = FilePipelineStorage(root_dir=str(output_dir))
        
        # 加载必要的数据文件
        try:
            self.entities = await load_table_from_storage("entities", self.storage)
            self.text_units = await load_table_from_storage("text_units", self.storage)
            self.communities = await load_table_from_storage("communities", self.storage)
            self.community_reports = await load_table_from_storage("community_reports", self.storage)
            self.relationships = await load_table_from_storage("relationships", self.storage)
            
            # 尝试加载协变量数据（可能不存在）
            try:
                self.covariates = await load_table_from_storage("covariates", self.storage)
            except Exception:
                self.covariates = None
            
            self.initialized = True
        except Exception as e:
            raise Exception(f"加载GraphRAG数据文件时出错: {str(e)}")
    
    async def query_graphrag(self, query: str) -> Dict[str, Any]:
        """执行GraphRAG查询"""
        await self.initialize()
        
        # 创建回调对象
        callbacks = []
        context_data = {}
        
        def on_context(context):
            nonlocal context_data
            context_data = context
        
        local_callbacks = NoopQueryCallbacks()
        local_callbacks.on_context = on_context
        callbacks.append(local_callbacks)
        
        try:
            # 根据查询类型执行不同的查询
            if self.query_type.lower() == "local":
                response, context = await api.local_search(
                    config=self.config,
                    entities=self.entities,
                    communities=self.communities,
                    community_reports=self.community_reports,
                    text_units=self.text_units,
                    relationships=self.relationships,
                    covariates=self.covariates,
                    community_level=self.community_level,
                    response_type=self.response_type,
                    query=query,
                    callbacks=callbacks
                )
            
            elif self.query_type.lower() == "global":
                response, context = await api.global_search(
                    config=self.config,
                    entities=self.entities,
                    communities=self.communities,
                    community_reports=self.community_reports,
                    community_level=self.community_level,
                    dynamic_community_selection=self.dynamic_community_selection,
                    response_type=self.response_type,
                    query=query,
                    callbacks=callbacks
                )
            
            elif self.query_type.lower() == "drift":
                response, context = await api.drift_search(
                    config=self.config,
                    entities=self.entities,
                    communities=self.communities,
                    community_reports=self.community_reports,
                    text_units=self.text_units,
                    relationships=self.relationships,
                    community_level=self.community_level,
                    response_type=self.response_type,
                    query=query,
                    callbacks=callbacks
                )
            
            elif self.query_type.lower() == "basic":
                response, context = await api.basic_search(
                    config=self.config,
                    text_units=self.text_units,
                    query=query,
                    callbacks=callbacks
                )
            
            else:
                raise ValueError(f"不支持的查询类型: {self.query_type}")
            
            # 构建结果字典
            result = {
                "response": response,
                "context": context_data
            }
            
            return result
            
        except Exception as e:
            raise Exception(f"执行GraphRAG查询时出错: {str(e)}")

def create_graphrag_query_node(
) -> Callable[
    [GraphRAGQueryInputState],
    Coroutine[Any, Any, Dict[str, List[GraphRAGQueryOutputState] | List[str]]],
]:
    """
    创建GraphRAG查询节点，用于LangGraph工作流。

    返回
    -------
    Callable[[GraphRAGQueryInputState], Dict[str, List[GraphRAGQueryOutputState] | List[str]]]
        名为`graphrag_query`的LangGraph节点。
    """

    async def graphrag_query(
        state: Dict[str, Any],
    ) -> Dict[str, List[GraphRAGQueryOutputState] | List[str]]:
        """
        执行GraphRAG查询并返回结果。
        """
        errors = list()
        search_result = {}
        
        # 获取查询文本
        query = state.get("task", "")
        if not query:
            errors.append("未提供查询文本")
        else:
            try:
                # 使用环境变量中的配置创建GraphRAGAPI实例
                graphrag_api = GraphRAGAPI()
                # 调用GraphRAG API获取数据
                search_result = await graphrag_api.query_graphrag(query)
            except Exception as e:
                errors.append(f"GraphRAG查询失败: {str(e)}")
  
            return {
                "cyphers": [
                    GraphRAGQueryOutputState(
                        **{
                            "task": state.get("task", ""),
                            "query": query,
                            "statement": "",
                            "parameters":"",
                            "errors": errors,
                            "records": {"result": search_result["response"]},
                            "steps": ["execute_graphrag_query"],
                        }
                    )
                ],
                "steps": ["execute_graphrag_query"],
            }
  
    return graphrag_query

