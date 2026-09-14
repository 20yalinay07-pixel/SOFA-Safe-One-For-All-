"""
Music Creator Module - Servis Katmanı (TASLAK)

Ücretsiz yerel ağ geçitleri (OmniRoute/FreeLLMAPI) genellikle tam bir
müzik üretim modeli (ör. Suno, Udio tarzı) sunmaz. Bu yüzden bu modül,
aynı gateway'in metinden-sese (TTS, `/audio/speech`) ucunu bir
taslak/yer tutucu olarak kullanır; gerçek bir melodi/müzik üretmez,
yalnızca konuşma sesi döndürür.

Gerçek müzik üretimi için:
  TODO: Özel bir müzik üretim API'si veya yerelde çalışan bir
  MusicGen/AudioCraft modeli entegre edin. Fonksiyon imzasını
  (prompt -> ses baytları) koruduğunuz sürece yalnızca bu dosyadaki
  gateway çağrısını değiştirmeniz yeterlidir.
"""
import base64

import httpx

from app.config import get_settings
from app.utils.logger import get_logger, safe_log_event

logger = get_logger(__name__)


class MusicServiceError(Exception):
    """Music servisiyle ilgili kullanıcıya gösterilebilir hatalar."""


def _resolve_gateway() -> tuple[str, str]:
    settings = get_settings()
    if settings.chat_provider == "freellmapi":
        if not settings.freellmapi_api_key:
            raise MusicServiceError(
                "FREELLMAPI_API_KEY .env dosyasında tanımlı değil. "
                "Müzik/ses üretimi için FreeLLMAPI'nin birleşik anahtarını girin."
            )
        return settings.freellmapi_base_url, settings.freellmapi_api_key
    return settings.omniroute_base_url, settings.omniroute_api_key


async def generate_music(prompt: str) -> bytes:
    """
    TASLAK: metinden ses üretir (gerçek müzik üretimi değil, TTS tabanlı
    bir yer tutucudur). Ağ geçidinin `/audio/speech` ucunu kullanır.
    """
    base_url, api_key = _resolve_gateway()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {"model": "tts-1", "input": prompt, "voice": "alloy"}
    url = f"{base_url.rstrip('/')}/audio/speech"

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            safe_log_event(logger, "music_generate_success", {})
            return response.content
    except httpx.HTTPStatusError as exc:
        safe_log_event(logger, "music_generate_http_error", {"status": exc.response.status_code})
        raise MusicServiceError(
            f"Müzik/ses üretim ağ geçidi hata döndürdü (HTTP {exc.response.status_code})."
        ) from exc
    except httpx.RequestError as exc:
        safe_log_event(logger, "music_generate_network_error", {})
        raise MusicServiceError(
            "Müzik/ses üretim servisine ulaşılamadı. Yerel ağ geçidinin çalıştığından emin olun."
        ) from exc


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")
