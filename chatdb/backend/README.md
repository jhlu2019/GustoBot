# ChatDB Backend

This is the backend for the ChatDB Text2SQL system. It's built with Python, FastAPI, SQLAlchemy, and Neo4j.

## Features

- RESTful API for database connection management
- Schema discovery and management
- Text2SQL conversion using LLM
- Value mapping for natural language terms

## Getting Started

### Prerequisites

- Python 3.9+
- MySQL
- Neo4j

### Installation

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3、 Create Database:
   手工创建数据库：
   ```
   create database chatdb;
   ```
4. Init database:
   ```
   python init_db.py
   ```
5. 修改 .env文件中的数据库配置信息

6. Start the development server:
   ```
   uvicorn main:app --reload
   ```

## Project Structure

- `app/api/`: API endpoints
- `app/core/`: Core functionality and configuration
- `app/db/`: Database models and connections
- `app/models/`: SQLAlchemy models
- `app/schemas/`: Pydantic schemas for API
- `app/services/`: Business logic


