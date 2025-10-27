FROM python:3.11-slim AS server

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN set -eux; \
    printf '%s\n' \
        "deb https://mirrors.tuna.tsinghua.edu.cn/debian trixie main contrib non-free" \
        "deb https://mirrors.tuna.tsinghua.edu.cn/debian trixie-updates main contrib non-free" \
        "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security trixie-security main contrib non-free" \
        > /etc/apt/sources.list; \
    rm -f /etc/apt/sources.list.d/*; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential; \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple && \
    pip install -r requirements.txt -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple

COPY app ./app
COPY data ./data
COPY scripts ./scripts

# Build-time arguments for LightRAG initialization
ARG INIT_LIGHTRAG_ON_BUILD=false
ARG OPENAI_API_KEY
ARG OPENAI_API_BASE=https://api.openai.com/v1
ARG OPENAI_MODEL=gpt-3.5-turbo
ARG EMBEDDING_MODEL=text-embedding-3-small
ARG EMBEDDING_DIMENSION=1536
ARG LIGHTRAG_INIT_LIMIT=1000

# Initialize LightRAG data during build (if enabled)
RUN if [ "$INIT_LIGHTRAG_ON_BUILD" = "true" ] && [ -n "$OPENAI_API_KEY" ]; then \
        echo "========================================"; \
        echo "Initializing LightRAG during build..."; \
        echo "========================================"; \
        export OPENAI_API_KEY=${OPENAI_API_KEY}; \
        export OPENAI_API_BASE=${OPENAI_API_BASE}; \
        export OPENAI_MODEL=${OPENAI_MODEL}; \
        export EMBEDDING_MODEL=${EMBEDDING_MODEL}; \
        export EMBEDDING_DIMENSION=${EMBEDDING_DIMENSION}; \
        export LIGHTRAG_WORKING_DIR=/app/data/lightrag; \
        mkdir -p /app/data/lightrag && \
        python scripts/init_lightrag.py \
            --source json \
            --json-path /app/data/recipe.json \
            ${LIGHTRAG_INIT_LIMIT:+--limit $LIGHTRAG_INIT_LIMIT} && \
        echo "========================================"; \
        echo "LightRAG initialization completed!"; \
        echo "Generated files:"; \
        ls -lh /app/data/lightrag/; \
        echo "========================================"; \
    else \
        echo "Skipping LightRAG initialization during build"; \
        echo "  INIT_LIGHTRAG_ON_BUILD=${INIT_LIGHTRAG_ON_BUILD}"; \
        echo "  API_KEY set: $([ -n \"${OPENAI_API_KEY}\" ] && echo 'yes' || echo 'no')"; \
        mkdir -p /app/data/lightrag; \
    fi

# Unset API key for security
ENV OPENAI_API_KEY=your_api_key_here

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


FROM neo4j:5.18 AS neo4j_seeded

USER root
# Use faster mirror and install Python
RUN sed -i 's|http://deb.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org|https://mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /var/lib/neo4j/build
COPY data ./data
COPY scripts ./scripts
COPY app/knowledge_base/recipe_kg ./app/knowledge_base/recipe_kg

ENV PYTHONPATH=/var/lib/neo4j/build
RUN mkdir -p ./import_generated && \
    rm -rf ./app/knowledge_base/recipe_kg/__pycache__ && \
    chown -R neo4j:neo4j /var/lib/neo4j/build

USER neo4j
RUN python3 scripts/recipe_kg_to_csv.py --recipe-json data/recipe.json --ingredient-json data/excipients.json --output-dir import_generated

USER root
RUN rm -rf /data/databases /data/transactions && mkdir -p /data/databases /data/transactions && chown -R neo4j:neo4j /data

USER neo4j
RUN neo4j-admin database import full --overwrite-destination=true --multiline-fields=true neo4j \
    --nodes=Dish=import_generated/dish_nodes.csv \
    --nodes=Ingredient=import_generated/ingredient_nodes.csv \
    --nodes=Flavor=import_generated/flavor_nodes.csv \
    --nodes=CookingMethod=import_generated/method_nodes.csv \
    --nodes=DishType=import_generated/type_nodes.csv \
    --nodes=CookingStep=import_generated/step_nodes.csv \
    --nodes=NutritionProfile=import_generated/nutrition_nodes.csv \
    --nodes=HealthBenefit=import_generated/benefit_nodes.csv \
    --relationships=HAS_MAIN_INGREDIENT=import_generated/rel_has_main.csv \
    --relationships=HAS_AUX_INGREDIENT=import_generated/rel_has_aux.csv \
    --relationships=HAS_FLAVOR=import_generated/rel_has_flavor.csv \
    --relationships=USES_METHOD=import_generated/rel_uses_method.csv \
    --relationships=BELONGS_TO_TYPE=import_generated/rel_belongs_type.csv \
    --relationships=HAS_STEP=import_generated/rel_has_step.csv \
    --relationships=HAS_NUTRITION_PROFILE=import_generated/rel_has_nutrition.csv \
    --relationships=HAS_HEALTH_BENEFIT=import_generated/rel_has_benefit.csv

WORKDIR /var/lib/neo4j
