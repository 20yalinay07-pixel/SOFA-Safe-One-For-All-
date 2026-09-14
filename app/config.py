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

    # --- Ağ Geçitleri (Gateways) ---
    # SOFA, ücretsiz LLM'lere tek tek anahtar aramak yerine yerel
    # OpenAI-uyumlu ağ geçitleri (gateway) üzerinden erişir:
    #   - OmniRoute:  https://github.com/diegosouzapw/OmniRoute
    #   - FreeLLMAPI: https://github.com/tashfeenahmed/freellmapi
    omniroute_base_url: str = "http://localhost:20128/v1"
    omniroute_api_key: str = ""

    freellmapi_base_url: str = "http://localhost:3001/v1"
    freellmapi_api_key: str = ""

    # --- Chat Modülü ---
    # Fallback zinciri: virgülle ayrılmış sağlayıcı sırası. İlk sağlayıcı
    # başarısız olursa (ağ hatası/HTTP hatası/eksik anahtar) otomatik
    # olarak bir sonrakine geçilir. Varsayılan: FreeLLMAPI (ör. Groq - hızlı
    # ve güvenilir) önce, OmniRoute yedek olarak sonra.
    chat_provider_order: str = "freellmapi,omniroute"
    chat_model: str = "auto"

    # --- Media (Image Creation) Modülü ---
    # Görsel üretimi için fallback zinciri. Varsayılan: OmniRoute önce
    # (ör. Stability AI orada bağlıysa), FreeLLMAPI yedek olarak sonra.
    media_provider_order: str = "omniroute,freellmapi"
    # ÖNEMLİ (OmniRoute kaynak koduyla doğrulandı): "model" alanı ZORUNLU
    # ve "provider/model" formatında olmalı - "auto" veya boş çalışmaz,
    # açıkça reddedilir. Ör. Stability AI bağlıysa:
    #   stability-ai/stable-image-core  (hızlı/ucuz)
    #   stability-ai/stable-image-ultra
    #   stability-ai/sd3.5-large
    # OmniRoute panelinizdeki "Resim" sekmesinden bağlı sağlayıcınızın tam
    # kimliğini görüp buraya yazın.
    image_model: str = ""

    # --- Music Creator Modülü ---
    # 1. Öncelik: SunoAPI.org (gerçek müzik üretimi). Anahtar tanımlıysa
    #    kullanılır: https://sunoapi.org
    # 2. Yedek: aynı ağ geçitlerinin metinden-sese (TTS) ucu — gerçek müzik
    #    üretmez, yalnızca bir ses taslağı döner (SunoAPI hiç tanımlı değilse
    #    veya başarısız olursa devreye girer).
    sunoapi_api_key: str = ""
    music_provider_order: str = "omniroute,freellmapi"
    # ÖNEMLİ (OmniRoute kaynak koduyla doğrulandı): "model" alanı burada da
    # ZORUNLU ve "provider/model" formatında olmalı - "auto" bile çalışmaz
    # ("No speech provider found..." hatası verir). Ör. Deepgram bağlıysa:
    #   deepgram/aura-asteria-en
    #   deepgram/aura-luna-en
    #   deepgram/aura-stella-en
    # Deepgram'da "model" zaten sesi de belirlediği için "voice" alanı
    # gerekmez (boşsa hiç gönderilmez).
    music_tts_model: str = ""
    music_tts_voice: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Ayarları uygulama boyunca tek sefer okuyup önbelleğe alır (singleton)."""
    return Settings()
