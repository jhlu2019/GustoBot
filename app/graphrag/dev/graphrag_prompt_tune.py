#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GraphRAG提示词自动生成脚本
这个脚本演示如何使用Python代码直接调用GraphRAG的提示词自动生成功能，
生成适合特定领域和语言的提示词模板。
"""

import asyncio
import logging
import warnings
import os
from pathlib import Path
import sys
import json

# 抑制不相关的警告
warnings.filterwarnings("ignore", category=SyntaxWarning)

# 导入我们的日志工具
from utils import setup_logging

import graphrag.api.prompt_tune as prompt_tune
from graphrag.config.load_config import load_config
from graphrag.logger.rich_progress import RichProgressLogger
from graphrag.prompt_tune.types import DocSelectionType

# ========================================
# 用户配置参数 - 直接修改这里的变量
# ========================================

# GraphRAG项目根目录路径
PROJECT_DIR = "E:\\my_graphrag\\graphrag_2.1.0\\graphrag"

# 数据目录名称（相对于项目根目录）
DATA_DIR_NAME = "data"

# 文档块大小
CHUNK_SIZE = 500

# 文档块重叠大小
OVERLAP = 100

# 要加载的文档块数量限制
# 注意：如果文档较少，请设置较小的值
LIMIT = 5

# 文档选择方法: "random", "auto", "all", "top"
# 参考DocSelectionType枚举的有效值
SELECTION_METHOD = "random"

# 领域（为None则自动检测）
DOMAIN = None

# 语言（为None则自动检测）
LANGUAGE = None

# 提示词最大令牌数
MAX_TOKENS = 4000

# 是否自动发现实体类型
DISCOVER_ENTITY_TYPES = True

# 最小所需的示例数
MIN_EXAMPLES_REQUIRED = 2

# 嵌入子集最大数量（对auto选择方法有效）
N_SUBSET_MAX = 300

# 文档选择数量（对auto选择方法有效）
K = 15

# 输出目录
OUTPUT_DIR = "E:\\my_graphrag\\graphrag_2.1.0\\graphrag\\data\\pdf_prompt_turn_output"

# 全局日志记录器
logger = None

async def run_prompt_tune(
    project_dir: str, 
    data_dir_name: str,
    output_dir: str,
    chunk_size: int = 500,
    overlap: int = 100,
    limit: int = 15,
    selection_method: str = "random",
    domain: str = None,
    language: str = None,
    max_tokens: int = 4000,
    discover_entity_types: bool = True,
    min_examples_required: int = 2,
    n_subset_max: int = 300,
    k: int = 15
):
    """
    运行GraphRAG提示词自动生成过程

    参数:
    project_dir (str): GraphRAG项目根目录路径
    data_dir_name (str): 数据目录名称
    output_dir (str): 输出目录路径
    chunk_size (int): 文档块大小
    overlap (int): 文档块重叠大小
    limit (int): 要加载的文档块数量限制
    selection_method (str): 文档选择方法
    domain (str): 领域，为None则自动检测
    language (str): 语言，为None则自动检测
    max_tokens (int): 提示词最大令牌数
    discover_entity_types (bool): 是否自动发现实体类型
    min_examples_required (int): 最小所需的示例数
    n_subset_max (int): 嵌入子集最大数量
    k (int): 文档选择数量
    """
    # 构建完整项目路径
    PROJECT_DIRECTORY = os.path.join(project_dir, data_dir_name)
    
    # 设置日志目录为项目的logs目录
    log_dir = Path(PROJECT_DIRECTORY) / "logs"
    global logger
    logger = setup_logging(log_dir, log_file="graphrag_prompt_tune.log", logger_name="dev-graphrag-prompt-tune")
    
    # 创建输出目录
    output_path = Path(project_dir) / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"从目录加载配置: {project_dir}")
    logger.info(f"使用数据目录: {PROJECT_DIRECTORY}")
    logger.info(f"输出目录: {output_path}")
    logger.info(f"文档块大小: {chunk_size}")
    logger.info(f"文档块重叠大小: {overlap}")
    logger.info(f"文档块数量限制: {limit}")
    logger.info(f"文档选择方法: {selection_method}")
    if domain:
        logger.info(f"指定领域: {domain}")
    else:
        logger.info(f"领域: 自动检测")
    if language:
        logger.info(f"指定语言: {language}")
    else:
        logger.info(f"语言: 自动检测")
    
    # 加载配置
    graphrag_config = load_config(Path(PROJECT_DIRECTORY))
    
    # 创建进度记录器
    progress_logger = RichProgressLogger(prefix="graphrag-prompt-tune")
    
    # 转换文档选择方法
    # 根据DocSelectionType的有效值
    doc_selection = DocSelectionType.RANDOM
    if selection_method.lower() == "auto":
        doc_selection = DocSelectionType.AUTO
    elif selection_method.lower() == "all":
        doc_selection = DocSelectionType.ALL
    elif selection_method.lower() == "top":
        doc_selection = DocSelectionType.TOP
    
    logger.info("开始生成提示词...")
    
    try:
        # 检查输入文件夹内容
        input_dir = Path(PROJECT_DIRECTORY) / "input"
        input_files = list(input_dir.glob("**/*.csv"))
        logger.info(f"找到 {len(input_files)} 个输入文件")
        
        # 调用prompt_tune函数生成提示词
        extract_graph_prompt, entity_summarization_prompt, community_summarization_prompt = await prompt_tune.generate_indexing_prompts(
            config=graphrag_config,
            logger=progress_logger,
            root=PROJECT_DIRECTORY,
            chunk_size=chunk_size,
            overlap=overlap,
            limit=limit,
            selection_method=doc_selection,
            domain=domain,
            language=language,
            max_tokens=max_tokens,
            discover_entity_types=discover_entity_types,
            min_examples_required=min_examples_required,
            n_subset_max=n_subset_max,
            k=k
        )
        
        # 保存提示词到文件
        logger.info("保存生成的提示词到文件...")
        
        # 保存实体提取提示词
        extract_graph_path = output_path / "extract_graph.txt"
        with open(extract_graph_path, "w", encoding="utf-8") as f:
            f.write(extract_graph_prompt)
        logger.info(f"实体提取提示词已保存到: {extract_graph_path}")
        
        # 保存实体摘要提示词
        entity_summarization_path = output_path / "summarize_descriptions.txt"
        with open(entity_summarization_path, "w", encoding="utf-8") as f:
            f.write(entity_summarization_prompt)
        logger.info(f"实体摘要提示词已保存到: {entity_summarization_path}")
        
        # 保存社区摘要提示词
        community_summarization_path = output_path / "community_report_graph.txt"
        with open(community_summarization_path, "w", encoding="utf-8") as f:
            f.write(community_summarization_prompt)
        logger.info(f"社区摘要提示词已保存到: {community_summarization_path}")
        
        # 创建元数据文件
        metadata = {
            "domain": domain or "自动检测",
            "language": language or "自动检测",
            "chunk_size": chunk_size,
            "overlap": overlap,
            "limit": limit,
            "selection_method": selection_method,
            "generated_at": Path(log_dir / "graphrag_prompt_tune.log").stat().st_mtime,
            "files": [
                {"name": "extract_graph.txt", "description": "实体提取提示词"},
                {"name": "summarize_descriptions.txt", "description": "实体摘要提示词"},
                {"name": "community_report_graph.txt", "description": "社区摘要提示词"}
            ]
        }
        
        metadata_path = output_path / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"元数据已保存到: {metadata_path}")
        
        logger.info("提示词生成成功完成!")
        return extract_graph_prompt, entity_summarization_prompt, community_summarization_prompt
    
    except Exception as e:
        logger.error(f"提示词生成过程中发生错误: {str(e)}", exc_info=True)
        raise

def main():
    """主函数入口点"""
    # 直接使用全局设置的变量
    try:
        asyncio.run(run_prompt_tune(
            project_dir=PROJECT_DIR,
            data_dir_name=DATA_DIR_NAME,
            output_dir=OUTPUT_DIR,
            chunk_size=CHUNK_SIZE,
            overlap=OVERLAP,
            limit=LIMIT,
            selection_method=SELECTION_METHOD,
            domain=DOMAIN,
            language=LANGUAGE,
            max_tokens=MAX_TOKENS,
            discover_entity_types=DISCOVER_ENTITY_TYPES,
            min_examples_required=MIN_EXAMPLES_REQUIRED,
            n_subset_max=N_SUBSET_MAX,
            k=K
        ))
        print(f"\n提示词生成成功完成!")
        print(f"生成的提示词已保存到: {os.path.join(PROJECT_DIR, OUTPUT_DIR)}")
    except Exception as e:
        print(f"运行错误: {str(e)}")
        exit(1)
    
if __name__ == "__main__":
    main() 