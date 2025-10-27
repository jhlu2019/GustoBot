
import argparse
import os
import sys
from datetime import datetime

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    """获取数据库连接"""
    return psycopg2.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        database=os.getenv("PGDATABASE", "vector_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", "postgres")
    )


def check_table_structure(conn):
    """检查表结构"""
    print("\n检查当前表结构...")

    cur = conn.cursor()

    # 检查表是否存在
    cur.execute("SELECT to_regclass('public.searchable_documents');")
    if cur.fetchone()[0] is None:
        print("❌ 表 searchable_documents 不存在")
        return None

    # 获取所有列
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'searchable_documents'
        ORDER BY ordinal_position
    """)

    columns = cur.fetchall()
    print(f"✓ 找到 {len(columns)} 列:")
    for col_name, col_type in columns:
        print(f"  - {col_name}: {col_type}")

    # 检查是否有旧列
    old_columns = ['company_name', 'report_year', 'credit_no', 'origin_status']
    cur.execute(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'searchable_documents'
          AND column_name IN ({','.join("'" + c + "'" for c in old_columns)})
    """)

    existing_old_columns = [row[0] for row in cur.fetchall()]

    if existing_old_columns:
        print(f"\n✓ 检测到旧版列: {existing_old_columns}")
        return 'old'
    else:
        print("\n✓ 已经是新版结构")
        return 'new'


def count_records(conn):
    """统计记录数"""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM searchable_documents")
    count = cur.fetchone()[0]
    print(f"✓ 当前有 {count} 条记录")
    return count


def backup_table(conn):
    """备份表"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_table_name = f"searchable_documents_backup_{timestamp}"

    print(f"\n创建备份表: {backup_table_name}")

    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE {backup_table_name} AS
        SELECT * FROM searchable_documents
    """)
    conn.commit()

    print(f"✓ 备份完成: {backup_table_name}")
    return backup_table_name


def migrate_data(conn, dry_run=False):
    """迁移数据"""
    print("\n开始迁移数据...")

    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 获取所有记录
    cur.execute("SELECT * FROM searchable_documents")
    records = cur.fetchall()

    print(f"需要迁移 {len(records)} 条记录")

    if dry_run:
        print("\n[DRY RUN] 显示前3条迁移示例:")
        for i, record in enumerate(records[:3], 1):
            print(f"\n记录 {i}:")
            print(f"  source_table: {record.get('source_table')}")
            print(f"  source_id: {record.get('source_id')}")

            # 构建新的 metadata
            metadata = {}

            # 从旧列迁移
            old_fields = ['company_name', 'report_year', 'credit_no', 'origin_status']
            for field in old_fields:
                if field in record and record[field]:
                    metadata[field] = record[field]

            # 从旧的 metadata 合并
            if record.get('metadata'):
                import json
                try:
                    old_meta = json.loads(record['metadata'])
                    metadata.update(old_meta)
                except:
                    pass

            print(f"  新 metadata: {metadata}")
        return

    # 实际迁移
    # 1. 创建临时表
    print("\n1. 创建临时表...")
    cur.execute("""
        CREATE TABLE searchable_documents_new (
            id BIGSERIAL PRIMARY KEY,
            source_table TEXT NOT NULL,
            source_id TEXT NOT NULL,
            content TEXT NOT NULL,
            embedding vector,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(source_table, source_id)
        )
    """)
    conn.commit()

    # 2. 迁移数据
    print("2. 迁移数据到新表...")
    import json

    migrated = 0
    for record in records:
        # 构建 metadata
        metadata = {}

        # 从旧列迁移
        old_fields = ['company_name', 'report_year', 'credit_no', 'origin_status']
        for field in old_fields:
            if field in record and record[field]:
                metadata[field] = record[field]

        # 从旧的 metadata 合并
        if record.get('metadata'):
            try:
                old_meta = json.loads(record['metadata']) if isinstance(record['metadata'], str) else record['metadata']
                if isinstance(old_meta, dict):
                    metadata.update(old_meta)
            except:
                pass

        # 插入新表
        cur.execute("""
            INSERT INTO searchable_documents_new
                (id, source_table, source_id, content, embedding, metadata, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            record['id'],
            record['source_table'],
            record['source_id'],
            record['content'],
            record['embedding'],
            json.dumps(metadata, ensure_ascii=False) if metadata else None,
            record.get('created_at')
        ))

        migrated += 1
        if migrated % 100 == 0:
            print(f"  已迁移 {migrated}/{len(records)} 条...")
            conn.commit()

    conn.commit()
    print(f"✓ 数据迁移完成: {migrated} 条")

    # 3. 替换表
    print("3. 替换旧表...")
    cur.execute("DROP TABLE searchable_documents")
    cur.execute("ALTER TABLE searchable_documents_new RENAME TO searchable_documents")
    conn.commit()

    # 4. 创建索引
    print("4. 创建索引...")
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_source_pair
        ON searchable_documents(source_table, source_id)
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_metadata
        ON searchable_documents USING GIN (metadata)
    """)
    conn.commit()

    print("✓ 迁移完成！")


def main():
    parser = argparse.ArgumentParser(description="迁移到通用表结构")
    parser.add_argument("--dry-run", action="store_true", help="只显示将要执行的操作")
    parser.add_argument("--backup", action="store_true", help="迁移前备份")
    args = parser.parse_args()

    print("=" * 60)
    print("数据库迁移工具：旧表结构 → 通用表结构")
    print("=" * 60)

    try:
        # 连接数据库
        conn = get_db_connection()
        print("✓ 数据库连接成功")

        # 检查表结构
        structure = check_table_structure(conn)

        if structure is None:
            print("\n❌ 表不存在，无需迁移")
            return 1

        if structure == 'new':
            print("\n✓ 已经是新版结构，无需迁移")
            return 0

        # 统计记录数
        count = count_records(conn)

        if count == 0:
            print("\n⚠️  表为空，无需迁移")
            print("提示：新数据将自动使用新表结构")
            return 0

        # 备份
        if args.backup and not args.dry_run:
            backup_table(conn)

        # 迁移
        if args.dry_run:
            print("\n" + "=" * 60)
            print("DRY RUN 模式 - 不会实际执行")
            print("=" * 60)

        migrate_data(conn, dry_run=args.dry_run)

        if not args.dry_run:
            print("\n" + "=" * 60)
            print("✅ 迁移成功！")
            print("=" * 60)
            print("\n你现在可以使用新的通用表结构处理任意表了")
            print("示例:")
            print("  python main.py ingest-mysql <url> <table> --mode rewrite")
        else:
            print("\n" + "=" * 60)
            print("DRY RUN 完成")
            print("=" * 60)
            print("\n如果上面的迁移计划看起来正确，请运行:")
            print("  python migrate_to_generic.py --backup")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if 'conn' in locals():
            conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
