# Import and re-export schema classes
from app.schemas.db_connection import DBConnection, DBConnectionCreate, DBConnectionUpdate, DBConnectionInDB
from app.schemas.schema_table import SchemaTable, SchemaTableCreate, SchemaTableUpdate, SchemaTableWithRelationships
from app.schemas.schema_column import SchemaColumn, SchemaColumnCreate, SchemaColumnUpdate, SchemaColumnWithMappings
from app.schemas.schema_relationship import SchemaRelationship, SchemaRelationshipCreate, SchemaRelationshipUpdate, SchemaRelationshipDetailed
from app.schemas.value_mapping import ValueMapping, ValueMappingCreate, ValueMappingUpdate
from app.schemas.query import QueryRequest, QueryResponse
from app.schemas.chat_history import (
    ChatSession, ChatSessionCreate, ChatSessionUpdate,
    ChatMessage, ChatMessageCreate, ChatMessageUpdate,
    ChatHistorySnapshot, ChatHistorySnapshotCreate,
    ChatHistoryResponse, ChatHistoryListResponse,
    SaveChatHistoryRequest, RestoreChatHistoryResponse
)
