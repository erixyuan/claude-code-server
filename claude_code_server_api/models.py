"""
API request and response models.
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request."""

    message: str = Field(..., description="The message to send to Claude")
    user_id: str = Field(..., description="Unique user identifier")
    session_id: Optional[str] = Field(None, description="Optional custom session ID")
    response_mode: Optional[Literal["sync", "stream", "async"]] = Field(
        None, description="Override default response mode"
    )
    timeout: Optional[int] = Field(None, description="Override default timeout")

    # Message debouncing (for async mode)
    enable_debounce: Optional[bool] = Field(
        None, description="Enable message debouncing (default: use server config)"
    )
    debounce_window: Optional[float] = Field(
        None, description="Debounce window in seconds (default: use server config)"
    )


class ChatResponse(BaseModel):
    """Synchronous chat response."""

    content: str = Field(..., description="Claude's response")
    session_id: str = Field(..., description="Session ID for this conversation")
    claude_session_id: Optional[str] = Field(None, description="Claude's internal UUID")
    success: bool = True
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class AsyncChatResponse(BaseModel):
    """Async chat response (immediate)."""

    task_id: str = Field(..., description="Task ID for checking status")
    status: str = "processing"
    message: str = "Task submitted successfully"


class TaskStatus(BaseModel):
    """Task status response."""

    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    result: Optional[ChatResponse] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class ConversationHistory(BaseModel):
    """Conversation history response."""

    session_id: str
    user_id: str
    messages: list[dict]
    total_messages: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str
    claude_version: Optional[str] = None
