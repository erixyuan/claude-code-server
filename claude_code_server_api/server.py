"""
FastAPI server for Claude Code Server.
"""

import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from claude_code_server import (
    ClaudeAgent,
    ClaudeConfig,
    InMemorySessionStore,
    FileSessionStore,
    get_formatter,
)
from claude_code_server.logger import logger
from .config import ServerConfig, ResponseMode
from .models import (
    ChatRequest,
    ChatResponse,
    AsyncChatResponse,
    TaskStatus,
    ConversationHistory,
    HealthResponse,
)
from .tasks import TaskManager


# Global state
task_manager: Optional[TaskManager] = None
agent: Optional[ClaudeAgent] = None
config: Optional[ServerConfig] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global task_manager, agent, config

    # Startup
    logger.info("🚀 启动 Claude Code Server API")
    logger.info(f"   工作目录: {config.working_directory}")
    logger.info(f"   Claude 二进制: {config.claude_bin}")

    # Initialize task manager
    task_manager = TaskManager(max_workers=config.max_concurrent_tasks)

    # Start background task cleanup
    async def cleanup_tasks():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            await task_manager.cleanup_old_tasks()

    asyncio.create_task(cleanup_tasks())

    logger.success("✅ 服务器就绪")

    yield

    # Shutdown
    logger.info("👋 关闭服务器...")


def create_app(server_config: ServerConfig) -> FastAPI:
    """
    Create FastAPI application.

    Args:
        server_config: Server configuration

    Returns:
        FastAPI application instance
    """
    global agent, config
    config = server_config

    # Create Claude Agent
    claude_config = ClaudeConfig(
        output_format="json",
        timeout=server_config.default_timeout,
        working_directory=server_config.working_directory,
        disable_prompt_caching=server_config.disable_prompt_caching,
        debug_print_command=server_config.debug_print_command,
        debug_print_full_prompt=server_config.debug_print_full_prompt,
        permission_mode=server_config.permission_mode,
    )

    # Get message formatter if specified
    message_formatter = None
    if server_config.message_formatter:
        message_formatter = get_formatter(server_config.message_formatter)
        if message_formatter:
            logger.info(f"   消息格式化器: {server_config.message_formatter}")
        else:
            logger.warning(f"   ⚠️ 未知的格式化器: {server_config.message_formatter}")

    # Session store
    if server_config.session_store_type == "redis":
        try:
            import redis
            from claude_code_server import RedisSessionStore

            redis_client = redis.from_url(server_config.redis_url)
            session_store = RedisSessionStore(
                redis_client, ttl=server_config.session_ttl
            )
        except ImportError:
            raise RuntimeError(
                "Redis support requires: pip install claude-code-server[redis]"
            )
    elif server_config.session_store_type == "file":
        session_store = FileSessionStore(
            storage_dir=server_config.session_storage_dir
        )
    else:
        session_store = InMemorySessionStore()

    agent = ClaudeAgent(
        config=claude_config,
        session_store=session_store,
        message_formatter=message_formatter,
    )

    # Create FastAPI app
    app = FastAPI(
        title="Claude Code Server API",
        description="FastAPI wrapper for Claude Code CLI",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    if server_config.enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=server_config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Dependencies
    async def verify_api_key(x_api_key: Optional[str] = Header(None)):
        """Verify API key if configured."""
        if config.api_key and x_api_key != config.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")

    async def verify_user(request: ChatRequest):
        """Verify user is allowed if configured."""
        if config.allowed_users and request.user_id not in config.allowed_users:
            raise HTTPException(status_code=403, detail="User not allowed")
        return request

    # Routes
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        claude_version = None
        try:
            claude_version = agent.client.get_version()
        except:
            pass

        return HealthResponse(
            status="healthy",
            version="0.1.0",
            claude_version=claude_version,
        )

    @app.post(
        "/chat",
        response_model=ChatResponse,
        dependencies=[Depends(verify_api_key)],
    )
    async def chat(request: ChatRequest = Depends(verify_user)):
        """
        Send a message to Claude (sync mode).

        Returns complete response once ready.
        """
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: agent.chat(
                    request.message, request.user_id, request.session_id
                ),
            )

            return ChatResponse(
                content=response.content,
                session_id=request.session_id or f"user_{request.user_id}",
                claude_session_id=response.metadata.get("claude_session_id"),
                success=response.success,
                metadata=response.metadata,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post(
        "/chat/stream",
        dependencies=[Depends(verify_api_key)],
    )
    async def chat_stream(request: ChatRequest = Depends(verify_user)):
        """
        Send a message to Claude (stream mode).

        Returns SSE stream of response chunks.
        """

        async def event_generator():
            try:
                # Note: Claude CLI doesn't support true streaming yet
                # We'll simulate by sending the full response as one chunk
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: agent.chat(
                        request.message, request.user_id, request.session_id
                    ),
                )

                # Send as SSE events
                yield {
                    "event": "message",
                    "data": response.content,
                }

                # Send completion event
                yield {
                    "event": "done",
                    "data": {
                        "session_id": request.session_id or f"user_{request.user_id}",
                        "claude_session_id": response.metadata.get("claude_session_id"),
                    },
                }

            except Exception as e:
                yield {
                    "event": "error",
                    "data": {"error": str(e)},
                }

        return EventSourceResponse(event_generator())

    @app.post(
        "/chat/async",
        response_model=AsyncChatResponse,
        dependencies=[Depends(verify_api_key)],
    )
    async def chat_async(request: ChatRequest = Depends(verify_user)):
        """
        Send a message to Claude (async mode).

        Returns immediately with task_id for status checking.
        """
        try:
            task_id = task_manager.create_task(
                agent, request.message, request.user_id, request.session_id
            )

            return AsyncChatResponse(
                task_id=task_id,
                status="processing",
                message="Task submitted successfully",
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get(
        "/task/{task_id}",
        response_model=TaskStatus,
        dependencies=[Depends(verify_api_key)],
    )
    async def get_task_status(task_id: str):
        """Get status of an async task."""
        status = await task_manager.get_task_status(task_id)
        if not status:
            raise HTTPException(status_code=404, detail="Task not found")
        return status

    @app.get(
        "/session/{session_id}/history",
        response_model=ConversationHistory,
        dependencies=[Depends(verify_api_key)],
    )
    async def get_conversation_history(session_id: str):
        """Get conversation history for a session."""
        try:
            # Extract user_id from session_id (format: user_{user_id})
            user_id = session_id.replace("user_", "")

            history = agent.get_conversation_history(user_id, session_id)

            return ConversationHistory(
                session_id=session_id,
                user_id=user_id,
                messages=[
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                    }
                    for msg in history
                ],
                total_messages=len(history),
            )
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

    @app.delete(
        "/session/{session_id}",
        dependencies=[Depends(verify_api_key)],
    )
    async def clear_session(session_id: str):
        """Clear a conversation session."""
        try:
            user_id = session_id.replace("user_", "")
            agent.clear_session(user_id, session_id)
            return {"message": "Session cleared successfully"}
        except Exception as e:
            raise HTTPException(status_code=404, detail=str(e))

    return app
