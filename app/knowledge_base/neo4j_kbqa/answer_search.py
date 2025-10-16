"""
Execute generated Cypher queries and format answers for the API response.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from .database import Neo4jDatabase


class AnswerSearcher:
    def __init__(self, database: Neo4jDatabase) -> None:
        self._database = database

    def search(self, parsed: Dict[str, Any]) -> str:
        question_type: str = parsed.get("question_type", "")
        sql_statements: List[str] = parsed.get("sql", [])
        parameters: Dict[str, Any] = parsed.get("parameters", {}) or {}

        answers: List[Dict[str, Any]] = []
        for statement in sql_statements:
            answers.extend(self._database.fetch(statement, parameters))

        return self._format_answers(question_type, answers)

    def _format_answers(self, question_type: str, answers: List[Dict[str, Any]]) -> str:
        if not answers:
            return "抱歉，小助手暂时无法回答您的问题。"

        if question_type == "recipe_property":
            return "\n".join(
                "、".join(f"{key}: {value}" for key, value in answer.items())
                for answer in answers
            )

        if question_type in {"property_constraint", "relationship_constraint"}:
            names = [answer.get("name") or answer.get("n.name") for answer in answers]
            filtered = [name for name in names if name]
            if filtered:
                return "、".join(filtered)

        if question_type == "relationship_query":
            quantities = [answer.get("quantity") or answer.get("r.用量") for answer in answers]
            filtered = [quantity for quantity in quantities if quantity]
            if filtered:
                return "、".join(filtered)

        # fallback: return JSON representation
        return "\n".join(str(answer) for answer in answers)

