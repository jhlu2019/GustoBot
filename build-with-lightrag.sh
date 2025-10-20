#!/bin/bash
set -e

# ========================================
# Docker Build with LightRAG Initialization
# ========================================

# Load environment variables from .env if exists
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required variables
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ ERROR: OPENAI_API_KEY is not set!"
    echo "Please set it in .env file or export it:"
    echo "  export OPENAI_API_KEY=sk-your-key"
    exit 1
fi

# Configuration
INIT_LIGHTRAG=${INIT_LIGHTRAG_ON_BUILD:-true}
LIMIT=${LIGHTRAG_INIT_LIMIT:-}
OPENAI_BASE=${OPENAI_API_BASE:-https://api.openai.com/v1}
OPENAI_MDL=${OPENAI_MODEL:-gpt-3.5-turbo}
EMBED_MDL=${EMBEDDING_MODEL:-text-embedding-3-small}
EMBED_DIM=${EMBEDDING_DIMENSION:-1536}

echo "========================================="
echo "Building Docker image with LightRAG"
echo "========================================="
echo "Init LightRAG: $INIT_LIGHTRAG"
echo "Limit: ${LIMIT:-none}"
echo "OpenAI Model: $OPENAI_MDL"
echo "Embedding Model: $EMBED_MDL"
echo "========================================="

# Build command
docker-compose build \
    --build-arg INIT_LIGHTRAG_ON_BUILD=$INIT_LIGHTRAG \
    --build-arg OPENAI_API_KEY=$OPENAI_API_KEY \
    --build-arg OPENAI_API_BASE=$OPENAI_BASE \
    --build-arg OPENAI_MODEL=$OPENAI_MDL \
    --build-arg EMBEDDING_MODEL=$EMBED_MDL \
    --build-arg EMBEDDING_DIMENSION=$EMBED_DIM \
    --build-arg LIGHTRAG_INIT_LIMIT="$LIMIT" \
    server

echo ""
echo "========================================="
echo "✅ Build completed!"
echo "========================================="
echo "To start the server:"
echo "  docker-compose up -d"
echo ""
echo "To verify LightRAG data:"
echo "  docker-compose run --rm server ls -lh /app/data/lightrag/"
echo "========================================="
