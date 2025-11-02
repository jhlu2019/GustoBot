#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple data check for all databases"""

import psycopg2
import mysql.connector
from neo4j import GraphDatabase
import requests

def check_postgres():
    print("=== PostgreSQL Check ===")
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5433,
            database="vector_db",
            user="postgres",
            password="postgres"
        )
        cursor = conn.cursor()

        # Check tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()
        print(f"Tables: {len(tables)}")

        for (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")

        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_mysql():
    print("\n=== MySQL Check ===")
    try:
        conn = mysql.connector.connect(
            host="localhost",
            port=13306,
            user="recipe_user",
            password="recipepass",
            database="recipe_db"
        )
        cursor = conn.cursor()

        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"Tables: {len(tables)}")

        for (table,) in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} records")

        conn.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_neo4j():
    print("\n=== Neo4j Check ===")
    try:
        driver = GraphDatabase.driver("bolt://localhost:17687", auth=("neo4j", "recipepass"))
        session = driver.session()

        # Count nodes
        result = session.run("MATCH (n) RETURN count(n) as count")
        count = result.single()["count"]
        print(f"Total nodes: {count}")

        # Count relationships
        result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result.single()["count"]
        print(f"Total relationships: {rel_count}")

        session.close()
        driver.close()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_apis():
    print("\n=== API Status Check ===")

    # Main API
    try:
        r = requests.get("http://localhost:8000/docs", timeout=5)
        print(f"Main API: {r.status_code}")
    except:
        print("Main API: Failed")

    # KB API
    try:
        r = requests.get("http://localhost:8100/docs", timeout=5)
        print(f"KB API: {r.status_code}")
    except:
        print("KB API: Failed")

def main():
    print("GustoBot Data Import Status\n")

    pg_ok = check_postgres()
    mysql_ok = check_mysql()
    neo4j_ok = check_neo4j()
    check_apis()

    print("\n=== Summary ===")
    print(f"PostgreSQL: {'OK' if pg_ok else 'FAIL'}")
    print(f"MySQL: {'OK' if mysql_ok else 'FAIL'}")
    print(f"Neo4j: {'OK' if neo4j_ok else 'FAIL'}")

    if all([pg_ok, mysql_ok, neo4j_ok]):
        print("\nAll databases are ready!")

if __name__ == "__main__":
    main()