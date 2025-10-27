from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session
from sqlalchemy import delete
from neo4j import GraphDatabase

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.db_connection import DBConnection
from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn
from app.models.schema_relationship import SchemaRelationship
from app.models.value_mapping import ValueMapping
from app.schemas.db_connection import DBConnectionCreate, DBConnectionUpdate


class CRUDDBConnection(CRUDBase[DBConnection, DBConnectionCreate, DBConnectionUpdate]):
    def create(self, db: Session, *, obj_in: DBConnectionCreate) -> DBConnection:
        # 在实际应用中，应该对密码进行加密
        # 但为了解决当前的连接问题，我们暂时存储明文密码
        # password_encrypted=get_password_hash(obj_in.password),
        db_obj = DBConnection(
            name=obj_in.name,
            db_type=obj_in.db_type,
            host=obj_in.host,
            port=obj_in.port,
            username=obj_in.username,
            password_encrypted=obj_in.password,  # 暂时存储明文密码
            database_name=obj_in.database_name,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: DBConnection, obj_in: Union[DBConnectionUpdate, Dict[str, Any]]
    ) -> DBConnection:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password"):
            # 在实际应用中，应该对密码进行加密
            # hashed_password = get_password_hash(update_data["password"])
            # 但为了解决当前的连接问题，我们暂时存储明文密码
            plain_password = update_data["password"]
            del update_data["password"]
            update_data["password_encrypted"] = plain_password  # 暂时存储明文密码
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def get_by_name(self, db: Session, *, name: str) -> Optional[DBConnection]:
        return db.query(DBConnection).filter(DBConnection.name == name).first()

    def remove(self, db: Session, *, id: int) -> DBConnection:
        """Override the base remove method to handle deletion of related entities"""
        # First, get the connection object
        connection = db.query(self.model).get(id)
        if not connection:
            return None

        try:
            # Step 0: 清理Neo4j图数据库中的相关数据
            self._clean_neo4j_data(id)

            # Step 1: Delete all relationships associated with this connection
            # This must be done first because relationships reference both tables and columns
            db.execute(delete(SchemaRelationship).where(SchemaRelationship.connection_id == id))

            # Get all tables associated with this connection
            tables = db.query(SchemaTable).filter(SchemaTable.connection_id == id).all()
            table_ids = [table.id for table in tables]

            if table_ids:
                # Get all columns associated with these tables
                columns = db.query(SchemaColumn).filter(SchemaColumn.table_id.in_(table_ids)).all()
                column_ids = [column.id for column in columns]

                if column_ids:
                    # Step 2: Delete all value mappings associated with these columns
                    db.execute(delete(ValueMapping).where(ValueMapping.column_id.in_(column_ids)))

                # Step 3: Delete all columns associated with these tables
                db.execute(delete(SchemaColumn).where(SchemaColumn.table_id.in_(table_ids)))

            # Step 4: Delete all tables associated with this connection
            db.execute(delete(SchemaTable).where(SchemaTable.connection_id == id))

            # Step 5: Delete the connection itself
            db.delete(connection)
            db.commit()

            return connection
        except Exception as e:
            db.rollback()
            print(f"Error deleting connection: {str(e)}")
            raise e

    def _clean_neo4j_data(self, connection_id: int) -> None:
        """清理Neo4j图数据库中与指定连接相关的所有数据"""
        try:
            print(f"开始清理Neo4j中连接ID为{connection_id}的数据")
            # 连接到Neo4j
            driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )

            with driver.session() as session:
                # 删除与此连接相关的所有节点和关系
                print(f"删除Neo4j中连接ID为{connection_id}的所有节点和关系")
                session.run(
                    "MATCH (n {connection_id: $connection_id}) DETACH DELETE n",
                    connection_id=connection_id
                )
                print(f"成功清理Neo4j中连接ID为{connection_id}的数据")

            driver.close()
        except Exception as e:
            print(f"清理Neo4j数据失败: {str(e)}")
            # 这里我们只记录错误，但不抛出异常，因为即使Neo4j清理失败，我们仍然希望继续删除MySQL中的数据


db_connection = CRUDDBConnection(DBConnection)
