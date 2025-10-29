"""
Keyword based question classifier for the Neo4j KBQA pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from typing import Dict, Iterable, List, Optional, Sequence, Set

import ahocorasick
from .fuzzy_matcher import FuzzyMatcher


def _load_dict(path) -> List[str]:
    with path.open("r", encoding="utf-8") as fp:  # type: ignore[call-arg]
        return [line.strip() for line in fp if line.strip()]


@dataclass
class ClassificationResult:
    question_type: str
    args: Dict[str, object]


class QuestionClassifier:
    """Use keyword matching to classify recipe related questions."""

    def __init__(self, dict_root=None) -> None:
        if dict_root is None:
            dict_root = resources.files("gustobot.infrastructure.knowledge.recipe_kg") / "dicts"

        self.recipe_words = _load_dict(dict_root / "recipe.txt")
        self.gongyi_words = _load_dict(dict_root / "gongyi.txt")
        self.haoshi_words = _load_dict(dict_root / "haoshi.txt")
        self.kouwei_words = _load_dict(dict_root / "kouwei.txt")
        self.leixing_words = _load_dict(dict_root / "leixing.txt")
        self.yongliang_words = _load_dict(dict_root / "yongliang.txt")
        self.caixi_words = _load_dict(dict_root / "caixi.txt")
        self.material_words = _load_dict(dict_root / "material.txt")
        self.deny_words = _load_dict(dict_root / "deny.txt")

        self.relation_keywords: Dict[str, List[str]] = {
            "HAS_MAIN_INGREDIENT": ["主食材", "主要食材", "主要材料", "由什么做", "要多少", "主料", "要用多少", "有哪些"],
            "HAS_AUX_INGREDIENT": ["辅料", "由什么做", "需要多少", "要用多少", "有哪些"],
        }
        relation_terms: List[str] = [term for keywords in self.relation_keywords.values() for term in keywords]

        self.region_words: Set[str] = set(
            self.recipe_words
            + self.gongyi_words
            + self.haoshi_words
            + self.kouwei_words
            + self.leixing_words
            + self.caixi_words
            + self.material_words
            + relation_terms
        )

        self.region_tree = self._build_actree(self.region_words)
        self.word_type_dict = self._build_word_type_dict()

        self.property_keywords: Dict[str, List[str]] = {
            "做法": ["做法", "怎么做", "做怎么"],
            "口味": ["口味", "味道"],
            "工艺": ["工艺"],
            "类型": ["类型"],
            "耗时": ["多久", "耗时"],
            "菜系": ["菜系"],
        }

        self._fuzzy_matcher = FuzzyMatcher(
            {
                "Dish": self.recipe_words,
                "Ingredient": self.material_words,
                "菜系": self.caixi_words,
                "工艺": self.gongyi_words,
                "口味": self.kouwei_words,
                "类型": self.leixing_words,
                "耗时": self.haoshi_words,
            }
        )
        self._fuzzy_threshold = 0.5

    @staticmethod
    def _build_actree(words: Iterable[str]) -> ahocorasick.Automaton:
        tree = ahocorasick.Automaton()
        for index, word in enumerate(words):
            tree.add_word(word, (index, word))
        tree.make_automaton()
        return tree

    def _build_word_type_dict(self) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}
        for word in self.region_words:
            mapping[word] = []
            if word in self.recipe_words:
                mapping[word].append("Dish")
            elif word in self.gongyi_words:
                mapping[word].append("工艺")
            elif word in self.haoshi_words:
                mapping[word].append("耗时")
            elif word in self.kouwei_words:
                mapping[word].append("口味")
            elif word in self.leixing_words:
                mapping[word].append("类型")
            elif word in self.caixi_words:
                mapping[word].append("菜系")
            elif word in self.material_words:
                mapping[word].append("Ingredient")
            elif any(word in keywords for keywords in self.relation_keywords.values()):
                mapping[word].append("relation")
        return mapping

    def classify(self, question: str) -> ClassificationResult:
        entities = self._extract_entities(question)
        entity_types = [label for labels in entities.values() for label in labels]

        question_type = ""
        args: Dict[str, object] = {}

        matched_properties = self._match_keywords(self.property_keywords, question)
        matched_relations = self._match_keywords(self.relation_keywords, question)

        if matched_properties and "Dish" in entity_types:
            question_type = "recipe_property"
            args["nodes"] = entities
            args["properties"] = matched_properties

        elif "Dish" not in entity_types and self._is_property_only(entity_types):
            question_type = "property_constraint"
            args["constraints"] = {labels[0]: name for name, labels in entities.items() if labels}

        elif "Dish" in entity_types and "Ingredient" not in entity_types and matched_relations:
            question_type = "relationship_constraint"
            args["nodes"] = entities
            args["relationships"] = matched_relations

        elif "Dish" in entity_types and "Ingredient" in entity_types and not matched_properties:
            question_type = "relationship_query"
            args["nodes"] = entities
            args["relationships"] = matched_relations or ["HAS_MAIN_INGREDIENT"]

        elif "Dish" not in entity_types and matched_relations:
            question_type = "relationship_constraint"
            args["nodes"] = entities
            args["relationships"] = matched_relations

        return ClassificationResult(question_type=question_type, args=args)

    def _extract_entities(self, question: str) -> Dict[str, List[str]]:
        matches = [value[1] for value in self.region_tree.iter(question)]
        stop_words = {a for a in matches for b in matches if a != b and a in b}
        final_words = [word for word in matches if word not in stop_words]
        entities: Dict[str, List[str]] = {}
        for word in final_words:
            labels = self.word_type_dict.get(word, [])
            if labels and labels != ["relation"]:
                entities[word] = labels

        fuzzy_candidates = self._fuzzy_matcher.match(question, threshold=self._fuzzy_threshold)
        for word, labels in fuzzy_candidates.items():
            filtered_labels = [label for label in labels if label != "relation"]
            if filtered_labels and word not in entities:
                entities[word] = filtered_labels

        return entities

    @staticmethod
    def _match_keywords(options: Dict[str, List[str]], sentence: str) -> List[str]:
        matched: List[str] = []
        for slot, keywords in options.items():
            if any(keyword in sentence for keyword in keywords):
                matched.append(slot)
        return matched

    @staticmethod
    def _is_property_only(types: Sequence[str]) -> bool:
        allowed = {"工艺", "耗时", "口味", "类型", "菜系"}
        return bool(types) and all(type_ in allowed for type_ in types)
