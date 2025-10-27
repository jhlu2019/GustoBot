"""
工具类模块，提供共享功能
"""
import json
import re
import time
from typing import Dict, Any, List, Optional, Set, Tuple


class CacheManager:
    """缓存管理器，提供缓存功能"""
    
    def __init__(self, max_size: int = 100, ttl: int = 3600):
        """初始化缓存管理器
        
        Args:
            max_size: 最大缓存条目数
            ttl: 缓存生存时间（秒）
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值
        
        Args:
            key: 缓存键
            
        Returns:
            Optional[Any]: 缓存值，如果不存在或已过期则返回None
        """
        if key not in self.cache:
            return None
        
        # 检查是否过期
        if time.time() - self.access_times[key] > self.ttl:
            self.remove(key)
            return None
        
        # 更新访问时间
        self.access_times[key] = time.time()
        return self.cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        # 如果缓存已满，移除最久未访问的条目
        if len(self.cache) >= self.max_size and key not in self.cache:
            oldest_key = min(self.access_times.items(), key=lambda x: x[1])[0]
            self.remove(oldest_key)
        
        self.cache[key] = value
        self.access_times[key] = time.time()
    
    def remove(self, key: str) -> None:
        """移除缓存条目
        
        Args:
            key: 缓存键
        """
        if key in self.cache:
            del self.cache[key]
        if key in self.access_times:
            del self.access_times[key]
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """从文本中提取JSON对象
    
    Args:
        text: 包含JSON的文本
        
    Returns:
        Optional[Dict[str, Any]]: 提取的JSON对象，如果提取失败则返回None
    """
    try:
        # 尝试直接解析整个文本
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试查找JSON对象
        json_match = re.search(r'\{[\s\S]*}', text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
    
    return None


def format_schema_context(schema_context: Dict[str, Any]) -> str:
    """将表结构信息格式化为SQL DDL字符串
    
    Args:
        schema_context: 表结构信息字典
        
    Returns:
        str: 格式化后的SQL DDL字符串
    """
    if not schema_context or not schema_context.get('tables'):
        return ""
    
    db_schema_str = ""
    for table in schema_context['tables']:
        table_name = table['name']
        db_schema_str += f"CREATE TABLE [{table_name}]\n(\n"
        
        # 添加列信息
        columns = [col for col in schema_context['columns'] if col['table_name'] == table_name]
        for column in columns:
            pk_flag = "PRIMARY KEY" if column['is_primary_key'] else ""
            fk_flag = "FOREIGN KEY" if column['is_foreign_key'] else ""
            db_schema_str += f"    [{column['name']}] {column['type']} {pk_flag} {fk_flag},\n"
        
        db_schema_str += ");\n\n"
    
    # 添加关系信息
    if schema_context.get('relationships'):
        db_schema_str += "/* 表关系 */\n"
        for rel in schema_context['relationships']:
            db_schema_str += f"-- {rel['source_table']}.{rel['source_column']} -> {rel['target_table']}.{rel['target_column']} ({rel['relationship_type'] or 'unknown'})\n"
    
    return db_schema_str


def format_schema_as_markdown(schema_context: Dict[str, Any]) -> str:
    """将表结构信息格式化为Markdown，适用于LLM提示中
    
    Args:
        schema_context: 表结构信息字典
        
    Returns:
        str: 格式化后的Markdown字符串
    """
    if not schema_context or not schema_context.get('tables'):
        return ""
    
    schema_info = "\n## 相关表结构\n"
    
    # 添加表信息
    for table in schema_context['tables']:
        table_name = table['name']
        table_desc = f" - {table['description']}" if table.get('description') else ""
        schema_info += f"### 表: {table_name}{table_desc}\n"
        
        # 添加列信息
        columns = [col for col in schema_context['columns'] if col['table_name'] == table_name]
        if columns:
            schema_info += "| 列名 | 类型 | 主键 | 外键 | 描述 |\n"
            schema_info += "| --- | --- | --- | --- | --- |\n"
            for column in columns:
                pk = "是" if column['is_primary_key'] else "否"
                fk = "是" if column['is_foreign_key'] else "否"
                desc = column.get('description', "")
                schema_info += f"| {column['name']} | {column['type']} | {pk} | {fk} | {desc} |\n"
        schema_info += "\n"
    
    # 添加关系信息
    if schema_context.get('relationships'):
        schema_info += "### 表关系\n"
        for rel in schema_context['relationships']:
            rel_type = f" ({rel['relationship_type']})" if rel.get('relationship_type') else ""
            schema_info += f"- {rel['source_table']}.{rel['source_column']} -> {rel['target_table']}.{rel['target_column']}{rel_type}\n"
    
    return schema_info
