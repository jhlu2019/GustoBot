from __future__ import annotations

import logging
import time
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import create_engine

from app.clients.llm import LLMClient
from app.core.config import Config
from app.prompts.manager import PromptManager, SchemaColumn, build_prompt_manager_from_env
from app.schemas.ingest import MySQLIngestRequest
from app.services.utils import flatten_row
from app.services.vector_store import VectorStoreWriter


class MySQLIngestor:
    """Ingests MySQL rows, rewrites or flattens them, and writes embeddings."""

    def __init__(self, config: Config, prompt_manager: Optional[PromptManager] = None):
        self.config = config
        self.prompt_manager = prompt_manager or build_prompt_manager_from_env()
        self.llm_client = LLMClient(config)
        self.vector_writer = VectorStoreWriter(config)
        self.logger = logging.getLogger(__name__)

    def ingest(self, request: MySQLIngestRequest) -> Dict[str, int]:
        engine = create_engine(request.connection_url)
        total_rows = 0
        embedded_rows = 0

        with engine.connect() as conn:
            schema = self._fetch_schema(conn, request.table)
            query = self._build_query(request)

            chunks = pd.read_sql_query(query, conn, chunksize=request.chunk_size)
            if isinstance(chunks, pd.DataFrame):
                embedded_rows += self._process_chunk(chunks, schema, request)
                total_rows += len(chunks)
            else:
                for chunk in chunks:
                    total_rows += len(chunk)
                    embedded_rows += self._process_chunk(chunk, schema, request)

        self.logger.info("MySQL ingest完成: 共读取 %s 条, 写入 %s 条", total_rows, embedded_rows)
        return {"rows_read": total_rows, "rows_embedded": embedded_rows}

    def _process_chunk(
        self,
        chunk: pd.DataFrame,
        schema: List[SchemaColumn],
        request: MySQLIngestRequest,
    ) -> int:
        if chunk.empty:
            return 0

        items: List[Dict] = []
        template_key = request.prompt_key or request.table
        override_template = request.prompt_template
        effective_schema = schema or [SchemaColumn(name=str(col)) for col in chunk.columns]

        for idx, row in chunk.iterrows():
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            merged_meta = {**row_dict, **request.extra_metadata}

            source_id = self._extract_identifier(row_dict, request.id_column, idx)
            company_name = self._extract_optional_field(row_dict, request.company_field)
            report_year = self._extract_optional_field(row_dict, request.report_year_field)

            if request.mode == "flatten":
                content = flatten_row(merged_meta, self.config)
            else:
                system_prompt, user_prompt = self.prompt_manager.get_prompt(
                    template_key,
                    merged_meta,
                    schema=effective_schema,
                    override_template=override_template,
                    context_table_name=request.table,
                )
                content = self._generate_with_retry(user_prompt, system_prompt)
                if not content:
                    self.logger.warning("跳过第 %s 行，LLM 未返回内容", idx)
                    continue

            items.append(
                {
                    "source_table": request.table,
                    "source_id": source_id,
                    "rewritten_content": content,
                    "company_name": company_name or "",
                    "report_year": report_year or "",
                    "original_data": merged_meta,
                }
            )

        if not items:
            return 0

        return self.vector_writer.upsert(items, self.logger)

    def _generate_with_retry(self, prompt: str, system_prompt: str) -> Optional[str]:
        for attempt in range(self.config.retry_times):
            try:
                content = self.llm_client.generate(prompt, system_prompt)
                if content:
                    return content
            except Exception as exc:
                self.logger.warning("LLM 生成失败 (尝试 %s/%s): %s", attempt + 1, self.config.retry_times, exc)
                if attempt < self.config.retry_times - 1:
                    time.sleep(self.config.retry_delay)
        return None

    def _extract_identifier(self, row: Dict, id_column: Optional[str], fallback_idx: int) -> str:
        if id_column and id_column in row and row[id_column] is not None:
            return str(row[id_column])
        return str(fallback_idx)

    def _extract_optional_field(self, row: Dict, field_name: Optional[str]) -> Optional[str]:
        if not field_name:
            return None
        value = row.get(field_name)
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _build_query(self, request: MySQLIngestRequest):
        base = f"SELECT * FROM `{request.table}`"
        if request.where:
            base += f" WHERE {request.where}"
        if request.limit:
            base += f" LIMIT {int(request.limit)}"
        return text(base)

    def _fetch_schema(self, conn, table: str) -> List[SchemaColumn]:
        result = conn.execute(text(f"SHOW FULL COLUMNS FROM `{table}`"))
        schema = []
        for row in result:
            mapping = row._mapping if hasattr(row, "_mapping") else row
            schema.append(
                SchemaColumn(
                    name=mapping.get("Field"),
                    data_type=mapping.get("Type"),
                    comment=mapping.get("Comment"),
                )
            )
        return schema
