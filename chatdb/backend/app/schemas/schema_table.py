from typing import Optional, Dict, Any, List, ForwardRef
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class SchemaTableBase(BaseModel):
    table_name: str
    description: Optional[str] = None
    ui_metadata: Optional[Dict[str, Any]] = None


# Properties to receive on table creation
class SchemaTableCreate(SchemaTableBase):
    connection_id: int


# Properties to receive on table update
class SchemaTableUpdate(BaseModel):
    table_name: Optional[str] = None
    description: Optional[str] = None
    ui_metadata: Optional[Dict[str, Any]] = None


# Properties shared by models stored in DB
class SchemaTableInDBBase(SchemaTableBase):
    id: int
    connection_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class SchemaTable(SchemaTableInDBBase):
    pass


# Properties with relationships
class SchemaTableWithRelationships(SchemaTable):
    columns: List[Any] = []
    relationships: List[Any] = []

# Update forward references after all classes are defined
from app.schemas.schema_column import SchemaColumn
from app.schemas.schema_relationship import SchemaRelationshipDetailed
SchemaTableWithRelationships.update_forward_refs()
