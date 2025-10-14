#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
webserver 实现测试
用于测试 webserver 中的 handle_sync_response 和 handle_stream_response 功能
"""

import logging
import os
import time
import uuid
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import json

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Webserver Test",
    description="测试 webserver 中的 handle_sync_response 和 handle_stream_response 功能",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建静态文件目录
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "webserver_static")
os.makedirs(STATIC_DIR, exist_ok=True)

# 挂载静态文件目录
app.mount("/webserver_static", StaticFiles(directory=STATIC_DIR), name="webserver_static")

# 请求和响应模型
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: list[Message]
    model: str
    stream: bool = False
    community_level: int = 1
    dynamic_community_selection: bool = False
    response_type: str = "text"

# 模拟OpenAI类型
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
    def __init__(self, index=0, finish_reason=None, delta=None, message=None):
        self.index = index
        self.finish_reason = finish_reason
        self.delta = delta
        self.message = message
        
    def dict(self):
        result = {
            "index": self.index,
            "finish_reason": self.finish_reason
        }
        if self.delta:
            result["delta"] = self.delta.dict()
        if self.message:
            result["message"] = self.message.dict()
        return result

class ChatCompletionMessage:
    def __init__(self, role=None, content=None):
        self.role = role
        self.content = content
    
    def dict(self):
        return {
            "role": self.role,
            "content": self.content
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

class ChatCompletion:
    def __init__(self, id=None, created=None, model=None, object=None, choices=None, usage=None):
        self.id = id
        self.created = created
        self.model = model
        self.object = object
        self.choices = choices or []
        self.usage = usage or {}
        
    def dict(self):
        return {
            "id": self.id,
            "created": self.created,
            "model": self.model,
            "object": self.object,
            "choices": [choice.dict() for choice in self.choices],
            "usage": self.usage
        }

class CompletionUsage:
    def __init__(self, completion_tokens=None, prompt_tokens=None, total_tokens=None):
        self.completion_tokens = completion_tokens
        self.prompt_tokens = prompt_tokens
        self.total_tokens = total_tokens
    
    def dict(self):
        return {
            "completion_tokens": self.completion_tokens,
            "prompt_tokens": self.prompt_tokens,
            "total_tokens": self.total_tokens
        }

# 主页
@app.get("/", response_class=HTMLResponse)
async def root():
    html_file_path = os.path.join(STATIC_DIR, "webserver_test.html")
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

# 处理同步响应的函数
async def handle_sync_response(request):
    """
    处理同步响应的函数，模拟 webserver 中的 handle_sync_response 实现
    """
    # 模拟查询过程，创建一些延迟
    await asyncio.sleep(0.5)  # 模拟查询延迟
    
    # 获取查询内容
    query = request.messages[-1].content if request.messages else "无查询内容"
    
    # 模拟响应生成
    response = f"这是对查询 '{query}' 的同步响应。\n\n使用了模型: {request.model}\n"
    response += f"社区级别: {request.community_level}\n"
    response += f"动态社区选择: {'是' if request.dynamic_community_selection else '否'}\n"
    response += f"响应类型: {request.response_type}\n\n"
    
    # 添加一些测试内容
    response += "# 测试标题\n\n"
    response += "这是一个测试响应，模拟了 webserver 的 handle_sync_response 函数的行为。\n\n"
    response += "- 项目1: 同步响应测试\n"
    response += "- 项目2: 无流式输出\n\n"
    response += "```python\n"
    response += "def test_function():\n"
    response += "    print('这是测试代码')\n"
    response += "```\n"

    # 构建 OpenAI 兼容格式的响应
    completion = ChatCompletion(
        id=f"chatcmpl-{uuid.uuid4().hex}",
        created=int(time.time()),
        model=request.model,
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(
                    role="assistant",
                    content=response
                )
            )
        ],
        usage=CompletionUsage(
            completion_tokens=len(response),
            prompt_tokens=len(query),
            total_tokens=len(response) + len(query)
        )
    )
    
    return JSONResponse(content=jsonable_encoder(completion.dict()))

# 处理流式响应的函数
async def handle_stream_response(request):
    """
    处理流式响应的函数，模拟 webserver 中的 handle_stream_response 实现
    """
    async def wrapper_astream_search():
        token_index = 0
        chat_id = f"chatcmpl-{uuid.uuid4().hex}"
        full_response = ""
        
        # 获取查询内容
        query = request.messages[-1].content if request.messages else "无查询内容"
        
        # 模拟响应生成
        response = f"这是对查询 '{query}' 的流式响应。\n\n使用了模型: {request.model}\n"
        response += f"社区级别: {request.community_level}\n"
        response += f"动态社区选择: {'是' if request.dynamic_community_selection else '否'}\n"
        response += f"响应类型: {request.response_type}\n\n"
        
        # 添加一些测试内容
        response += "# 测试标题\n\n"
        response += "这是一个测试响应，模拟了 webserver 的 handle_stream_response 函数的行为。\n\n"
        response += "- 项目1: 流式响应测试\n"
        response += "- 项目2: 字符逐个输出\n\n"
        response += "```python\n"
        response += "def test_function():\n"
        response += "    print('这是测试代码')\n"
        response += "```\n"

        # 发送第一个包含角色的块
        chunk = ChatCompletionChunk(
            id=chat_id,
            created=int(time.time()),
            model=request.model,
            object="chat.completion.chunk",
            choices=[
                Choice(
                    index=token_index,
                    finish_reason=None,
                    delta=ChoiceDelta(
                        role="assistant"
                    )
                )
            ]
        )
        yield f"data: {chunk.json()}\n\n"
        token_index += 1

        # 逐个字符发送响应
        for token in response:
            # 模拟一点处理时间
            await asyncio.sleep(0.01)  # 减少延迟让字符更快输出
            
            chunk = ChatCompletionChunk(
                id=chat_id,
                created=int(time.time()),
                model=request.model,
                object="chat.completion.chunk",
                choices=[
                    Choice(
                        index=token_index,
                        finish_reason=None,
                        delta=ChoiceDelta(
                            content=token
                        )
                    )
                ]
            )
            yield f"data: {chunk.json()}\n\n"
            token_index += 1
            full_response += token

        # 发送结束标记
        finish_reason = 'stop'
        chunk = ChatCompletionChunk(
            id=chat_id,
            created=int(time.time()),
            model=request.model,
            object="chat.completion.chunk",
            choices=[
                Choice(
                    index=token_index,
                    finish_reason=finish_reason,
                    delta=ChoiceDelta()
                ),
            ],
        )
        yield f"data: {chunk.json()}\n\n"
        yield f"data: [DONE]\n\n"

    return StreamingResponse(wrapper_astream_search(), media_type="text/event-stream")

# API端点
@app.post("/api/chat_completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    模拟 webserver 的 /v1/chat/completions 端点
    """
    try:
        if not request.stream:
            return await handle_sync_response(request)
        else:
            return await handle_stream_response(request)
    except Exception as e:
        logger.error(msg=f"chat_completions error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 添加获取模型列表的端点，便于前端选择
@app.get("/api/models")
async def list_models():
    """
    返回可用的模型列表
    """
    models = [
        {"id": "local", "name": "局部查询 (Local)"},
        {"id": "global", "name": "全局查询 (Global)"},
        {"id": "drift", "name": "漂移查询 (Drift)"},
        {"id": "basic", "name": "基础查询 (Basic)"}
    ]
    return {"data": models}

# 启动服务
if __name__ == "__main__":
    import uvicorn
    
    # 确保静态文件目录存在
    os.makedirs(STATIC_DIR, exist_ok=True)
    
    # 启动服务
    port = 8088  # 使用不同端口避免与现有服务冲突
    host = "0.0.0.0"
    logger.info(f"启动 Webserver 测试服务 http://{host}:{port}")
    uvicorn.run("webserver_test:app", host=host, port=port, reload=True) 