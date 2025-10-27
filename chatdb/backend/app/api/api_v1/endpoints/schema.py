from typing import Any, List, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.services.schema_service import discover_schema, sync_schema_to_graph_db, save_discovered_schema

router = APIRouter()


@router.get("/{connection_id}/discover", response_model=List[Dict[str, Any]])
def discover_connection_schema(
    *,
    db: Session = Depends(deps.get_db),
    connection_id: int,
) -> Any:
    """
    Discover schema from a database connection.
    """
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Discover schema from the database
        schema_info = discover_schema(connection)

        # For each table, check if it already exists in our metadata
        for table_info in schema_info:
            table_name = table_info["table_name"]
            existing_table = crud.schema_table.get_by_name_and_connection(
                db=db,
                table_name=table_name,
                connection_id=connection_id
            )

            # If the table exists in our metadata, add its ID to the schema info
            if existing_table:
                table_info["id"] = existing_table.id

                # Add column IDs if they exist in our metadata
                for column_info in table_info["columns"]:
                    column_name = column_info["column_name"]
                    existing_column = crud.schema_column.get_by_name_and_table(
                        db=db,
                        column_name=column_name,
                        table_id=existing_table.id
                    )
                    if existing_column:
                        column_info["id"] = existing_column.id

        return schema_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error discovering schema: {str(e)}")


@router.get("/{connection_id}/metadata", response_model=List[schemas.SchemaTableWithRelationships])
def get_schema_metadata(
    *,
    db: Session = Depends(deps.get_db),
    connection_id: int,
) -> Any:
    """
    Get maintained schema metadata for a connection.
    """
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Get tables for this connection
        tables = crud.schema_table.get_by_connection(db=db, connection_id=connection_id)

        # Prepare the response with tables, columns and relationships
        result = []
        for table in tables:
            # Get columns for this table
            columns = crud.schema_column.get_by_table(db=db, table_id=table.id)

            # Get relationships for this table (both source and target)
            source_relationships = crud.schema_relationship.get_by_source_table(db=db, source_table_id=table.id)
            target_relationships = crud.schema_relationship.get_by_target_table(db=db, target_table_id=table.id)

            # Convert relationships to detailed format
            detailed_relationships = []

            for rel in source_relationships:
                source_column = crud.schema_column.get(db=db, id=rel.source_column_id)
                target_column = crud.schema_column.get(db=db, id=rel.target_column_id)
                target_table = crud.schema_table.get(db=db, id=rel.target_table_id)

                if source_column and target_column and target_table:
                    detailed_rel = schemas.SchemaRelationshipDetailed(
                        id=rel.id,
                        connection_id=rel.connection_id,
                        source_table_id=rel.source_table_id,
                        source_column_id=rel.source_column_id,
                        target_table_id=rel.target_table_id,
                        target_column_id=rel.target_column_id,
                        relationship_type=rel.relationship_type,
                        description=rel.description,
                        created_at=rel.created_at,
                        updated_at=rel.updated_at,
                        source_table_name=table.table_name,
                        source_column_name=source_column.column_name,
                        target_table_name=target_table.table_name,
                        target_column_name=target_column.column_name
                    )
                    detailed_relationships.append(detailed_rel)

            for rel in target_relationships:
                source_column = crud.schema_column.get(db=db, id=rel.source_column_id)
                target_column = crud.schema_column.get(db=db, id=rel.target_column_id)
                source_table = crud.schema_table.get(db=db, id=rel.source_table_id)

                if source_column and target_column and source_table:
                    detailed_rel = schemas.SchemaRelationshipDetailed(
                        id=rel.id,
                        connection_id=rel.connection_id,
                        source_table_id=rel.source_table_id,
                        source_column_id=rel.source_column_id,
                        target_table_id=rel.target_table_id,
                        target_column_id=rel.target_column_id,
                        relationship_type=rel.relationship_type,
                        description=rel.description,
                        created_at=rel.created_at,
                        updated_at=rel.updated_at,
                        source_table_name=source_table.table_name,
                        source_column_name=source_column.column_name,
                        target_table_name=table.table_name,
                        target_column_name=target_column.column_name
                    )
                    detailed_relationships.append(detailed_rel)

            # Convert SQLAlchemy model objects to Pydantic model objects
            pydantic_columns = [
                schemas.SchemaColumn(
                    id=column.id,
                    table_id=column.table_id,
                    column_name=column.column_name,
                    data_type=column.data_type,
                    description=column.description,
                    is_primary_key=column.is_primary_key,
                    is_foreign_key=column.is_foreign_key,
                    created_at=column.created_at,
                    updated_at=column.updated_at
                ) for column in columns
            ]

            # Create a SchemaTableWithRelationships object
            table_with_columns = schemas.SchemaTableWithRelationships(
                id=table.id,
                connection_id=table.connection_id,
                table_name=table.table_name,
                description=table.description,
                ui_metadata=table.ui_metadata,
                created_at=table.created_at,
                updated_at=table.updated_at,
                columns=pydantic_columns,
                relationships=detailed_relationships
            )
            result.append(table_with_columns)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving schema metadata: {str(e)}")


@router.post("/{connection_id}/publish", response_model=Dict[str, Any])
def publish_schema(
    *,
    db: Session = Depends(deps.get_db),
    connection_id: int,
    schema_data: Dict[str, Any],
) -> Any:
    """
    Publish schema metadata to MySQL and Graph DB.
    """
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Save to MySQL
        tables_data = schema_data.get("tables", [])
        relationships_data = schema_data.get("relationships", [])

        # Process tables and columns
        for table_data in tables_data:
            table_obj = crud.schema_table.get_by_name_and_connection(
                db=db,
                table_name=table_data["table_name"],
                connection_id=connection_id
            )

            if table_obj:
                # Update existing table
                table_update = schemas.SchemaTableUpdate(
                    description=table_data.get("description"),
                    ui_metadata=table_data.get("ui_metadata")
                )
                table_obj = crud.schema_table.update(db=db, db_obj=table_obj, obj_in=table_update)
            else:
                # Create new table
                table_create = schemas.SchemaTableCreate(
                    connection_id=connection_id,
                    table_name=table_data["table_name"],
                    description=table_data.get("description"),
                    ui_metadata=table_data.get("ui_metadata")
                )
                table_obj = crud.schema_table.create(db=db, obj_in=table_create)

            # Process columns
            for column_data in table_data.get("columns", []):
                column_obj = crud.schema_column.get_by_name_and_table(
                    db=db,
                    column_name=column_data["column_name"],
                    table_id=table_obj.id
                )

                if column_obj:
                    # Update existing column
                    column_update = schemas.SchemaColumnUpdate(
                        description=column_data.get("description"),
                        is_primary_key=column_data.get("is_primary_key"),
                        is_foreign_key=column_data.get("is_foreign_key")
                    )
                    crud.schema_column.update(db=db, db_obj=column_obj, obj_in=column_update)
                else:
                    # Create new column
                    column_create = schemas.SchemaColumnCreate(
                        table_id=table_obj.id,
                        column_name=column_data["column_name"],
                        data_type=column_data["data_type"],
                        description=column_data.get("description"),
                        is_primary_key=column_data.get("is_primary_key", False),
                        is_foreign_key=column_data.get("is_foreign_key", False)
                    )
                    crud.schema_column.create(db=db, obj_in=column_create)

        # Get all existing relationships for this connection
        existing_relationships = crud.schema_relationship.get_by_connection(db=db, connection_id=connection_id)

        # Track which relationships are still valid
        processed_relationship_ids = set()

        # Process relationships from the frontend
        for rel_data in relationships_data:
            # Find source and target tables
            source_table = crud.schema_table.get_by_name_and_connection(
                db=db,
                table_name=rel_data["source_table"],
                connection_id=connection_id
            )
            target_table = crud.schema_table.get_by_name_and_connection(
                db=db,
                table_name=rel_data["target_table"],
                connection_id=connection_id
            )

            if not source_table or not target_table:
                continue

            # Find source and target columns
            source_column = crud.schema_column.get_by_name_and_table(
                db=db,
                column_name=rel_data["source_column"],
                table_id=source_table.id
            )
            target_column = crud.schema_column.get_by_name_and_table(
                db=db,
                column_name=rel_data["target_column"],
                table_id=target_table.id
            )

            if not source_column or not target_column:
                continue

            # Check if relationship exists
            rel_obj = crud.schema_relationship.get_by_columns(
                db=db,
                source_column_id=source_column.id,
                target_column_id=target_column.id
            )

            if rel_obj:
                # Update existing relationship
                rel_update = schemas.SchemaRelationshipUpdate(
                    relationship_type=rel_data.get("relationship_type"),
                    description=rel_data.get("description")
                )
                crud.schema_relationship.update(db=db, db_obj=rel_obj, obj_in=rel_update)
                # Mark this relationship as processed
                processed_relationship_ids.add(rel_obj.id)
            else:
                # Create new relationship
                rel_create = schemas.SchemaRelationshipCreate(
                    connection_id=connection_id,
                    source_table_id=source_table.id,
                    source_column_id=source_column.id,
                    target_table_id=target_table.id,
                    target_column_id=target_column.id,
                    relationship_type=rel_data.get("relationship_type"),
                    description=rel_data.get("description")
                )
                new_rel = crud.schema_relationship.create(db=db, obj_in=rel_create)
                # Mark this new relationship as processed
                processed_relationship_ids.add(new_rel.id)

        # Delete relationships that are no longer in the frontend
        for rel in existing_relationships:
            if rel.id not in processed_relationship_ids:
                # This relationship was not in the frontend data, so delete it
                crud.schema_relationship.remove(db=db, id=rel.id)

        # Sync to Graph DB
        sync_schema_to_graph_db(connection_id)

        return {"status": "success", "message": "Schema published successfully"}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error publishing schema: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Error publishing schema: {str(e)}")


@router.get("/{connection_id}/saved", response_model=Dict[str, Any])
def get_saved_schema(
    *,
    db: Session = Depends(deps.get_db),
    connection_id: int,
) -> Any:
    """
    Get saved schema with UI metadata for a connection.
    """
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Get tables for this connection
        tables = crud.schema_table.get_by_connection(db=db, connection_id=connection_id)

        # Prepare tables data with UI metadata
        tables_data = []
        for table in tables:
            # Get columns for this table
            columns = crud.schema_column.get_by_table(db=db, table_id=table.id)

            # Convert columns to simple dict format
            columns_data = [
                {
                    "id": column.id,
                    "column_name": column.column_name,
                    "data_type": column.data_type,
                    "description": column.description,
                    "is_primary_key": column.is_primary_key,
                    "is_foreign_key": column.is_foreign_key
                } for column in columns
            ]

            # Add table with UI metadata
            tables_data.append({
                "id": table.id,
                "table_name": table.table_name,
                "description": table.description,
                "ui_metadata": table.ui_metadata,
                "columns": columns_data
            })

        # Get all relationships for this connection
        relationships = crud.schema_relationship.get_by_connection(db=db, connection_id=connection_id)

        # Convert relationships to simple dict format
        relationships_data = []
        for rel in relationships:
            source_table = crud.schema_table.get(db=db, id=rel.source_table_id)
            target_table = crud.schema_table.get(db=db, id=rel.target_table_id)
            source_column = crud.schema_column.get(db=db, id=rel.source_column_id)
            target_column = crud.schema_column.get(db=db, id=rel.target_column_id)

            if source_table and target_table and source_column and target_column:
                relationships_data.append({
                    "id": rel.id,
                    "source_table": source_table.table_name,
                    "source_table_id": source_table.id,
                    "source_column": source_column.column_name,
                    "source_column_id": source_column.id,
                    "target_table": target_table.table_name,
                    "target_table_id": target_table.id,
                    "target_column": target_column.column_name,
                    "target_column_id": target_column.id,
                    "relationship_type": rel.relationship_type,
                    "description": rel.description
                })

        return {
            "tables": tables_data,
            "relationships": relationships_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving saved schema: {str(e)}")


@router.post("/{connection_id}/sync-to-neo4j", response_model=Dict[str, Any])
def sync_to_neo4j(
    *,
    db: Session = Depends(deps.get_db),
    connection_id: int,
) -> Any:
    """
    Manually sync schema metadata to Neo4j graph database.
    """
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Sync to Graph DB
        result = sync_schema_to_graph_db(connection_id)
        if result:
            return {"status": "success", "message": "Schema synced to Neo4j successfully"}
        else:
            return {"status": "warning", "message": "No tables found to sync to Neo4j"}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error syncing to Neo4j: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Error syncing to Neo4j: {str(e)}")


@router.post("/{connection_id}/discover-and-sync", response_model=Dict[str, Any])
def discover_and_sync(
    *,
    db: Session = Depends(deps.get_db),
    connection_id: int,
) -> Any:
    """
    Discover schema from database, save it, and sync to Neo4j.
    """
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Discover schema
        schema_info = discover_schema(connection)

        # Save discovered schema
        tables_data, relationships_data = save_discovered_schema(db, connection_id, schema_info)

        return {
            "status": "success",
            "message": "Schema discovered and synced to Neo4j successfully",
            "tables": len(tables_data),
            "relationships": len(relationships_data)
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error discovering and syncing schema: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Error discovering and syncing schema: {str(e)}")


@router.put("/tables/{table_id}", response_model=schemas.SchemaTable)
def update_table(
    *,
    db: Session = Depends(deps.get_db),
    table_id: int,
    table_in: schemas.SchemaTableUpdate,
) -> Any:
    """
    Update a table's information.
    """
    table = crud.schema_table.get(db=db, id=table_id)
    if not table:
        raise HTTPException(status_code=404, detail="Table not found")

    try:
        table = crud.schema_table.update(db=db, db_obj=table, obj_in=table_in)
        return table
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating table: {str(e)}")


@router.put("/columns/{column_id}", response_model=schemas.SchemaColumn)
def update_column(
    *,
    db: Session = Depends(deps.get_db),
    column_id: int,
    column_in: schemas.SchemaColumnUpdate,
) -> Any:
    """
    Update a column's information.
    """
    column = crud.schema_column.get(db=db, id=column_id)
    if not column:
        raise HTTPException(status_code=404, detail="Column not found")

    try:
        column = crud.schema_column.update(db=db, db_obj=column, obj_in=column_in)
        return column
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating column: {str(e)}")
