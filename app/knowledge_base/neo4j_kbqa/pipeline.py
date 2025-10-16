"""
Main KBQA pipeline wiring the classifier, parser and answer searcher together.
"""
from __future__ import annotations

from typing import Any, Dict

from .answer_search import AnswerSearcher
from .database import Neo4jDatabase
from .question_classifier import QuestionClassifier
from .question_parser import QuestionParser


class Neo4jQAPipeline:
    def __init__(self, database: Neo4jDatabase) -> None:
        self._classifier = QuestionClassifier()
        self._parser = QuestionParser()
        self._searcher = AnswerSearcher(database)

    def ask(self, question: str) -> Dict[str, Any]:
        classification = self._classifier.classify(question)
        parsed = self._parser.parse(
            {"question_type": classification.question_type, "args": classification.args},
        )
        answer = self._searcher.search(parsed)

        return {
            "question_type": classification.question_type,
            "answer": answer,
            "cypher": parsed.get("sql", []),
        }
