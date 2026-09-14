"""Music Creator Module - API Router"""
from fastapi import APIRouter, HTTPException

from app.modules.music.schemas import MusicGenerateRequest, MusicGenerateResponse
from app.modules.music.service import MusicServiceError, bytes_to_base64, generate_music

router = APIRouter(prefix="/api/music", tags=["music"])


@router.post("/generate", response_model=MusicGenerateResponse)
async def generate_music_endpoint(payload: MusicGenerateRequest) -> MusicGenerateResponse:
    """Metinden ses/müzik taslağı üretir (TTS tabanlı yer tutucu)."""
    try:
        audio_bytes = await generate_music(payload.prompt)
        return MusicGenerateResponse(
            status="success",
            message=(
                "Ses üretildi (taslak mod, TTS tabanlı). Gerçek müzik modeli "
                "entegrasyonu için service.py'deki TODO'ya bakın."
            ),
            audio_base64=bytes_to_base64(audio_bytes),
        )
    except MusicServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # Beklenmeyen hatalar için son güvenlik ağı
        raise HTTPException(status_code=500, detail=f"Beklenmeyen bir hata oluştu: {exc}") from exc
