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
    # Boş bırakılırsa "model" alanı hiç gönderilmez (gateway kendi
    # varsayılanını/otomatik seçimini kullanır). OmniRoute panelinizde
    # bağlı görsel sağlayıcısının (ör. Stability) tam model kimliğini
    # görüyorsanız buraya yazabilirsiniz.
    image_model: str = ""

    # --- Music Creator Modülü ---
    # 1. Öncelik: SunoAPI.org (gerçek müzik üretimi). Anahtar tanımlıysa
    #    kullanılır: https://sunoapi.org
    # 2. Yedek: aynı ağ geçitlerinin metinden-sese (TTS) ucu — gerçek müzik
    #    üretmez, yalnızca bir ses taslağı döner (SunoAPI hiç tanımlı değilse
    #    veya başarısız olursa devreye girer).
    sunoapi_api_key: str = ""
    music_provider_order: str = "omniroute,freellmapi"
    # ÖNEMLİ: eski varsayılanlar ("tts-1"/"alloy") OpenAI'ye özel model/ses
    # adlarıydı — OmniRoute bunları görünce isteği OpenAI sağlayıcısına
    # yönlendirmeye çalışıyor ve OpenAI anahtarınız yoksa reddediliyordu.
    # "auto", chat modülündeki gibi gateway'in bağlı bir sağlayıcıyı (ör.
    # Deepgram) otomatik seçmesini ister. Belirli bir sağlayıcıyı
    # hedeflemek isterseniz OmniRoute panelinizden gördüğünüz tam model
    # kimliğini buraya yazın. Ses (voice) alanı sağlayıcıya özel olduğu
    # için varsayılan olarak boş bırakılır (boşsa hiç gönderilmez).
    music_tts_model: str = "auto"
    music_tts_voice: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Ayarları uygulama boyunca tek sefer okuyup önbelleğe alır (singleton)."""
    return Settings()
