#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GraphRAG日志工具模块
提供统一的日志配置函数，可在开发脚本中复用
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

def setup_logging(log_dir=None, log_file="graphrag.log", logger_name="graphrag", console_level=logging.INFO):
    """
    配置日志系统，支持同时输出到控制台和文件
    
    参数:
    log_dir (str, Path, optional): 日志目录路径。如不提供，则只输出到控制台
    log_file (str, optional): 日志文件名。默认为"graphrag.log"
    logger_name (str, optional): 日志记录器名称。默认为"graphrag"
    console_level (int, optional): 控制台日志级别。默认为INFO
    
    返回:
    logging.Logger: 配置好的日志记录器
    """
    # 获取或创建日志记录器
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器，避免重复
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建控制台处理器，并设置格式
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 如果提供了日志目录，添加文件日志处理器
    if log_dir:
        log_path = Path(log_dir)
        if not log_path.exists():
            log_path.mkdir(parents=True, exist_ok=True)
        
        # 使用UTF-8编码创建文件处理器来解决中文乱码问题
        file_handler = RotatingFileHandler(
            log_path / log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'  # 指定UTF-8编码
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger 