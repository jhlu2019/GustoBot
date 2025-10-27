from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from neo4j import GraphDatabase

from app import crud
from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/{connection_id}", response_model=Dict[str, Any])
def get_graph_data(
    *,
    db: Session = Depends(deps.get_db),
    connection_id: int,
) -> Any:
    """
    Get graph visualization data for a specific connection from Neo4j.
    Returns nodes and edges in a format suitable for visualization.
    """
    # Check if connection exists
    connection = crud.db_connection.get(db=db, id=connection_id)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    try:
        # Connect to Neo4j
        print(f"Connecting to Neo4j at {settings.NEO4J_URI} with user {settings.NEO4J_USER}")
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )

        # Prepare result structure
        result = {
            "nodes": [],
            "edges": []
        }

        print(f"Fetching graph data for connection_id: {connection_id}")

        with driver.session() as session:
            # Get all tables for this connection
            table_query = """
            MATCH (t:Table {connection_id: $connection_id})
            RETURN t
            """
            print(f"Executing table query: {table_query}")
            table_records = session.run(table_query, connection_id=connection_id)

            # Process tables into nodes
            table_count = 0
            for record in table_records:
                table_count += 1
                table = record["t"]
                result["nodes"].append({
                    "id": f"table-{table['id']}",
                    "type": "table",
                    "data": {
                        "id": table["id"],
                        "label": table["name"],
                        "description": table.get("description", ""),
                        "nodeType": "table"
                    }
                })
            print(f"Found {table_count} tables")

            # Get all columns for this connection
            column_query = """
            MATCH (t:Table {connection_id: $connection_id})-[:HAS_COLUMN]->(c:Column)
            RETURN c, t.id as table_id, t.name as table_name
            """
            print(f"Executing column query: {column_query}")
            column_records = session.run(column_query, connection_id=connection_id)

            # Process columns into nodes
            column_count = 0
            for record in column_records:
                column_count += 1
                column = record["c"]
                table_id = record["table_id"]
                table_name = record["table_name"]

                result["nodes"].append({
                    "id": f"column-{column['id']}",
                    "type": "column",
                    "data": {
                        "id": column["id"],
                        "label": column["name"],
                        "dataType": column["type"],
                        "description": column.get("description", ""),
                        "isPrimaryKey": column.get("is_pk", False),
                        "isForeignKey": column.get("is_fk", False),
                        "tableId": table_id,
                        "tableName": table_name,
                        "nodeType": "column"
                    }
                })

                # Add edge from table to column
                result["edges"].append({
                    "id": f"table-{table_id}-column-{column['id']}",
                    "source": f"table-{table_id}",
                    "target": f"column-{column['id']}",
                    "type": "hasColumn",
                    "data": {
                        "relationshipType": "HAS_COLUMN"
                    }
                })
            print(f"Found {column_count} columns")

            # Get all relationships between columns
            relationship_query = """
            MATCH (source:Column {connection_id: $connection_id})-[r:REFERENCES]->(target:Column)
            RETURN source, target, r
            """
            print(f"Executing relationship query: {relationship_query}")
            relationship_records = session.run(relationship_query, connection_id=connection_id)

            # Process relationships into edges
            relationship_count = 0
            for record in relationship_records:
                relationship_count += 1
                source = record["source"]
                target = record["target"]
                relationship = record["r"]

                result["edges"].append({
                    "id": f"rel-{source['id']}-{target['id']}",
                    "source": f"column-{source['id']}",
                    "target": f"column-{target['id']}",
                    "type": "references",
                    "data": {
                        "relationshipType": relationship.get("type", "unknown"),
                        "description": relationship.get("description", "")
                    }
                })
            print(f"Found {relationship_count} relationships")

        driver.close()
        print(f"Returning result with {len(result['nodes'])} nodes and {len(result['edges'])} edges")
        return result

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error retrieving graph data: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail=f"Error retrieving graph data: {str(e)}")
