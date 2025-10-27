from typing import Optional
from datetime import datetime
from pydantic import BaseModel


# Shared properties
class DBConnectionBase(BaseModel):
    name: str
    db_type: str
    host: str
    port: int
    username: str
    database_name: str


# Properties to receive on connection creation
class DBConnectionCreate(DBConnectionBase):
    password: str


# Properties to receive on connection update
class DBConnectionUpdate(BaseModel):
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database_name: Optional[str] = None


# Properties shared by models stored in DB
class DBConnectionInDBBase(DBConnectionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Properties to return to client
class DBConnection(DBConnectionInDBBase):
    pass


# Properties stored in DB
class DBConnectionInDB(DBConnectionInDBBase):
    password_encrypted: str
