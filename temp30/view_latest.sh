#!/bin/bash
# 查看最新的处理结果

LATEST_DIR=$(ls -td save/20*/ 2>/dev/null | head -1)

if [ -z "$LATEST_DIR" ]; then
    echo "没有找到处理记录"
    exit 1
fi

echo "最新处理结果目录: $LATEST_DIR"
echo "================================"
echo ""
echo "文件列表:"
ls -lh "$LATEST_DIR"
echo ""
echo "日志摘要 (前20行):"
head -20 "${LATEST_DIR}processing.log"
