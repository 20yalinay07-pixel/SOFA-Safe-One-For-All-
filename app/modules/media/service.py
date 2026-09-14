"""
Media Generation & Processing Module - Servis Katmanı

- Görsel üretimi: Chat modülüyle aynı OpenAI-uyumlu yerel ağ geçidi
  (OmniRoute / FreeLLMAPI) üzerindeki `/images/generations` ucu kullanılır.
  Böylece ayrı bir görsel-üretim API anahtarı aramaya gerek kalmaz.

- Filigran temizleme: Tamamen yerelde çalışan PIL tabanlı bir TASLAK
  (template) fonksiyondur. Gerçek bir inpainting modeli (ör. LaMa,
  OpenCV Telea/NS) entegre etmek için `remove_watermark()` içindeki
  TODO kısmını doldurun. Görsel hiçbir zaman kullanıcı izni olmadan
  üçüncü bir sunucuya gönderilmez.
"""
import base64
import io

import httpx
from PIL import Image, ImageFilter

from app.config import get_settings
from app.utils.logger import get_logger, safe_log_event

logger = get_logger(__name__)


class MediaServiceError(Exception):
    """Medya servisiyle ilgili kullanıcıya gösterilebilir hatalar."""


def _resolve_media_gateway() -> tuple[str, str]:
    """Seçili sağlayıcı için (base_url, api_key) döndürür."""
    settings = get_settings()

    if settings.media_provider == "freellmapi":
        if not settings.freellmapi_api_key:
            raise MediaServiceError(
                "FREELLMAPI_API_KEY .env dosyasında tanımlı değil. "
                "Görsel üretimi için FreeLLMAPI'nin birleşik anahtarını girin."
            )
        return settings.freellmapi_base_url, settings.freellmapi_api_key

    return settings.omniroute_base_url, settings.omniroute_api_key


async def generate_image(prompt: str, negative_prompt: str | None, width: int, height: int) -> bytes:
    """
    Yerel OpenAI-uyumlu ağ geçidi üzerinden (OmniRoute/FreeLLMAPI)
    metinden görsel üretir ve ham PNG baytlarını döndürür.
    """
    base_url, api_key = _resolve_media_gateway()
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt or "",
        "size": f"{width}x{height}",
        "response_format": "b64_json",
    }
    url = f"{base_url.rstrip('/')}/images/generations"

    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            b64_image = data["data"][0]["b64_json"]
            safe_log_event(logger, "image_generate_success", {})
            return base64.b64decode(b64_image)
    except httpx.HTTPStatusError as exc:
        safe_log_event(logger, "image_generate_http_error", {"status": exc.response.status_code})
        raise MediaServiceError(
            f"Görsel üretim ağ geçidi hata döndürdü (HTTP {exc.response.status_code})."
        ) from exc
    except httpx.RequestError as exc:
        safe_log_event(logger, "image_generate_network_error", {})
        raise MediaServiceError(
            "Görsel üretim servisine ulaşılamadı. Yerel ağ geçidinin (OmniRoute/FreeLLMAPI) "
            "çalıştığından emin olun."
        ) from exc
    except (KeyError, IndexError) as exc:
        safe_log_event(logger, "image_generate_parse_error", {})
        raise MediaServiceError("Sağlayıcıdan beklenmeyen bir görsel yanıt formatı geldi.") from exc


def remove_watermark(image_bytes: bytes) -> bytes:
    """
    TASLAK (template) filigran temizleme fonksiyonu.

    Şu an basit bir yumuşatma/blur tabanlı yer tutucu (placeholder) mantık
    içerir; gerçek üretim kullanımı için burada bir inpainting modeli
    entegre edilmelidir.

    Beklenen gerçek akış:
      1. Kullanıcıdan filigranın konumunu (maske) al.
      2. cv2.inpaint(...) veya yerel bir diffusion-inpainting modeli çalıştır.
      3. Sonucu PNG olarak döndür.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # TODO: Gerçek filigran temizleme mantığını buraya entegre edin.
        processed = image.filter(ImageFilter.SMOOTH_MORE)

        buffer = io.BytesIO()
        processed.save(buffer, format="PNG")
        safe_log_event(logger, "watermark_remove_success", {})
        return buffer.getvalue()
    except Exception as exc:
        raise MediaServiceError(
            "Görsel işlenirken hata oluştu. Dosyanın geçerli bir görsel olduğundan emin olun."
        ) from exc


def bytes_to_base64(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")
