"""
Translate classifier output into concrete cypher queries.
"""
from __future__ import annotations

from typing import Dict, List


NODE_PROPERTY_MAP = {
    "做法": ("instructions", "做法"),
    "耗时": ("cook_time", "耗时"),
}

RELATION_PROPERTY_MAP = {
    "口味": ("HAS_FLAVOR", "Flavor", "口味"),
    "工艺": ("USES_METHOD", "CookingMethod", "工艺"),
    "类型": ("BELONGS_TO_TYPE", "DishType", "类型"),
    "菜系": ("BELONGS_TO_CUISINE", "CuisineStyle", "菜系"),
}


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
                for prop in properties:
                    if prop in NODE_PROPERTY_MAP:
                        field, alias = NODE_PROPERTY_MAP[prop]
                        sql_statements.append(
                            f"MATCH (n:{label} {{name: $name}}) RETURN n.{field} AS `{alias}`",
                        )
                    elif prop in RELATION_PROPERTY_MAP:
                        rel, target_label, alias = RELATION_PROPERTY_MAP[prop]
                        sql_statements.append(
                            (
                                "MATCH (n:{label} {{name: $name}})-[:{rel}]->(m:{target_label}) "
                                "RETURN collect(m.name) AS `{alias}`"
                            ).format(label=label, rel=rel, target_label=target_label, alias=alias),
                        )
                args["parameters"] = {"name": name}

        elif question_type == "property_constraint":
            constraints = args.get("constraints", {})
            if constraints:
                clauses = ["MATCH (dish:Dish)"]
                conditions = []
                parameters: Dict[str, object] = {}
                rel_counter = 0

                for slot, value in constraints.items():
                    if slot in NODE_PROPERTY_MAP:
                        field, _ = NODE_PROPERTY_MAP[slot]
                        param_key = field
                        parameters[param_key] = value
                        conditions.append(f"dish.{field} = ${param_key}")
                    elif slot in RELATION_PROPERTY_MAP:
                        rel, target_label, _ = RELATION_PROPERTY_MAP[slot]
                        alias = f"rel_{rel_counter}"
                        rel_counter += 1
                        parameters[f"{alias}_name"] = value
                        clauses.append(
                            f"MATCH (dish)-[:{rel}]->({alias}:{target_label} {{name: ${alias}_name}})"
                        )

                if parameters or conditions or rel_counter:
                    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
                    query = "\n".join(clauses)
                    if where_clause:
                        query = f"{query}\n{where_clause}"
                    query = f"{query}\nRETURN dish.name AS name LIMIT 15"

                    args["parameters"] = parameters
                    sql_statements.append(query)

        elif question_type == "relationship_constraint":
            nodes = args.get("nodes", {})
            relationships = args.get("relationships", [])
            for name, labels in nodes.items():
                if not labels:
                    continue
                label = labels[0]
                if label == "Ingredient":
                    statements = [
                        (
                            "MATCH (dish:Dish)-[rel:{rel}]->(ingredient:Ingredient {{name: $name}}) "
                            "RETURN type(rel) AS relation, dish.name AS name LIMIT 15"
                        ).format(rel=rel_label)
                        for rel_label in relationships
                    ]
                else:
                    statements = [
                        (
                            "MATCH (dish:Dish {{name: $name}})-[rel:{rel}]->(ingredient:Ingredient) "
                            "RETURN type(rel) AS relation, ingredient.name AS name"
                        ).format(rel=rel_label)
                        for rel_label in relationships
                    ]
                sql_statements.extend(statements)
                args["parameters"] = {"name": name}

        elif question_type == "relationship_query":
            nodes = args.get("nodes", {})
            relationships = args.get("relationships", [])
            recipe_name = next((name for name, labels in nodes.items() if labels and labels[0] == "Dish"), "")
            material_name = next(
                (name for name, labels in nodes.items() if labels and labels[0] == "Ingredient"), "",
            )
            if recipe_name and material_name:
                args["parameters"] = {"recipe_name": recipe_name, "material_name": material_name}
                sql_statements.extend(
                    (
                        "MATCH (dish:Dish {{name: $recipe_name}})-[rel:{rel}]->(ingredient:Ingredient {{name: $material_name}}) "
                        "RETURN rel.amount_text AS amount_text"
                    ).format(rel=rel_label)
                    for rel_label in relationships
                )

        return {
            "question_type": question_type,
            "sql": [stmt for stmt in sql_statements if stmt],
            "parameters": args.get("parameters", {}),
        }
