#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GraphRAG索引API调用测试脚本
这个脚本演示如何使用Python代码直接调用GraphRAG的索引功能，
而不是通过命令行'poetry run poe index'命令。
"""

import asyncio
import logging
import warnings
import os
from pathlib import Path
from pprint import pprint
import sys

# 抑制不相关的警告
warnings.filterwarnings("ignore", category=SyntaxWarning)

# 导入我们的日志工具
from utils import setup_logging

import pandas as pd

import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.config.enums import IndexingMethod
from graphrag.logger.rich_progress import RichProgressLogger
from graphrag.index.typing.pipeline_run_result import PipelineRunResult

# ========================================
# 用户配置参数 - 直接修改这里的变量
# ========================================

# GraphRAG项目根目录路径
PROJECT_DIR = "E:\\my_graphrag\\graphrag_2.1.0\\graphrag"

# 数据目录名称（相对于项目根目录）
DATA_DIR_NAME = "data"

# 索引方法: "Standard" 或 "Fast"
INDEX_METHOD = "Standard"

# 是否进行增量更新
IS_UPDATE = True

# 是否进行内存分析
MEMORY_PROFILE = False

# 配置文件路径（为None则使用默认配置, 如果是增量更新，则需要指定配置文件，比如："E:\\my_graphrag\\graphrag_2.1.0\\graphrag\\data\\settings_pdf.yaml"）
CONFIG_FILE = "E:\\my_graphrag\\graphrag_2.1.0\\graphrag\\data\\settings_csv.yaml"

# 输出目录（为None则使用配置中的默认输出目录，）
OUTPUT_DIR = None

config_overrides = {}

# 全局日志记录器
logger = None

async def run_indexing(project_dir: str, data_dir_name: str):
    """运行GraphRAG索引过程"""
    # 构建完整项目路径
    PROJECT_DIRECTORY = os.path.join(project_dir, data_dir_name)
    
    # 设置日志目录为项目的logs目录
    log_dir = Path(PROJECT_DIRECTORY) / "logs"
    global logger
    logger = setup_logging(log_dir, log_file="dev_graphrag_indexing.log", logger_name="dev-graphrag-indexing")
    
    logger.info(f"从目录加载配置: {project_dir}")
    logger.info(f"使用数据目录: {PROJECT_DIRECTORY}")
    logger.info(f"日志保存在: {log_dir}")
    logger.info(f"索引方法: {INDEX_METHOD}")
    logger.info(f"增量更新: {'是' if IS_UPDATE else '否'}")
    logger.info(f"内存分析: {'是' if MEMORY_PROFILE else '否'}")
    
    # 如果指定了输出目录，记录日志
    if OUTPUT_DIR:
        logger.info(f"使用指定的输出目录: {OUTPUT_DIR}")
        config_overrides['output.base_dir'] = OUTPUT_DIR
    
    # 加载配置
    if CONFIG_FILE:
        config_path = Path(CONFIG_FILE)
        logger.info(f"使用指定配置文件: {config_path}")
        graphrag_config = load_config(Path(PROJECT_DIRECTORY), config_path, config_overrides)
    else:
        logger.info(f"使用默认配置文件")
        graphrag_config = load_config(Path(PROJECT_DIRECTORY), None, config_overrides)
    
    # 创建进度记录器
    progress_logger = RichProgressLogger(prefix="graphrag-index")
    
    logger.info("开始构建索引...")
    
    try:
        # 设置索引方法
        method = IndexingMethod.Standard
        if INDEX_METHOD.lower() == "fast":
            method = IndexingMethod.Fast
        
        # 调用build_index函数
        index_result: list[PipelineRunResult] = await api.build_index(
            config=graphrag_config,
            method=method,
            is_update_run=IS_UPDATE,
            memory_profile=MEMORY_PROFILE,
            progress_logger=progress_logger
        )
        
        # 处理和显示结果
        logger.info("索引构建完成，处理结果:")
        for workflow_result in index_result:
            status = f"错误\n{workflow_result.errors}" if workflow_result.errors else "成功"
            logger.info(f"工作流名称: {workflow_result.workflow}\t状态: {status}")
            
        return index_result
    
    except Exception as e:
        logger.error(f"索引过程中发生错误: {str(e)}", exc_info=True)
        raise

def main():
    """主函数入口点"""
    # 直接使用全局设置的项目路径和数据目录
    try:
        asyncio.run(run_indexing(PROJECT_DIR, DATA_DIR_NAME))
        log_path = os.path.join(PROJECT_DIR, DATA_DIR_NAME, "logs", "dev_graphrag_indexing.log")
        print(f"索引构建完成，日志保存在 {log_path}")
        
        # 如果是增量更新，显示额外消息
        if IS_UPDATE:
            if OUTPUT_DIR:
                print(f"增量更新已完成，输出目录: {OUTPUT_DIR}")
            else:
                default_output = os.path.join(PROJECT_DIR, DATA_DIR_NAME, "text_output")
                print(f"增量更新已完成，使用默认输出目录: {default_output}")
    except Exception as e:
        print(f"运行错误: {str(e)}")
        exit(1)
    
if __name__ == "__main__":
    main()