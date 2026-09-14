"""
Music Creator Module - Servis Katmanı

Öncelik sırası:
  1. SunoAPI.org (https://sunoapi.org) - gerçek müzik üretimi. `.env`'de
     SUNOAPI_API_KEY tanımlıysa kullanılır. Asenkron çalışır: bir görev
     (task) başlatılır, sonucu hazır olana kadar periyodik olarak sorgulanır.
  2. Yedek: MUSIC_PROVIDER_ORDER'daki ağ geçitlerinin metinden-sese (TTS,
     `/audio/speech`) ucu. Bu gerçek bir müzik üretmez, yalnızca bir konuşma
     sesi taslağı döner; SunoAPI tanımlı değilse veya başarısız olursa
     devreye girer.
"""
import asyncio
import base64

import httpx

from app.config import get_settings
from app.utils.gateway import error_body_snippet, get_gateway_config, is_gateway_usable, parse_provider_order
from app.utils.logger import get_logger, safe_log_event

logger = get_logger(__name__)

SUNOAPI_BASE_URL = "https://api.sunoapi.org"
SUNOAPI_POLL_INTERVAL_SECONDS = 5
SUNOAPI_MAX_POLL_ATTEMPTS = 36  # ~3 dakika (5s * 36)


class MusicServiceError(Exception):
    """Music servisiyle ilgili kullanıcıya gösterilebilir hatalar."""


async def _generate_with_sunoapi(prompt: str, api_key: str) -> bytes:
    """
    SunoAPI.org ile gerçek müzik üretir.
    Akış: POST /api/v1/generate -> taskId -> GET /api/v1/generate/record-info
    ile durum tamamlanana (SUCCESS) kadar periyodik sorgulama -> audioUrl'i indir.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"prompt": prompt, "customMode": False, "instrumental": False}

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{SUNOAPI_BASE_URL}/api/v1/generate", headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        data = body.get("data")
        if not isinstance(data, dict) or "taskId" not in data:
            # SunoAPI 200 dondurse bile "data": null ile basarisizlik
            # bildirebiliyor (ör. kredi/limit sorunu) - gercek mesaji gosterelim.
            raise MusicServiceError(f"SunoAPI.org görev başlatamadı: {body.get('msg') or body}")
        task_id = data["taskId"]

        for _ in range(SUNOAPI_MAX_POLL_ATTEMPTS):
            await asyncio.sleep(SUNOAPI_POLL_INTERVAL_SECONDS)

            status_response = await client.get(
                f"{SUNOAPI_BASE_URL}/api/v1/generate/record-info",
                headers=headers,
                params={"taskId": task_id},
            )
            status_response.raise_for_status()
            status_body = status_response.json()
            status_data = status_body.get("data")
            if not isinstance(status_data, dict):
                raise MusicServiceError(f"SunoAPI.org durum sorgusu başarısız: {status_body.get('msg') or status_body}")
            status = status_data.get("status")

            if status == "SUCCESS":
                tracks = status_data.get("response", {}).get("sunoData", [])
                if not tracks:
                    raise MusicServiceError("SunoAPI.org üretimi tamamlandı ama parça döndürmedi.")
                audio_url = tracks[0]["audioUrl"]
                audio_response = await client.get(audio_url)
                audio_response.raise_for_status()
                return audio_response.content

            if status not in ("GENERATING", "PENDING", None):
                raise MusicServiceError(f"SunoAPI.org üretimi başarısız oldu (durum: {status}).")

        raise MusicServiceError("SunoAPI.org zaman aşımına uğradı (3 dakikadan uzun sürdü).")


async def _generate_with_tts_fallback(prompt: str) -> bytes:
    """
    TASLAK: gerçek müzik üretimi değil, TTS tabanlı bir yer tutucudur.
    MUSIC_PROVIDER_ORDER'daki ağ geçitlerini sırayla dener.
    """
    settings = get_settings()
    order = parse_provider_order(settings.music_provider_order)

    errors: list[str] = []
    for provider in order:
        gateway = get_gateway_config(provider)
        if not is_gateway_usable(gateway):
            errors.append(f"{provider}: anahtar tanımlı değil, atlandı")
            continue

        headers = {"Content-Type": "application/json"}
        if gateway.api_key:
            headers["Authorization"] = f"Bearer {gateway.api_key}"

        payload = {"input": prompt}
        if settings.music_tts_model:
            payload["model"] = settings.music_tts_model
        if settings.music_tts_voice:
            payload["voice"] = settings.music_tts_voice
        url = f"{gateway.base_url.rstrip('/')}/audio/speech"

        try:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                safe_log_event(logger, "music_generate_success", {"provider": provider})
                return response.content
        except httpx.HTTPStatusError as exc:
            snippet = error_body_snippet(exc.response)
            errors.append(f"{provider}: HTTP {exc.response.status_code}" + (f" - {snippet}" if snippet else ""))
            safe_log_event(logger, "music_generate_http_error", {"provider": provider, "status": exc.response.status_code})
        except httpx.RequestError:
            errors.append(f"{provider}: ağa ulaşılamadı")
            safe_log_event(logger, "music_generate_network_error", {"provider": provider})

    raise MusicServiceError("Tüm ses üretim sağlayıcıları başarısız oldu: " + "; ".join(errors))


async def generate_music(prompt: str) -> tuple[bytes, str, str | None]:
    """
    SunoAPI.org ile gerçek müzik üretmeyi dener; olmazsa TTS taslağına düşer.
    Dönüş: (ses_baytları, kaynak, sunoapi_basarisiz_olduysa_nedeni)
    "kaynak": "sunoapi" (gerçek müzik) veya "tts" (yer tutucu, şarkı değil).
    """
    settings = get_settings()

    if settings.sunoapi_api_key:
        try:
            audio = await _generate_with_sunoapi(prompt, settings.sunoapi_api_key)
            safe_log_event(logger, "music_generate_success", {"provider": "sunoapi"})
            return audio, "sunoapi", None
        except httpx.HTTPStatusError as exc:
            snippet = error_body_snippet(exc.response)
            reason = f"HTTP {exc.response.status_code}" + (f" - {snippet}" if snippet else "")
            safe_log_event(logger, "music_generate_http_error", {"provider": "sunoapi", "status": exc.response.status_code})
        except httpx.RequestError:
            reason = "SunoAPI.org'a ağ üzerinden ulaşılamadı."
            safe_log_event(logger, "music_generate_network_error", {"provider": "sunoapi"})
        except MusicServiceError as exc:
            reason = str(exc)
            safe_log_event(logger, "music_generate_sunoapi_failed", {})
        except Exception as exc:
            # SunoAPI'nin yanıt şekli beklenmedik olsa bile TTS yedeğine
            # düşmeye devam edelim - tüm istek çökmesin.
            reason = f"beklenmeyen hata: {exc}"
            safe_log_event(logger, "music_generate_sunoapi_unexpected_error", {})
        # SunoAPI başarısız oldu; aşağıdaki TTS taslağına düşülüyor.
        audio = await _generate_with_tts_fallback(prompt)
        return audio, "tts", reason

    audio = await _generate_with_tts_fallback(prompt)
    return audio, "tts", None


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")
