from fastapi import APIRouter

from app.api.api_v1.endpoints import connections, schema, query, value_mappings, text2sql, text2sql_sse, graph_visualization, relationship_tips, hybrid_qa, chat_history

# 强制重新加载 - 修复API路由问题

api_router = APIRouter()

# 添加API根路径处理器
@api_router.get("/")
async def api_root():
    """API根路径"""
    return {
        "message": "ChatDB API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "connections": "/api/connections/",
            "schema": "/api/schema/",
            "query": "/api/query/",
            "text2sql-sse": "/api/text2sql-sse/",
            "value_mappings": "/api/value-mappings/",
            "graph_visualization": "/api/graph-visualization/",
            "relationship_tips": "/api/relationship-tips/",
            "hybrid_qa": "/api/hybrid-qa/",
            "chat_history": "/api/chat-history/",
            "docs": "/docs",
            "openapi": "/openapi.json"
        }
    }

api_router.include_router(connections.router, prefix="/connections", tags=["connections"])
api_router.include_router(schema.router, prefix="/schema", tags=["schema"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
# api_router.include_router(text2sql.router, prefix="/text2sql", tags=["text2sql"])
api_router.include_router(text2sql_sse.router, prefix="/text2sql-sse", tags=["text2sql-sse"])
api_router.include_router(value_mappings.router, prefix="/value-mappings", tags=["value-mappings"])
api_router.include_router(graph_visualization.router, prefix="/graph-visualization", tags=["graph-visualization"])
api_router.include_router(relationship_tips.router, prefix="/relationship-tips", tags=["relationship-tips"])
api_router.include_router(hybrid_qa.router, prefix="/hybrid-qa", tags=["hybrid-qa"])
api_router.include_router(chat_history.router, prefix="/chat-history", tags=["chat-history"])
