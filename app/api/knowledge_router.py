"""
Knowledge base and Neo4j QA API endpoints.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


# Vector store models ---------------------------------------------------------
class RecipeModel(BaseModel):
    """Recipe payload stored in the vector knowledge base."""

    id: Optional[str] = Field(None, description="Recipe identifier")
    name: str = Field(..., description="Recipe name")
    category: Optional[str] = Field(None, description="Category")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    time: Optional[str] = Field(None, description="Cooking time")
    ingredients: Optional[List[str]] = Field(None, description="Ingredient list")
    steps: Optional[List[str]] = Field(None, description="Preparation steps")
    tips: Optional[str] = Field(None, description="Cooking tips")
    nutrition: Optional[Dict[str, Any]] = Field(None, description="Nutrition facts")


class SearchRequest(BaseModel):
    """Vector store search request."""

    query: str = Field(..., description="Query text")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of results to return")


class SearchResponse(BaseModel):
    """Vector store search response."""

    results: List[Dict[str, Any]] = Field(..., description="Matched documents")
    count: int = Field(..., description="Result count")


class GraphResponse(BaseModel):
    """Neo4j graph payload."""

    nodes: List[Dict[str, Any]] = Field(..., description="List of nodes")
    relationships: List[Dict[str, Any]] = Field(..., description="List of relationships")


class QARequest(BaseModel):
    """Neo4j QA request."""

    query: str = Field(..., description="User question")
    include_graph: bool = Field(False, description="Return the cached graph in the response")
    refresh_graph: bool = Field(False, description="Refresh the cached graph before returning it")


class QAResponse(BaseModel):
    """Neo4j QA response."""

    answer: str = Field(..., description="Natural language answer")
    question_type: str = Field(..., description="Detected question type")
    cypher: List[str] = Field(..., description="Generated Cypher queries")
    graph: Optional[GraphResponse] = Field(None, description="Optional graph data")


# Dependency helpers ----------------------------------------------------------
def get_knowledge_service():
    """Return the vector knowledge base service."""
    from ..knowledge_base import KnowledgeService

    return KnowledgeService()


@lru_cache
def get_neo4j_qa_service():
    """Return the Neo4j QA service."""
    from ..knowledge_base.recipe_kg import Neo4jQAService

    return Neo4jQAService()


# Vector store CRUD -----------------------------------------------------------
@router.post("/recipes", status_code=201)
async def add_recipe(
    recipe: RecipeModel,
    service=Depends(get_knowledge_service),
) -> Dict[str, Any]:
    """Add a single recipe to the vector knowledge base."""
    try:
        if not recipe.id:
            import uuid

            recipe.id = f"recipe_{uuid.uuid4().hex[:8]}"

        success = await service.add_recipe(recipe_id=recipe.id, recipe_data=recipe.dict())
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add recipe")

        return {"status": "success", "message": "Recipe added", "recipe_id": recipe.id}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Error adding recipe: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/recipes/batch", status_code=201)
async def add_recipes_batch(
    recipes: List[RecipeModel],
    service=Depends(get_knowledge_service),
) -> Dict[str, Any]:
    """Add recipes in batch."""
    try:
        import uuid

        for recipe in recipes:
            if not recipe.id:
                recipe.id = f"recipe_{uuid.uuid4().hex[:8]}"

        result = await service.add_recipes_batch([recipe.dict() for recipe in recipes])
        return {
            "status": "success",
            "message": f"Inserted {result['success']} recipes",
            "statistics": result,
        }
    except Exception as exc:
        logger.error(f"Error in batch add: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/search", response_model=SearchResponse)
async def search_knowledge(
    request: SearchRequest,
    service=Depends(get_knowledge_service),
) -> SearchResponse:
    """Search the vector knowledge base."""
    try:
        results = await service.search(query=request.query, top_k=request.top_k)
        return SearchResponse(results=results, count=len(results))
    except Exception as exc:
        logger.error(f"Search error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/recipes/{recipe_id}")
async def delete_recipe(
    recipe_id: str,
    service=Depends(get_knowledge_service),
) -> Dict[str, Any]:
    """Delete a recipe."""
    try:
        success = await service.delete_recipe(recipe_id)
        if not success:
            raise HTTPException(status_code=404, detail="Recipe not found or deletion failed")

        return {"status": "success", "message": f"Recipe {recipe_id} deleted"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Delete error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/stats")
async def get_stats(
    service=Depends(get_knowledge_service),
) -> Dict[str, Any]:
    """Return vector store statistics."""
    try:
        stats = await service.get_stats()
        return {"status": "success", "data": stats}
    except Exception as exc:
        logger.error(f"Stats error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/clear")
async def clear_knowledge_base(
    confirm: bool = False,
    service=Depends(get_knowledge_service),
) -> Dict[str, Any]:
    """Clear the vector store (dangerous operation)."""
    if not confirm:
        raise HTTPException(status_code=400, detail="confirm=true is required to clear the store")

    try:
        success = await service.clear()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear the store")
        return {"status": "success", "message": "Knowledge base cleared"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Clear error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# Neo4j endpoints -------------------------------------------------------------
@router.get("/graph", response_model=GraphResponse)
async def get_default_graph(
    refresh: bool = False,
    service=Depends(get_neo4j_qa_service),
) -> GraphResponse:
    """Return the default Neo4j graph snapshot."""
    try:
        graph_payload = service.get_default_graph(refresh=refresh)
        return GraphResponse(**graph_payload)
    except Exception as exc:
        logger.error(f"Graph retrieval error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/graph/qa", response_model=QAResponse)
async def qa_over_graph(
    request: QARequest,
    service=Depends(get_neo4j_qa_service),
) -> QAResponse:
    """Run natural-language QA over the Neo4j graph."""
    try:
        qa_payload = service.ask(request.query)
        graph_payload = (
            service.get_default_graph(refresh=request.refresh_graph)
            if request.include_graph
            else None
        )

        return QAResponse(
            answer=qa_payload.get("answer", ""),
            question_type=qa_payload.get("question_type", ""),
            cypher=qa_payload.get("cypher", []),
            graph=GraphResponse(**graph_payload) if graph_payload else None,
        )
    except Exception as exc:
        logger.error(f"QA error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))
