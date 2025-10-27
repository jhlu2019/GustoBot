# from autogen_core import CancellationToken, MessageContext, ClosureContext
# from fastapi import APIRouter
# import asyncio
# import logging
# import datetime
# from starlette.websockets import WebSocket, WebSocketDisconnect
#
# from app.schemas.text2sql import ResponseMessage
# from app.services.agent_service import Text2SQLService, StreamResponseCollector, AGENT_NAMES
#
# router = APIRouter()
#
# # 设置日志记录器
# logger = logging.getLogger(__name__)
#
# # 创建一个反馈消息队列
# feedback_queue = asyncio.Queue()
#
# @router.websocket("/websocket")
# async def text2sql_websocket(websocket: WebSocket):
#     """WebSocket端点处理Text2SQL查询
#
#     建立WebSocket连接，接收前端发送的查询请求，并将处理结果实时发送回前端
#     """
#     try:
#         # 记录详细的连接信息以便调试
#         client_info = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "未知客户端"
#         logger.info(f"收到WebSocket连接请求: {client_info}")
#         logger.info(f"请求头信息: {websocket.headers}")
#
#         # 记录请求详情以便调试
#         origin = websocket.headers.get("origin", "未知")
#         user_agent = websocket.headers.get("user-agent", "未知")
#         logger.info(f"请求来源: {origin}, 用户代理: {user_agent}")
#
#         # 接受所有WebSocket连接，不做任何限制
#         try:
#             await websocket.accept()
#             logger.info("WebSocket连接已建立成功")
#         except Exception as accept_error:
#             logger.error(f"WebSocket接受连接失败: {str(accept_error)}")
#             import traceback
#             logger.error(traceback.format_exc())
#             return
#
#         # 发送一条欢迎消息
#         try:
#             await websocket.send_json({
#                 "type": "message",
#                 "source": "系统",
#                 "content": "WebSocket连接已建立，可以开始查询",
#                 "region": "process"
#             })
#             logger.info("已发送欢迎消息")
#         except Exception as welcome_error:
#             logger.error(f"发送欢迎消息失败: {str(welcome_error)}")
#             import traceback
#             logger.error(traceback.format_exc())
#             # 继续执行，不因为欢迎消息失败而中断连接
#         # 循环处理消息
#         while True:
#             try:
#                 # 接收消息
#                 try:
#                     data = await websocket.receive_json()
#                     logger.info(f"收到查询: {data}")
#                 except Exception as receive_error:
#                     logger.error(f"接收消息失败: {str(receive_error)}")
#                     if isinstance(receive_error, WebSocketDisconnect):
#                         logger.info("客户端断开连接")
#                         break
#                     else:
#                         import traceback
#                         logger.error(traceback.format_exc())
#                         # 尝试发送错误消息
#                         try:
#                             await websocket.send_json({
#                                 "type": "error",
#                                 "content": f"接收消息失败: {str(receive_error)}"
#                             })
#                             continue
#                         except Exception as send_error:
#                             logger.error(f"无法发送错误响应: {str(send_error)}")
#                             break
#
#                 # 检查是否是心跳消息
#                 if data.get("type") == "heartbeat":
#                     logger.debug("收到心跳消息")
#                     # 响应心跳消息
#                     try:
#                         await websocket.send_json({
#                             "type": "heartbeat_response",
#                             "timestamp": str(datetime.datetime.now())
#                         })
#                     except Exception as heartbeat_error:
#                         logger.error(f"发送心跳响应失败: {str(heartbeat_error)}")
#                     continue  # 跳过普通消息处理流程
#
#                 # 检查是否是反馈消息
#                 if data.get("is_feedback"):
#                     # 如果是反馈消息，放入队列供user_input函数获取
#                     await feedback_queue.put(data)
#                     logger.info("检测到用户反馈消息，已放入队列")
#                     continue  # 跳过普通消息处理流程
#
#                 # 检查消息格式
#                 if "query" not in data:
#                     logger.warning(f"收到的消息缺少query字段: {data}")
#                     await websocket.send_json({
#                         "type": "error",
#                         "content": "缺少查询参数'query'"
#                     })
#                     continue
#
#                 # 获取连接ID
#                 connection_id = data.get("connectionId")
#                 if connection_id:
#                     logger.info(f"收到连接ID: {connection_id}")
#                 else:
#                     logger.warning("未指定连接ID，将使用默认连接")
#
#                 # 处理查询
#                 query_text = data["query"]
#                 logger.info(f"开始处理查询: '{query_text}', 连接ID: {connection_id}")
#                 await process_websocket_query(query_text, websocket, connection_id)
#                 logger.info(f"查询处理完成: '{query_text}'")
#
#             except WebSocketDisconnect as disconnect_error:
#                 logger.info(f"客户端断开连接: {str(disconnect_error)}")
#                 break
#             except Exception as msg_error:
#                 logger.error(f"处理消息时出错: {str(msg_error)}")
#                 import traceback
#                 logger.error(traceback.format_exc())
#
#                 # 尝试发送错误消息
#                 try:
#                     error_message = {
#                         "type": "error",
#                         "content": f"处理查询时出错: {str(msg_error)}"
#                     }
#                     logger.info(f"发送错误消息: {error_message}")
#                     await websocket.send_json(error_message)
#                 except Exception as send_error:
#                     logger.error(f"无法发送错误响应: {str(send_error)}")
#                     # 检查是否是因为连接已关闭
#                     if isinstance(send_error, WebSocketDisconnect) or "connection closed" in str(send_error).lower():
#                         logger.info("检测到WebSocket连接已关闭")
#                         break
#                     # 其他错误类型也中断处理
#                     break
#     except Exception as conn_error:
#         logger.error(f"WebSocket连接处理出错: {str(conn_error)}")
#         import traceback
#         logger.error(traceback.format_exc())
#         return
#
# # 处理查询的独立函数，供WebSocket调用
# async def process_websocket_query(query: str, websocket: WebSocket, connection_id: int = None):
#     """处理Text2SQL查询并通过WebSocket发送结果
#
#     Args:
#         query: 自然语言查询
#         websocket: WebSocket连接
#         connection_id: 数据库连接ID，可选
#     """
#     try:
#         # 创建Text2SQL服务
#         # 不需要传递数据库类型，因为服务会根据连接ID自动获取
#         service = Text2SQLService()
#         collector = StreamResponseCollector()
#
#         # 设置消息回调函数，将消息发送到WebSocket
#         async def message_callback(ctx: ClosureContext, message: ResponseMessage, message_ctx: MessageContext) -> None:
#             try:
#                 # 转换为字典，添加消息类型
#                 msg_dict = message.model_dump()
#
#                 # 根据消息来源确定区域
#                 region = "process"  # 默认
#                 if message.source == AGENT_NAMES["query_analyzer"] or message.source == AGENT_NAMES["schema_retriever"]:
#                     region = "analysis"
#                 elif message.source == AGENT_NAMES["sql_generator"]:
#                     region = "sql"
#                 elif message.source == AGENT_NAMES["sql_explainer"]:
#                     region = "explanation"
#                 elif message.source == AGENT_NAMES["sql_executor"]:
#                     region = "data"
#                 elif message.source == AGENT_NAMES["visualization_recommender"]:
#                     region = "visualization"
#                 elif message.source == "user_proxy":
#                     region = "user_proxy"
#
#                 msg_dict["region"] = region
#                 msg_dict["type"] = "message"
#
#                 # 截取消息内容前50个字符用于日志记录
#                 content_preview = message.content[:50] + "..." if len(message.content) > 50 else message.content
#                 logger.info(f"发送WebSocket消息: 来源={message.source}, 区域={region}, 内容={content_preview}")
#
#                 # 发送消息到WebSocket
#                 try:
#                     await websocket.send_json(msg_dict)
#                 except Exception as send_error:
#                     logger.error(f"发送WebSocket消息失败: {str(send_error)}")
#                     import traceback
#                     logger.error(traceback.format_exc())
#                     # 如果是WebSocketDisconnect错误或连接关闭错误，抛出异常以中断处理
#                     if isinstance(send_error, WebSocketDisconnect) or "connection closed" in str(send_error).lower() or "going away" in str(send_error).lower():
#                         logger.info("检测到WebSocket连接已关闭或客户端断开")
#                         raise WebSocketDisconnect(code=1001)
#
#             except Exception as e:
#                 logger.error(f"消息回调处理错误: {str(e)}")
#                 import traceback
#                 logger.error(traceback.format_exc())
#                 # 如果是WebSocketDisconnect错误或连接关闭错误，抛出异常以中断处理
#                 if isinstance(e, WebSocketDisconnect) or "connection closed" in str(e).lower() or "going away" in str(e).lower():
#                     logger.info("检测到WebSocket连接已关闭或客户端断开")
#                     raise WebSocketDisconnect(code=1001)
#
#         async def user_input(prompt: str, cancellation_token: CancellationToken | None) -> str:
#             global feedback_queue
#             logger.info(f"等待用户输入: {prompt}")
#
#             try:
#                 # 发送提示消息到前端
#                 try:
#                     await websocket.send_json({
#                         "type": "message",
#                         "source": "user_proxy",
#                         "content": prompt,
#                         "region": "analysis"
#                     })
#                 except Exception as send_error:
#                     logger.error(f"发送用户提示消息失败: {str(send_error)}")
#                     # 如果是连接关闭错误，抛出异常
#                     if isinstance(send_error, WebSocketDisconnect) or "connection closed" in str(send_error).lower() or "going away" in str(send_error).lower():
#                         logger.info("检测到WebSocket连接已关闭或客户端断开")
#                         raise WebSocketDisconnect(code=1001)
#                     # 如果发送失败但不是连接关闭，返回默认值
#                     return "同意"
#
#                 # 设置超时时间，防止无限期等待
#                 try:
#                     # 等待反馈队列中的消息，设置60秒超时
#                     data = await asyncio.wait_for(feedback_queue.get(), timeout=120)
#                     logger.info(f"收到用户反馈: {data}")
#                     # 解析消息
#                     return data.get("content", "")
#                 except asyncio.TimeoutError:
#                     logger.warning("等待用户反馈超时，使用默认值继续")
#                     return "同意"  # 超时时使用默认值
#             except WebSocketDisconnect as ws_error:
#                 logger.error(f"WebSocket连接已断开: {str(ws_error)}")
#                 # 重新抛出异常，以便上层函数处理
#                 raise
#             except Exception as input_error:
#                 logger.error(f"用户输入处理错误: {str(input_error)}")
#                 import traceback
#                 logger.error(traceback.format_exc())
#                 # 如果出错，返回默认值
#                 return "同意"
#
#         # 设置收集器回调
#         collector.set_callback(message_callback)
#         collector.set_user_input(user_input)
#
#         # 发送开始处理的消息
#         try:
#             start_message = {
#                 "type": "message",
#                 "source": "系统",
#                 "content": f"开始处理查询: {query}",
#                 "region": "process"
#             }
#             logger.info(f"发送开始处理消息: {start_message}")
#             await websocket.send_json(start_message)
#         except Exception as start_error:
#             logger.error(f"发送开始处理消息失败: {str(start_error)}")
#             import traceback
#             logger.error(traceback.format_exc())
#             # 如果是WebSocketDisconnect错误或连接关闭错误，抛出异常以中断处理
#             if isinstance(start_error, WebSocketDisconnect) or "connection closed" in str(start_error).lower() or "going away" in str(start_error).lower():
#                 logger.info("检测到WebSocket连接已关闭或客户端断开")
#                 raise WebSocketDisconnect(code=1001)
#
#         # 处理查询
#         try:
#             logger.info(f"开始调用服务处理查询: '{query}', 连接ID: {connection_id}")
#             # 将连接ID打印到日志中
#             if connection_id:
#                 logger.info(f"使用数据库连接ID: {connection_id} 处理查询")
#
#             # 调用服务处理查询，传递连接ID
#             await service.process_query(query, collector, connection_id)
#             logger.info(f"查询处理完成: '{query}'")
#
#             # 发送完成消息
#             try:
#                 complete_message = {
#                     "type": "message",
#                     "source": "系统",
#                     "content": f"查询处理完成",
#                     "region": "process",
#                     "is_final": True
#                 }
#                 logger.info(f"发送完成消息: {complete_message}")
#                 await websocket.send_json(complete_message)
#             except Exception as complete_error:
#                 logger.error(f"发送完成消息失败: {str(complete_error)}")
#                 import traceback
#                 logger.error(traceback.format_exc())
#
#         except Exception as process_error:
#             logger.error(f"查询处理错误: {str(process_error)}")
#             import traceback
#             logger.error(traceback.format_exc())
#
#             # 发送错误消息
#             try:
#                 error_message = {
#                     "type": "error",
#                     "content": f"处理查询时出错: {str(process_error)}"
#                 }
#                 logger.info(f"发送错误消息: {error_message}")
#                 await websocket.send_json(error_message)
#             except Exception as error_send_error:
#                 logger.error(f"发送错误消息失败: {str(error_send_error)}")
#                 # 如果是WebSocketDisconnect错误或连接关闭错误，抛出异常以中断处理
#                 if isinstance(error_send_error, WebSocketDisconnect) or "connection closed" in str(error_send_error).lower() or "going away" in str(error_send_error).lower():
#                     logger.info("检测到WebSocket连接已关闭或客户端断开")
#                     raise WebSocketDisconnect(code=1001)
#
#     except WebSocketDisconnect as disconnect_error:
#         logger.warning(f"WebSocket连接已断开，中止处理查询: {str(disconnect_error)}")
#         # 返回而不抛出异常，因为这是预期的行为
#         return
#     except Exception as e:
#         logger.error(f"WebSocket查询处理异常: {str(e)}")
#         import traceback
#         logger.error(traceback.format_exc())
#         try:
#             error_message = {
#                 "type": "error",
#                 "content": f"处理查询时发生错误: {str(e)}"
#             }
#             logger.info(f"发送异常错误消息: {error_message}")
#             await websocket.send_json(error_message)
#         except Exception as final_error:
#             logger.error(f"发送最终错误消息失败: {str(final_error)}")
#             # 如果是连接关闭错误，只记录日志不重新抛出
#             if isinstance(final_error, WebSocketDisconnect) or "connection closed" in str(final_error).lower() or "going away" in str(final_error).lower():
#                 logger.info("检测到WebSocket连接已关闭或客户端断开，不再尝试发送消息")
