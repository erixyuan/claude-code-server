"""
Configuration management for Claude Code Server API.
"""

import os
from enum import Enum
from typing import Optional
from pathlib import Path
import yaml
from pydantic import BaseModel, Field

from claude_code_server.logger import logger


class ResponseMode(str, Enum):
    """Response mode for chat API."""

    SYNC = "sync"  # 同步返回完整响应
    STREAM = "stream"  # SSE 流式返回
    ASYNC = "async"  # 立即返回 task_id，后台处理


class SessionStoreType(str, Enum):
    """Session storage backend type."""

    MEMORY = "memory"  # InMemory storage
    FILE = "file"  # File-based storage (persistent)
    REDIS = "redis"  # Redis storage


class LoggingConfig(BaseModel):
    """日志配置 - 基于 Loguru"""

    level: str = "INFO"  # 日志级别
    console_output: bool = True  # 是否输出到控制台
    console_format: str = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    file_output: bool = True  # 是否输出到文件
    file_path: str = "logs/app_{time:YYYY-MM-DD}.log"  # 文件路径
    rotation: str = "00:00"  # 轮动策略
    retention: str = "7 days"  # 保留时长
    compression: Optional[str] = "zip"  # 压缩格式
    file_level: str = "INFO"  # 文件日志级别
    file_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


class ServerConfig(BaseModel):
    """Server configuration."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False

    # Claude Code settings
    claude_bin: str = "claude"  # Claude CLI 可执行文件路径
    working_directory: str = Field(
        default_factory=lambda: os.getcwd()
    )  # Claude CLI 工作目录
    disable_prompt_caching: bool = True
    default_timeout: int = 300
    debug_print_command: bool = True  # Print CLI command to stdout
    debug_print_full_prompt: bool = False  # Print full system prompt
    permission_mode: str = "bypassPermissions"

    # Message formatting
    message_formatter: Optional[str] = None  # Formatter name: simple, imessage, platform, detailed

    # API settings
    default_response_mode: ResponseMode = ResponseMode.SYNC
    enable_cors: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Session settings
    session_store_type: SessionStoreType = SessionStoreType.FILE  # 默认使用文件存储
    session_storage_dir: str = ".sessions"  # 文件存储目录
    redis_url: Optional[str] = "redis://localhost:6379"
    session_ttl: Optional[int] = None  # Session TTL in seconds (None = never expire)

    # Security (optional)
    api_key: Optional[str] = None  # If set, require X-API-Key header
    allowed_users: Optional[list[str]] = None  # If set, restrict user_ids

    # Task queue settings (for async mode)
    max_concurrent_tasks: int = 10
    task_timeout: int = 600

    # Logging settings
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        use_enum_values = True


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """
    Load configuration from YAML file or environment variables.

    Args:
        config_path: Path to YAML config file (optional)
                    If not provided, will look for config.yaml in current directory

    Returns:
        ServerConfig instance
    """
    # If no config path provided, try to find config.yaml automatically
    if not config_path:
        default_paths = [
            Path("config.yaml"),           # Current directory
            Path.cwd() / "config.yaml",    # Explicit current directory
        ]
        for path in default_paths:
            if path.exists():
                config_path = str(path)
                logger.info(f"📄 自动检测到配置文件: {config_path}")
                break

    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        return ServerConfig(**config_data)
    else:
        # Load from environment variables
        logger.warning("⚠️ 未找到 config.yaml，使用默认配置")
        logger.info("   提示：可以创建 config.yaml 或使用 --config 选项")
        return ServerConfig(
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "8000")),
            claude_bin=os.getenv("CLAUDE_BIN", "claude"),
            working_directory=os.getenv(
                "CLAUDE_WORKING_DIR", os.getcwd()
            ),
            api_key=os.getenv("API_KEY"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
        )
