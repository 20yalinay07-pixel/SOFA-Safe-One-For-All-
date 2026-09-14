"""Media Generation & Processing Module - Veri Modelleri (Pydantic Schemas)"""
from pydantic import BaseModel


class ImageGenerateRequest(BaseModel):
    prompt: str
    negative_prompt: str | None = None
    width: int = 512
    height: int = 512


class ImageGenerateResponse(BaseModel):
    status: str
    message: str
    image_base64: str | None = None


class WatermarkRemoveResponse(BaseModel):
    status: str
    message: str
    image_base64: str | None = None
