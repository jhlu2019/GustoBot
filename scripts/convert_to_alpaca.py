#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_to_alpaca.py (fixed)

遍历文件或目录，把各种常见数据结构转换为 Alpaca 格式 JSONL：
  {"instruction": "...", "input": "...", "output": "..."}

支持：JSON 数组 / JSONL、递归遍历目录、常见字段自动映射、去重与跳过不完整样本。
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict, List, Tuple

def list_candidate_files(p: str) -> List[str]:
    if os.path.isdir(p):
        out = []
        for root, _, files in os.walk(p):
            for fn in files:
                if fn.lower().endswith(('.json', '.jsonl')):
                    out.append(os.path.join(root, fn))
        return sorted(out)
    elif os.path.isfile(p):
        return [p]
    else:
        return []

def read_any_json(path: str) -> List[Dict[str, Any]]:
    with open(path, 'r', encoding='utf-8') as f:
        first = f.read(1)
        f.seek(0)
        if first == '[':
            data = json.load(f)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
            else:
                return []
        else:
            items = []
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(obj, dict):
                    items.append(obj)
            return items

def to_text(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return "\n".join(to_text(i) for i in v)
    if isinstance(v, dict):
        try:
            return json.dumps(v, ensure_ascii=False, indent=2)
        except Exception:
            return str(v)
    return str(v)

def is_recipe(obj: Dict[str, Any]) -> bool:
    keys = set(k.lower() for k in obj.keys())
    return "recipeingredient" in keys or "recipeinstructions" in keys

def build_recipe(obj: Dict[str, Any]) -> Tuple[str, str, str]:
    name = obj.get("name") or obj.get("dish") or "未命名菜品"
    ingredients = obj.get("recipeIngredient") or obj.get("ingredients") or []
    instructions = obj.get("recipeInstructions") or obj.get("steps") or []

    ing_txt = "\n".join(f"- {to_text(i)}" for i in ingredients) if ingredients else "（未提供）"
    if isinstance(instructions, list):
        steps_txt = "\n".join(f"{i+1}. {to_text(s)}" for i, s in enumerate(instructions)) or "（未提供）"
    else:
        steps_txt = to_text(instructions) or "（未提供）"

    instruction = "根据给定的原始字段，整理并输出一份可读的中文菜谱（包含菜名、简介、配料、步骤）。"
    _input = to_text({"raw": obj})
    output = f"""菜名：{name}

简介：{to_text(obj.get("description") or "")}

配料：
{ing_txt}

做法：
{steps_txt}""".strip()
    return instruction, _input, output

def map_to_alpaca(obj: Dict[str, Any]) -> Tuple[str, str, str]:
    # 已是 Alpaca
    if "instruction" in obj and "output" in obj:
        instruction = to_text(obj.get("instruction"))
        _input = to_text(obj.get("input", ""))
        output = to_text(obj.get("output"))
        return instruction, _input, output

    # 问答/对话：src/tgt[/context]
    if "src" in obj and "tgt" in obj:
        instruction = to_text(obj.get("src"))
        ctx = obj.get("context")
        _input = to_text(ctx) if ctx is not None else to_text(obj.get("input", ""))
        output = to_text(obj.get("tgt"))
        return instruction, _input, output

    # question/answer
    if "question" in obj and "answer" in obj:
        instruction = to_text(obj.get("question"))
        _input = to_text(obj.get("input", ""))
        output = to_text(obj.get("answer"))
        return instruction, _input, output

    # 菜谱对象
    if is_recipe(obj):
        return build_recipe(obj)

    # 其它：如果只有 prompt/response
    if "prompt" in obj and "response" in obj:
        return to_text(obj.get("prompt")), to_text(obj.get("input","")), to_text(obj.get("response"))

    # 兜底：把整条作为 input
    return "根据输入生成合适的回答。", to_text(obj), ""

def normalize_record(rec: Tuple[str, str, str]) -> Dict[str, str]:
    instruction, _input, output = rec
    return {
        "instruction": instruction.strip() if isinstance(instruction, str) else to_text(instruction),
        "input": _input if isinstance(_input, str) else to_text(_input),
        "output": output.strip() if isinstance(output, str) else to_text(output),
    }

def sha1_of_sample(d: Dict[str, str]) -> str:
    m = hashlib.sha1()
    m.update(d["instruction"].encode("utf-8"))
    m.update(b"\x00")
    m.update(d["input"].encode("utf-8"))
    m.update(b"\x00")
    m.update(d["output"].encode("utf-8"))
    return m.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="inputs", action="append", required=True,
                        help="输入文件或目录（可多次传入 --in）")
    parser.add_argument("--out", required=True, help="输出 JSONL 文件路径")
    parser.add_argument("--skip-incomplete", dest="skip_incomplete", action="store_true",
                        help="跳过缺少 output 的样本")
    parser.add_argument("--dedupe", action="store_true", help="按 instruction+input+output 去重")
    args = parser.parse_args()

    # 收集所有候选文件
    files = []
    for p in args.inputs:
        files.extend(list_candidate_files(p))
    files = sorted(set(files))

    if not files:
        print("未找到可处理的 .json/.jsonl 文件", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    seen = set()
    kept = 0
    total = 0

    with open(args.out, "w", encoding="utf-8") as fout:
        for fp in files:
            items = read_any_json(fp)
            for obj in items:
                total += 1
                try:
                    alp = normalize_record(map_to_alpaca(obj))
                except Exception:
                    continue

                # 跳过不完整
                if args.skip_incomplete and (not alp["instruction"] or not alp["output"]):
                    continue

                # 去重
                if args.dedupe:
                    sig = sha1_of_sample(alp)
                    if sig in seen:
                        continue
                    seen.add(sig)

                fout.write(json.dumps(alp, ensure_ascii=False) + "\n")
                kept += 1

    print(f"Done. Loaded {total} records from {len(files)} files; wrote {kept} Alpaca samples to {args.out}")

if __name__ == "__main__":
    main()
