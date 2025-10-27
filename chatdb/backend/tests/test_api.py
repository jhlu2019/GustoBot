import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create the tables
        Base.metadata.create_all(bind=engine)
        
        # Create a test connection
        response = client.post(
            "/api/connections/",
            json={
                "name": "Test Connection",
                "db_type": "mysql",
                "host": "localhost",
                "port": 3306,
                "username": "test",
                "password": "test",
                "database_name": "test_db"
            },
        )
        cls.connection_id = response.json()["id"]

    def test_read_connections(self):
        response = client.get("/api/connections/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["name"], "Test Connection")

    def test_read_connection(self):
        response = client.get(f"/api/connections/{self.connection_id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Test Connection")

    def test_update_connection(self):
        response = client.put(
            f"/api/connections/{self.connection_id}",
            json={"name": "Updated Test Connection"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Updated Test Connection")

    def test_create_value_mapping(self):
        # First, create a schema table
        table_response = client.post(
            f"/api/schema/{self.connection_id}/publish",
            json={
                "tables": [
                    {
                        "table_name": "customers",
                        "description": "Customer information",
                        "columns": [
                            {
                                "column_name": "customer_name",
                                "data_type": "VARCHAR",
                                "description": "Customer name",
                                "is_primary_key": False,
                                "is_foreign_key": False
                            }
                        ]
                    }
                ],
                "relationships": []
            }
        )
        self.assertEqual(table_response.status_code, 200)
        
        # Get the schema metadata to find the column ID
        schema_response = client.get(f"/api/schema/{self.connection_id}/metadata")
        self.assertEqual(schema_response.status_code, 200)
        
        # Find the column ID for customer_name
        column_id = None
        for table in schema_response.json():
            if table["table_name"] == "customers":
                for column in table["columns"]:
                    if column["column_name"] == "customer_name":
                        column_id = column["id"]
                        break
                break
        
        self.assertIsNotNone(column_id)
        
        # Create a value mapping
        mapping_response = client.post(
            "/api/value-mappings/",
            json={
                "column_id": column_id,
                "nl_term": "中石化",
                "db_value": "中国石化"
            }
        )
        self.assertEqual(mapping_response.status_code, 200)
        self.assertEqual(mapping_response.json()["nl_term"], "中石化")
        self.assertEqual(mapping_response.json()["db_value"], "中国石化")


if __name__ == "__main__":
    unittest.main()
