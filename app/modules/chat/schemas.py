"""Chat & Assistant Module - Veri Modelleri (Pydantic Schemas)"""
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant' veya 'system'")
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
    model: str | None = None
    temperature: float = 0.7


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model: str
