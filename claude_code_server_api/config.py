"""
Configuration management for Claude Code Server API.
"""

import os
from enum import Enum
from typing import Optional
from pathlib import Path
import yaml
from pydantic import BaseModel, Field


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

    # API settings
    default_response_mode: ResponseMode = ResponseMode.SYNC
    enable_cors: bool = True
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    # Session settings
    session_store_type: SessionStoreType = SessionStoreType.FILE  # 默认使用文件存储
    session_storage_dir: str = ".sessions"  # 文件存储目录
    redis_url: Optional[str] = "redis://localhost:6379"
    session_ttl: int = 3600  # Session TTL in seconds

    # Security (optional)
    api_key: Optional[str] = None  # If set, require X-API-Key header
    allowed_users: Optional[list[str]] = None  # If set, restrict user_ids

    # Task queue settings (for async mode)
    max_concurrent_tasks: int = 10
    task_timeout: int = 600

    class Config:
        use_enum_values = True


def load_config(config_path: Optional[str] = None) -> ServerConfig:
    """
    Load configuration from YAML file or environment variables.

    Args:
        config_path: Path to YAML config file (optional)

    Returns:
        ServerConfig instance
    """
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        return ServerConfig(**config_data)
    else:
        # Load from environment variables
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
