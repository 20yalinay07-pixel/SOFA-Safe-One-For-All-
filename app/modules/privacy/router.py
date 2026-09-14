"""System & Privacy Helper Module - API Router"""
from fastapi import APIRouter, HTTPException

from app.modules.privacy.schemas import PrivacyStatus, WipeResponse
from app.modules.privacy.service import (
    PrivacyServiceError,
    get_privacy_status,
    wipe_temp_files,
)

router = APIRouter(prefix="/api/privacy", tags=["privacy"])


@router.get("/status", response_model=PrivacyStatus)
async def privacy_status_endpoint() -> PrivacyStatus:
    """Uygulamanın gizlilik durumunu (log modu vb.) döndürür."""
    try:
        return PrivacyStatus(**get_privacy_status())
    except PrivacyServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/wipe", response_model=WipeResponse)
async def wipe_endpoint() -> WipeResponse:
    """SOFA'ya ait tüm geçici dosyaları anında siler."""
    try:
        removed = wipe_temp_files()
        return WipeResponse(status="success", files_removed=removed)
    except PrivacyServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
