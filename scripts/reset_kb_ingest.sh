#!/usr/bin/env bash
# 重置知识库导入状态（清除 pgvector / Milvus 哨兵文件，避免 Docker build 时自动执行）
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

remove_file() {
  local path="$1"
  if [ -f "$path" ]; then
    rm -f "$path"
    echo "已删除: $path"
  else
    echo "无需处理: $path (不存在)"
  fi
}

main() {
  echo "开始清理知识库导入标记..."
  remove_file "$ROOT_DIR/data/.kb_milvus_ingested"
  remove_file "$ROOT_DIR/data/.kb_excel_ingested"
  echo "清理完成。不影响后续 docker build。"
}

main "$@"
