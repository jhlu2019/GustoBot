"""
MySQL 到 pgvector 的数据同步脚本
支持增量同步和全量同步
"""
import pymysql
import psycopg2
from psycopg2.extras import Json
import openai
from typing import List, Dict, Optional
from datetime import datetime
import time

class DataSyncService:
    """数据同步服务"""

    def __init__(
        self,
        mysql_config: Dict,
        pg_config: Dict,
        openai_api_key: str,
        embedding_model: str = "text-embedding-3-small"
    ):
        self.mysql_config = mysql_config
        self.pg_config = pg_config
        self.openai_api_key = openai_api_key
        self.embedding_model = embedding_model
        self.openai_client = openai.OpenAI(api_key=openai_api_key)

    def get_mysql_connection(self):
        """获取 MySQL 连接"""
        return pymysql.connect(
            host=self.mysql_config['host'],
            user=self.mysql_config['user'],
            password=self.mysql_config['password'],
            database=self.mysql_config['database'],
            cursorclass=pymysql.cursors.DictCursor
        )

    def get_pg_connection(self):
        """获取 PostgreSQL 连接"""
        return psycopg2.connect(
            host=self.pg_config['host'],
            user=self.pg_config['user'],
            password=self.pg_config['password'],
            database=self.pg_config['database']
        )

    def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[str]:
        """
        将长文本切分成多个 chunk

        Args:
            text: 原始文本
            chunk_size: 每个 chunk 的大小
            overlap: chunk 之间的重叠

        Returns:
            chunk 列表
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap

        return chunks

    def get_embedding(self, text: str) -> List[float]:
        """生成文本向量"""
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Embedding error: {e}")
            raise

    def sync_document(
        self,
        document_id: int,
        title: str,
        content: str,
        metadata: Optional[Dict] = None,
        chunk_size: int = 500
    ) -> int:
        """
        同步单个文档到 pgvector

        Args:
            document_id: MySQL 文档 ID
            title: 文档标题
            content: 文档内容
            metadata: 元数据
            chunk_size: 分块大小

        Returns:
            插入的向量数量
        """
        pg_conn = self.get_pg_connection()
        cursor = pg_conn.cursor()

        try:
            # 检查是否已存在
            cursor.execute(
                "SELECT COUNT(*) FROM document_embeddings WHERE document_id = %s",
                (document_id,)
            )
            exists_count = cursor.fetchone()[0]

            if exists_count > 0:
                # 删除旧的向量
                cursor.execute(
                    "DELETE FROM document_embeddings WHERE document_id = %s",
                    (document_id,)
                )
                print(f"删除文档 {document_id} 的 {exists_count} 个旧向量")

            # 构建完整文本（标题 + 内容）
            full_text = f"{title}\n\n{content}"

            # 切分文本
            chunks = self.chunk_text(full_text, chunk_size=chunk_size)
            print(f"文档 {document_id} 被切分为 {len(chunks)} 个 chunk")

            # 为每个 chunk 生成向量并存储
            insert_count = 0
            for chunk_index, chunk_text in enumerate(chunks):
                # 生成向量
                embedding = self.get_embedding(chunk_text)

                # 准备元数据
                chunk_metadata = metadata or {}
                chunk_metadata.update({
                    'title': title,
                    'chunk_index': chunk_index,
                    'total_chunks': len(chunks)
                })

                # 插入向量
                cursor.execute("""
                    INSERT INTO document_embeddings
                    (document_id, chunk_index, content, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    document_id,
                    chunk_index,
                    chunk_text,
                    embedding,
                    Json(chunk_metadata)
                ))

                insert_count += 1

                # 避免 API 限流
                time.sleep(0.1)

            pg_conn.commit()
            print(f"✓ 文档 {document_id} 同步完成，插入 {insert_count} 个向量")
            return insert_count

        except Exception as e:
            pg_conn.rollback()
            print(f"✗ 文档 {document_id} 同步失败: {e}")
            raise

        finally:
            cursor.close()
            pg_conn.close()

    def full_sync(
        self,
        table_name: str = "documents",
        title_column: str = "title",
        content_column: str = "content",
        metadata_columns: Optional[List[str]] = None,
        batch_size: int = 100
    ):
        """
        全量同步 MySQL 数据到 pgvector

        Args:
            table_name: MySQL 表名
            title_column: 标题列名
            content_column: 内容列名
            metadata_columns: 需要同步的元数据列
            batch_size: 批量处理大小
        """
        mysql_conn = self.get_mysql_connection()
        cursor = mysql_conn.cursor()

        try:
            # 获取总数
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            total = cursor.fetchone()['count']
            print(f"开始全量同步，共 {total} 条记录")

            # 分批处理
            offset = 0
            synced_count = 0
            failed_count = 0

            while offset < total:
                # 查询一批数据
                query = f"""
                    SELECT id, {title_column}, {content_column}
                    {', ' + ', '.join(metadata_columns) if metadata_columns else ''}
                    FROM {table_name}
                    ORDER BY id
                    LIMIT {batch_size} OFFSET {offset}
                """
                cursor.execute(query)
                documents = cursor.fetchall()

                # 同步每个文档
                for doc in documents:
                    try:
                        # 准备元数据
                        metadata = {}
                        if metadata_columns:
                            for col in metadata_columns:
                                if col in doc:
                                    value = doc[col]
                                    # 处理日期类型
                                    if isinstance(value, datetime):
                                        metadata[col] = value.isoformat()
                                    else:
                                        metadata[col] = value

                        # 同步文档
                        self.sync_document(
                            document_id=doc['id'],
                            title=doc[title_column] or "",
                            content=doc[content_column] or "",
                            metadata=metadata
                        )
                        synced_count += 1

                    except Exception as e:
                        print(f"同步文档 {doc['id']} 失败: {e}")
                        failed_count += 1

                offset += batch_size
                print(f"进度: {min(offset, total)}/{total} ({synced_count} 成功, {failed_count} 失败)")

            print(f"\n全量同步完成！")
            print(f"总计: {total}, 成功: {synced_count}, 失败: {failed_count}")

        finally:
            cursor.close()
            mysql_conn.close()

    def incremental_sync(
        self,
        table_name: str = "documents",
        title_column: str = "title",
        content_column: str = "content",
        updated_at_column: str = "updated_at",
        last_sync_time: Optional[datetime] = None,
        metadata_columns: Optional[List[str]] = None
    ):
        """
        增量同步（仅同步最近更新的数据）

        Args:
            table_name: MySQL 表名
            title_column: 标题列名
            content_column: 内容列名
            updated_at_column: 更新时间列名
            last_sync_time: 上次同步时间
            metadata_columns: 需要同步的元数据列
        """
        mysql_conn = self.get_mysql_connection()
        cursor = mysql_conn.cursor()

        try:
            # 构建查询
            query = f"""
                SELECT id, {title_column}, {content_column}, {updated_at_column}
                {', ' + ', '.join(metadata_columns) if metadata_columns else ''}
                FROM {table_name}
            """

            if last_sync_time:
                query += f" WHERE {updated_at_column} > %s"
                cursor.execute(query, (last_sync_time,))
            else:
                cursor.execute(query)

            documents = cursor.fetchall()
            print(f"发现 {len(documents)} 条待同步记录")

            synced_count = 0
            failed_count = 0

            for doc in documents:
                try:
                    # 准备元数据
                    metadata = {}
                    if metadata_columns:
                        for col in metadata_columns:
                            if col in doc:
                                value = doc[col]
                                if isinstance(value, datetime):
                                    metadata[col] = value.isoformat()
                                else:
                                    metadata[col] = value

                    # 同步文档
                    self.sync_document(
                        document_id=doc['id'],
                        title=doc[title_column] or "",
                        content=doc[content_column] or "",
                        metadata=metadata
                    )
                    synced_count += 1

                except Exception as e:
                    print(f"同步文档 {doc['id']} 失败: {e}")
                    failed_count += 1

            print(f"\n增量同步完成！成功: {synced_count}, 失败: {failed_count}")

        finally:
            cursor.close()
            mysql_conn.close()


# ============ 使用示例 ============
if __name__ == "__main__":
    # 配置
    MYSQL_CONFIG = {
        'host': 'localhost',
        'user': 'root',
        'password': 'password',
        'database': 'documents_db'
    }

    PG_CONFIG = {
        'host': 'localhost',
        'user': 'postgres',
        'password': 'password',
        'database': 'vector_db'
    }

    OPENAI_API_KEY = "your-openai-api-key"

    # 创建同步服务
    sync_service = DataSyncService(
        mysql_config=MYSQL_CONFIG,
        pg_config=PG_CONFIG,
        openai_api_key=OPENAI_API_KEY
    )

    # 全量同步
    print("开始全量同步...")
    sync_service.full_sync(
        table_name="documents",
        title_column="title",
        content_column="content",
        metadata_columns=["category", "author", "created_at"],
        batch_size=50
    )

    # 增量同步示例
    # last_sync = datetime(2024, 1, 1)
    # sync_service.incremental_sync(
    #     last_sync_time=last_sync,
    #     metadata_columns=["category", "author"]
    # )
