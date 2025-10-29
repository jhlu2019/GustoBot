from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from gustobot.infrastructure.core.logger import get_logger
import time

logger = get_logger(service="http")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录请求日志
        logger.info(
            f"{request.client.host}:{request.client.port} - "
            f"\"{request.method} {request.url.path} HTTP/{request.scope.get('http_version', '1.1')}\" "
            f"{response.status_code} - {process_time:.2f}s"
        )
        
        return response 