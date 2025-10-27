from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class QueryRequest(BaseModel):
    connection_id: int
    natural_language_query: str


class QueryResponse(BaseModel):
    sql: str
    results: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    context: Optional[Dict[str, Any]] = None  # For debugging/explanation
