"""
SOFA - Merkezi Konfigürasyon Modülü
Tüm ayarlar burada tek bir yerden .env dosyasından okunur.
Hiçbir API anahtarı kod içine gömülmez (hardcode edilmez).
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Genel ---
    app_name: str = "SOFA - Safe One For All"
    sofa_host: str = "127.0.0.1"
    sofa_port: int = 8000
    sofa_no_log: bool = True  # Gizlilik: varsayılan olarak içerik loglanmaz

    # --- Chat Modülü ---
    # SOFA, ücretsiz LLM'lere tek tek anahtar aramak yerine yerel bir
    # OpenAI-uyumlu ağ geçidi (gateway) üzerinden erişir:
    #   - OmniRoute:  https://github.com/diegosouzapw/OmniRoute
    #   - FreeLLMAPI: https://github.com/tashfeenahmed/freellmapi
    chat_provider: str = "omniroute"  # "omniroute" | "freellmapi"
    chat_model: str = "auto"

    omniroute_base_url: str = "http://localhost:20128/v1"
    omniroute_api_key: str = ""

    freellmapi_base_url: str = "http://localhost:3001/v1"
    freellmapi_api_key: str = ""

    # --- Media Modülü ---
    media_provider: str = "omniroute"  # aynı gateway'in /v1/images/generations ucu kullanılır

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Ayarları uygulama boyunca tek sefer okuyup önbelleğe alır (singleton)."""
    return Settings()
