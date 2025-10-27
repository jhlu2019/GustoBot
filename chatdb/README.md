# ChatDB - Text2SQL System（但问智能100%自研）

ChatDB is an intelligent Text2SQL system that allows users to query databases using natural language. The system features a React frontend for schema visualization and management, a Python FastAPI backend for processing queries, and uses MySQL and Neo4j for metadata storage and schema relationship management.

## Features

- **Database Connection Management**: Connect to various database systems
- **Schema Visualization & Management**: Visualize and maintain database schema with an interactive graph interface
- **Intelligent Query**: Convert natural language questions to SQL queries using LLM technology
- **Value Mappings**: Map natural language terms to actual database values

## Architecture

- **Frontend**: React with Ant Design and React Flow for visualization
- **Backend**: Python FastAPI
- **Metadata Storage**: MySQL
- **Schema Relationship Storage**: Neo4j
- **LLM Integration**: OpenAI GPT-4 (or other LLM services)

## Prerequisites

- Docker and Docker Compose
- OpenAI API Key (or other LLM service API key)

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/chatdb.git
   cd chatdb
   ```

2. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Start the services using Docker Compose:
   ```
   docker-compose up -d
   ```

4. Initialize the database (first time only):
   ```
   docker-compose exec backend python init_db.py
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs
   - Neo4j Browser: http://localhost:7474 (username: neo4j, password: password)

## Usage Guide

### 1. Database Connections

1. Navigate to the "Database Connections" page
2. Click "Add Connection" to create a new database connection
3. Fill in the connection details and click "Save"
4. Test the connection using the "Test" button

### 2. Schema Management

1. Navigate to the "Schema Management" page
2. Select a database connection from the dropdown
3. The system will discover the schema from the target database
4. Drag tables from the left panel to the canvas
5. Connect tables by dragging from one table to another
6. Click on tables or relationships to edit their properties
7. Click "Publish Schema" to save your changes

### 3. Intelligent Query

1. Navigate to the "Intelligent Query" page
2. Select a database connection from the dropdown
3. Enter your question in natural language
4. Click "Execute Query" to generate and run the SQL
5. View the generated SQL, query results, and context information

### 4. Value Mappings

1. Navigate to the "Value Mappings" page
2. Select a connection, table, and column
3. Add mappings between natural language terms and database values
4. These mappings will be used when processing natural language queries

## Development

### Backend

The backend is built with FastAPI and uses SQLAlchemy for database ORM.

```
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

The frontend is built with React and uses Ant Design for UI components.

```
cd frontend
npm install
npm start
```

