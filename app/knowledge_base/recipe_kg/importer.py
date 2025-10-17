"""
Utility helpers to bootstrap the recipe knowledge graph from JSON sources.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from loguru import logger

from .database import Neo4jDatabase
from .parser import IngredientProfile, RecipeRecord, load_ingredient_profiles, load_recipe_records


class RecipeGraphImporter:
    """Load recipes and ingredient metadata from JSON files into Neo4j."""

    def __init__(self, database: Neo4jDatabase, batch_size: int = 200) -> None:
        self._database = database
        self._batch_size = max(50, batch_size)

    def bootstrap_from_json(
        self,
        recipe_json: Path,
        ingredient_json: Optional[Path] = None,
        *,
        force: bool = False,
    ) -> bool:
        """Populate the graph from JSON sources."""
        try:
            recipes, ingredients_used = load_recipe_records(recipe_json)
        except FileNotFoundError:
            logger.warning(f"Recipe JSON not found at {recipe_json}, skipping import.")
            return False
        except Exception as exc:
            logger.error(f"Failed to parse recipe JSON: {exc}")
            return False

        if not recipes:
            logger.info("No recipe records found; skipping Neo4j bootstrap.")
            return False

        if not force and not self._is_graph_empty():
            logger.info("Neo4j dataset already populated; skipping bootstrap.")
            return False

        if force:
            logger.info("Forcing recipe graph reload from JSON.")
            self._database.execute("MATCH (n) DETACH DELETE n")
        else:
            logger.info("Recipe graph is empty; importing dataset from JSON.")

        profiles = load_ingredient_profiles(ingredient_json, ingredients_used)

        self._create_recipe_nodes(recipes)
        self._create_relationships(recipes)
        if profiles:
            self._attach_ingredient_metadata(profiles)

        logger.info(
            "Imported %s recipes and %s unique ingredients into Neo4j.",
            len(recipes),
            len(ingredients_used),
        )
        return True

    def _is_graph_empty(self) -> bool:
        query = "MATCH (n:Dish) RETURN COUNT(n) AS count"
        result = self._database.fetch(query)
        count = result[0]["count"] if result else 0
        return count == 0

    def _chunked(self, data: Iterable[Dict[str, Any]]) -> Iterable[List[Dict[str, Any]]]:
        batch: List[Dict[str, Any]] = []
        for record in data:
            batch.append(record)
            if len(batch) >= self._batch_size:
                yield batch
                batch = []
        if batch:
            yield batch

    def _create_recipe_nodes(self, recipes: List[RecipeRecord]) -> None:
        query = """
        UNWIND $batch AS dish
        MERGE (d:Dish {name: dish.name})
        SET d.cook_time = dish.cook_time,
            d.instructions = dish.instructions
        WITH d, dish
        FOREACH (flavor IN dish.flavors |
            MERGE (f:Flavor {name: flavor})
            MERGE (d)-[:HAS_FLAVOR]->(f)
        )
        FOREACH (method IN dish.methods |
            MERGE (m:CookingMethod {name: method})
            MERGE (d)-[:USES_METHOD]->(m)
        )
        FOREACH (dtype IN dish.dish_types |
            MERGE (t:DishType {name: dtype})
            MERGE (d)-[:BELONGS_TO_TYPE]->(t)
        )
        """

        serialised = [
            {
                "name": record.name,
                "cook_time": record.cook_time,
                "instructions": record.instructions,
                "flavors": record.flavors,
                "methods": record.methods,
                "dish_types": record.dish_types,
            }
            for record in recipes
        ]

        for batch in self._chunked(serialised):
            self._database.execute(query, {"batch": batch})

    def _create_relationships(self, recipes: List[RecipeRecord]) -> None:
        step_query = """
        UNWIND $batch AS dish
        MATCH (d:Dish {name: dish.name})
        FOREACH (step IN dish.steps |
            MERGE (s:CookingStep {dish_name: dish.name, order: step.order})
            SET s.order = step.order,
                s.instruction = step.instruction
            MERGE (d)-[hs:HAS_STEP]->(s)
            SET hs.order = step.order
        )
        """

        ingredient_query = """
        UNWIND $batch AS dish
        MATCH (d:Dish {name: dish.name})
        FOREACH (item IN dish.main_ingredients |
            MERGE (i:Ingredient {name: item.name})
            MERGE (d)-[rel:HAS_MAIN_INGREDIENT]->(i)
            SET rel.amount_text = item.amount,
                rel.role = item.role
        )
        FOREACH (item IN dish.aux_ingredients |
            MERGE (i:Ingredient {name: item.name})
            MERGE (d)-[rel:HAS_AUX_INGREDIENT]->(i)
            SET rel.amount_text = item.amount,
                rel.role = item.role
        )
        """

        steps_data = [
            {
                "name": record.name,
                "steps": [
                    {"order": step.order, "instruction": step.instruction}
                    for step in record.steps
                ],
            }
            for record in recipes
        ]
        ingredients_data = [
            {
                "name": record.name,
                "main_ingredients": [
                    {"name": item.name, "amount": item.amount, "role": item.role}
                    for item in record.main_ingredients
                ],
                "aux_ingredients": [
                    {"name": item.name, "amount": item.amount, "role": item.role}
                    for item in record.aux_ingredients
                ],
            }
            for record in recipes
        ]

        for batch in self._chunked(steps_data):
            self._database.execute(step_query, {"batch": batch})

        for batch in self._chunked(ingredients_data):
            self._database.execute(ingredient_query, {"batch": batch})

    def _attach_ingredient_metadata(self, profiles: List[IngredientProfile]) -> None:
        query = """
        UNWIND $profiles AS profile
        MERGE (i:Ingredient {name: profile.name})
        FOREACH (_ IN CASE WHEN profile.nutrition IS NULL THEN [] ELSE [1] END |
            MERGE (np:NutritionProfile {name: profile.name})
            SET np.description = profile.nutrition
            MERGE (i)-[:HAS_NUTRITION_PROFILE]->(np)
        )
        FOREACH (benefit IN profile.benefits |
            MERGE (hb:HealthBenefit {name: benefit})
            MERGE (i)-[:HAS_HEALTH_BENEFIT]->(hb)
        )
        """

        serialised = [
            {
                "name": profile.name,
                "nutrition": profile.nutrition,
                "benefits": profile.benefits,
            }
            for profile in profiles
        ]

        for batch in self._chunked(serialised):
            self._database.execute(query, {"profiles": batch})
