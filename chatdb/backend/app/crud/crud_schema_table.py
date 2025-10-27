from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.schema_table import SchemaTable
from app.schemas.schema_table import SchemaTableCreate, SchemaTableUpdate


class CRUDSchemaTable(CRUDBase[SchemaTable, SchemaTableCreate, SchemaTableUpdate]):
    def get_by_connection(
        self, db: Session, *, connection_id: int, skip: int = 0, limit: int = 100
    ) -> List[SchemaTable]:
        return (
            db.query(SchemaTable)
            .filter(SchemaTable.connection_id == connection_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_name_and_connection(
        self, db: Session, *, table_name: str, connection_id: int
    ) -> Optional[SchemaTable]:
        return (
            db.query(SchemaTable)
            .filter(
                SchemaTable.table_name == table_name,
                SchemaTable.connection_id == connection_id
            )
            .first()
        )


schema_table = CRUDSchemaTable(SchemaTable)
