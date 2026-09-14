"""Chat & Assistant Module - API Router"""
from fastapi import APIRouter, HTTPException

from app.modules.chat.schemas import ChatRequest, ChatResponse
from app.modules.chat.service import ChatServiceError, generate_reply

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    """Kullanıcı mesajlarını alır, seçili LLM ağ geçidinden yanıt üretir."""
    try:
        messages = [m.model_dump() for m in payload.messages]
        reply, provider, model = await generate_reply(
            messages=messages, model=payload.model, temperature=payload.temperature
        )
        return ChatResponse(reply=reply, provider=provider, model=model)
    except ChatServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # Beklenmeyen hatalar için son güvenlik ağı
        raise HTTPException(status_code=500, detail=f"Beklenmeyen bir hata oluştu: {exc}") from exc
