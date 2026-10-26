"""Pydantic models for the agent system."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# --- Chat ---


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', 'system', or 'tool'")
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    provider: Optional[str] = None  # Use BYOK key for this provider
    temperature: float = 0.7
    max_tokens: int = 2048
    tools_enabled: Optional[List[str]] = None  # Tool names to enable
    skill_ids: Optional[List[str]] = None  # Skills to load
    stream: bool = False
    system_prompt: Optional[str] = None


class ToolCallResult(BaseModel):
    tool_call_id: str
    name: str
    arguments: Dict[str, Any]
    result: str


class ChatResponse(BaseModel):
    message: ChatMessage
    tool_calls_made: List[ToolCallResult] = []
    usage: Optional[Dict[str, int]] = None
    model: Optional[str] = None
    provider: Optional[str] = None


# --- Batch ---


class BatchPrompt(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    max_tokens: int = 1024
    temperature: float = 0.7


class BatchRequest(BaseModel):
    prompts: List[BatchPrompt] = Field(..., max_length=50)
    model: Optional[str] = None
    provider: Optional[str] = None


class BatchResponse(BaseModel):
    batch_id: str
    status: str
    total_prompts: int
    completed_prompts: int = 0
    results: Optional[List[Dict[str, Any]]] = None


# --- BYOK ---


class AddAPIKeyRequest(BaseModel):
    provider: str = Field(..., description="Provider name: openai, anthropic, google, etc.")
    api_key: str = Field(..., min_length=8)


class APIKeyResponse(BaseModel):
    id: str
    provider: str
    key_prefix: str
    is_active: bool
    created_at: Optional[str] = None
    last_used_at: Optional[str] = None


# --- Skills ---


class SkillCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = Field(None, max_length=1024)
    category: Optional[str] = None
    content: str = Field(..., min_length=1)
    is_public: bool = False
    metadata: Optional[Dict[str, Any]] = None


class SkillUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = Field(None, max_length=1024)
    category: Optional[str] = None
    content: Optional[str] = None
    is_public: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class SkillResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None  # Omitted in list view
    version: str = "1.0.0"
    author: Optional[str] = None
    is_public: bool = False
    is_bundled: bool = False
    usage_count: int = 0


# --- Cron ---


class CronJobCreate(BaseModel):
    name: str
    prompt: str
    schedule: str  # Cron expression like '0 9 * * *' or interval like 'every 30m'
    skill_ids: Optional[List[str]] = None
    tool_ids: Optional[List[str]] = None
    max_iterations: int = 10


class CronJobUpdate(BaseModel):
    name: Optional[str] = None
    prompt: Optional[str] = None
    schedule: Optional[str] = None
    is_active: Optional[bool] = None
    max_iterations: Optional[int] = None


class CronJobResponse(BaseModel):
    id: str
    name: str
    prompt: str
    schedule: str
    schedule_type: str
    is_active: bool
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    run_count: int = 0
    last_output: Optional[str] = None


# --- Delegate ---


class DelegateRequest(BaseModel):
    goal: str
    context: Optional[str] = None
    tools_enabled: Optional[List[str]] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    max_iterations: int = Field(default=10, le=30)


class DelegateResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None
    tool_calls_made: List[ToolCallResult] = []
    iterations_used: int = 0
