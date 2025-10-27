import asyncio
import logging
import uuid
import json
from typing import Dict, List, Optional, Any, Callable, Awaitable
from datetime import datetime
from starlette.websockets import WebSocket, WebSocketDisconnect

# 设置日志记录器
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket连接管理器

    管理多个WebSocket连接，支持多用户同时访问系统
    """
    def __init__(self):
        # 活跃连接字典 {connection_id: {"websocket": WebSocket, "user_id": str, "created_at": datetime, "last_activity": datetime}}
        self.active_connections: Dict[str, Dict[str, Any]] = {}

        # 用户连接映射 {user_id: [connection_id1, connection_id2, ...]}
        self.user_connections: Dict[str, List[str]] = {}

        # 消息队列 {connection_id: Queue}
        self.message_queues: Dict[str, asyncio.Queue] = {}

        # 反馈队列 {connection_id: Queue}
        self.feedback_queues: Dict[str, asyncio.Queue] = {}

        # 连接计数器
        self.connection_counter = 0

        # 会话超时（秒）
        self.session_timeout = 7200  # 2小时

        # 心跳间隔（秒）
        self.heartbeat_interval = 60

        # 心跳任务 {connection_id: Task}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

        # 监控统计
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }

        logger.info("WebSocket连接管理器已初始化")

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None) -> str:
        """
        建立新的WebSocket连接

        Args:
            websocket: WebSocket连接
            user_id: 用户ID，如果为None则自动生成

        Returns:
            connection_id: 连接ID
        """
        # 接受WebSocket连接
        await websocket.accept()

        # 生成连接ID
        connection_id = str(uuid.uuid4())

        # 如果没有提供用户ID，则使用连接ID作为用户ID
        if not user_id:
            user_id = f"anonymous-{connection_id[:8]}"

        # 记录连接信息
        self.active_connections[connection_id] = {
            "websocket": websocket,
            "user_id": user_id,
            "created_at": datetime.now(),
            "last_activity": datetime.now(),
            "client_info": f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "未知客户端",
            "headers": dict(websocket.headers)
        }

        # 更新用户连接映射
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)

        # 创建消息队列
        self.message_queues[connection_id] = asyncio.Queue()

        # 创建反馈队列
        self.feedback_queues[connection_id] = asyncio.Queue()

        # 更新统计信息
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.active_connections)

        # 启动心跳任务
        self.heartbeat_tasks[connection_id] = asyncio.create_task(
            self._heartbeat_task(connection_id)
        )

        # 发送欢迎消息
        await self.send_message(connection_id, {
            "type": "system",
            "content": "WebSocket连接已建立，可以开始查询",
            "connection_id": connection_id,
            "user_id": user_id
        })

        logger.info(f"新的WebSocket连接已建立: connection_id={connection_id}, user_id={user_id}")
        return connection_id

    async def disconnect(self, connection_id: str) -> None:
        """
        关闭WebSocket连接

        Args:
            connection_id: 连接ID
        """
        if connection_id not in self.active_connections:
            logger.warning(f"尝试关闭不存在的连接: {connection_id}")
            return

        # 获取连接信息
        connection_info = self.active_connections[connection_id]
        user_id = connection_info["user_id"]
        websocket = connection_info["websocket"]

        # 关闭WebSocket连接
        try:
            await websocket.close()
        except Exception as e:
            logger.error(f"关闭WebSocket连接时出错: {str(e)}")

        # 停止心跳任务
        if connection_id in self.heartbeat_tasks:
            self.heartbeat_tasks[connection_id].cancel()
            del self.heartbeat_tasks[connection_id]

        # 从活跃连接中移除
        del self.active_connections[connection_id]

        # 从用户连接映射中移除
        if user_id in self.user_connections:
            self.user_connections[user_id].remove(connection_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # 清理消息队列
        if connection_id in self.message_queues:
            del self.message_queues[connection_id]

        # 清理反馈队列
        if connection_id in self.feedback_queues:
            del self.feedback_queues[connection_id]

        # 更新统计信息
        self.stats["active_connections"] = len(self.active_connections)

        logger.info(f"WebSocket连接已关闭: connection_id={connection_id}, user_id={user_id}")

    async def disconnect_all(self) -> None:
        """
        关闭所有WebSocket连接
        """
        connection_ids = list(self.active_connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

        logger.info("所有WebSocket连接已关闭")

    async def disconnect_user(self, user_id: str) -> None:
        """
        关闭指定用户的所有WebSocket连接

        Args:
            user_id: 用户ID
        """
        if user_id not in self.user_connections:
            logger.warning(f"尝试关闭不存在用户的连接: {user_id}")
            return

        connection_ids = list(self.user_connections[user_id])
        for connection_id in connection_ids:
            await self.disconnect(connection_id)

        logger.info(f"用户的所有WebSocket连接已关闭: user_id={user_id}")

    async def send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        向指定连接发送消息

        Args:
            connection_id: 连接ID
            message: 消息内容

        Returns:
            bool: 是否发送成功
        """
        if connection_id not in self.active_connections:
            logger.warning(f"尝试向不存在的连接发送消息: {connection_id}")
            return False

        websocket = self.active_connections[connection_id]["websocket"]

        try:
            # 添加时间戳
            if "timestamp" not in message:
                message["timestamp"] = datetime.now().isoformat()

            # 发送消息
            await websocket.send_json(message)

            # 更新最后活动时间
            self.active_connections[connection_id]["last_activity"] = datetime.now()

            # 更新统计信息
            self.stats["messages_sent"] += 1

            return True
        except WebSocketDisconnect:
            logger.info(f"发送消息时检测到连接已断开: {connection_id}")
            await self.disconnect(connection_id)
            return False
        except Exception as e:
            logger.error(f"发送消息时出错: {str(e)}")
            self.stats["errors"] += 1
            return False

    async def broadcast(self, message: Dict[str, Any], exclude: Optional[List[str]] = None) -> None:
        """
        广播消息给所有连接

        Args:
            message: 消息内容
            exclude: 排除的连接ID列表
        """
        exclude = exclude or []
        connection_ids = [cid for cid in self.active_connections.keys() if cid not in exclude]

        for connection_id in connection_ids:
            await self.send_message(connection_id, message)

        logger.info(f"广播消息已发送给 {len(connection_ids)} 个连接")

    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]) -> None:
        """
        广播消息给指定用户的所有连接

        Args:
            user_id: 用户ID
            message: 消息内容
        """
        if user_id not in self.user_connections:
            logger.warning(f"尝试向不存在用户广播消息: {user_id}")
            return

        connection_ids = self.user_connections[user_id]
        for connection_id in connection_ids:
            await self.send_message(connection_id, message)

        logger.info(f"广播消息已发送给用户 {user_id} 的 {len(connection_ids)} 个连接")

    async def receive_message(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        从指定连接接收消息

        Args:
            connection_id: 连接ID

        Returns:
            Dict[str, Any]: 接收到的消息，如果连接不存在或出错则返回None
        """
        if connection_id not in self.active_connections:
            logger.warning(f"尝试从不存在的连接接收消息: {connection_id}")
            return None

        websocket = self.active_connections[connection_id]["websocket"]

        try:
            # 接收消息
            data = await websocket.receive_json()

            # 更新最后活动时间
            self.active_connections[connection_id]["last_activity"] = datetime.now()

            # 更新统计信息
            self.stats["messages_received"] += 1

            return data
        except WebSocketDisconnect:
            logger.info(f"接收消息时检测到连接已断开: {connection_id}")
            await self.disconnect(connection_id)
            return None
        except Exception as e:
            logger.error(f"接收消息时出错: {str(e)}")
            self.stats["errors"] += 1
            return None

    async def get_feedback(self, connection_id: str, timeout: float = 60.0) -> Optional[Dict[str, Any]]:
        """
        从指定连接的反馈队列获取反馈

        Args:
            connection_id: 连接ID
            timeout: 超时时间（秒）

        Returns:
            Dict[str, Any]: 反馈内容，如果超时或出错则返回None
        """
        if connection_id not in self.feedback_queues:
            logger.warning(f"尝试从不存在的连接获取反馈: {connection_id}")
            return None

        feedback_queue = self.feedback_queues[connection_id]

        try:
            # 等待反馈
            feedback = await asyncio.wait_for(feedback_queue.get(), timeout=timeout)
            return feedback
        except asyncio.TimeoutError:
            logger.warning(f"等待反馈超时: {connection_id}")
            return None
        except Exception as e:
            logger.error(f"获取反馈时出错: {str(e)}")
            self.stats["errors"] += 1
            return None

    async def put_feedback(self, connection_id: str, feedback: Dict[str, Any]) -> bool:
        """
        将反馈放入指定连接的反馈队列

        Args:
            connection_id: 连接ID
            feedback: 反馈内容

        Returns:
            bool: 是否成功
        """
        if connection_id not in self.feedback_queues:
            logger.warning(f"尝试向不存在的连接放入反馈: {connection_id}")
            return False

        feedback_queue = self.feedback_queues[connection_id]

        try:
            # 添加时间戳
            if "timestamp" not in feedback:
                feedback["timestamp"] = datetime.now().isoformat()

            # 放入反馈队列
            await feedback_queue.put(feedback)

            # 更新最后活动时间
            self.active_connections[connection_id]["last_activity"] = datetime.now()

            return True
        except Exception as e:
            logger.error(f"放入反馈时出错: {str(e)}")
            self.stats["errors"] += 1
            return False

    async def handle_connection(self, websocket: WebSocket, user_id: Optional[str] = None,
                               message_handler: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None) -> None:
        """
        处理WebSocket连接的主循环

        Args:
            websocket: WebSocket连接
            user_id: 用户ID，如果为None则自动生成
            message_handler: 消息处理函数，接收connection_id和消息内容
        """
        # 建立连接
        connection_id = await self.connect(websocket, user_id)

        try:
            # 处理消息循环
            while True:
                # 接收消息
                data = await self.receive_message(connection_id)

                # 如果连接已断开，退出循环
                if data is None:
                    break

                # 处理心跳消息
                if data.get("type") == "heartbeat":
                    await self.send_message(connection_id, {
                        "type": "heartbeat_response",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue

                # 处理反馈消息
                if data.get("is_feedback", False):
                    await self.put_feedback(connection_id, data)
                    continue

                # 如果提供了消息处理函数，则调用
                if message_handler:
                    await message_handler(connection_id, data)
        except WebSocketDisconnect:
            logger.info(f"WebSocket连接已断开: {connection_id}")
        except Exception as e:
            logger.error(f"处理WebSocket连接时出错: {str(e)}")
            self.stats["errors"] += 1
        finally:
            # 确保连接被关闭
            await self.disconnect(connection_id)

    async def _heartbeat_task(self, connection_id: str) -> None:
        """
        心跳任务，定期检查连接是否活跃

        Args:
            connection_id: 连接ID
        """
        try:
            while connection_id in self.active_connections:
                # 等待心跳间隔
                await asyncio.sleep(self.heartbeat_interval)

                # 检查连接是否超时
                if connection_id in self.active_connections:
                    last_activity = self.active_connections[connection_id]["last_activity"]
                    now = datetime.now()
                    elapsed = (now - last_activity).total_seconds()

                    # 如果超过会话超时时间，则关闭连接
                    if elapsed > self.session_timeout:
                        logger.info(f"连接超时，准备关闭: {connection_id}, 最后活动: {elapsed}秒前")
                        await self.disconnect(connection_id)
                        break

                    # 发送心跳消息
                    await self.send_message(connection_id, {
                        "type": "heartbeat",
                        "timestamp": now.isoformat()
                    })
        except asyncio.CancelledError:
            # 任务被取消，正常退出
            pass
        except Exception as e:
            logger.error(f"心跳任务出错: {str(e)}")
            self.stats["errors"] += 1

            # 确保连接被关闭
            if connection_id in self.active_connections:
                await self.disconnect(connection_id)

    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """
        获取连接信息

        Args:
            connection_id: 连接ID

        Returns:
            Dict[str, Any]: 连接信息，如果连接不存在则返回None
        """
        if connection_id not in self.active_connections:
            return None

        # 复制连接信息，排除websocket对象
        connection_info = dict(self.active_connections[connection_id])
        connection_info.pop("websocket", None)

        # 转换datetime为ISO格式字符串
        for key in ["created_at", "last_activity"]:
            if key in connection_info and isinstance(connection_info[key], datetime):
                connection_info[key] = connection_info[key].isoformat()

        return connection_info

    def get_user_connections(self, user_id: str) -> List[str]:
        """
        获取用户的所有连接ID

        Args:
            user_id: 用户ID

        Returns:
            List[str]: 连接ID列表
        """
        return self.user_connections.get(user_id, [])

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 复制统计信息
        stats = dict(self.stats)

        # 添加当前时间
        stats["timestamp"] = datetime.now().isoformat()

        return stats

    def reset_stats(self) -> None:
        """
        重置统计信息
        """
        self.stats = {
            "total_connections": self.stats["total_connections"],
            "active_connections": len(self.active_connections),
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0
        }

        logger.info("统计信息已重置")

# 创建全局连接管理器实例
manager = ConnectionManager()
