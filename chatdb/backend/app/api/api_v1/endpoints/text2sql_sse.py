from autogen_core import CancellationToken, MessageContext, ClosureContext
from fastapi import APIRouter, Request, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import logging
import uuid
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.schemas.text2sql import ResponseMessage
from app.services.agent_orchestrator import AgentOrchestrator
from app.agents.base import StreamResponseCollector
from app.agents.types import AGENT_NAMES
from sqlalchemy.orm import Session
from app.api import deps
from app import crud
from app.schemas.chat_history import SaveChatHistoryRequest

router = APIRouter()

# 设置日志记录器
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """SSE健康检查端点"""
    return {"status": "ok", "service": "text2sql-sse", "timestamp": datetime.now().isoformat()}

# 会话存储
active_sessions: Dict[str, Dict[str, Any]] = {}

# 消息队列存储
message_queues: Dict[str, asyncio.Queue] = {}

# 反馈队列存储
feedback_queues: Dict[str, asyncio.Queue] = {}

# 会话超时（秒）
SESSION_TIMEOUT = 3600  # 1小时


async def cleanup_session(session_id: str, delay: int = SESSION_TIMEOUT):
    """
    在指定延迟后清理会话资源
    """
    await asyncio.sleep(delay)
    if session_id in active_sessions:
        logger.info(f"清理过期会话: {session_id}")
        active_sessions.pop(session_id, None)
        message_queues.pop(session_id, None)
        feedback_queues.pop(session_id, None)


@router.get("/stream")
async def stream_response(
    request: Request,
    background_tasks: BackgroundTasks,
    query: Optional[str] = None,
    connection_id: Optional[int] = None,
    session_id: Optional[str] = None,
    direct_process: bool = False,
    user_feedback_enabled: bool = False,
    db: Session = Depends(deps.get_db)
):
    """
    SSE端点，用于流式返回Text2SQL处理结果

    - 如果提供了query参数，则开始新的处理流程
    - 如果提供了session_id参数，则继续现有会话的流
    - 如果两者都提供，则使用session_id并忽略query
    """
    # 记录请求参数
    logger.info(f"SSE请求参数: query={query}, connection_id={connection_id}, session_id={session_id}, user_feedback_enabled={user_feedback_enabled}")
    logger.info(f"SSE请求头信息: {request.headers}")

    # 检查是否需要创建新会话
    create_new_session = False

    if not session_id:
        # 没有提供session_id，必须有query才能创建新会话
        if not query:
            logger.error("缺少必要参数: query或session_id")
            raise HTTPException(status_code=400, detail="必须提供query或session_id参数")
        create_new_session = True
        session_id = str(uuid.uuid4())
        logger.info(f"未提供session_id，创建新会话: {session_id}")
    else:
        # 提供了session_id，检查是否存在
        if session_id not in active_sessions:
            # 会话不存在，如果有query就创建新会话，否则报错
            if query:
                create_new_session = True
                logger.info(f"会话 {session_id} 不存在，但提供了query，将创建新会话")
            else:
                logger.error(f"会话 {session_id} 不存在且未提供query")
                raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或已过期")
        else:
            logger.info(f"继续现有会话: {session_id}")
            # 更新最后活动时间
            active_sessions[session_id]["last_activity"] = datetime.now().isoformat()

    # 如果需要创建新会话
    if create_new_session:
        logger.info(f"创建新会话: {session_id}, 查询: {query}")

        # 创建消息队列
        message_queue = asyncio.Queue()
        message_queues[session_id] = message_queue
        logger.info(f"创建消息队列: {session_id}")

        # 创建反馈队列
        feedback_queue = asyncio.Queue()
        feedback_queues[session_id] = feedback_queue
        logger.info(f"创建反馈队列: {session_id}")

        # 存储会话信息
        active_sessions[session_id] = {
            "query": query,
            "connection_id": connection_id,
            "user_feedback_enabled": user_feedback_enabled,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "status": "initializing"
        }
        logger.info(f"存储会话信息: {session_id}")

        # 设置会话超时清理
        background_tasks.add_task(cleanup_session, session_id)
        logger.info(f"添加会话清理任务: {session_id}")

        # 先尝试发送一条初始消息到队列
        try:
            await message_queue.put({
                "type": "message",
                "source": "系统",
                "content": "正在启动查询处理...",
                "region": "process",
                "is_final": False,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"发送初始消息到队列: {session_id}")

            # 检查是否直接处理查询
            if direct_process:
                logger.info(f"将直接处理查询(非后台任务): {session_id}, 查询: {query}")

                # 发送消息通知前端
                await message_queue.put({
                    "type": "message",
                    "source": "系统",
                    "content": "直接处理查询中...",
                    "region": "process",
                    "is_final": False,
                    "timestamp": datetime.now().isoformat()
                })

                # 直接启动异步任务，而不是使用background_tasks
                # 创建一个异步任务来处理查询
                asyncio.create_task(
                    process_query_task(query, session_id, connection_id, user_feedback_enabled, db)
                )

                logger.info(f"直接异步任务已启动: {session_id}")
            else:
                # 启动处理任务
                logger.info(f"正在启动异步查询处理任务: {session_id}, 查询: {query}, 连接ID: {connection_id}")
                # 使用asyncio.create_task而不是background_tasks
                asyncio.create_task(
                    process_query_task(query, session_id, connection_id, user_feedback_enabled, db)
                )
                logger.info(f"异步查询处理任务已启动: {session_id}")

                # 发送任务启动消息
                await message_queue.put({
                    "type": "message",
                    "source": "系统",
                    "content": "查询处理任务已启动，请等待结果...",
                    "region": "process",
                    "is_final": False,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"发送任务启动消息到队列: {session_id}")
        except Exception as e:
            logger.error(f"启动查询处理任务失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    # 返回SSE响应
    response = EventSourceResponse(
        event_generator(session_id, request),
        media_type="text/event-stream"
    )

    # 添加必要的响应头
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    response.headers["X-Accel-Buffering"] = "no"  # 禁用Nginx缓冲

    return response


async def event_generator(session_id: str, request: Request):
    """
    生成SSE事件流
    """
    # 记录开始生成事件流
    print(f"\n\n开始生成事件流: 会话ID={session_id}\n\n")
    logger.info(f"开始生成事件流: 会话ID={session_id}")

    # 发送会话初始化事件
    init_data = json.dumps({
        "session_id": session_id,
        "status": "connected"
    })
    logger.info(f"发送初始化事件: {init_data}")
    yield f"event: session\nid: 0\ndata: {init_data}\n\n"

    # 获取消息队列
    message_queue = message_queues.get(session_id)
    if not message_queue:
        error_data = json.dumps({
            "error": "会话队列不存在"
        })
        logger.error(f"会话队列不存在: {session_id}")
        yield f"event: error\nid: error-1\ndata: {error_data}\n\n"
        return

    # 消息ID计数器
    message_id = 1

    try:
        # 持续从队列获取消息并发送
        while True:
            # 检查客户端是否断开连接
            if await request.is_disconnected():
                logger.info(f"客户端断开连接: {session_id}")
                break

            # 尝试从队列获取消息（非阻塞）
            try:
                # 使用较短的超时时间，确保更频繁地检查连接状态
                message = await asyncio.wait_for(message_queue.get(), timeout=0.5)

                # 更新会话最后活动时间
                active_sessions[session_id]["last_activity"] = datetime.now().isoformat()

                # 确定事件类型
                event_type = message.get("type", "message")

                # 将消息转换为JSON字符串
                message_json = json.dumps(message)

                # 记录发送的消息（截断长消息以避免日志过大）
                content_preview = message.get("content", "")
                if content_preview and len(content_preview) > 100:
                    content_preview = content_preview[:100] + "..."

                print(f"\n\n发送事件: id={message_id}, type={event_type}, region={message.get('region', 'unknown')}, content={content_preview}\n\n")
                logger.info(f"发送事件: id={message_id}, type={event_type}, region={message.get('region', 'unknown')}, content={content_preview}")

                # 使用正确的SSE格式发送消息
                yield f"event: {event_type}\nid: {message_id}\ndata: {message_json}\n\n"

                message_id += 1

                # 如果是最终消息，结束流
                # if message.get("is_final", False):
                #     logger.info(f"会话 {session_id} 处理完成，发送最终消息")
                #     active_sessions[session_id]["status"] = "completed"
                #
                #     # 发送一个额外的关闭事件
                #     close_data = json.dumps({
                #         "message": "流已关闭",
                #         "is_final": True
                #     })
                #     yield f"event: close\nid: close-{message_id}\ndata: {close_data}\n\n"
                #     break

            except asyncio.TimeoutError:
                # 发送保持连接的消息
                ping_data = json.dumps({"timestamp": datetime.now().isoformat()})
                logger.debug(f"发送ping事件: id=ping-{message_id}")
                yield f"event: ping\nid: ping-{message_id}\ndata: {ping_data}\n\n"
                message_id += 1
                continue

    except Exception as e:
        logger.error(f"生成事件流时出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        error_data = json.dumps({
            "error": f"生成事件流时出错: {str(e)}"
        })
        yield f"event: error\nid: error-{message_id}\ndata: {error_data}\n\n"

    # 发送关闭事件
    close_data = json.dumps({
        "message": "流已关闭"
    })
    logger.info(f"事件流结束: 会话ID={session_id}")
    yield f"event: close\nid: close-{message_id}\ndata: {close_data}\n\n"


async def process_query_task(
    query: str,
    session_id: str,
    connection_id: Optional[int] = None,
    user_feedback_enabled: bool = False,
    db: Session = None
):
    """
    处理查询的后台任务
    """
    print(f"\n\n===== 开始执行 process_query_task: 会话ID={session_id}, 查询={query}, 连接ID={connection_id}, 用户反馈={user_feedback_enabled} =====\n\n")
    logger.info(f"===== 开始执行 process_query_task: 会话ID={session_id}, 查询={query}, 连接ID={connection_id}, 用户反馈={user_feedback_enabled} =====")

    try:
        # 获取消息队列
        message_queue = message_queues.get(session_id)
        if not message_queue:
            logger.error(f"会话 {session_id} 的消息队列不存在")
            return

        # 获取反馈队列
        feedback_queue = feedback_queues.get(session_id)
        logger.info(f"process_query_task: 成功获取反馈队列: {session_id}")

        # 更新会话状态
        active_sessions[session_id]["status"] = "processing"


        # 创建智能体编排器
        orchestrator = AgentOrchestrator()
        # 创建响应收集器
        collector = StreamResponseCollector()

        # 设置消息回调函数
        async def message_callback(ctx: ClosureContext, message: ResponseMessage, message_ctx: MessageContext) -> None:
            try:
                # 转换为字典
                msg_dict = message.model_dump() if hasattr(message, "model_dump") else message.dict()

                # 根据消息来源确定区域
                region = "process"  # 默认
                if (message.source == AGENT_NAMES.get("query_analyzer") or
                    message.source == AGENT_NAMES.get("schema_retriever") or
                    message.source == "查询分析智能体" or
                    message.source == "表结构检索智能体"):
                    region = "analysis"
                elif (message.source == AGENT_NAMES.get("sql_generator") or
                      message.source == "SQL生成智能体" or
                      message.source == "混合SQL生成智能体"):
                    region = "sql"
                elif (message.source == AGENT_NAMES.get("sql_explainer") or
                      message.source == "SQL解释智能体"):
                    region = "explanation"
                elif (message.source == AGENT_NAMES.get("sql_executor") or
                      message.source == "SQL执行智能体"):
                    region = "data"
                elif (message.source == AGENT_NAMES.get("visualization_recommender") or
                      message.source == "可视化推荐智能体"):
                    region = "visualization"
                elif message.source == "user_proxy":
                    region = "user_proxy"

                # 添加区域和消息类型
                msg_dict["region"] = region
                msg_dict["type"] = "message"

                # 添加唯一ID，确保消息不重复
                msg_dict["message_id"] = f"{session_id}-{region}-{uuid.uuid4()}"

                # 添加时间戳
                msg_dict["timestamp"] = datetime.now().isoformat()

                # 处理包含结果数据的消息
                if message.result and message.is_final:
                    logger.info(f"处理包含结果数据的最终消息: {list(message.result.keys())}")
                    # 如果消息包含结果数据，需要发送专门的结果消息
                    result_data = message.result

                    # 根据结果数据类型发送到对应区域
                    if "sql" in result_data:
                        # SQL结果
                        await message_queue.put({
                            "type": "result",
                            "source": message.source,
                            "content": result_data["sql"],
                            "region": "sql",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-sql-result-{uuid.uuid4()}"
                        })
                        logger.info(f"发送SQL结果到队列: {result_data['sql'][:50]}...")

                    if "results" in result_data:
                        # 数据结果
                        await message_queue.put({
                            "type": "result",
                            "source": message.source,
                            "content": json.dumps(result_data["results"], ensure_ascii=False),
                            "region": "data",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-data-result-{uuid.uuid4()}"
                        })
                        logger.info(f"发送数据结果到队列: {len(result_data['results'])} 条记录")

                    if "explanation" in result_data:
                        # 解释结果
                        await message_queue.put({
                            "type": "result",
                            "source": message.source,
                            "content": result_data["explanation"],
                            "region": "explanation",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-explanation-result-{uuid.uuid4()}"
                        })
                        logger.info(f"发送解释结果到队列: {result_data['explanation'][:50]}...")

                    if "visualization_type" in result_data or "visualization_config" in result_data:
                        # 可视化结果
                        viz_data = {
                            "type": result_data.get("visualization_type", "bar"),
                            "config": result_data.get("visualization_config", {})
                        }
                        await message_queue.put({
                            "type": "result",
                            "source": message.source,
                            "content": json.dumps(viz_data, ensure_ascii=False),
                            "region": "visualization",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-visualization-result-{uuid.uuid4()}"
                        })
                        logger.info(f"发送可视化结果到队列: {viz_data['type']}")

                # 发送原始消息到队列
                await message_queue.put(msg_dict)

            except Exception as e:
                logger.error(f"消息回调处理错误: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())

        # 设置用户输入回调函数
        async def user_input_callback(prompt: str, cancellation_token: CancellationToken | None) -> str:
            try:
                # 发送反馈请求消息
                await message_queue.put({
                    "type": "feedback_request",
                    "source": "系统",
                    "content": prompt,
                    "region": "user_proxy",
                    "is_final": False,
                    "timestamp": datetime.now().isoformat()
                })

                # 等待用户反馈
                logger.info(f"等待用户反馈: {session_id}")
                feedback = await feedback_queue.get()
                logger.info(f"收到用户反馈: {feedback}")

                # 返回用户反馈内容
                return feedback.get("content", "")

            except Exception as e:
                logger.error(f"用户输入回调错误: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return "取消操作"

        # 设置收集器回调
        logger.info(f"process_query_task: 设置消息回调函数: 会话ID={session_id}")

        # 设置回调函数（使用新架构的方法）
        try:
            logger.info(f"process_query_task: 设置回调函数: {session_id}")
            collector.set_callback(message_callback)
            collector.set_user_input(user_input_callback)
            logger.info(f"process_query_task: 回调函数设置成功: {session_id}")
        except Exception as e:
            logger.error(f"process_query_task: 设置回调函数失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

        # 发送消息确认回调设置成功
        callback_message = {
            "type": "message",
            "source": "系统",
            "content": "消息回调设置成功，开始处理查询...",
            "region": "process",
            "is_final": False,
            "timestamp": datetime.now().isoformat()
        }

        await message_queue.put(callback_message)

        # 处理查询
        logger.info(f"process_query_task: 开始处理查询: {query}, 会话ID: {session_id}, 连接ID: {connection_id}")
        try:
            result = await orchestrator.process_query(query, collector, connection_id, user_feedback_enabled)
            logger.info(f"process_query_task: 查询处理完成: {session_id}")

            # 发送最终结果
            if result:
                # 转换为字典
                result_dict = result.model_dump() if hasattr(result, "model_dump") else result.dict()
                logger.info(f"process_query_task: 已获取最终结果: {session_id}")

                # 分别发送各个区域的最终结果
                try:
                    # 发送SQL结果
                    if "sql" in result_dict and result_dict["sql"]:
                        await message_queue.put({
                            "type": "result",
                            "source": "系统",
                            "content": result_dict["sql"],
                            "region": "sql",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-final-sql-{uuid.uuid4()}"
                        })
                        logger.info(f"process_query_task: SQL结果已发送: {session_id}")

                    # 发送解释结果
                    if "explanation" in result_dict and result_dict["explanation"]:
                        await message_queue.put({
                            "type": "result",
                            "source": "系统",
                            "content": result_dict["explanation"],
                            "region": "explanation",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-final-explanation-{uuid.uuid4()}"
                        })
                        logger.info(f"process_query_task: 解释结果已发送: {session_id}")

                    # 发送数据结果
                    if "results" in result_dict and result_dict["results"]:
                        await message_queue.put({
                            "type": "result",
                            "source": "系统",
                            "content": json.dumps(result_dict["results"], ensure_ascii=False),
                            "region": "data",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-final-data-{uuid.uuid4()}"
                        })
                        logger.info(f"process_query_task: 数据结果已发送: {session_id}")

                    # 发送可视化结果
                    if ("visualization_type" in result_dict and result_dict["visualization_type"]) or \
                       ("visualization_config" in result_dict and result_dict["visualization_config"]):
                        viz_data = {
                            "type": result_dict.get("visualization_type", "bar"),
                            "config": result_dict.get("visualization_config", {})
                        }
                        await message_queue.put({
                            "type": "result",
                            "source": "系统",
                            "content": json.dumps(viz_data, ensure_ascii=False),
                            "region": "visualization",
                            "is_final": True,
                            "timestamp": datetime.now().isoformat(),
                            "message_id": f"{session_id}-final-visualization-{uuid.uuid4()}"
                        })
                        logger.info(f"process_query_task: 可视化结果已发送: {session_id}")

                except Exception as e:
                    logger.error(f"process_query_task: 发送最终结果时出错: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())

                # 发送完整的最终结果消息（保持向后兼容）
                final_result_message = {
                    "type": "final_result",
                    "result": result_dict,
                    "is_final": True,
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"process_query_task: 发送完整最终结果消息: {session_id}")
                await message_queue.put(final_result_message)
                logger.info(f"process_query_task: 完整最终结果消息已发送: {session_id}")
            else:
                logger.warning(f"process_query_task: 未获取到最终结果: {session_id}")

            # 发送处理完成消息
            complete_message = {
                "type": "message",
                "source": "系统",
                "content": "查询处理完成",
                "region": "process",
                "is_final": True,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"process_query_task: 发送处理完成消息: {session_id}")
            await message_queue.put(complete_message)
            logger.info(f"process_query_task: 处理完成消息已发送: {session_id}")

            # 更新会话状态
            active_sessions[session_id]["status"] = "completed"
            logger.info(f"process_query_task: 会话状态已更新为'completed': {session_id}")

            logger.info(f"===== process_query_task 执行完成: 会话ID={session_id} =====")
        except Exception as query_error:
            logger.error(f"process_query_task: 处理查询时出错: {str(query_error)}")
            import traceback
            logger.error(traceback.format_exc())

            # 发送错误消息
            error_message = {
                "type": "error",
                "source": "系统",
                "content": f"处理查询时出错: {str(query_error)}",
                "region": "process",
                "is_final": True,
                "timestamp": datetime.now().isoformat()
            }

            try:
                await message_queue.put(error_message)
                logger.info(f"process_query_task: 错误消息已发送: {session_id}")
            except Exception as e:
                logger.error(f"process_query_task: 发送错误消息失败: {str(e)}")

    except Exception as e:
        logger.error(f"process_query_task: 处理查询任务出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

        # 发送错误消息
        try:
            error_message = {
                "type": "error",
                "source": "系统",
                "content": f"处理查询时出错: {str(e)}",
                "region": "process",
                "is_final": True,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"process_query_task: 尝试发送全局错误消息: {session_id}")
            await message_queue.put(error_message)
            logger.info(f"process_query_task: 全局错误消息已发送: {session_id}")
        except Exception as send_error:
            logger.error(f"process_query_task: 发送错误消息失败: {str(send_error)}")

        # 更新会话状态
        try:
            active_sessions[session_id]["status"] = "error"
            logger.info(f"process_query_task: 会话状态已更新为'error': {session_id}")
        except Exception as status_error:
            logger.error(f"process_query_task: 更新会话状态失败: {str(status_error)}")

        logger.info(f"===== process_query_task 执行失败: 会话ID={session_id} =====")


@router.post("/feedback/{session_id}")
async def send_feedback(
    session_id: str,
    feedback: Dict[str, Any]
):
    """
    发送用户反馈到指定会话
    """
    # 验证会话是否存在
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或已过期")

    # 获取反馈队列
    feedback_queue = feedback_queues.get(session_id)
    if not feedback_queue:
        raise HTTPException(status_code=500, detail=f"会话 {session_id} 的反馈队列不存在")

    # 添加时间戳
    feedback["timestamp"] = datetime.now().isoformat()

    # 放入反馈队列
    await feedback_queue.put(feedback)

    # 更新会话最后活动时间
    active_sessions[session_id]["last_activity"] = datetime.now().isoformat()

    return JSONResponse({
        "status": "success",
        "message": "反馈已发送",
        "session_id": session_id
    })


@router.get("/sessions")
async def list_sessions():
    """
    列出所有活动会话
    """
    return JSONResponse({
        "sessions": active_sessions
    })


@router.get("/sessions/{session_id}")
async def get_session(session_id: str):
    """
    获取指定会话的信息
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或已过期")

    return JSONResponse(active_sessions[session_id])


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    删除指定会话
    """
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在或已过期")

    # 删除会话资源
    active_sessions.pop(session_id, None)
    message_queues.pop(session_id, None)
    feedback_queues.pop(session_id, None)

    return JSONResponse({
        "status": "success",
        "message": f"会话 {session_id} 已删除"
    })


@router.post("/save-history")
async def save_session_history(
    history_request: SaveChatHistoryRequest,
    db: Session = Depends(deps.get_db)
):
    """
    保存会话历史到数据库
    """
    try:
        # 检查会话是否存在
        if history_request.session_id not in active_sessions:
            logger.warning(f"尝试保存不存在的会话历史: {history_request.session_id}")

        # 调用聊天历史API保存数据
        from app.api.api_v1.endpoints.chat_history import save_chat_history

        # 直接调用保存函数
        result = save_chat_history(db=db, history_request=history_request)

        logger.info(f"会话历史保存成功: {history_request.session_id}")
        return result

    except Exception as e:
        logger.error(f"保存会话历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存会话历史失败: {str(e)}")
