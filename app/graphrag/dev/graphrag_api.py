#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GraphRAG API服务
使用FastAPI封装GraphRAG的查询功能，提供HTTP接口
"""

import asyncio
import logging
import warnings
import os
from pathlib import Path
import json
import sys
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
import uuid
import time

# 抑制不相关的警告
warnings.filterwarnings("ignore", category=SyntaxWarning)

# 导入FastAPI相关
from fastapi import FastAPI, HTTPException, Query, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# 导入OpenAI类型
try:
    from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta
    from openai.types.chat import ChatCompletionChunk
except ImportError:
    # 如果没有安装OpenAI包，我们创建兼容的模拟类
    class ChoiceDelta:
        def __init__(self, role=None, content=None):
            self.role = role
            self.content = content
        
        def __getattr__(self, name):
            return None
            
        def dict(self):
            result = {}
            if self.role:
                result["role"] = self.role
            if self.content:
                result["content"] = self.content
            return result
    
    class Choice:
        def __init__(self, index=0, finish_reason=None, delta=None):
            self.index = index
            self.finish_reason = finish_reason
            self.delta = delta if delta else ChoiceDelta()
            
        def dict(self):
            return {
                "index": self.index,
                "finish_reason": self.finish_reason,
                "delta": self.delta.dict()
            }
    
    class ChatCompletionChunk:
        def __init__(self, id=None, created=None, model=None, object=None, choices=None):
            self.id = id
            self.created = created
            self.model = model
            self.object = object
            self.choices = choices or []
            
        def dict(self):
            return {
                "id": self.id,
                "created": self.created,
                "model": self.model,
                "object": self.object,
                "choices": [choice.dict() for choice in self.choices]
            }
            
        def json(self):
            return json.dumps(self.dict())

# 导入我们的日志工具
from utils import setup_logging

# 导入GraphRAG相关
import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.callbacks.noop_query_callbacks import NoopQueryCallbacks
from graphrag.utils.storage import load_table_from_storage
from graphrag.storage.file_pipeline_storage import FilePipelineStorage

# ========================================
# 用户配置参数 - 直接修改这里的变量
# ========================================

# GraphRAG项目根目录路径
PROJECT_DIR = "E:\\my_graphrag\\graphrag_2.1.0\\graphrag"

# 数据目录名称（相对于项目根目录）
DATA_DIR_NAME = "data"

# 日志目录
LOG_DIR = os.path.join(PROJECT_DIR, DATA_DIR_NAME, "logs")

# 静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# 确保目录存在
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# 全局日志记录器
logger = setup_logging(LOG_DIR, log_file="graphrag_api.log", logger_name="dev-graphrag-api")

# 配置预加载的数据
data_cache = {}

# 创建FastAPI应用
app = FastAPI(
    title="GraphRAG API",
    description="GraphRAG查询API，支持多种查询方式",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 请求模型
class QueryRequest(BaseModel):
    query: str = Field(..., description="查询文本")
    query_type: str = Field(default="local", description="查询类型: local, global, drift, basic")
    response_type: str = Field(default="text", description="响应类型: text, json")
    community_level: int = Field(default=1, description="社区级别")
    dynamic_community_selection: bool = Field(default=False, description="是否使用动态社区选择")

# 响应模型
class QueryResponse(BaseModel):
    query: str = Field(..., description="查询文本")
    response: str = Field(..., description="查询结果")
    query_type: str = Field(..., description="使用的查询类型")
    context: str = Field(default="", description="查询上下文信息")
    
# 帮助函数：处理不可序列化的对象
def format_context(context):
    """将上下文对象转换为可序列化的格式"""
    try:
        # 先尝试将特殊对象转换为字典
        if hasattr(context, "__dict__"):
            simple_context = {}
            for key, value in context.__dict__.items():
                if not key.startswith("_"):  # 跳过私有属性
                    try:
                        # 尝试简单转换
                        if isinstance(value, (str, int, float, bool, type(None))):
                            simple_context[key] = value
                        else:
                            simple_context[key] = str(value)
                    except:
                        simple_context[key] = f"无法序列化的{type(value)}"
            return json.dumps(simple_context, ensure_ascii=False)
        
        # 如果不是对象，尝试json序列化
        try:
            return json.dumps(context, ensure_ascii=False)
        except:
            pass
            
        # 最后使用字符串表示
        return str(context)
    except Exception as e:
        logger.warning(f"无法序列化上下文对象: {str(e)}")
        return "无法序列化的上下文数据"
    
# 加载数据函数
async def load_data():
    """预加载GraphRAG数据"""
    global data_cache
    
    # 如果数据已经加载，直接返回
    if data_cache:
        return data_cache
    
    try:
        # 构建完整项目路径
        PROJECT_DIRECTORY = os.path.join(PROJECT_DIR, DATA_DIR_NAME)
        
        # 加载配置
        logger.info(f"加载配置...")
        graphrag_config = load_config(Path(PROJECT_DIRECTORY))
        
        # 创建存储路径
        output_dir = Path(graphrag_config.output.base_dir)
        if not output_dir.is_absolute():
            output_dir = Path(PROJECT_DIRECTORY) / output_dir
        
        logger.info(f"使用输出目录: {output_dir}")
        
        # 创建一个FilePipelineStorage对象
        storage = FilePipelineStorage(root_dir=str(output_dir))
        
        # 加载必要的数据文件
        logger.info("加载索引数据...")
        
        # 尝试加载parquet文件
        entities = await load_table_from_storage("entities", storage)
        logger.info(f"已加载实体数据，共 {len(entities)} 条记录")
        
        text_units = await load_table_from_storage("text_units", storage)
        logger.info(f"已加载文本单元数据，共 {len(text_units)} 条记录")
        
        communities = await load_table_from_storage("communities", storage)
        logger.info(f"已加载社区数据，共 {len(communities)} 条记录")
        
        community_reports = await load_table_from_storage("community_reports", storage)
        logger.info(f"已加载社区报告数据，共 {len(community_reports)} 条记录")
        
        relationships = await load_table_from_storage("relationships", storage)
        logger.info(f"已加载关系数据，共 {len(relationships)} 条记录")
        
        # 尝试加载协变量数据（可能不存在）
        try:
            covariates = await load_table_from_storage("covariates", storage)
            logger.info(f"已加载协变量数据，共 {len(covariates)} 条记录")
        except Exception:
            covariates = None
            logger.info("未找到协变量数据，将使用None")
        
        # 将加载的数据存入缓存
        data_cache = {
            "config": graphrag_config,
            "entities": entities,
            "text_units": text_units,
            "communities": communities,
            "community_reports": community_reports,
            "relationships": relationships,
            "covariates": covariates
        }
        
        logger.info("数据加载完成")
        return data_cache
        
    except Exception as e:
        logger.error(f"加载数据时出错: {str(e)}", exc_info=True)
        raise

# 查询函数
async def run_query(
    query: str, 
    query_type: str = "local", 
    response_type: str = "text", 
    community_level: int = 1,
    dynamic_community_selection: bool = False
):
    """执行GraphRAG查询"""
    try:
        # 加载数据
        data = await load_data()
        
        # 创建回调对象
        callbacks = []
        context_data = {}
        
        def on_context(context):
            nonlocal context_data
            context_data = context
        
        local_callbacks = NoopQueryCallbacks()
        local_callbacks.on_context = on_context
        callbacks.append(local_callbacks)
        
        logger.info(f"开始执行查询: {query}")
        logger.info(f"查询类型: {query_type}")
        
        # 根据查询类型执行不同的查询
        if query_type.lower() == "local":
            response, context = await api.local_search(
                config=data["config"],
                entities=data["entities"],
                communities=data["communities"],
                community_reports=data["community_reports"],
                text_units=data["text_units"],
                relationships=data["relationships"],
                covariates=data["covariates"],
                community_level=community_level,
                response_type=response_type,
                query=query,
                callbacks=callbacks
            )
        
        elif query_type.lower() == "global":
            response, context = await api.global_search(
                config=data["config"],
                entities=data["entities"],
                communities=data["communities"],
                community_reports=data["community_reports"],
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                query=query,
                callbacks=callbacks
            )
        
        elif query_type.lower() == "drift":
            response, context = await api.drift_search(
                config=data["config"],
                entities=data["entities"],
                communities=data["communities"],
                community_reports=data["community_reports"],
                text_units=data["text_units"],
                relationships=data["relationships"],
                community_level=community_level,
                response_type=response_type,
                query=query,
                callbacks=callbacks
            )
        
        elif query_type.lower() == "basic":
            response, context = await api.basic_search(
                config=data["config"],
                text_units=data["text_units"],
                query=query,
                callbacks=callbacks
            )
        
        else:
            raise ValueError(f"不支持的查询类型: {query_type}")
        
        logger.info("查询成功完成")
        
        # 安全处理上下文，避免序列化问题
        context_str = format_context(context_data)
        
        # 返回结果
        return {
            "query": query,
            "response": response,
            "query_type": query_type,
            "context": context_str  # 使用字符串形式的上下文
        }
    
    except Exception as e:
        logger.error(f"查询过程中发生错误: {str(e)}", exc_info=True)
        raise

# API路由

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径，重定向到静态HTML页面"""
    return RedirectResponse(url="/static/index.html")

@app.get("/simple", response_class=HTMLResponse)
async def simple_ui():
    """提供一个更简单的查询界面"""
    return RedirectResponse(url="/static/simple.html")

@app.get("/stream", response_class=HTMLResponse)
async def stream_ui():
    """提供一个流式查询界面，支持Markdown渲染"""
    return RedirectResponse(url="/static/stream.html")

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "version": "1.0.0"}

# 自定义响应模型，避免序列化问题
@app.post("/api/query")
async def query(request: QueryRequest):
    """
    执行GraphRAG查询
    """
    try:
        result = await run_query(
            query=request.query,
            query_type=request.query_type,
            response_type=request.response_type,
            community_level=request.community_level,
            dynamic_community_selection=request.dynamic_community_selection
        )
        # 使用JSONResponse确保响应被正确序列化
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"API查询出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")

@app.get("/api/query")
async def query_get(
    query: str = Query(..., description="查询文本"),
    query_type: str = Query("local", description="查询类型: local, global, drift, basic"),
    response_type: str = Query("text", description="响应类型: text, json"),
    community_level: int = Query(1, description="社区级别"),
    dynamic_community_selection: bool = Query(False, description="是否使用动态社区选择")
):
    """
    执行GraphRAG查询（GET方法）
    """
    try:
        result = await run_query(
            query=query,
            query_type=query_type,
            response_type=response_type,
            community_level=community_level,
            dynamic_community_selection=dynamic_community_selection
        )
        # 使用JSONResponse确保响应被正确序列化
        return JSONResponse(content=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"API查询出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"查询处理失败: {str(e)}")

# 添加一个流式响应API
@app.post("/api/query_stream")
async def query_stream(request: QueryRequest):
    """
    执行GraphRAG查询并以流的形式返回结果
    """
    async def generate():
        try:
            # 加载数据
            data = await load_data()
            
            # 前置部分，模拟流式传输的开始
            yield "开始处理查询...\n\n"
            
            # 创建回调对象
            context_data = {}
            
            def on_context(context):
                nonlocal context_data
                context_data = context
            
            local_callbacks = NoopQueryCallbacks()
            local_callbacks.on_context = on_context
            
            logger.info(f"开始执行流式查询: {request.query}")
            logger.info(f"查询类型: {request.query_type}")
            
            # 根据查询类型执行不同的查询
            if request.query_type.lower() == "local":
                response, context = await api.local_search(
                    config=data["config"],
                    entities=data["entities"],
                    communities=data["communities"],
                    community_reports=data["community_reports"],
                    text_units=data["text_units"],
                    relationships=data["relationships"],
                    covariates=data["covariates"],
                    community_level=request.community_level,
                    response_type=request.response_type,
                    query=request.query,
                    callbacks=[local_callbacks]
                )
            
            elif request.query_type.lower() == "global":
                response, context = await api.global_search(
                    config=data["config"],
                    entities=data["entities"],
                    communities=data["communities"],
                    community_reports=data["community_reports"],
                    community_level=request.community_level,
                    dynamic_community_selection=request.dynamic_community_selection,
                    response_type=request.response_type,
                    query=request.query,
                    callbacks=[local_callbacks]
                )
            
            elif request.query_type.lower() == "drift":
                response, context = await api.drift_search(
                    config=data["config"],
                    entities=data["entities"],
                    communities=data["communities"],
                    community_reports=data["community_reports"],
                    text_units=data["text_units"],
                    relationships=data["relationships"],
                    community_level=request.community_level,
                    response_type=request.response_type,
                    query=request.query,
                    callbacks=[local_callbacks]
                )
            
            elif request.query_type.lower() == "basic":
                response, context = await api.basic_search(
                    config=data["config"],
                    text_units=data["text_units"],
                    query=request.query,
                    callbacks=[local_callbacks]
                )
            
            else:
                yield "错误：不支持的查询类型\n"
                return
            
            logger.info("流式查询成功完成")
            
            # 将结果分段发送
            # 每个段落最多25个词
            words = response.split()
            for i in range(0, len(words), 25):
                segment = " ".join(words[i:i+25])
                yield segment + " "
                await asyncio.sleep(0.1)  # 模拟流式传输的延迟
                
            # 添加流式传输结束标记
            yield "\n\n---\n*流式传输完成*"
            
        except Exception as e:
            logger.error(f"流式查询过程中发生错误: {str(e)}", exc_info=True)
            yield f"\n\n错误: {str(e)}"
    
    return StreamingResponse(generate(), media_type="text/plain")

# 添加流式搜索辅助函数
async def mock_astream_search(query: str, search_func, kwargs: dict) -> AsyncGenerator[str, None]:
    """
    模拟流式搜索功能。这个函数接收查询方法和参数，然后将结果以流的形式输出。
    
    参数:
    query (str): 用户查询
    search_func (callable): 搜索函数
    kwargs (dict): 搜索函数的参数
    
    返回:
    AsyncGenerator[str, None]: 异步生成器，逐个字符产生响应
    """
    try:
        # 执行查询获取完整响应
        response, context = await search_func(**kwargs)
        
        # 将响应按字符逐个输出（可根据需要调整为词、句子等）
        for char in response:
            yield char
            # 我们这里不添加人为延迟，以达到最快速度
    except Exception as e:
        # 出现错误时，返回错误消息
        error_message = f"流式搜索出错: {str(e)}"
        logger.error(error_message, exc_info=True)
        for char in error_message:
            yield char


# 启动应用的部分
def start():
    """启动FastAPI应用"""
    import uvicorn
    
    # 预加载数据
    asyncio.run(load_data())
    
    # 启动服务
    host = "0.0.0.0"
    port = 8000
    logger.info(f"启动API服务 http://{host}:{port}")
    uvicorn.run("graphrag_api:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    start() 