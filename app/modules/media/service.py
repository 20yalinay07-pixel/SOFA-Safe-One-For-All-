"""
Media Generation & Processing Module - Servis Katmanı

- Görsel üretimi: MEDIA_PROVIDER_ORDER'daki ağ geçitlerini sırayla dener
  (fallback zinciri), aynı OpenAI-uyumlu `/images/generations` ucu
  üzerinden. Varsayılan sıra: OmniRoute önce (ör. Stability AI orada
  bağlıysa), FreeLLMAPI yedek olarak sonra.

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
from app.utils.gateway import error_body_snippet, get_gateway_config, is_gateway_usable, parse_provider_order
from app.utils.logger import get_logger, safe_log_event

logger = get_logger(__name__)


class MediaServiceError(Exception):
    """Medya servisiyle ilgili kullanıcıya gösterilebilir hatalar."""


async def _generate_with_gateway(
    base_url: str, api_key: str, model: str, prompt: str, negative_prompt: str, width: int, height: int
) -> bytes:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "prompt": prompt,
        "size": f"{width}x{height}",
        "response_format": "b64_json",
    }
    if model:
        payload["model"] = model
    # "negative_prompt" OpenAI'nin resmi şemasında yok; bazı gateway'ler
    # bilinmeyen alanları görünce isteği reddedebiliyor, o yüzden yalnızca
    # kullanıcı gerçekten bir şey yazdıysa gönderilir.
    if negative_prompt:
        payload["negative_prompt"] = negative_prompt
    url = f"{base_url.rstrip('/')}/images/generations"

    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return base64.b64decode(data["data"][0]["b64_json"])


async def generate_image(prompt: str, negative_prompt: str | None, width: int, height: int) -> bytes:
    """
    MEDIA_PROVIDER_ORDER'daki ağ geçitlerini sırayla dener; biri başarısız
    olursa otomatik olarak bir sonrakine geçer.
    """
    settings = get_settings()
    order = parse_provider_order(settings.media_provider_order)

    errors: list[str] = []
    for provider in order:
        gateway = get_gateway_config(provider)
        if not is_gateway_usable(gateway):
            errors.append(f"{provider}: anahtar tanımlı değil, atlandı")
            continue

        try:
            image_bytes = await _generate_with_gateway(
                gateway.base_url, gateway.api_key, settings.image_model, prompt, negative_prompt, width, height
            )
            safe_log_event(logger, "image_generate_success", {"provider": provider})
            return image_bytes
        except httpx.HTTPStatusError as exc:
            snippet = error_body_snippet(exc.response)
            errors.append(f"{provider}: HTTP {exc.response.status_code}" + (f" - {snippet}" if snippet else ""))
            safe_log_event(logger, "image_generate_http_error", {"provider": provider, "status": exc.response.status_code})
        except httpx.RequestError:
            errors.append(f"{provider}: ağa ulaşılamadı")
            safe_log_event(logger, "image_generate_network_error", {"provider": provider})
        except (KeyError, IndexError):
            errors.append(f"{provider}: beklenmeyen görsel yanıt formatı")
            safe_log_event(logger, "image_generate_parse_error", {"provider": provider})

    raise MediaServiceError("Tüm görsel üretim sağlayıcıları başarısız oldu: " + "; ".join(errors))


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
