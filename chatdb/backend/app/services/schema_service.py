from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from neo4j import GraphDatabase

from app.core.config import settings
from app.models.db_connection import DBConnection
from app.services.db_service import get_db_engine
from app import crud, schemas
from app.services.schema_utils import is_column_unique_in_table, has_composite_primary_key, is_junction_table, determine_relationship_type


def discover_schema(connection: DBConnection) -> List[Dict[str, Any]]:
    """
    Discover schema from a database connection.
    """
    try:
        print(f"Discovering schema for {connection.name} ({connection.db_type} at {connection.host}:{connection.port}/{connection.database_name})")
        engine = get_db_engine(connection)
        inspector = inspect(engine)

        # Choose the appropriate discovery method based on database type
        if connection.db_type.lower() == "mysql":
            return discover_mysql_schema(inspector)
        elif connection.db_type.lower() == "postgresql":
            return discover_postgresql_schema(inspector)
        elif connection.db_type.lower() == "sqlite":
            return discover_sqlite_schema(inspector)
        else:
            # Default discovery method
            return discover_generic_schema(inspector)
    except Exception as e:
        error_msg = f"Schema discovery failed: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise Exception(error_msg)


def discover_generic_schema(inspector) -> List[Dict[str, Any]]:
    """
    Generic schema discovery that works with most database types.
    """
    schema_info = []

    # Get all tables and views
    tables = inspector.get_table_names()
    try:
        views = inspector.get_view_names()
        tables.extend(views)
    except Exception as view_error:
        print(f"Warning: Could not get views: {str(view_error)}")
        views = []

    print(f"Found {len(tables)} tables/views: {', '.join(tables)}")

    for table_name in tables:
        print(f"Processing table/view: {table_name}")
        table_info = {
            "table_name": table_name,
            "columns": [],
            "is_view": table_name in views,
            "unique_constraints": [],  # 添加唯一约束信息
            "indexes": []  # 添加索引信息
        }

        # Get columns for each table
        try:
            columns = inspector.get_columns(table_name)
            print(f"Found {len(columns)} columns in {table_name}")

            for column in columns:
                column_info = {
                    "column_name": column["name"],
                    "data_type": str(column["type"]),
                    "is_primary_key": False,
                    "is_foreign_key": False,
                    "is_nullable": column.get("nullable", True),
                    "is_unique": False  # 添加唯一标记
                }
                table_info["columns"].append(column_info)

            # Mark primary keys
            try:
                pks = inspector.get_primary_keys(table_name)
                print(f"Primary keys for {table_name}: {pks}")
                for pk in pks:
                    for column in table_info["columns"]:
                        if column["column_name"] == pk:
                            column["is_primary_key"] = True
            except Exception as pk_error:
                # Some databases might not support primary key inspection
                print(f"Warning: Could not get primary keys for {table_name}: {str(pk_error)}")
                # Try to identify primary keys by naming convention
                for column in table_info["columns"]:
                    col_name = column["column_name"].lower()
                    if col_name == 'id' or col_name.endswith('_id') or col_name == f"{table_name.lower()}_id":
                        if 'int' in column["data_type"].lower() or 'serial' in column["data_type"].lower():
                            print(f"Identified potential primary key by naming convention: {column['column_name']}")
                            column["is_primary_key"] = True

            # Mark foreign keys
            try:
                fks = inspector.get_foreign_keys(table_name)
                print(f"Foreign keys for {table_name}: {len(fks)}")
                for fk in fks:
                    print(f"  FK: {fk}")
                    # 处理复合外键
                    for i, constrained_column in enumerate(fk["constrained_columns"]):
                        for column in table_info["columns"]:
                            if column["column_name"] == constrained_column:
                                column["is_foreign_key"] = True
                                # 确保引用列索引有效
                                referred_column_idx = min(i, len(fk["referred_columns"]) - 1) if fk["referred_columns"] else 0
                                referred_column = fk["referred_columns"][referred_column_idx] if fk["referred_columns"] else "id"
                                column["references"] = {
                                    "table": fk["referred_table"],
                                    "column": referred_column,
                                    "constraint_name": fk.get("name", ""),  # 保存约束名称
                                    "is_part_of_composite_key": len(fk["constrained_columns"]) > 1  # 标记是否为复合键的一部分
                                }
            except Exception as fk_error:
                # Some databases might not support foreign key inspection
                print(f"Warning: Could not get foreign keys for {table_name}: {str(fk_error)}")
                # Try to identify foreign keys by naming convention
                for column in table_info["columns"]:
                    col_name = column["column_name"].lower()

                    # 如果列名以_id结尾且不是主键，可能是外键
                    if col_name.endswith('_id') and not column["is_primary_key"]:
                        # 提取可能的表名
                        potential_table = col_name[:-3]  # 移除 '_id' 后缀

                        # 检查这个表是否存在
                        table_exists = potential_table in [t.lower() for t in tables]

                        # 如果表存在，标记为外键
                        if table_exists:
                            print(f"Identified potential foreign key by naming convention: {column['column_name']} -> {potential_table}")
                            column["is_foreign_key"] = True
                            column["references"] = {
                                "table": next(t for t in tables if t.lower() == potential_table),
                                "column": "id",  # 假设主键是 'id'
                                "constraint_name": f"fk_{table_name}_{column['column_name']}_inferred",  # 生成一个约束名
                                "is_part_of_composite_key": False,  # 默认不是复合键的一部分
                                "is_inferred": True  # 标记为推断的外键
                            }

                    # 如果列名与其他表名相同，也可能是外键
                    elif not column["is_primary_key"] and not column["is_foreign_key"]:
                        for table_name_to_check in tables:
                            if col_name == table_name_to_check.lower() or col_name == f"{table_name_to_check.lower()}id":
                                print(f"Identified potential foreign key by table name match: {column['column_name']} -> {table_name_to_check}")
                                column["is_foreign_key"] = True
                                column["references"] = {
                                    "table": table_name_to_check,
                                    "column": "id",  # 假设主键是 'id'
                                    "constraint_name": f"fk_{table_name}_{column['column_name']}_inferred",  # 生成一个约束名
                                    "is_part_of_composite_key": False,  # 默认不是复合键的一部分
                                    "is_inferred": True  # 标记为推断的外键
                                }
                                break

            # 获取唯一约束
            try:
                unique_constraints = inspector.get_unique_constraints(table_name)
                print(f"Unique constraints for {table_name}: {len(unique_constraints)}")
                for uc in unique_constraints:
                    print(f"  UC: {uc}")
                    table_info["unique_constraints"].append(uc)

                    # 标记列为唯一
                    for column in table_info["columns"]:
                        if column["column_name"] in uc.get("column_names", []):
                            column["is_unique"] = True
            except Exception as uc_error:
                print(f"Warning: Could not get unique constraints for {table_name}: {str(uc_error)}")

            # 获取索引
            try:
                indexes = inspector.get_indexes(table_name)
                print(f"Indexes for {table_name}: {len(indexes)}")
                for idx in indexes:
                    print(f"  Index: {idx}")
                    table_info["indexes"].append(idx)

                    # 标记列为唯一（如果索引是唯一的）
                    if idx.get("unique", False):
                        for column in table_info["columns"]:
                            if column["column_name"] in idx.get("column_names", []):
                                column["is_unique"] = True
            except Exception as idx_error:
                print(f"Warning: Could not get indexes for {table_name}: {str(idx_error)}")

        except Exception as column_error:
            print(f"Warning: Could not process columns for {table_name}: {str(column_error)}")
            continue

        schema_info.append(table_info)

    print(f"Schema discovery completed successfully. Found {len(schema_info)} tables/views.")
    return schema_info


def discover_mysql_schema(inspector) -> List[Dict[str, Any]]:
    """
    MySQL-specific schema discovery.
    """
    print("Using MySQL-specific schema discovery")
    schema_info = []

    # Get all tables and views
    tables = inspector.get_table_names()
    try:
        views = inspector.get_view_names()
        tables.extend(views)
    except Exception as view_error:
        print(f"Warning: Could not get views: {str(view_error)}")
        views = []

    print(f"Found {len(tables)} tables/views: {', '.join(tables)}")

    for table_name in tables:
        print(f"Processing table/view: {table_name}")
        table_info = {
            "table_name": table_name,
            "columns": [],
            "is_view": table_name in views
        }

        # Get columns for each table
        try:
            columns = inspector.get_columns(table_name)
            print(f"Found {len(columns)} columns in {table_name}")

            for column in columns:
                column_info = {
                    "column_name": column["name"],
                    "data_type": str(column["type"]),
                    "is_primary_key": False,
                    "is_foreign_key": False,
                    "is_nullable": column.get("nullable", True)
                }
                table_info["columns"].append(column_info)

            # Mark primary keys - MySQL has reliable PK detection
            try:
                pks = inspector.get_primary_keys(table_name)
                print(f"Primary keys for {table_name}: {pks}")
                for pk in pks:
                    for column in table_info["columns"]:
                        if column["column_name"] == pk:
                            column["is_primary_key"] = True
            except Exception as pk_error:
                print(f"Warning: Could not get primary keys for {table_name}: {str(pk_error)}")
                # Try to identify primary keys by naming convention
                for column in table_info["columns"]:
                    col_name = column["column_name"].lower()
                    if col_name == 'id' or col_name.endswith('_id') or col_name == f"{table_name.lower()}_id":
                        if 'int' in column["data_type"].lower():
                            print(f"Identified potential primary key by naming convention: {column['column_name']}")
                            column["is_primary_key"] = True

            # Mark foreign keys - MySQL has reliable FK detection through INFORMATION_SCHEMA
            try:
                fks = inspector.get_foreign_keys(table_name)
                print(f"Foreign keys for {table_name}: {len(fks)}")
                for fk in fks:
                    print(f"  FK: {fk}")
                    for column in table_info["columns"]:
                        if column["column_name"] in fk["constrained_columns"]:
                            column["is_foreign_key"] = True
                            column["references"] = {
                                "table": fk["referred_table"],
                                "column": fk["referred_columns"][0]
                            }
            except Exception as fk_error:
                print(f"Warning: Could not get foreign keys for {table_name}: {str(fk_error)}")
                # Try to identify foreign keys by naming convention
                for column in table_info["columns"]:
                    col_name = column["column_name"].lower()
                    if col_name.endswith('_id') and not column["is_primary_key"]:
                        # Extract potential table name from column name
                        potential_table = col_name[:-3]  # Remove '_id' suffix
                        # Check if this table exists
                        if potential_table in [t.lower() for t in tables]:
                            print(f"Identified potential foreign key by naming convention: {column['column_name']} -> {potential_table}")
                            column["is_foreign_key"] = True
                            column["references"] = {
                                "table": next(t for t in tables if t.lower() == potential_table),
                                "column": "id"  # Assume the primary key is 'id'
                            }
        except Exception as column_error:
            print(f"Warning: Could not process columns for {table_name}: {str(column_error)}")
            continue

        schema_info.append(table_info)

    return schema_info


def discover_postgresql_schema(inspector) -> List[Dict[str, Any]]:
    """
    PostgreSQL-specific schema discovery.
    """
    print("Using PostgreSQL-specific schema discovery")
    schema_info = []

    # Get all tables and views
    tables = inspector.get_table_names()
    try:
        views = inspector.get_view_names()
        tables.extend(views)
    except Exception as view_error:
        print(f"Warning: Could not get views: {str(view_error)}")
        views = []

    print(f"Found {len(tables)} tables/views: {', '.join(tables)}")

    for table_name in tables:
        print(f"Processing table/view: {table_name}")
        table_info = {
            "table_name": table_name,
            "columns": [],
            "is_view": table_name in views
        }

        # Get columns for each table
        try:
            columns = inspector.get_columns(table_name)
            print(f"Found {len(columns)} columns in {table_name}")

            for column in columns:
                column_info = {
                    "column_name": column["name"],
                    "data_type": str(column["type"]),
                    "is_primary_key": False,
                    "is_foreign_key": False,
                    "is_nullable": column.get("nullable", True)
                }
                table_info["columns"].append(column_info)

            # Mark primary keys - PostgreSQL has reliable PK detection
            try:
                pks = inspector.get_pk_constraint(table_name)["constrained_columns"]
                print(f"Primary keys for {table_name}: {pks}")
                for pk in pks:
                    for column in table_info["columns"]:
                        if column["column_name"] == pk:
                            column["is_primary_key"] = True
            except Exception as pk_error:
                print(f"Warning: Could not get primary keys for {table_name}: {str(pk_error)}")
                # Try to identify primary keys by naming convention and data type
                for column in table_info["columns"]:
                    col_name = column["column_name"].lower()
                    if col_name == 'id' or col_name.endswith('_id') or col_name == f"{table_name.lower()}_id":
                        if 'int' in column["data_type"].lower() or 'serial' in column["data_type"].lower():
                            print(f"Identified potential primary key by naming convention: {column['column_name']}")
                            column["is_primary_key"] = True

            # Mark foreign keys - PostgreSQL has reliable FK detection
            try:
                fks = inspector.get_foreign_keys(table_name)
                print(f"Foreign keys for {table_name}: {len(fks)}")
                for fk in fks:
                    print(f"  FK: {fk}")
                    for column in table_info["columns"]:
                        if column["column_name"] in fk["constrained_columns"]:
                            column["is_foreign_key"] = True
                            column["references"] = {
                                "table": fk["referred_table"],
                                "column": fk["referred_columns"][0]
                            }
            except Exception as fk_error:
                print(f"Warning: Could not get foreign keys for {table_name}: {str(fk_error)}")
                # Try to identify foreign keys by naming convention
                for column in table_info["columns"]:
                    col_name = column["column_name"].lower()
                    if col_name.endswith('_id') and not column["is_primary_key"]:
                        # Extract potential table name from column name
                        potential_table = col_name[:-3]  # Remove '_id' suffix
                        # Check if this table exists
                        if potential_table in [t.lower() for t in tables]:
                            print(f"Identified potential foreign key by naming convention: {column['column_name']} -> {potential_table}")
                            column["is_foreign_key"] = True
                            column["references"] = {
                                "table": next(t for t in tables if t.lower() == potential_table),
                                "column": "id"  # Assume the primary key is 'id'
                            }
        except Exception as column_error:
            print(f"Warning: Could not process columns for {table_name}: {str(column_error)}")
            continue

        schema_info.append(table_info)

    return schema_info


def discover_sqlite_schema(inspector) -> List[Dict[str, Any]]:
    """
    SQLite-specific schema discovery.
    """
    print("Using SQLite-specific schema discovery")
    schema_info = []

    # Get all tables and views
    tables = inspector.get_table_names()
    try:
        views = inspector.get_view_names()
        tables.extend(views)
    except Exception as view_error:
        print(f"Warning: Could not get views: {str(view_error)}")
        views = []

    print(f"Found {len(tables)} tables/views: {', '.join(tables)}")

    for table_name in tables:
        print(f"Processing table/view: {table_name}")
        table_info = {
            "table_name": table_name,
            "columns": [],
            "is_view": table_name in views
        }

        # Get columns for each table
        try:
            columns = inspector.get_columns(table_name)
            print(f"Found {len(columns)} columns in {table_name}")

            for column in columns:
                column_info = {
                    "column_name": column["name"],
                    "data_type": str(column["type"]),
                    "is_primary_key": column.get("primary_key", False),  # SQLite provides primary_key info directly
                    "is_foreign_key": False,
                    "is_nullable": column.get("nullable", True)
                }
                table_info["columns"].append(column_info)

            # SQLite doesn't always expose primary key info through the column attributes
            # so we also check through the inspector
            try:
                pks = inspector.get_pk_constraint(table_name)["constrained_columns"]
                print(f"Primary keys for {table_name}: {pks}")
                for pk in pks:
                    for column in table_info["columns"]:
                        if column["column_name"] == pk:
                            column["is_primary_key"] = True
            except Exception as pk_error:
                print(f"Warning: Could not get primary keys for {table_name}: {str(pk_error)}")
                # Already tried to identify primary keys from column attributes

            # Mark foreign keys - SQLite has basic FK support
            try:
                fks = inspector.get_foreign_keys(table_name)
                print(f"Foreign keys for {table_name}: {len(fks)}")
                for fk in fks:
                    print(f"  FK: {fk}")
                    for column in table_info["columns"]:
                        if column["column_name"] in fk["constrained_columns"]:
                            column["is_foreign_key"] = True
                            column["references"] = {
                                "table": fk["referred_table"],
                                "column": fk["referred_columns"][0]
                            }
            except Exception as fk_error:
                print(f"Warning: Could not get foreign keys for {table_name}: {str(fk_error)}")
                # Try to identify foreign keys by naming convention
                for column in table_info["columns"]:
                    col_name = column["column_name"].lower()
                    if col_name.endswith('_id') and not column["is_primary_key"]:
                        # Extract potential table name from column name
                        potential_table = col_name[:-3]  # Remove '_id' suffix
                        # Check if this table exists
                        if potential_table in [t.lower() for t in tables]:
                            print(f"Identified potential foreign key by naming convention: {column['column_name']} -> {potential_table}")
                            column["is_foreign_key"] = True
                            column["references"] = {
                                "table": next(t for t in tables if t.lower() == potential_table),
                                "column": "id"  # Assume the primary key is 'id'
                            }
        except Exception as column_error:
            print(f"Warning: Could not process columns for {table_name}: {str(column_error)}")
            continue

        schema_info.append(table_info)

    return schema_info


def save_discovered_schema(db: Session, connection_id: int, schema_info: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Save discovered schema to the database and detect relationships.
    Returns a tuple of (tables_data, relationships_data) for frontend display.
    """
    print(f"Saving discovered schema for connection {connection_id}")

    # Get the connection
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise ValueError(f"Connection with ID {connection_id} not found")

    # 创建数据库检查器，用于获取更详细的表结构信息
    engine = get_db_engine(connection)
    inspector = inspect(engine)

    # Track created tables and relationships
    tables_data = []
    relationships_data = []

    # Process each table
    for table_info in schema_info:
        table_name = table_info["table_name"]
        print(f"Processing table: {table_name}")

        # Create or update the table
        existing_table = crud.schema_table.get_by_name_and_connection(
            db=db, table_name=table_name, connection_id=connection_id
        )

        if existing_table:
            print(f"Table {table_name} already exists, updating...")
            table_obj = existing_table
        else:
            print(f"Creating new table: {table_name}")
            table_create = schemas.SchemaTableCreate(
                connection_id=connection_id,
                table_name=table_name,
                description=f"Auto-discovered table: {table_name}",
                ui_metadata={"position": {"x": 0, "y": 0}}  # Default position
            )
            table_obj = crud.schema_table.create(db=db, obj_in=table_create)

        # Add to tables_data for frontend
        tables_data.append({
            "id": table_obj.id,
            "table_name": table_obj.table_name,
            "description": table_obj.description,
            "ui_metadata": table_obj.ui_metadata
        })

        # Process columns for this table
        for column_info in table_info["columns"]:
            column_name = column_info["column_name"]

            # Check if column already exists
            existing_column = crud.schema_column.get_by_name_and_table(
                db=db, column_name=column_name, table_id=table_obj.id
            )

            if existing_column:
                print(f"Column {column_name} already exists, updating...")
                column_update = schemas.SchemaColumnUpdate(
                    data_type=column_info["data_type"],
                    is_primary_key=column_info["is_primary_key"],
                    is_foreign_key=column_info["is_foreign_key"],
                    is_unique=column_info.get("is_unique", False)  # 添加唯一标记
                )
                column_obj = crud.schema_column.update(
                    db=db, db_obj=existing_column, obj_in=column_update
                )
            else:
                print(f"Creating new column: {column_name}")
                column_create = schemas.SchemaColumnCreate(
                    table_id=table_obj.id,
                    column_name=column_name,
                    data_type=column_info["data_type"],
                    description=f"Auto-discovered column: {column_name}",
                    is_primary_key=column_info["is_primary_key"],
                    is_foreign_key=column_info["is_foreign_key"],
                    is_unique=column_info.get("is_unique", False)  # 添加唯一标记
                )
                column_obj = crud.schema_column.create(db=db, obj_in=column_create)

    # Process relationships after all tables and columns are created
    for table_info in schema_info:
        for column_info in table_info["columns"]:
            if column_info.get("is_foreign_key") and column_info.get("references"):
                source_table_name = table_info["table_name"]
                source_column_name = column_info["column_name"]
                target_table_name = column_info["references"]["table"]
                target_column_name = column_info["references"]["column"]

                print(f"Processing relationship: {source_table_name}.{source_column_name} -> {target_table_name}.{target_column_name}")

                # Get source and target tables
                source_table = crud.schema_table.get_by_name_and_connection(
                    db=db, table_name=source_table_name, connection_id=connection_id
                )
                target_table = crud.schema_table.get_by_name_and_connection(
                    db=db, table_name=target_table_name, connection_id=connection_id
                )

                if not source_table or not target_table:
                    print(f"Warning: Could not find tables for relationship")
                    continue

                # Get source and target columns
                source_column = crud.schema_column.get_by_name_and_table(
                    db=db, column_name=source_column_name, table_id=source_table.id
                )
                target_column = crud.schema_column.get_by_name_and_table(
                    db=db, column_name=target_column_name, table_id=target_table.id
                )

                if not source_column or not target_column:
                    print(f"Warning: Could not find columns for relationship")
                    continue

                # Check if relationship already exists
                existing_rel = crud.schema_relationship.get_by_columns(
                    db=db, source_column_id=source_column.id, target_column_id=target_column.id
                )

                # 使用优化后的关系类型判断逻辑
                print(f"\n[DEBUG] 分析关系: {source_table_name}.{source_column_name} -> {target_table_name}.{target_column_name}")
                print(f"[DEBUG] 源列是主键: {source_column.is_primary_key}")
                print(f"[DEBUG] 目标列是主键: {target_column.is_primary_key}")

                # 使用 schema_utils 中的函数确定关系类型
                try:
                    relationship_type = determine_relationship_type(
                        inspector=inspector,
                        source_table=source_table_name,
                        source_column=source_column_name,
                        target_table=target_table_name,
                        target_column=target_column_name,
                        schema_info=schema_info
                    )
                    print(f"[DEBUG] 确定的关系类型: {relationship_type}")
                except Exception as e:
                    print(f"[WARNING] 确定关系类型时出错: {str(e)}")
                    # 回退到基本逻辑
                    relationship_type = "1-to-N"  # 默认为一对多



                print(f"[DEBUG] 最终确定的关系类型: {relationship_type}")

                if existing_rel:
                    print(f"Relationship already exists, updating...")
                    rel_update = schemas.SchemaRelationshipUpdate(
                        relationship_type=relationship_type,
                        description=f"Auto-discovered relationship: {source_table_name}.{source_column_name} -> {target_table_name}.{target_column_name}"
                    )
                    rel_obj = crud.schema_relationship.update(
                        db=db, db_obj=existing_rel, obj_in=rel_update
                    )
                else:
                    print(f"Creating new relationship")
                    rel_create = schemas.SchemaRelationshipCreate(
                        connection_id=connection_id,
                        source_table_id=source_table.id,
                        source_column_id=source_column.id,
                        target_table_id=target_table.id,
                        target_column_id=target_column.id,
                        relationship_type=relationship_type,
                        description=f"Auto-discovered relationship: {source_table_name}.{source_column_name} -> {target_table_name}.{target_column_name}"
                    )
                    rel_obj = crud.schema_relationship.create(db=db, obj_in=rel_create)

                # Add to relationships_data for frontend
                relationships_data.append({
                    "id": rel_obj.id,
                    "source_table": source_table.table_name,
                    "source_table_id": source_table.id,
                    "source_column": source_column.column_name,
                    "source_column_id": source_column.id,
                    "target_table": target_table.table_name,
                    "target_table_id": target_table.id,
                    "target_column": target_column.column_name,
                    "target_column_id": target_column.id,
                    "relationship_type": rel_obj.relationship_type,
                    "description": rel_obj.description
                })

    # Sync to graph database
    try:
        sync_schema_to_graph_db(connection_id)
    except Exception as e:
        print(f"Warning: Failed to sync to graph database: {str(e)}")

    return tables_data, relationships_data


def sync_schema_to_graph_db(connection_id: int):
    """
    Sync schema metadata to Neo4j graph database.
    """
    try:
        print(f"Starting sync to Neo4j for connection_id: {connection_id}")
        # Connect to Neo4j
        print(f"Connecting to Neo4j at {settings.NEO4J_URI} with user {settings.NEO4J_USER}")
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        with driver.session() as session:
            # Clear existing schema for this connection
            print(f"Clearing existing schema for connection_id: {connection_id}")
            session.run(
                "MATCH (n {connection_id: $connection_id}) DETACH DELETE n",
                connection_id=connection_id
            )

            # Get all tables for this connection from MySQL
            from sqlalchemy.orm import Session
            from app.db.session import SessionLocal

            db = SessionLocal()
            try:
                print(f"Fetching tables for connection_id: {connection_id}")
                tables = crud.schema_table.get_by_connection(db=db, connection_id=connection_id)
                print(f"Found {len(tables)} tables for connection_id: {connection_id}")

                if len(tables) == 0:
                    print(f"Warning: No tables found for connection_id: {connection_id}")
                    return False

                # Create Table nodes
                for table in tables:
                    print(f"Creating Table node for table: {table.table_name} (id: {table.id})")
                    session.run(
                        """
                        CREATE (t:Table {
                            id: $id,
                            connection_id: $connection_id,
                            name: $name,
                            description: $description
                        })
                        """,
                        id=table.id,
                        connection_id=connection_id,
                        name=table.table_name,
                        description=table.description or ""
                    )

                    # Get columns for this table
                    columns = crud.schema_column.get_by_table(db=db, table_id=table.id)
                    print(f"Found {len(columns)} columns for table: {table.table_name}")

                    # Create Column nodes and HAS_COLUMN relationships
                    for column in columns:
                        print(f"Creating Column node for column: {column.column_name} (id: {column.id})")
                        session.run(
                            """
                            CREATE (c:Column {
                                id: $id,
                                name: $name,
                                type: $type,
                                description: $description,
                                is_pk: $is_pk,
                                is_fk: $is_fk,
                                connection_id: $connection_id
                            })
                            WITH c
                            MATCH (t:Table {id: $table_id})
                            CREATE (t)-[:HAS_COLUMN]->(c)
                            """,
                            id=column.id,
                            name=column.column_name,
                            type=column.data_type,
                            description=column.description or "",
                            is_pk=column.is_primary_key,
                            is_fk=column.is_foreign_key,
                            connection_id=connection_id,
                            table_id=table.id
                        )

                # Create FOREIGN_KEY relationships
                relationships = crud.schema_relationship.get_by_connection(db=db, connection_id=connection_id)
                print(f"Found {len(relationships)} relationships for connection_id: {connection_id}")

                for rel in relationships:
                    print(f"Creating REFERENCES relationship from column id: {rel.source_column_id} to column id: {rel.target_column_id}")
                    session.run(
                        """
                        MATCH (source:Column {id: $source_column_id})
                        MATCH (target:Column {id: $target_column_id})
                        CREATE (source)-[:REFERENCES {
                            type: $relationship_type,
                            description: $description,
                            connection_id: $connection_id
                        }]->(target)
                        """,
                        source_column_id=rel.source_column_id,
                        target_column_id=rel.target_column_id,
                        relationship_type=rel.relationship_type or "unknown",
                        description=rel.description or "",
                        connection_id=connection_id
                    )

                print(f"Successfully synced schema to Neo4j for connection_id: {connection_id}")
            finally:
                db.close()

        driver.close()
        return True
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Graph DB sync failed: {str(e)}\n{error_trace}")
        raise Exception(f"Graph DB sync failed: {str(e)}")
