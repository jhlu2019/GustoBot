FROM neo4j:5.18

USER root
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /var/lib/neo4j/build
COPY data ./data
COPY app/knowledge_base/recipe_kg ./app/knowledge_base/recipe_kg
COPY app/knowledge_base/__init__.py ./app/knowledge_base/__init__.py
COPY app/__init__.py ./app/__init__.py
COPY scripts/recipe_kg_to_csv.py ./scripts/recipe_kg_to_csv.py

ENV PYTHONPATH=/var/lib/neo4j/build
RUN mkdir -p ./import_generated && \
    rm -rf ./app/knowledge_base/recipe_kg/__pycache__ && \
    chown -R neo4j:neo4j /var/lib/neo4j/build

USER neo4j
RUN python3 scripts/recipe_kg_to_csv.py --recipe-json data/recipe.json --ingredient-json data/excipients.json --output-dir import_generated

USER root
RUN rm -rf /data/databases /data/transactions && mkdir -p /data/databases /data/transactions && chown -R neo4j:neo4j /data

USER neo4j
RUN neo4j-admin database import full --overwrite-destination=true neo4j \
    --nodes=import_generated/dish_nodes.csv \
    --nodes=import_generated/ingredient_nodes.csv \
    --nodes=import_generated/flavor_nodes.csv \
    --nodes=import_generated/method_nodes.csv \
    --nodes=import_generated/type_nodes.csv \
    --nodes=import_generated/step_nodes.csv \
    --nodes=import_generated/nutrition_nodes.csv \
    --nodes=import_generated/benefit_nodes.csv \
    --relationships=HAS_MAIN_INGREDIENT=import_generated/rel_has_main.csv \
    --relationships=HAS_AUX_INGREDIENT=import_generated/rel_has_aux.csv \
    --relationships=HAS_FLAVOR=import_generated/rel_has_flavor.csv \
    --relationships=USES_METHOD=import_generated/rel_uses_method.csv \
    --relationships=BELONGS_TO_TYPE=import_generated/rel_belongs_type.csv \
    --relationships=HAS_STEP=import_generated/rel_has_step.csv \
    --relationships=HAS_NUTRITION_PROFILE=import_generated/rel_has_nutrition.csv \
    --relationships=HAS_HEALTH_BENEFIT=import_generated/rel_has_benefit.csv

WORKDIR /var/lib/neo4j
ENV NEO4J_AUTH=none
