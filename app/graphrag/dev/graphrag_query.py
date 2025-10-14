#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GraphRAG查询API调用测试脚本
这个脚本演示如何使用Python代码直接调用GraphRAG的查询功能
"""

import asyncio
import logging
import warnings
import os
from pathlib import Path
import pandas as pd
import json
import sys

# 导入我们的日志工具
from utils import setup_logging

# 抑制不相关的警告
warnings.filterwarnings("ignore", category=SyntaxWarning)

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.callbacks.noop_query_callbacks import NoopQueryCallbacks
from graphrag.callbacks.query_callbacks import QueryCallbacks
from graphrag.utils.storage import load_table_from_storage
from graphrag.storage.file_pipeline_storage import FilePipelineStorage

# ========================================
# 用户配置参数 - 直接修改这里的变量
# ========================================

# GraphRAG项目根目录路径
PROJECT_DIR = "E:\\my_graphrag\\graphrag_2.1.0\\graphrag"

# 数据目录名称（相对于项目根目录）
DATA_DIR_NAME = "data"

# 查询内容
QUERY = "微软的创始人是谁？"
# QUERY = "创联世纪传媒有限公司智能科技都购买了哪些产品？？"

# 查询类型: "local", "global", "drift", "basic"
QUERY_TYPE = "local"

# 响应类型: "text", "json" 等
RESPONSE_TYPE = "text"

# 社区级别
COMMUNITY_LEVEL = 3

# 是否使用动态社区选择
DYNAMIC_COMMUNITY_SELECTION = False

# 输出文件路径（设为None表示不输出到文件）
OUTPUT_FILE = None

# 全局日志记录器
logger = None

async def run_query(
    project_dir: str, 
    data_dir_name: str,
    query: str, 
    query_type: str = "local", 
    response_type: str = "text", 
    community_level: int = 1,
    dynamic_community_selection: bool = False,
    config_overrides: dict = None
):
    """
    运行GraphRAG查询过程

    参数:
    project_dir (str): GraphRAG项目根目录路径
    data_dir_name (str): 数据目录名称
    query (str): 用户查询文本
    query_type (str): 查询类型，可选值: "local", "global", "drift", "basic"
    response_type (str): 响应类型，默认为"text"
    community_level (int): 社区级别，默认为1
    dynamic_community_selection (bool): 是否使用动态社区选择
    config_overrides (dict): 配置覆盖参数
    """
    # 构建完整项目路径
    PROJECT_DIRECTORY = os.path.join(project_dir, data_dir_name)
    
    # 设置日志目录为项目的logs目录
    log_dir = Path(PROJECT_DIRECTORY) / "logs"
    global logger
    logger = setup_logging(log_dir, log_file="graphrag_query.log", logger_name="dev-graphrag-query")
    
    logger.info(f"从目录加载配置: {project_dir}")
    logger.info(f"使用数据目录: {PROJECT_DIRECTORY}")
    logger.info(f"查询类型: {query_type}")
    logger.info(f"查询内容: {query}")
    logger.info(f"社区级别: {community_level}")
    logger.info(f"动态社区选择: {'是' if dynamic_community_selection else '否'}")
    
    # 加载配置
    graphrag_config = load_config(Path(PROJECT_DIRECTORY), None, config_overrides)
    
    # 创建存储路径
    output_dir = Path(graphrag_config.output.base_dir)
    if not output_dir.is_absolute():
        output_dir = Path(PROJECT_DIRECTORY) / output_dir
    
    logger.info(f"使用输出目录: {output_dir}")
    
    # 创建一个FilePipelineStorage对象
    storage = FilePipelineStorage(root_dir=str(output_dir))
    
    # 加载必要的数据文件
    try:
        # 使用PipelineStorage对象加载parquet文件
        entities = await load_table_from_storage("entities", storage)
        logger.info(f"已加载实体数据，共 {len(entities)} 条记录")
        
        text_units = await load_table_from_storage("text_units", storage)
        logger.info(f"已加载文本单元数据，共 {len(text_units)} 条记录")
        
        communities = await load_table_from_storage("communities", storage)
        logger.info(f"已加载社区数据，共 {len(communities)} 条记录")
        
        community_reports = await load_table_from_storage("community_reports", storage)
        logger.info(f"已加载社区报告数据，共 {len(community_reports)} 条记录")
        
        relationships = await load_table_from_storage("relationships", storage)
        logger.info(f"已加载关系数据，共 {len(relationships)} 条记录")
        
        # 尝试加载协变量数据（可能不存在）
        try:
            covariates = await load_table_from_storage("covariates", storage)
            logger.info(f"已加载协变量数据，共 {len(covariates)} 条记录")
        except Exception:
            covariates = None
            logger.info("未找到协变量数据，将使用None")
        
    except Exception as e:
        logger.error(f"加载数据文件时出错: {str(e)}", exc_info=True)
        raise
    
    # 创建回调对象
    callbacks = []
    context_data = {}
    
    def on_context(context):
        nonlocal context_data
        context_data = context
    
    local_callbacks = NoopQueryCallbacks()
    local_callbacks.on_context = on_context
    callbacks.append(local_callbacks)
    
    logger.info("开始执行查询...")
    
    try:
        # 根据查询类型执行不同的查询
        if query_type.lower() == "local":
            response, context = await api.local_search(
                config=graphrag_config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                text_units=text_units,
                relationships=relationships,
                covariates=covariates,
                community_level=community_level,
                response_type=response_type,
                query=query,
                callbacks=callbacks
            )
        
        elif query_type.lower() == "global":
            response, context = await api.global_search(
                config=graphrag_config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                community_level=community_level,
                dynamic_community_selection=dynamic_community_selection,
                response_type=response_type,
                query=query,
                callbacks=callbacks
            )
        
        elif query_type.lower() == "drift":
            response, context = await api.drift_search(
                config=graphrag_config,
                entities=entities,
                communities=communities,
                community_reports=community_reports,
                text_units=text_units,
                relationships=relationships,
                community_level=community_level,
                response_type=response_type,
                query=query,
                callbacks=callbacks
            )
        
        elif query_type.lower() == "basic":
            response, context = await api.basic_search(
                config=graphrag_config,
                text_units=text_units,
                query=query,
                callbacks=callbacks
            )
        
        else:
            raise ValueError(f"不支持的查询类型: {query_type}，支持的类型有: local, global, drift, basic")
        
        logger.info("查询成功完成")
        
        # 返回响应和上下文
        return response, context
    
    except Exception as e:
        logger.error(f"查询过程中发生错误: {str(e)}", exc_info=True)
        raise

def main():
    """主函数入口点"""
    # 直接使用全局设置的变量
    try:
        response, context = asyncio.run(run_query(
            project_dir=PROJECT_DIR,
            data_dir_name=DATA_DIR_NAME,
            query=QUERY,
            query_type=QUERY_TYPE,
            response_type=RESPONSE_TYPE,
            community_level=COMMUNITY_LEVEL,
            dynamic_community_selection=DYNAMIC_COMMUNITY_SELECTION
        ))
        
        # 打印响应
        print("\n" + "="*50)
        print("查询结果:")
        print("="*50)
        print(response)
        print("="*50)
        
        # 如果指定了输出文件，则将结果保存到文件
        if OUTPUT_FILE:
            output_path = Path(OUTPUT_FILE)
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入结果
            with open(output_path, "w", encoding="utf-8") as f:
                result = {
                    "query": QUERY,
                    "response": response,
                    "context": str(context)  # 简单转换为字符串，实际应用中可能需要更复杂的序列化
                }
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"\n结果已保存到文件: {output_path}")
        
    except Exception as e:
        print(f"运行查询时发生错误: {str(e)}")
        exit(1)
    
if __name__ == "__main__":
    main()
