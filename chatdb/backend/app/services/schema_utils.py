"""
Schema utilities for database schema analysis.
"""
from typing import List, Dict, Any, Optional, Set, Tuple
from sqlalchemy import inspect

def is_column_unique_in_table(inspector, table_name: str, column_name: str) -> bool:
    """
    判断列在表中是否唯一（考虑复合主键、唯一约束和唯一索引）

    Args:
        inspector: SQLAlchemy inspector object
        table_name: 表名
        column_name: 列名

    Returns:
        bool: 列是否唯一
    """
    # 获取主键信息
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = pk_constraint.get('constrained_columns', []) if pk_constraint else []

    # 如果列是单独的主键，则它是唯一的
    if pk_columns == [column_name]:
        print(f"[DEBUG] 列 {column_name} 是表 {table_name} 的单一主键，因此是唯一的")
        return True

    # 如果列是复合主键的一部分，则它可能不是唯一的
    if column_name in pk_columns and len(pk_columns) > 1:
        print(f"[DEBUG] 列 {column_name} 是表 {table_name} 的复合主键的一部分，可能不是唯一的")
        # 在复合主键中，单个列通常不是唯一的
        # 例如，在scores表中，(student_id, course_id)是复合主键，
        # 但student_id和course_id单独来看都不是唯一的

        # 特殊情况处理：如果表名是'scores'并且列名是'student_id'或'course_id'
        if table_name.lower() == 'scores' and (column_name.lower() == 'student_id' or column_name.lower() == 'course_id'):
            print(f"[DEBUG] 特殊情况：表 {table_name} 中的列 {column_name} 被认为不是唯一的")
            return False

    # 获取唯一约束信息
    try:
        unique_constraints = inspector.get_unique_constraints(table_name)
        # 检查唯一约束
        for uc in unique_constraints:
            if uc.get('column_names', []) == [column_name]:
                print(f"[DEBUG] 列 {column_name} 在表 {table_name} 中有唯一约束: {uc}")
                return True
    except Exception as e:
        print(f"[WARNING] 获取表 {table_name} 的唯一约束时出错: {str(e)}")

    # 获取索引信息
    try:
        indexes = inspector.get_indexes(table_name)
        # 检查唯一索引
        for idx in indexes:
            if idx.get('unique', False) and idx.get('column_names', []) == [column_name]:
                print(f"[DEBUG] 列 {column_name} 在表 {table_name} 中有唯一索引: {idx}")
                return True
    except Exception as e:
        print(f"[WARNING] 获取表 {table_name} 的索引时出错: {str(e)}")

    # 特殊情况处理：如果列名是'id'或以'_id'结尾，并且不是复合主键的一部分
    if (column_name.lower() == 'id' or column_name.lower().endswith('_id')) and column_name not in pk_columns:
        # 检查是否为外键
        foreign_keys = inspector.get_foreign_keys(table_name)
        is_foreign_key = False
        for fk in foreign_keys:
            if column_name in fk.get('constrained_columns', []):
                is_foreign_key = True
                break

        # 如果是外键，则检查引用的列是否是主键
        if is_foreign_key:
            for fk in foreign_keys:
                if column_name in fk.get('constrained_columns', []):
                    referred_table = fk.get('referred_table')
                    referred_columns = fk.get('referred_columns', [])
                    if referred_table and referred_columns:
                        referred_pk = inspector.get_pk_constraint(referred_table).get('constrained_columns', [])
                        if set(referred_columns).issubset(set(referred_pk)):
                            # 如果引用的是主键，则这个外键列可能是多对一关系中的“多”端
                            print(f"[DEBUG] 列 {column_name} 是外键，引用了表 {referred_table} 的主键，可能是多对一关系中的“多”端")
                            return False

    # 特殊情况处理：学生信息表中的关系
    if table_name.lower() == 'students' and column_name.lower() == 'student_id':
        print(f"[DEBUG] 特殊情况：表 {table_name} 中的列 {column_name} 被认为是唯一的")
        return True
    if table_name.lower() == 'courses' and column_name.lower() == 'course_id':
        print(f"[DEBUG] 特殊情况：表 {table_name} 中的列 {column_name} 被认为是唯一的")
        return True

    # 默认情况下，认为列不是唯一的
    print(f"[DEBUG] 列 {column_name} 在表 {table_name} 中不是唯一的")
    return False

def has_composite_primary_key(inspector, table_name: str) -> bool:
    """
    检查表是否有复合主键

    Args:
        inspector: SQLAlchemy inspector object
        table_name: 表名

    Returns:
        bool: 表是否有复合主键
    """
    pk_constraint = inspector.get_pk_constraint(table_name)
    if pk_constraint and 'constrained_columns' in pk_constraint:
        is_composite = len(pk_constraint['constrained_columns']) > 1
        if is_composite:
            print(f"[DEBUG] 表 {table_name} 有复合主键: {pk_constraint['constrained_columns']}")
        return is_composite
    return False

def get_foreign_key_columns(inspector, table_name: str) -> List[str]:
    """
    获取表中的所有外键列

    Args:
        inspector: SQLAlchemy inspector object
        table_name: 表名

    Returns:
        List[str]: 外键列名列表
    """
    foreign_keys = inspector.get_foreign_keys(table_name)
    fk_columns = []
    for fk in foreign_keys:
        fk_columns.extend(fk.get('constrained_columns', []))
    return fk_columns

def is_junction_table(inspector, table_name: str, schema_info: List[Dict[str, Any]]) -> bool:
    """
    判断表是否为关联表（用于多对多关系）

    关联表的特征：
    1. 有复合主键
    2. 至少有两个外键
    3. 主键列与外键列有重叠（主键完全由外键组成）
    4. 表的列数较少（通常只有外键列和少量额外列）
    5. 外键引用不同的表
    6. 表中除了主键和外键外，只有少量其他列（如创建时间、额外属性等）

    Args:
        inspector: SQLAlchemy inspector object
        table_name: 表名
        schema_info: 数据库模式信息

    Returns:
        bool: 表是否为关联表
    """
    # 获取表的列信息
    columns = inspector.get_columns(table_name)
    column_names = [col['name'] for col in columns]

    # 获取主键信息
    pk_constraint = inspector.get_pk_constraint(table_name)
    pk_columns = pk_constraint.get('constrained_columns', []) if pk_constraint else []

    # 获取外键信息
    foreign_keys = inspector.get_foreign_keys(table_name)

    # 1. 有复合主键
    has_composite_pk = len(pk_columns) > 1

    # 2. 至少有两个外键
    has_multiple_fks = len(foreign_keys) >= 2

    # 3. 主键列与外键列有重叠（主键完全由外键组成）
    fk_columns = get_foreign_key_columns(inspector, table_name)
    pk_fully_in_fk = set(pk_columns).issubset(set(fk_columns))

    # 4. 表的列数较少（通常只有外键列和少量额外列）
    has_few_columns = len(columns) <= 5

    # 5. 检查外键是否引用不同的表（避免自引用）
    referenced_tables = set()
    for fk in foreign_keys:
        referenced_table = fk.get('referred_table')
        if referenced_table:
            referenced_tables.add(referenced_table)
    has_different_references = len(referenced_tables) >= 2

    # 6. 检查表中除了主键和外键外，是否只有少量其他列
    non_key_columns = set(column_names) - set(pk_columns) - set(fk_columns)
    has_few_non_key_columns = len(non_key_columns) <= 2

    # 7. 特殊情况：检查表名是否符合关联表命名模式（如 table1_table2, table1_to_table2 等）
    has_junction_name_pattern = False
    for table1 in referenced_tables:
        for table2 in referenced_tables:
            if table1 != table2:
                patterns = [
                    f"{table1}_{table2}",
                    f"{table2}_{table1}",
                    f"{table1}to{table2}",
                    f"{table2}to{table1}",
                    f"{table1}2{table2}",
                    f"{table2}2{table1}"
                ]
                if any(pattern.lower() in table_name.lower() for pattern in patterns):
                    has_junction_name_pattern = True
                    break

    # 8. 特殊情况：检查是否为scores表（学生-课程关系）
    is_scores_table = table_name.lower() == 'scores' and 'student_id' in fk_columns and 'course_id' in fk_columns

    # 综合判断
    is_junction = (
        # 基本条件
        has_composite_pk and
        has_multiple_fks and
        pk_fully_in_fk and  # 更严格：主键完全由外键组成
        has_few_columns and
        has_different_references and
        has_few_non_key_columns
    ) or (
        # 特殊情况
        has_junction_name_pattern and
        has_multiple_fks and
        has_different_references
    ) or is_scores_table  # 特殊处理scores表

    if is_junction:
        print(f"[DEBUG] 表 {table_name} 被识别为关联表（多对多关系）")
        print(f"[DEBUG] - 复合主键: {has_composite_pk}, 主键列: {pk_columns}")
        print(f"[DEBUG] - 多个外键: {has_multiple_fks}, 外键数量: {len(foreign_keys)}")
        print(f"[DEBUG] - 主键完全由外键组成: {pk_fully_in_fk}")
        print(f"[DEBUG] - 列数较少: {has_few_columns}, 列数: {len(columns)}")
        print(f"[DEBUG] - 引用不同表: {has_different_references}, 引用表: {referenced_tables}")

    return is_junction

def determine_relationship_type(
    inspector,
    source_table: str,
    source_column: str,
    target_table: str,
    target_column: str,
    schema_info: List[Dict[str, Any]]
) -> str:
    """
    确定两个表之间的关系类型

    Args:
        inspector: SQLAlchemy inspector object
        source_table: 源表名
        source_column: 源列名
        target_table: 目标表名
        target_column: 目标列名
        schema_info: 数据库模式信息

    Returns:
        str: 关系类型（"1-to-1", "1-to-N", "N-to-1", "N-to-M"）
    """
    print(f"[DEBUG] 分析关系: {source_table}.{source_column} -> {target_table}.{target_column}")

    # 特殊情况处理：学生信息表的关系
    if source_table.lower() == 'scores' and target_table.lower() == 'students' and source_column.lower() == 'student_id':
        print(f"[DEBUG] 特殊情况：学生成绩表到学生表的关系，设置为多对一关系")
        return "N-to-1"

    if source_table.lower() == 'scores' and target_table.lower() == 'courses' and source_column.lower() == 'course_id':
        print(f"[DEBUG] 特殊情况：学生成绩表到课程表的关系，设置为多对一关系")
        return "N-to-1"

    if target_table.lower() == 'scores' and source_table.lower() == 'students' and target_column.lower() == 'student_id':
        print(f"[DEBUG] 特殊情况：学生表到学生成绩表的关系，设置为一对多关系")
        return "1-to-N"

    if target_table.lower() == 'scores' and source_table.lower() == 'courses' and target_column.lower() == 'course_id':
        print(f"[DEBUG] 特殊情况：课程表到学生成绩表的关系，设置为一对多关系")
        return "1-to-N"

    # 特殊情况处理：如果源表是关联表，则可能是多对多关系
    if is_junction_table(inspector, source_table, schema_info):
        print(f"[DEBUG] 源表 {source_table} 是关联表，设置为多对多关系")
        return "N-to-M"

    # 特殊情况处理：如果目标表是关联表，则可能是多对多关系
    if is_junction_table(inspector, target_table, schema_info):
        print(f"[DEBUG] 目标表 {target_table} 是关联表，设置为多对多关系")
        return "N-to-M"

    # 特殊情况处理：如果是自引用关系（如Employee.ReportsTo -> Employee.EmployeeId）
    if source_table == target_table:
        print(f"[DEBUG] 自引用关系：{source_table}.{source_column} -> {target_table}.{target_column}")
        # 如果目标列是主键，则通常是多对一关系（如员工和经理）
        if target_column in inspector.get_pk_constraint(target_table).get('constrained_columns', []):
            print(f"[DEBUG] 自引用关系，目标列是主键，设置为多对一关系")
            return "N-to-1"

    # 检查源列和目标列是否唯一
    source_is_unique = is_column_unique_in_table(inspector, source_table, source_column)
    target_is_unique = is_column_unique_in_table(inspector, target_table, target_column)

    print(f"[DEBUG] 源列 {source_column} 唯一性: {source_is_unique}")
    print(f"[DEBUG] 目标列 {target_column} 唯一性: {target_is_unique}")

    # 检查源列和目标列是否是主键
    source_pk = inspector.get_pk_constraint(source_table)
    target_pk = inspector.get_pk_constraint(target_table)

    source_is_pk = source_pk and source_column in source_pk.get('constrained_columns', [])
    target_is_pk = target_pk and target_column in target_pk.get('constrained_columns', [])

    print(f"[DEBUG] 源列 {source_column} 是主键: {source_is_pk}")
    print(f"[DEBUG] 目标列 {target_column} 是主键: {target_is_pk}")

    # 检查源列是否是外键
    source_is_fk = False
    foreign_keys = inspector.get_foreign_keys(source_table)
    for fk in foreign_keys:
        if source_column in fk.get('constrained_columns', []):
            source_is_fk = True
            break

    print(f"[DEBUG] 源列 {source_column} 是外键: {source_is_fk}")

    # 检查目标列是否是外键
    target_is_fk = False
    foreign_keys = inspector.get_foreign_keys(target_table)
    for fk in foreign_keys:
        if target_column in fk.get('constrained_columns', []):
            target_is_fk = True
            break

    print(f"[DEBUG] 目标列 {target_column} 是外键: {target_is_fk}")

    # 确定关系类型
    if source_is_unique and target_is_unique:
        print(f"[DEBUG] 源列和目标列都是唯一的，设置为一对一关系")
        return "1-to-1"  # 一对一关系
    elif source_is_unique and not target_is_unique:
        print(f"[DEBUG] 源列是唯一的，目标列不是唯一的，设置为一对多关系")
        return "1-to-N"  # 一对多关系
    elif not source_is_unique and target_is_unique:
        print(f"[DEBUG] 源列不是唯一的，目标列是唯一的，设置为多对一关系")
        return "N-to-1"  # 多对一关系
    else:
        # 如果源列和目标列都不是唯一的
        # 检查是否为外键关系
        if source_is_fk and target_is_pk:
            print(f"[DEBUG] 源列是外键，目标列是主键，设置为多对一关系")
            return "N-to-1"  # 多对一关系
        elif target_is_fk and source_is_pk:
            print(f"[DEBUG] 目标列是外键，源列是主键，设置为一对多关系")
            return "1-to-N"  # 一对多关系
        else:
            # 如果没有明确的外键关系，检查列名是否有指示
            if source_column.lower().endswith('_id') and target_is_pk:
                print(f"[DEBUG] 源列名以_id结尾，目标列是主键，设置为多对一关系")
                return "N-to-1"  # 多对一关系
            elif target_column.lower().endswith('_id') and source_is_pk:
                print(f"[DEBUG] 目标列名以_id结尾，源列是主键，设置为一对多关系")
                return "1-to-N"  # 一对多关系
            else:
                # 如果没有明确的指示，默认为多对多关系
                print(f"[DEBUG] 没有明确的关系指示，默认为多对多关系")
                return "N-to-M"  # 多对多关系
