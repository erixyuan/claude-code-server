"""
日志模块 - 基于 Loguru

统一的日志管理，支持：
- 控制台彩色输出
- 按日期轮动的文件日志
- 灵活的配置（通过 config.yaml）

Simple is better than complex.
"""

import sys
from typing import Optional
from loguru import logger

# 全局标志：是否已初始化
_initialized = False


def setup_logging(log_config: Optional[dict] = None):
    """
    初始化日志系统
    
    Args:
        log_config: 日志配置字典，通常来自 ServerConfig.logging
                   如果为 None，使用默认配置
    
    Example:
        >>> from claude_code_server_api.config import load_config
        >>> config = load_config()
        >>> setup_logging(config.logging.dict())
    """
    global _initialized
    
    # 避免重复初始化
    if _initialized:
        logger.warning("日志系统已初始化，跳过重复配置")
        return
    
    # 默认配置
    if log_config is None:
        log_config = {
            "level": "INFO",
            "console_output": True,
            "file_output": False,
        }
    
    # 移除 Loguru 的默认 handler
    logger.remove()
    
    # 1. 控制台输出（彩色）
    if log_config.get("console_output", True):
        console_format = log_config.get(
            "console_format",
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        )
        logger.add(
            sys.stderr,
            level=log_config.get("level", "INFO"),
            format=console_format,
            colorize=True,
        )
    
    # 2. 文件输出（按日期轮动）
    if log_config.get("file_output", False):
        file_path = log_config.get("file_path", "logs/app_{time:YYYY-MM-DD}.log")
        file_format = log_config.get(
            "file_format",
            "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
            "{name}:{function}:{line} - {message}"
        )
        
        logger.add(
            file_path,
            rotation=log_config.get("rotation", "00:00"),      # 每天午夜轮动
            retention=log_config.get("retention", "7 days"),   # 保留7天
            compression=log_config.get("compression", "zip"),  # 压缩旧日志
            level=log_config.get("file_level", "INFO"),
            format=file_format,
            encoding="utf-8",
            enqueue=True,  # 异步写入，高性能
        )
    
    _initialized = True
    logger.info("✅ 日志系统初始化完成")
    logger.debug(f"日志配置: {log_config}")


# 导出 logger 实例
# 其他模块只需: from claude_code_server.logger import logger
__all__ = ["logger", "setup_logging"]

