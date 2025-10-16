#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse, json, os, sys
from typing import Any, Dict, List

def read_any(path: str) -> List[Dict[str, Any]]:
    """读取 JSON 数组 或 JSONL；返回 list[dict]"""
    if path == "-":
        data = sys.stdin.read()
        # 尝试按 JSON 数组解析；失败则当作JSONL
        try:
            arr = json.loads(data)
            if isinstance(arr, list):
                return [x for x in arr if isinstance(x, dict)]
        except Exception:
            pass
        items = []
        for line in data.splitlines():
            line = line.strip()
            if not line: 
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                items.append(obj)
        return items

    with open(path, "r", encoding="utf-8") as f:
        first = f.read(1); f.seek(0)
        if first == "[":
            try:
                arr = json.load(f)
            except Exception:
                return []
            return [x for x in arr if isinstance(x, dict)]
        else:
            items = []
            for line in f:
                line = line.strip()
                if not line: 
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if isinstance(obj, dict):
                    items.append(obj)
            return items

def qa_to_alpaca(obj: Dict[str, Any]) -> Dict[str, str]:
    ins = str(obj.get("src", "") or "")
    out = str(obj.get("tgt", "") or "")
    return {"instruction": ins, "input": "", "output": out}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qa", required=True, help="问答样本文件（JSON/JSONL），或 '-' 从标准输入读取")
    ap.add_argument("--append-to", required=True, help="目标 Alpaca JSONL 文件（不存在则创建）")
    args = ap.parse_args()

    items = read_any(args.qa)
    if not items:
        print("未读取到任何问答条目（检查 --qa 输入）", file=sys.stderr)
        sys.exit(1)

    # 确保目录存在
    os.makedirs(os.path.dirname(args.append_to) or ".", exist_ok=True)

    appended = 0
    with open(args.append_to, "a", encoding="utf-8") as fout:
        for obj in items:
            if "src" not in obj or "tgt" not in obj:
                continue
            rec = qa_to_alpaca(obj)
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            appended += 1

    print(f"Done. appended={appended} -> {args.append_to}")

if __name__ == "__main__":
    main()
