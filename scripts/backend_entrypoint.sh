#!/bin/bash
set -euo pipefail

INIT_KB_MILVUS="${INIT_KB_MILVUS:-true}"
KB_DATA_FILE="${KB_DATA_FILE:-/app/data/kb/data.txt}"
KB_MILVUS_SENTINEL="${KB_MILVUS_SENTINEL:-/app/data/.kb_milvus_ingested}"
AUTO_BOOTSTRAP_LIGHTRAG="${AUTO_BOOTSTRAP_LIGHTRAG:-true}"
LIGHTRAG_BOOTSTRAP_DIR="${LIGHTRAG_BOOTSTRAP_DIR:-/app/bootstrap/lightrag_template}"
LIGHTRAG_WORKING_DIR="${LIGHTRAG_WORKING_DIR:-./data/lightrag}"

resolve_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    ""|.) printf '%s\n' "/app" ;;
    ./*) printf '%s\n' "/app/${1#./}" ;;
    *) printf '%s\n' "/app/$1" ;;
  esac
}

LIGHTRAG_WORKING_DIR_ABS=$(resolve_path "$LIGHTRAG_WORKING_DIR")
LIGHTRAG_BOOTSTRAP_DIR_ABS=$(resolve_path "$LIGHTRAG_BOOTSTRAP_DIR")

bootstrap_lightrag_data() {
  if [ "${AUTO_BOOTSTRAP_LIGHTRAG,,}" != "true" ]; then
    echo "[backend] LightRAG bootstrap disabled via AUTO_BOOTSTRAP_LIGHTRAG=${AUTO_BOOTSTRAP_LIGHTRAG}"
    return
  fi

  if [ ! -d "${LIGHTRAG_BOOTSTRAP_DIR_ABS}" ] || [ -z "$(ls -A "${LIGHTRAG_BOOTSTRAP_DIR_ABS}" 2>/dev/null)" ]; then
    echo "[backend] LightRAG bootstrap目录不存在或为空，跳过自动导入。"
    return
  fi

  mkdir -p "${LIGHTRAG_WORKING_DIR_ABS}"
  if [ -n "$(ls -A "${LIGHTRAG_WORKING_DIR_ABS}" 2>/dev/null)" ]; then
    echo "[backend] LightRAG 工作目录已存在内容，跳过自动导入。"
    return
  fi

  echo "[backend] LightRAG 工作目录为空，正在从模板复制初始数据..."
  cp -a "${LIGHTRAG_BOOTSTRAP_DIR_ABS}/." "${LIGHTRAG_WORKING_DIR_ABS}/"
  echo "[backend] LightRAG 初始数据复制完成。"
}

bootstrap_lightrag_data

wait_for_milvus() {
  python - <<'PY'
import os
import time
from pymilvus import connections

host = os.getenv("MILVUS_HOST", "milvus")
port = os.getenv("MILVUS_PORT", "19530")
deadline = time.monotonic() + 120

while time.monotonic() < deadline:
    try:
        connections.connect(alias="default", host=host, port=port, timeout=5)
        connections.disconnect("default")
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("Milvus is not reachable for KB initialisation")
PY
}

run_milvus_ingest() {
  if [ "${INIT_KB_MILVUS,,}" = "false" ]; then
    echo "[backend] KB Milvus ingestion disabled via INIT_KB_MILVUS=false."
    return
  fi

  if [ ! -f "${KB_DATA_FILE}" ]; then
    echo "[backend] KB data file not found: ${KB_DATA_FILE}, skipping Milvus ingestion."
    return
  fi

  if [ -f "${KB_MILVUS_SENTINEL}" ]; then
    echo "[backend] KB Milvus dataset already ingested, skipping."
    return
  fi

  echo "[backend] Waiting for Milvus to become available..."
  wait_for_milvus

  echo "[backend] Importing KB dataset into Milvus from ${KB_DATA_FILE}"
  if python scripts/init_kb_milvus.py; then
    touch "${KB_MILVUS_SENTINEL}"
    echo "[backend] Milvus ingestion completed."
  else
    echo "[backend] Milvus ingestion failed; continuing without bootstrap data." >&2
  fi
}

run_milvus_ingest

exec "$@"
