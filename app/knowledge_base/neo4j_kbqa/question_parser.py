"""
Translate classifier output into concrete cypher queries.
"""
from __future__ import annotations

from typing import Dict, List


class QuestionParser:
    """Build simple Cypher snippets based on the detected question intent."""

    def parse(self, classification: Dict[str, object]) -> Dict[str, object]:
        question_type = classification.get("question_type") or ""
        args = classification.get("args") or {}
        sql_statements: List[str] = []

        if question_type == "recipe_property":
            nodes = args.get("nodes", {})
            properties: List[str] = args.get("properties", [])
            for name, labels in nodes.items():
                if not labels:
                    continue
                label = labels[0]
                projections = ", ".join(f"n.{prop}" for prop in properties)
                sql_statements.append(
                    f"MATCH (n:{label} {{name: $name}}) RETURN {projections}",
                )
                args["parameters"] = {"name": name}

        elif question_type == "property_constraint":
            constraints = args.get("constraints", {})
            conditions = " AND ".join(f"n.{k} = ${k}" for k in constraints.keys())
            if conditions:
                args["parameters"] = constraints
                sql_statements.append(
                    f"MATCH (n) WHERE {conditions} RETURN n.name LIMIT 15",
                )

        elif question_type == "relationship_constraint":
            nodes = args.get("nodes", {})
            relationships = args.get("relationships", [])
            for name, labels in nodes.items():
                if not labels:
                    continue
                label = labels[0]
                if label == "material":
                    statements = [
                        (
                            "MATCH (recipe:recipe)-[r:{rel}]->(material:material {{name: $name}}) "
                            "RETURN type(r) AS relation, recipe.name AS name LIMIT 15"
                        ).format(rel=rel_label)
                        for rel_label in relationships
                    ]
                else:
                    statements = [
                        (
                            "MATCH (recipe:recipe {{name: $name}})-[r:{rel}]->(material:material) "
                            "RETURN type(r) AS relation, material.name AS name"
                        ).format(rel=rel_label)
                        for rel_label in relationships
                    ]
                sql_statements.extend(statements)
                args["parameters"] = {"name": name}

        elif question_type == "relationship_query":
            nodes = args.get("nodes", {})
            relationships = args.get("relationships", [])
            recipe_name = next((name for name, labels in nodes.items() if labels and labels[0] == "recipe"), "")
            material_name = next(
                (name for name, labels in nodes.items() if labels and labels[0] == "material"), "",
            )
            if recipe_name and material_name:
                args["parameters"] = {"recipe_name": recipe_name, "material_name": material_name}
                sql_statements.extend(
                    (
                        "MATCH (recipe:recipe {{name: $recipe_name}})-[r:{rel}]->(material:material {{name: $material_name}}) "
                        "RETURN r.用量 AS quantity"
                    ).format(rel=rel_label)
                    for rel_label in relationships
                )

        return {
            "question_type": question_type,
            "sql": [stmt for stmt in sql_statements if stmt],
            "parameters": args.get("parameters", {}),
        }

