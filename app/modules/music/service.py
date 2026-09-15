"""
Music Creator Module - Servis Katmanı

Öncelik sırası:
  1. SunoAPI.org (https://sunoapi.org) - gerçek müzik üretimi, SÖZLÜ (melodi +
     ritim + kafiyeli söz hepsi var, "instrumental" bilerek false gönderiliyor).
     Ayrı bir hesap/anahtar gerektirir (SUNOAPI_API_KEY). Asenkron çalışır: bir
     görev (task) başlatılır, sonucu hazır olana kadar biz periyodik sorgularız.
  2. OmniRoute'un kendi `/v1/music/generations` ucu (MUSIC_MODEL ayarlıysa) -
     KIE.AI (Suno) veya MiniMax gibi sağlayıcılara görevi kendi içinde
     gönderip bekler (polling) ve tek istekte hazır sesi döner. ÖNEMLİ
     SINIRLAMA (OmniRoute kaynak koduyla doğrulandı - bkz.
     open-sse/handlers/musicGeneration.ts): OmniRoute'un KIE entegrasyonu
     "instrumental: true"yi SABİT KODLUYOR, biz ne gönderirsek gönderelim
     değişmiyor - yani bu yoldan ASLA sözlü/kafiyeli şarkı çıkmaz, sadece
     enstrümantal (melodi+ritim var, söz yok). Bu OmniRoute'un kendi
     kısıtlaması, SOFA'nın kodundan bağımsız - bu yüzden SunoAPI.org önce
     denenir.
  3. Yedek: MUSIC_PROVIDER_ORDER'daki ağ geçitlerinin metinden-sese (TTS,
     `/audio/speech`) ucu. Bu gerçek bir müzik üretmez, yalnızca bir konuşma
     sesi taslağı döner; yukarıdakilerin ikisi de tanımlı değilse veya
     başarısız olursa devreye girer.
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

OMNIROUTE_MUSIC_TIMEOUT_SECONDS = 310  # OmniRoute'un kendi ic bekleme suresinden (300s) biraz fazla


class MusicServiceError(Exception):
    """Music servisiyle ilgili kullanıcıya gösterilebilir hatalar."""


async def _generate_with_omniroute_music(prompt: str) -> tuple[bytes, str]:
    """
    OmniRoute'un native `/v1/music/generations` ucuyla gerçek müzik üretir
    (ör. KIE.AI üzerinden Suno, ya da MiniMax). OmniRoute görev oluşturma +
    bekleme (polling) işini kendi içinde yapar; biz tek istekte hazır sonucu
    alırız (bu yüzden zaman aşımı geniş tutulur, istek uzun sürebilir).
    Dönüş: (ses_baytları, ses_formatı ör. "mp3"/"wav")
    """
    settings = get_settings()
    headers = {"Content-Type": "application/json"}
    if settings.omniroute_api_key:
        headers["Authorization"] = f"Bearer {settings.omniroute_api_key}"

    payload = {"model": settings.music_model, "prompt": prompt}
    url = f"{settings.omniroute_base_url.rstrip('/')}/music/generations"

    async with httpx.AsyncClient(timeout=OMNIROUTE_MUSIC_TIMEOUT_SECONDS) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        body = response.json()
        tracks = body.get("data")
        if not isinstance(tracks, list) or not tracks:
            raise MusicServiceError(f"OmniRoute müzik üretimi boş/geçersiz sonuç döndü: {body}")
        track = tracks[0]
        b64 = track.get("b64_json")
        if not b64:
            raise MusicServiceError(f"OmniRoute müzik üretimi ses verisi döndürmedi: {track}")
        return base64.b64decode(b64), track.get("format", "mp3")


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


def _describe_exception(exc: Exception) -> str:
    """Bir istisnayı kullanıcıya gösterilebilir kısa bir metne çevirir."""
    if isinstance(exc, httpx.HTTPStatusError):
        snippet = error_body_snippet(exc.response)
        return f"HTTP {exc.response.status_code}" + (f" - {snippet}" if snippet else "")
    if isinstance(exc, httpx.RequestError):
        return "ağa ulaşılamadı"
    return str(exc)


async def generate_music(prompt: str) -> tuple[bytes, str, str | None, str]:
    """
    Gerçek müzik üretmeyi dener (önce SunoAPI.org - sözlü/kafiyeli, sonra
    OmniRoute native - yalnızca enstrümantal); ikisi de tanımlı değilse veya
    başarısız olursa TTS taslağına düşer.
    Dönüş: (ses_baytları, kaynak, başarısız_denemelerin_nedeni, ses_formatı)
    "kaynak": "sunoapi" veya "omniroute-music" (gerçek müzik) ya da "tts" (yer tutucu, şarkı değil).
    """
    settings = get_settings()
    attempted_reasons: list[str] = []

    if settings.sunoapi_api_key:
        try:
            audio = await _generate_with_sunoapi(prompt, settings.sunoapi_api_key)
            safe_log_event(logger, "music_generate_success", {"provider": "sunoapi"})
            return audio, "sunoapi", None, "mp3"
        except Exception as exc:
            reason = _describe_exception(exc)
            attempted_reasons.append(f"SunoAPI.org: {reason}")
            safe_log_event(logger, "music_generate_sunoapi_failed", {})

    if settings.music_model:
        try:
            audio, audio_format = await _generate_with_omniroute_music(prompt)
            safe_log_event(logger, "music_generate_success", {"provider": "omniroute-music"})
            return audio, "omniroute-music", None, audio_format
        except Exception as exc:
            reason = _describe_exception(exc)
            attempted_reasons.append(f"OmniRoute müzik: {reason}")
            safe_log_event(logger, "music_generate_omniroute_music_failed", {})

    try:
        audio = await _generate_with_tts_fallback(prompt)
    except MusicServiceError as exc:
        # Ucuncu (son) katman da basarisiz oldu - kullaniciya sadece TTS'in
        # hatasini degil, gercek muzik katmanlarinin neden basarisiz
        # oldugunu da gosterelim, yoksa o bilgi kaybolur.
        if attempted_reasons:
            raise MusicServiceError("; ".join(attempted_reasons) + f"; TTS: {exc}") from exc
        raise

    combined_reason = "; ".join(attempted_reasons) if attempted_reasons else None
    return audio, "tts", combined_reason, "mp3"


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")
