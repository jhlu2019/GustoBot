import uvicorn
import logging
import sys
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.api.api_v1.api import api_router
from app.core.config import settings

# 注释掉过度的日志过滤，保持正常日志显示
# 这样我们可以看到完整的连接信息来诊断问题

app = FastAPI(
    title="ChatDB API",
    description="Text2SQL API for intelligent database querying",
    version="0.1.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

# 添加对前端开发服务器请求的处理，避免404日志
@app.get("/__webpack_hmr")
async def webpack_hmr():
    """处理Webpack热重载请求，避免404日志"""
    return {"status": "not_supported", "message": "Webpack HMR not supported on backend"}

@app.get("/socket.io/")
async def socket_io_fallback():
    """处理Socket.IO请求，避免403日志"""
    return {"status": "not_supported", "message": "Socket.IO not configured on this server"}

@app.websocket("/socket.io/")
async def socket_io_websocket(websocket: WebSocket):
    """处理Socket.IO WebSocket连接，避免403日志"""
    try:
        await websocket.accept()
        await websocket.send_json({
            "status": "not_supported",
            "message": "Socket.IO WebSocket not configured on this server"
        })
        await websocket.close(code=1000, reason="Not supported")
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# 添加通用的Socket.IO WebSocket处理器（带查询参数）
@app.websocket("/socket.io/{path:path}")
async def socket_io_websocket_with_params(websocket: WebSocket, path: str):
    """处理带参数的Socket.IO WebSocket连接"""
    try:
        await websocket.accept()
        await websocket.send_json({
            "status": "not_supported",
            "message": f"Socket.IO WebSocket path '{path}' not configured on this server"
        })
        await websocket.close(code=1000, reason="Not supported")
    except WebSocketDisconnect:
        pass
    except Exception:
        pass

# 强制重新加载 - 修复路由问题

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, timeout_keep_alive=120)  # 120秒的keep-alive超时
