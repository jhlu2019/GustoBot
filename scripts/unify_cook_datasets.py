#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
unify_cook_datasets.py

将“菜谱类”与“问答/推荐类”两份数据集合并为一个指令微调（instruction tuning）数据集（JSONL）。
- 自动识别 JSON 数组 或 JSONL（逐行 JSON）。
- 生成统一 schema：{"instruction","input","output","meta":{"task_type","source_id"}}。
- 菜谱样本自动把配料与步骤拼成可读输出文本；问答样本保持问答逻辑。
- 便于用于中文大模型的 SFT/微调；也可以只用其中一个任务子集。

用法：
python unify_cook_datasets.py --ds1 path/to/file1.jsonl --ds2 path/to/file2.json --out unified.jsonl
（可只传一个输入，或传多个 --dsN）
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, Iterable, List, Union

def read_any_json(path: str) -> List[Dict[str, Any]]:
    """读取 JSONL 或 JSON 数组。返回 list[dict]."""
    with open(path, 'r', encoding='utf-8') as f:
        first = f.read(1)
        f.seek(0)
        if first == '[':
            data = json.load(f)
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
            else:
                raise ValueError(f"{path} 是 JSON，但不是数组。")
        else:
            # JSONL
            items = []
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path} 第 {i} 行不是合法 JSON: {e}") from e
                if isinstance(obj, dict):
                    items.append(obj)
                else:
                    raise ValueError(f"{path} 第 {i} 行 JSON 不是对象。")
            return items

def is_recipe(obj: Dict[str, Any]) -> bool:
    """粗略判定是否为菜谱样本。"""
    keys = set(k.lower() for k in obj.keys())
    recipe_signals = {"recipeingredient", "recipeinstructions", "dish", "name"}
    return len(keys & recipe_signals) >= 2 or "recipeingredient" in keys

def is_qa(obj: Dict[str, Any]) -> bool:
    """粗略判定是否为问答/对话推荐样本。"""
    keys = set(k.lower() for k in obj.keys())
    return "src" in keys and "tgt" in keys

def norm_text(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, (list, tuple)):
        return "\n".join([norm_text(i) for i in x])
    return str(x)

def build_recipe_sample(obj: Dict[str, Any], idx: int, source: str) -> Dict[str, Any]:
    name = obj.get("name") or obj.get("dish") or "未命名菜品"
    ingredients = obj.get("recipeIngredient") or obj.get("ingredients") or []
    instructions = obj.get("recipeInstructions") or obj.get("steps") or []

    ingredients_txt = "\n".join(f"- {norm_text(i)}" for i in ingredients)
    steps_txt = "\n".join(
        f"{i+1}. {norm_text(step)}" for i, step in enumerate(instructions if isinstance(instructions, list) else [instructions])
    )

    # instruction 设计：让模型根据“原始字段”产出一份可读的菜谱说明
    instruction = "根据给定的菜谱原始字段，整理并输出一份可读的中文菜谱说明（包含菜名、简介、配料清单、步骤）。"
    input_payload = {
        "raw": obj
    }
    # output 我们用已有字段拼出“参考答案”（便于监督微调）
    output_txt = f"""菜名：{name}

简介：{norm_text(obj.get("description") or "")}

配料：
{ingredients_txt if ingredients_txt.strip() else "（未提供）"}

做法：
{steps_txt if steps_txt.strip() else "（未提供）"}"""

    sample = {
        "instruction": instruction,
        "input": input_payload,
        "output": output_txt.strip(),
        "meta": {
            "task_type": "recipe_generation",
            "source_id": f"{source}#rec_{idx}",
            # 可选补充字段，方便过滤
            "name": name,
            "dish": obj.get("dish") or "",
            "keywords": obj.get("keywords", []),
            "author": obj.get("author", ""),
        }
    }
    return sample

def build_qa_sample(obj: Dict[str, Any], idx: int, source: str) -> Dict[str, Any]:
    src = norm_text(obj.get("src"))
    tgt = norm_text(obj.get("tgt"))
    context = obj.get("context") or {}

    instruction = src
    input_payload = {
        "context": context
    }
    output_txt = tgt

    return {
        "instruction": instruction,
        "input": input_payload,
        "output": output_txt,
        "meta": {
            "task_type": "culinary_qa",
            "source_id": f"{source}#qa_{idx}"
        }
    }

def convert_items(items: List[Dict[str, Any]], source: str) -> Iterable[Dict[str, Any]]:
    rec_i = qa_i = 0
    for obj in items:
        try:
            if is_recipe(obj):
                sample = build_recipe_sample(obj, rec_i, source)
                rec_i += 1
            elif is_qa(obj):
                sample = build_qa_sample(obj, qa_i, source)
                qa_i += 1
            else:
                # 兜底：当作普通问答（如果含有 name/description 也会落到这里）
                instruction = norm_text(obj.get("question") or obj.get("instruction") or obj.get("src") or "根据输入生成合适的烹饪相关回答。")
                output_txt = norm_text(obj.get("answer") or obj.get("tgt") or obj.get("output") or "")
                input_payload = {k: v for k, v in obj.items() if k not in ["question", "answer", "instruction", "output", "src", "tgt"]}
                sample = {
                    "instruction": instruction,
                    "input": input_payload,
                    "output": output_txt,
                    "meta": {
                        "task_type": "generic",
                        "source_id": f"{source}#gen_{rec_i+qa_i}"
                    }
                }
        except Exception as e:
            # 如果某条出错，给出最小化可用样本，避免整个流程中断
            sample = {
                "instruction": "根据输入生成合适的烹饪相关回答。",
                "input": {"raw": obj, "error": str(e)},
                "output": "",
                "meta": {"task_type": "fallback", "source_id": f"{source}#fallback_{rec_i+qa_i}"}
            }
        yield sample

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, help="输出 JSONL 路径")
    # 允许多个 --ds 参数，方便传入两份或多份数据
    parser.add_argument("--ds", action="append", dest="datasets", required=True, help="输入数据文件（JSON 或 JSONL），可多次传入")
    args = parser.parse_args()

    out_path = args.out
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    total = 0
    with open(out_path, "w", encoding="utf-8") as fout:
        for ds_idx, in_path in enumerate(args.datasets):
            items = read_any_json(in_path)
            for sample in convert_items(items, source=os.path.basename(in_path) or f"ds{ds_idx}"):
                fout.write(json.dumps(sample, ensure_ascii=False) + "\n")
                total += 1

    print(f"Done. Wrote {total} samples to {out_path}")

if __name__ == "__main__":
    main()
