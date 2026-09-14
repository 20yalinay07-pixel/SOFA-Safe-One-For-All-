"""Media Generation & Processing Module - Veri Modelleri (Pydantic Schemas)"""
from pydantic import BaseModel


class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    # 1024x1024 varsayılan: birçok gateway/sağlayıcı (ör. OmniRoute + Stability AI)
    # yalnızca belirli boyutları destekliyor (1024x1024 / 1024x1280 / 1280x1024).
    width: int = 1024
    height: int = 1024


class ImageGenerateResponse(BaseModel):
    status: str
    message: str
    image_base64: str | None = None


class WatermarkRemoveResponse(BaseModel):
    status: str
    message: str
    image_base64: str | None = None
