from typing import List, Optional

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.schema_column import SchemaColumn
from app.schemas.schema_column import SchemaColumnCreate, SchemaColumnUpdate


class CRUDSchemaColumn(CRUDBase[SchemaColumn, SchemaColumnCreate, SchemaColumnUpdate]):
    def get_by_table(
        self, db: Session, *, table_id: int, skip: int = 0, limit: int = 100
    ) -> List[SchemaColumn]:
        return (
            db.query(SchemaColumn)
            .filter(SchemaColumn.table_id == table_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_name_and_table(
        self, db: Session, *, column_name: str, table_id: int
    ) -> Optional[SchemaColumn]:
        return (
            db.query(SchemaColumn)
            .filter(
                SchemaColumn.column_name == column_name,
                SchemaColumn.table_id == table_id
            )
            .first()
        )


schema_column = CRUDSchemaColumn(SchemaColumn)
