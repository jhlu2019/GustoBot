"""
Fuzzy entity matcher for recipe knowledge graph queries.
"""
from __future__ import annotations

from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Tuple


class FuzzyMatcher:
    """Approximate matcher that uses character overlap along with edit distance."""

    def __init__(self, entity_dict: Dict[str, Iterable[str]]) -> None:
        self.entity_dict: Dict[str, List[str]] = {
            entity_type: list(entities) for entity_type, entities in entity_dict.items()
        }
        self.entity_to_type: Dict[str, List[str]] = {}
        for entity_type, entities in self.entity_dict.items():
            for entity in entities:
                self.entity_to_type.setdefault(entity, []).append(entity_type)

    def match(self, question: str, threshold: float = 0.85, top_k: int = 3) -> Dict[str, List[str]]:
        candidates: List[Tuple[str, List[str], float]] = []
        for entity, types in self.entity_to_type.items():
            score = self._calculate_similarity(question, entity)
            if score >= threshold:
                candidates.append((entity, types, score))

        candidates.sort(key=lambda item: item[2], reverse=True)
        result: Dict[str, List[str]] = {}
        for entity, types, _ in candidates[:top_k]:
            result[entity] = list(types)
        return result

    def match_entity_type(
        self, question: str, entity_type: str, threshold: float = 0.85
    ) -> Tuple[str | None, float]:
        entities = self.entity_dict.get(entity_type, [])
        best_entity = None
        best_score = 0.0
        for entity in entities:
            score = self._calculate_similarity(question, entity)
            if score > best_score and score >= threshold:
                best_score = score
                best_entity = entity
        return best_entity, best_score

    def _calculate_similarity(self, question: str, entity: str) -> float:
        if entity in question:
            return 1.0
        overall_score = SequenceMatcher(None, question, entity).ratio()
        substring_score = self._substring_similarity(question, entity)
        return max(overall_score, substring_score)

    @staticmethod
    def _substring_similarity(text: str, entity: str) -> float:
        if not entity:
            return 0.0
        match_count = sum(1 for char in entity if char in text)
        return match_count / len(entity)
