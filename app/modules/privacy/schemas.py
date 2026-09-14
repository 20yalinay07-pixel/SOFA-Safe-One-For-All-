"""System & Privacy Helper Module - Veri Modelleri (Pydantic Schemas)"""
from pydantic import BaseModel


class PrivacyStatus(BaseModel):
    no_log_mode: bool
    temp_files_cleared: int
    message: str


class WipeResponse(BaseModel):
    status: str
    files_removed: int
