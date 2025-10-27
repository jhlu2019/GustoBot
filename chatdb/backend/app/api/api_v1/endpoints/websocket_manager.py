# from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
# from fastapi.responses import JSONResponse
# from sqlalchemy.orm import Session
# from typing import Dict, List, Optional, Any
# import logging
# import asyncio
# import json
# from datetime import datetime
#
# from app.api import deps
# from app.services.websocket_manager import manager
# from app.services.agent_service import Text2SQLService, StreamResponseCollector, AGENT_NAMES
#
# router = APIRouter()
#
# # 设置日志记录器
# logger = logging.getLogger(__name__)
#
# @router.websocket("/connect")
# async def websocket_connect(websocket: WebSocket, user_id: Optional[str] = None):
#     """
#     建立WebSocket连接
#
#     Args:
#         websocket: WebSocket连接
#         user_id: 可选的用户ID
#     """
#     # 记录连接请求
#     client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "未知客户端"
#     logger.info(f"收到WebSocket连接请求: {client_info}, user_id={user_id}")
#
#     # 处理连接
#     async def message_handler(connection_id: str, data: Dict[str, Any]):
#         """处理接收到的消息"""
#         try:
#             # 检查消息格式
#             if "query" not in data:
#                 logger.warning(f"收到的消息缺少query字段: {data}")
#                 await manager.send_message(connection_id, {
#                     "type": "error",
#                     "content": "缺少查询参数'query'"
#                 })
#                 return
#
#             # 获取连接ID
#             connection_id_db = data.get("connectionId")
#
#             # 处理查询
#             query_text = data["query"]
#             logger.info(f"开始处理查询: '{query_text}', 连接ID: {connection_id_db}, WebSocket连接ID: {connection_id}")
#
#             # 创建Text2SQL服务
#             service = Text2SQLService()
#
#             # 创建响应收集器
#             collector = StreamResponseCollector()
#
#             # 设置消息回调函数
#             async def message_callback(ctx, message, message_ctx):
#                 try:
#                     # 转换为字典
#                     msg_dict = message.model_dump() if hasattr(message, "model_dump") else message.dict()
#
#                     # 根据消息来源确定区域
#                     region = "process"  # 默认
#                     if message.source == AGENT_NAMES["query_analyzer"] or message.source == AGENT_NAMES["schema_retriever"]:
#                         region = "analysis"
#                     elif message.source == AGENT_NAMES["sql_generator"]:
#                         region = "sql"
#                     elif message.source == AGENT_NAMES["sql_explainer"]:
#                         region = "explanation"
#                     elif message.source == AGENT_NAMES["sql_executor"]:
#                         region = "data"
#                     elif message.source == AGENT_NAMES["visualization_recommender"]:
#                         region = "visualization"
#                     elif message.source == "user_proxy":
#                         region = "user_proxy"
#
#                     # 添加区域和消息类型
#                     msg_dict["region"] = region
#                     msg_dict["type"] = "message"
#
#                     # 发送消息
#                     await manager.send_message(connection_id, msg_dict)
#
#                 except Exception as e:
#                     logger.error(f"消息回调处理错误: {str(e)}")
#                     import traceback
#                     logger.error(traceback.format_exc())
#
#             # 设置用户输入函数
#             async def user_input(prompt, cancellation_token):
#                 logger.info(f"等待用户输入: {prompt}")
#
#                 try:
#                     # 发送提示消息
#                     await manager.send_message(connection_id, {
#                         "type": "message",
#                         "source": "user_proxy",
#                         "content": prompt,
#                         "region": "analysis"
#                     })
#
#                     # 等待反馈
#                     feedback = await manager.get_feedback(connection_id, timeout=300.0)
#                     if feedback:
#                         logger.info(f"收到用户反馈: {feedback}")
#                         return feedback.get("content", "")
#                     else:
#                         logger.warning("等待用户反馈超时")
#                         return ""
#                 except Exception as e:
#                     logger.error(f"用户输入处理错误: {str(e)}")
#                     import traceback
#                     logger.error(traceback.format_exc())
#                     return ""
#
#             # 设置收集器回调
#             collector.set_callback(message_callback)
#             collector.set_user_input(user_input)
#
#             # 发送开始处理的消息
#             await manager.send_message(connection_id, {
#                 "type": "message",
#                 "source": "系统",
#                 "content": f"开始处理查询: {query_text}",
#                 "region": "process"
#             })
#
#             # 处理查询
#             try:
#                 logger.info(f"开始调用服务处理查询: '{query_text}', 连接ID: {connection_id_db}")
#
#                 # 调用服务处理查询
#                 await service.process_query(query_text, collector, connection_id_db)
#                 logger.info(f"查询处理完成: '{query_text}'")
#
#                 # 发送完成消息
#                 await manager.send_message(connection_id, {
#                     "type": "message",
#                     "source": "系统",
#                     "content": "查询处理完成",
#                     "region": "process",
#                     "is_final": True
#                 })
#             except Exception as e:
#                 logger.error(f"处理查询时出错: {str(e)}")
#                 import traceback
#                 logger.error(traceback.format_exc())
#
#                 # 发送错误消息
#                 await manager.send_message(connection_id, {
#                     "type": "error",
#                     "content": f"处理查询时出错: {str(e)}"
#                 })
#         except Exception as e:
#             logger.error(f"消息处理器出错: {str(e)}")
#             import traceback
#             logger.error(traceback.format_exc())
#
#             # 发送错误消息
#             await manager.send_message(connection_id, {
#                 "type": "error",
#                 "content": f"处理消息时出错: {str(e)}"
#             })
#
#     # 处理连接
#     await manager.handle_connection(websocket, user_id, message_handler)
#
# @router.get("/connections")
# async def get_connections():
#     """
#     获取所有活跃连接
#
#     Returns:
#         Dict: 连接信息
#     """
#     connections = {}
#     for connection_id in manager.active_connections:
#         connections[connection_id] = manager.get_connection_info(connection_id)
#
#     return JSONResponse({
#         "connections": connections,
#         "count": len(connections)
#     })
#
# @router.get("/connections/{connection_id}")
# async def get_connection(connection_id: str):
#     """
#     获取指定连接的信息
#
#     Args:
#         connection_id: 连接ID
#
#     Returns:
#         Dict: 连接信息
#     """
#     connection_info = manager.get_connection_info(connection_id)
#     if not connection_info:
#         raise HTTPException(status_code=404, detail=f"连接 {connection_id} 不存在")
#
#     return JSONResponse(connection_info)
#
# @router.delete("/connections/{connection_id}")
# async def close_connection(connection_id: str):
#     """
#     关闭指定连接
#
#     Args:
#         connection_id: 连接ID
#
#     Returns:
#         Dict: 操作结果
#     """
#     if connection_id not in manager.active_connections:
#         raise HTTPException(status_code=404, detail=f"连接 {connection_id} 不存在")
#
#     await manager.disconnect(connection_id)
#
#     return JSONResponse({
#         "status": "success",
#         "message": f"连接 {connection_id} 已关闭"
#     })
#
# @router.get("/users/{user_id}/connections")
# async def get_user_connections(user_id: str):
#     """
#     获取指定用户的所有连接
#
#     Args:
#         user_id: 用户ID
#
#     Returns:
#         Dict: 连接信息
#     """
#     connection_ids = manager.get_user_connections(user_id)
#     connections = {}
#
#     for connection_id in connection_ids:
#         connections[connection_id] = manager.get_connection_info(connection_id)
#
#     return JSONResponse({
#         "user_id": user_id,
#         "connections": connections,
#         "count": len(connections)
#     })
#
# @router.delete("/users/{user_id}/connections")
# async def close_user_connections(user_id: str):
#     """
#     关闭指定用户的所有连接
#
#     Args:
#         user_id: 用户ID
#
#     Returns:
#         Dict: 操作结果
#     """
#     connection_ids = manager.get_user_connections(user_id)
#     if not connection_ids:
#         raise HTTPException(status_code=404, detail=f"用户 {user_id} 没有活跃连接")
#
#     await manager.disconnect_user(user_id)
#
#     return JSONResponse({
#         "status": "success",
#         "message": f"用户 {user_id} 的所有连接已关闭",
#         "count": len(connection_ids)
#     })
#
# @router.post("/broadcast")
# async def broadcast_message(message: Dict[str, Any], exclude: Optional[List[str]] = None):
#     """
#     广播消息给所有连接
#
#     Args:
#         message: 消息内容
#         exclude: 排除的连接ID列表
#
#     Returns:
#         Dict: 操作结果
#     """
#     await manager.broadcast(message, exclude)
#
#     return JSONResponse({
#         "status": "success",
#         "message": "消息已广播",
#         "recipients": len(manager.active_connections) - (len(exclude) if exclude else 0)
#     })
#
# @router.post("/users/{user_id}/broadcast")
# async def broadcast_to_user(user_id: str, message: Dict[str, Any]):
#     """
#     广播消息给指定用户的所有连接
#
#     Args:
#         user_id: 用户ID
#         message: 消息内容
#
#     Returns:
#         Dict: 操作结果
#     """
#     connection_ids = manager.get_user_connections(user_id)
#     if not connection_ids:
#         raise HTTPException(status_code=404, detail=f"用户 {user_id} 没有活跃连接")
#
#     await manager.broadcast_to_user(user_id, message)
#
#     return JSONResponse({
#         "status": "success",
#         "message": f"消息已广播给用户 {user_id}",
#         "recipients": len(connection_ids)
#     })
#
# @router.get("/stats")
# async def get_stats():
#     """
#     获取WebSocket连接统计信息
#
#     Returns:
#         Dict: 统计信息
#     """
#     return JSONResponse(manager.get_stats())
#
# @router.post("/stats/reset")
# async def reset_stats():
#     """
#     重置WebSocket连接统计信息
#
#     Returns:
#         Dict: 操作结果
#     """
#     manager.reset_stats()
#
#     return JSONResponse({
#         "status": "success",
#         "message": "统计信息已重置"
#     })
