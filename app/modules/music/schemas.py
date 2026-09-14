"""Music Creator Module - Veri Modelleri (Pydantic Schemas)"""
from pydantic import BaseModel


class MusicGenerateRequest(BaseModel):
    prompt: str


class MusicGenerateResponse(BaseModel):
    status: str
    message: str
    audio_base64: str | None = None
    audio_format: str = "mp3"
