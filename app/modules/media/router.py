"""Media Generation & Processing Module - API Router"""
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.modules.media.schemas import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    WatermarkRemoveResponse,
)
from app.modules.media.service import (
    MediaServiceError,
    bytes_to_base64,
    generate_image,
    remove_watermark,
)

router = APIRouter(prefix="/api/media", tags=["media"])


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image_endpoint(payload: ImageGenerateRequest) -> ImageGenerateResponse:
    """Metinden görsel üretir (OmniRoute/FreeLLMAPI ağ geçidi üzerinden)."""
    try:
        image_bytes = await generate_image(
            prompt=payload.prompt,
            negative_prompt=payload.negative_prompt,
            width=payload.width,
            height=payload.height,
        )
        return ImageGenerateResponse(
            status="success",
            message="Görsel başarıyla üretildi.",
            image_base64=bytes_to_base64(image_bytes),
        )
    except MediaServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:  # Beklenmeyen hatalar için son güvenlik ağı
        raise HTTPException(status_code=500, detail=f"Beklenmeyen bir hata oluştu: {exc}") from exc


@router.post("/watermark/remove", response_model=WatermarkRemoveResponse)
async def remove_watermark_endpoint(file: UploadFile = File(...)) -> WatermarkRemoveResponse:
    """Yüklenen görselden filigranı temizlemeye çalışır (yerel taslak fonksiyon)."""
    try:
        raw = await file.read()
        if not raw:
            raise HTTPException(status_code=400, detail="Boş dosya yüklendi.")

        processed = remove_watermark(raw)
        return WatermarkRemoveResponse(
            status="success",
            message="Görsel işlendi (taslak mod). Gerçek model entegrasyonu için service.py'deki TODO'ya bakın.",
            image_base64=bytes_to_base64(processed),
        )
    except MediaServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # Beklenmeyen hatalar için son güvenlik ağı
        raise HTTPException(status_code=500, detail=f"Beklenmeyen bir hata oluştu: {exc}") from exc
