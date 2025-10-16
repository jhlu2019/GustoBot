#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
recipe_to_alpaca_kw_desc.py

将菜谱对象转换为 Alpaca 格式：
- instruction: 根据 keywords 拼接成问句；无 keywords 时退化为“如何制作『菜名』？”
- input: 使用 description（可为空）
- output: 先配料（recipeIngredient），再空行，然后编号后的做法（recipeInstructions）

输入文件可为：
- JSON 数组（[ {...}, {...} ]）
- JSONL（每行一个 JSON 对象）

只处理含有 recipeIngredient/recipeInstructions 的“菜谱对象”，其他条目会被跳过。
"""

import json
import argparse
import os
import sys
from typing import Any, Dict, List

def read_any(path: str) -> List[Dict[str, Any]]:
    """读取 JSON 数组或 JSONL；返回 list[dict]"""
    with open(path, "r", encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            try:
                arr = json.load(f)
            except Exception:
                return []
            return [x for x in arr if isinstance(x, dict)]
        # JSONL
        out = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                out.append(obj)
        return out

def is_recipe(o: Dict[str, Any]) -> bool:
    ks = {k.lower() for k in o.keys()}
    return ("recipeingredient" in ks) or ("recipeinstructions" in ks)

def join_kw2q(kws, name=None) -> str:
    """由 keywords 生成问句；无 keywords 时退化到菜名问句"""
    kws = [str(k).strip() for k in (kws or []) if str(k).strip()]
    if kws:
        return f"根据关键词（{'、'.join(kws)}），列出所需配料并给出详细做法。"
    return f"如何制作『{name}』？" if name else "这道菜需要哪些配料并如何制作？"

def to_lines(v: Any) -> List[str]:
    """把列表/标量转成行列表；对嵌套列表用 '、' 拼接"""
    if v is None:
        return []
    if isinstance(v, list):
        return [("、".join(map(str, x)) if isinstance(x, (list, tuple)) else str(x)) for x in v]
    return [str(v)]

def build_output(ings, steps) -> str:
    ing_lines = to_lines(ings)
    step_lines = to_lines(steps)
    out = []
    if ing_lines:
        out.append("【配料】")
        out.extend(ing_lines)
    if step_lines:
        out.append("")  # 空行
        out.append("【做法】")
        out.extend([f"{i+1}. {s}" for i, s in enumerate(step_lines)])
    return "\n".join(out).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="in_path",  required=True, help="输入 JSON/JSONL 文件")
    ap.add_argument("--out", dest="out_path", required=True, help="输出 Alpaca JSONL 文件")
    args = ap.parse_args()

    items = read_any(args.in_path)
    if not items:
        print("未读取到有效条目（请检查输入文件格式是否为 JSON 数组或 JSONL）", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(args.out_path) or ".", exist_ok=True)

    kept = 0
    with open(args.out_path, "w", encoding="utf-8") as fout:
        for o in items:
            if not is_recipe(o):
                continue
            instr = join_kw2q(o.get("keywords"), o.get("name") or o.get("dish"))
            inp = str(o.get("description") or "")
            out_text = build_output(
                o.get("recipeIngredient") or o.get("ingredients"),
                o.get("recipeInstructions") or o.get("steps")
            )
            rec = {"instruction": instr, "input": inp, "output": out_text}
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            kept += 1

    print(f"Done. total={len(items)}, wrote={kept}, out={args.out_path}")

if __name__ == "__main__":
    main()

