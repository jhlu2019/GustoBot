#!/bin/bash
set -euo pipefail

# Optional toggle: INIT_KB_EXCEL=false to skip Excel ingestion
INIT_KB_EXCEL="${INIT_KB_EXCEL:-true}"
KB_EXCEL_PATH="${KB_EXCEL_PATH:-/app/data/历史菜谱源头.xlsx}"
KB_EXCEL_SENTINEL="${KB_EXCEL_SENTINEL:-/app/data/.kb_excel_ingested}"

wait_for_postgres() {
  python - <<'PY'
import os
import time
import psycopg2

host = os.getenv("PGHOST", "kb_postgres")
port = int(os.getenv("PGPORT", "5432"))
user = os.getenv("PGUSER", "postgres")
password = os.getenv("PGPASSWORD", "postgres")
dbname = os.getenv("PGDATABASE", "vector_db")

deadline = time.monotonic() + 120
while time.monotonic() < deadline:
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname=dbname,
        )
        conn.close()
        break
    except Exception:
        time.sleep(2)
else:
    raise SystemExit("PostgreSQL is not reachable for kb_ingest initialisation")
PY
}

if [ "${INIT_KB_EXCEL}" != "false" ]; then
  if [ -f "${KB_EXCEL_PATH}" ]; then
    if [ ! -f "${KB_EXCEL_SENTINEL}" ]; then
      echo "[kb_ingest] Waiting for PostgreSQL to become available..."
      wait_for_postgres
      echo "[kb_ingest] Importing Excel dataset: ${KB_EXCEL_PATH}"
      if python -m kb_service.cli process-excel "${KB_EXCEL_PATH}"; then
        touch "${KB_EXCEL_SENTINEL}"
        echo "[kb_ingest] Excel ingestion completed."
      else
        echo "[kb_ingest] Excel ingestion failed; continuing without preloaded data." >&2
      fi
    else
      echo "[kb_ingest] Excel dataset already ingested, skipping."
    fi
  else
    echo "[kb_ingest] Excel dataset not found at ${KB_EXCEL_PATH}, skipping ingestion."
  fi
else
  echo "[kb_ingest] Excel ingestion disabled via INIT_KB_EXCEL=false."
fi

exec "$@"
