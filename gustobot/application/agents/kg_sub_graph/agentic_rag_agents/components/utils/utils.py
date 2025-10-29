from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import regex as re
from langchain_neo4j import Neo4jGraph

from .regex_patterns import get_cypher_query_node_graph_schema

COL_CHINESE_MEANING = "\u4e2d\u6587\u542b\u4e49"
COL_MAIN_PROPERTIES = "\u4e3b\u8981\u5c5e\u6027"
COL_NOTE_EXAMPLE = "\u5907\u6ce8\u793a\u4f8b"
COL_REL_TYPE = "\u7c7b\u578b"
COL_REL_DIRECTION = "\u8d77\u70b9 \u2192 \u7ec8\u70b9"
ALT_REL_DIRECTION = "\u8d77\u70b9 -> \u7ec8\u70b9"
SECTION_ATTRIBUTES = "\u8282\u70b9\u4e0e\u5173\u7cfb\u5c5e\u6027"


def _extract_table_blocks(markdown: str) -> list[list[str]]:
    """
    Extract consecutive Markdown table blocks (lines starting with '|').
    """
    tables: list[list[str]] = []
    current_block: list[str] = []

    for line in markdown.splitlines():
        if line.strip().startswith("|"):
            current_block.append(line)
        elif current_block:
            tables.append(current_block)
            current_block = []

    if current_block:
        tables.append(current_block)

    return tables


def _parse_markdown_table(lines: Iterable[str]) -> tuple[list[str], list[list[str]]]:
    """
    Parse a Markdown table block into a header row and table body.
    """
    header: list[str] | None = None
    rows: list[list[str]] = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue

        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]

        if header is None:
            header = cells
            continue

        # Skip separator rows like | --- | --- |
        if all(not cell or set(cell) <= {"-", ":", " "} for cell in cells):
            continue

        rows.append(cells)

    return (header or []), rows


def _extract_markdown_section(markdown: str, heading: str) -> str:
    """
    Extract the content of a Markdown section by its '## ' heading.
    """
    pattern = rf"^##\s*{re.escape(heading)}\s*$([\s\S]*?)(?=^##\s|\Z)"
    match = re.search(pattern, markdown, flags=re.MULTILINE)
    if not match:
        return ""

    section_text = match.group(1).strip()
    cleaned_lines = [
        line.rstrip()
        for line in section_text.splitlines()
        if line.strip() and line.strip() != "** End Patch"
    ]

    return "\n".join(cleaned_lines).strip()


def _lookup_cell(
    cells: Sequence[str],
    header: Sequence[str],
    possible_keys: Sequence[str],
    fallback_index: int | None = None,
) -> str:
    """
    Fetch a cell value by column name, with optional positional fallback.
    """
    for key in possible_keys:
        if key in header:
            idx = header.index(key)
            if idx < len(cells):
                return cells[idx].strip()
    if fallback_index is not None and fallback_index < len(cells):
        return cells[fallback_index].strip()
    return ""


def _format_recipe_schema_from_docs() -> str:
    """
    Build a concise, LLM-friendly schema summary based on docs/recipe_kg_schema.md.
    """
    doc_path = (
        Path(__file__).resolve().parents[6]
        / "docs"
        / "recipe_kg_schema.md"
    )
    if not doc_path.exists():
        return ""

    try:
        markdown = doc_path.read_text(encoding="utf-8")
    except OSError:
        return ""

    markdown = "\n".join(
        line for line in markdown.splitlines() if line.strip() != "** End Patch"
    )

    tables = _extract_table_blocks(markdown)

    node_header, node_rows = (
        _parse_markdown_table(tables[0]) if tables else ([], [])
    )
    relationship_header, relationship_rows = (
        _parse_markdown_table(tables[1]) if len(tables) > 1 else ([], [])
    )

    summary_lines: list[str] = []

    if node_rows:
        summary_lines.append("Recipe KG node types:")
        for cells in node_rows:
            label = _lookup_cell(cells, node_header, ["Label"], fallback_index=0)
            meaning = _lookup_cell(
                cells, node_header, [COL_CHINESE_MEANING], fallback_index=1
            )
            properties = _lookup_cell(
                cells, node_header, [COL_MAIN_PROPERTIES], fallback_index=2
            )
            note = _lookup_cell(
                cells, node_header, [COL_NOTE_EXAMPLE], fallback_index=3
            )

            if not label:
                continue

            bullet = label
            if meaning:
                bullet = f"{bullet} ({meaning})"

            details: list[str] = []
            if properties:
                details.append(f"properties: {properties}")
            if note:
                details.append(f"example: {note}")

            if details:
                bullet = f"{bullet}; " + "; ".join(details)

            summary_lines.append(f"- {bullet}")

    if relationship_rows:
        if summary_lines:
            summary_lines.append("")
        summary_lines.append("Recipe KG relationship types:")
        for cells in relationship_rows:
            rel_type = _lookup_cell(
                cells, relationship_header, [COL_REL_TYPE], fallback_index=0
            )
            direction = _lookup_cell(
                cells,
                relationship_header,
                [COL_REL_DIRECTION, ALT_REL_DIRECTION],
                fallback_index=1,
            )
            meaning = _lookup_cell(
                cells, relationship_header, [COL_CHINESE_MEANING], fallback_index=2
            )
            properties = _lookup_cell(
                cells, relationship_header, [COL_MAIN_PROPERTIES], fallback_index=3
            )

            if not rel_type:
                continue

            bullet = rel_type
            if direction:
                bullet = f"{bullet} ({direction})"

            details = []
            if meaning:
                details.append(f"meaning: {meaning}")
            if properties:
                details.append(f"properties: {properties}")

            if details:
                bullet = f"{bullet}; " + "; ".join(details)

            summary_lines.append(f"- {bullet}")

    attribute_section = _extract_markdown_section(markdown, SECTION_ATTRIBUTES)
    if attribute_section:
        if summary_lines:
            summary_lines.append("")
        summary_lines.append("Property notes:")
        summary_lines.append(attribute_section)

    return "\n".join(summary_lines).strip()


def retrieve_and_parse_schema_from_graph_for_prompts(graph: Neo4jGraph) -> str:
    """
    Retrieve the runtime schema, clean it for prompt usage, and enrich
    it with curated information from docs/recipe_kg_schema.md.
    """
    schema: str = graph.get_schema

    if "CypherQuery" in schema:
        schema = re.sub(
            get_cypher_query_node_graph_schema(), r"\2", schema, flags=re.MULTILINE
        )

    schema = schema.replace("{", "[").replace("}", "]")

    doc_summary = _format_recipe_schema_from_docs()
    if doc_summary:
        return f"{doc_summary}\n\n{schema}"

    return schema
