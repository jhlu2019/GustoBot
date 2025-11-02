#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Milvus data import status"""

from pymilvus import connections, Collection, utility
import sys

def check_milvus():
    try:
        # Connect to Milvus
        connections.connect(
            alias="default",
            host="localhost",
            port="19530"
        )

        # Check if collection exists
        collection_names = utility.list_collections()
        print(f"Available collections: {collection_names}")

        if "recipes" in collection_names:
            collection = Collection("recipes")
            print(f"Collection 'recipes' loaded")
            print(f"Number of entities: {collection.num_entities}")

            # Get a sample of data
            if collection.num_entities > 0:
                results = collection.query(
                    expr="doc_id != ''",
                    output_fields=["doc_id", "source", "content"],
                    limit=3
                )

                print("\nSample records:")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. Document ID: {result['doc_id']}")
                    print(f"   Source: {result['source']}")
                    print(f"   Content: {result['content'][:100]}...")
        else:
            print("Collection 'recipes' not found")

    except Exception as e:
        print(f"Error: {e}")
        return False

    return True

if __name__ == "__main__":
    print("=== Checking Milvus Data ===")
    check_milvus()