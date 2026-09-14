"""Music Creator Module - API Router"""
from fastapi import APIRouter, HTTPException

from app.modules.music.schemas import MusicGenerateRequest, MusicGenerateResponse
from app.modules.music.service import MusicServiceError, bytes_to_base64, generate_music

router = APIRouter(prefix="/api/music", tags=["music"])


@router.post("/generate", response_model=MusicGenerateResponse)
async def generate_music_endpoint(payload: MusicGenerateRequest) -> MusicGenerateResponse:
    """Metinden ses/müzik taslağı üretir (TTS tabanlı yer tutucu)."""
    try:
        audio_bytes, source, sunoapi_failure_reason = await generate_music(payload.prompt)

        if source == "sunoapi":
            message = "Gerçek müzik üretildi (SunoAPI.org)."
        elif sunoapi_failure_reason:
            message = (
                "Bu bir şarkı DEĞİL — SunoAPI.org başarısız olduğu için "
                f"metinden-sese (TTS) taslağına düşüldü. Sebep: {sunoapi_failure_reason}"
            )
        else:
            message = (
                "Bu bir şarkı DEĞİL — SunoAPI.org anahtarı tanımlı değil, "
                "metinden-sese (TTS) taslağı üretildi. Gerçek müzik için "
                ".env'e SUNOAPI_API_KEY ekleyin."
            )

        return MusicGenerateResponse(
            status="success",
            message=message,
            audio_base64=bytes_to_base64(audio_bytes),
        )
    except MusicServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # Beklenmeyen hatalar için son güvenlik ağı
        raise HTTPException(status_code=500, detail=f"Beklenmeyen bir hata oluştu: {exc}") from exc
