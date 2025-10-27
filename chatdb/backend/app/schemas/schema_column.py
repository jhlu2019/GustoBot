from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class SchemaColumnBase(BaseModel):
    column_name: str
    data_type: str
    description: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    is_unique: bool = False  # 添加唯一标记


# Properties to receive on column creation
class SchemaColumnCreate(SchemaColumnBase):
    table_id: int


# Properties to receive on column update
class SchemaColumnUpdate(BaseModel):
    column_name: Optional[str] = None
    data_type: Optional[str] = None
    description: Optional[str] = None
    is_primary_key: Optional[bool] = None
    is_foreign_key: Optional[bool] = None
    is_unique: Optional[bool] = None  # 添加唯一标记


# Properties shared by models stored in DB
class SchemaColumnInDBBase(SchemaColumnBase):
    id: int
    table_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class SchemaColumn(SchemaColumnInDBBase):
    pass


# Properties with relationships
class SchemaColumnWithMappings(SchemaColumn):
    value_mappings: List[Any] = []

# Update forward references after all classes are defined
from app.schemas.value_mapping import ValueMapping
SchemaColumnWithMappings.update_forward_refs()
