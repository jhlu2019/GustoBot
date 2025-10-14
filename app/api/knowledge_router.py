"""
知识库管理API端点
Knowledge Base Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from loguru import logger

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# 请求/响应模型
class RecipeModel(BaseModel):
    """菜谱模型"""
    id: Optional[str] = Field(None, description="菜谱ID")
    name: str = Field(..., description="菜名")
    category: Optional[str] = Field(None, description="分类")
    difficulty: Optional[str] = Field(None, description="难度")
    time: Optional[str] = Field(None, description="耗时")
    ingredients: Optional[List[str]] = Field(None, description="食材列表")
    steps: Optional[List[str]] = Field(None, description="步骤列表")
    tips: Optional[str] = Field(None, description="小贴士")
    nutrition: Optional[Dict[str, Any]] = Field(None, description="营养信息")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "recipe_001",
                "name": "红烧肉",
                "category": "家常菜",
                "difficulty": "中等",
                "time": "1小时",
                "ingredients": ["五花肉500g", "冰糖30g", "生抽2勺"],
                "steps": [
                    "五花肉切块，焯水",
                    "炒糖色，加入五花肉上色",
                    "加入调料，小火炖煮40分钟"
                ],
                "tips": "糖色不要炒过头，容易发苦"
            }
        }


class SearchRequest(BaseModel):
    """搜索请求"""
    query: str = Field(..., description="搜索关键词")
    top_k: Optional[int] = Field(5, description="返回结果数量", ge=1, le=20)


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[Dict[str, Any]] = Field(..., description="搜索结果")
    count: int = Field(..., description="结果数量")


# 依赖注入
def get_knowledge_service():
    """获取知识库服务实例"""
    from ..knowledge_base import KnowledgeService
    return KnowledgeService()


@router.post("/recipes", status_code=201)
async def add_recipe(
    recipe: RecipeModel,
    service=Depends(get_knowledge_service)
) -> Dict[str, Any]:
    """
    添加单个菜谱到知识库

    - **recipe**: 菜谱数据
    """
    try:
        # 生成ID（如果未提供）
        if not recipe.id:
            import uuid
            recipe.id = f"recipe_{uuid.uuid4().hex[:8]}"

        # 添加到知识库
        success = await service.add_recipe(
            recipe_id=recipe.id,
            recipe_data=recipe.dict()
        )

        if success:
            return {
                "status": "success",
                "message": "菜谱添加成功",
                "recipe_id": recipe.id
            }
        else:
            raise HTTPException(status_code=500, detail="添加菜谱失败")

    except Exception as e:
        logger.error(f"Error adding recipe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recipes/batch", status_code=201)
async def add_recipes_batch(
    recipes: List[RecipeModel],
    service=Depends(get_knowledge_service)
) -> Dict[str, Any]:
    """
    批量添加菜谱

    - **recipes**: 菜谱列表
    """
    try:
        # 确保所有菜谱都有ID
        for recipe in recipes:
            if not recipe.id:
                import uuid
                recipe.id = f"recipe_{uuid.uuid4().hex[:8]}"

        # 批量添加
        result = await service.add_recipes_batch(
            [r.dict() for r in recipes]
        )

        return {
            "status": "success",
            "message": f"成功添加 {result['success']} 个菜谱",
            "statistics": result
        }

    except Exception as e:
        logger.error(f"Error in batch add: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    service=Depends(get_knowledge_service)
) -> SearchResponse:
    """
    搜索知识库

    - **query**: 搜索关键词
    - **top_k**: 返回结果数量（默认5）
    """
    try:
        results = await service.search(
            query=request.query,
            top_k=request.top_k
        )

        return SearchResponse(
            results=results,
            count=len(results)
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/recipes/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    service=Depends(get_knowledge_service)
) -> Dict[str, Any]:
    """
    删除菜谱

    - **recipe_id**: 菜谱ID
    """
    try:
        success = await service.delete_recipe(recipe_id)

        if success:
            return {
                "status": "success",
                "message": f"菜谱 {recipe_id} 已删除"
            }
        else:
            raise HTTPException(status_code=404, detail="菜谱不存在或删除失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats(
    service=Depends(get_knowledge_service)
) -> Dict[str, Any]:
    """
    获取知识库统计信息

    返回知识库中的文档数量等信息
    """
    try:
        stats = await service.get_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_knowledge_base(
    confirm: bool = False,
    service=Depends(get_knowledge_service)
) -> Dict[str, Any]:
    """
    清空知识库（危险操作）

    - **confirm**: 必须设置为true才能执行
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="必须设置confirm=true才能清空知识库"
        )

    try:
        success = await service.clear()

        if success:
            return {
                "status": "success",
                "message": "知识库已清空"
            }
        else:
            raise HTTPException(status_code=500, detail="清空失败")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
