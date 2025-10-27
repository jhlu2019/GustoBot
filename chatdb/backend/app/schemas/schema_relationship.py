from typing import Optional
from datetime import datetime
from pydantic import BaseModel


# 关系类型常量
RELATIONSHIP_TYPES = {
    "ONE_TO_ONE": "1-to-1",
    "ONE_TO_MANY": "1-to-N",
    "MANY_TO_ONE": "N-to-1",  # 添加多对一关系类型
    "MANY_TO_MANY": "N-to-M"
}

# Shared properties
class SchemaRelationshipBase(BaseModel):
    connection_id: int
    source_table_id: int
    source_column_id: int
    target_table_id: int
    target_column_id: int
    relationship_type: Optional[str] = None
    description: Optional[str] = None


# Properties to receive on relationship creation
class SchemaRelationshipCreate(SchemaRelationshipBase):
    pass


# Properties to receive on relationship update
class SchemaRelationshipUpdate(BaseModel):
    relationship_type: Optional[str] = None
    description: Optional[str] = None


# Properties shared by models stored in DB
class SchemaRelationshipInDBBase(SchemaRelationshipBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class SchemaRelationship(SchemaRelationshipInDBBase):
    pass


# Properties with detailed information
class SchemaRelationshipDetailed(SchemaRelationship):
    source_table_name: str
    source_column_name: str
    target_table_name: str
    target_column_name: str
