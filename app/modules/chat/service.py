"""
Chat & Assistant Module - Servis Katmanı

SOFA, sohbet isteklerini birden fazla ücretsiz ağ geçidi arasında sırayla
dener (fallback zinciri): CHAT_PROVIDER_ORDER'daki ilk sağlayıcı başarısız
olursa (ağ hatası, HTTP hatası veya eksik anahtar), otomatik olarak bir
sonrakine geçer. Kullanıcı hiçbir şey fark etmez; yalnızca zincirdeki
HERKES başarısız olursa hata görür.

Varsayılan sıra: FreeLLMAPI (ör. Groq - hızlı/güvenilir) önce, OmniRoute
yedek olarak sonra; `.env`'deki CHAT_PROVIDER_ORDER ile değiştirilebilir.
"""
import httpx

from app.config import get_settings
from app.utils.gateway import error_body_snippet, get_gateway_config, is_gateway_usable, parse_provider_order
from app.utils.logger import get_logger, safe_log_event

logger = get_logger(__name__)


class ChatServiceError(Exception):
    """Chat servisiyle ilgili kullanıcıya gösterilebilir (bilinen) hatalar için."""


async def _call_gateway(base_url: str, api_key: str, model: str, messages: list[dict], temperature: float) -> str:
    """OpenAI-uyumlu /chat/completions ucuna istek atar (OmniRoute veya FreeLLMAPI)."""
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {"model": model, "messages": messages, "temperature": temperature}
    url = f"{base_url.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def generate_reply(
    messages: list[dict], model: str | None = None, temperature: float = 0.7
) -> tuple[str, str, str]:
    """
    Sohbet yanıtı üretir; CHAT_PROVIDER_ORDER'daki sağlayıcıları sırayla dener.
    Dönüş: (yanit_metni, kullanilan_saglayici, kullanilan_model)
    """
    settings = get_settings()
    chosen_model = model or settings.chat_model
    order = parse_provider_order(settings.chat_provider_order)

    errors: list[str] = []
    for provider in order:
        gateway = get_gateway_config(provider)
        if not is_gateway_usable(gateway):
            errors.append(f"{provider}: anahtar tanımlı değil, atlandı")
            continue

        try:
            reply = await _call_gateway(gateway.base_url, gateway.api_key, chosen_model, messages, temperature)
            safe_log_event(logger, "chat_reply_success", {"provider": provider})
            return reply, provider, chosen_model
        except httpx.HTTPStatusError as exc:
            snippet = error_body_snippet(exc.response)
            errors.append(f"{provider}: HTTP {exc.response.status_code}" + (f" - {snippet}" if snippet else ""))
            safe_log_event(logger, "chat_http_error", {"provider": provider, "status": exc.response.status_code})
        except httpx.RequestError:
            errors.append(f"{provider}: ağa ulaşılamadı")
            safe_log_event(logger, "chat_network_error", {"provider": provider})
        except (KeyError, IndexError):
            errors.append(f"{provider}: beklenmeyen yanıt formatı")
            safe_log_event(logger, "chat_parse_error", {"provider": provider})

    raise ChatServiceError("Tüm sohbet sağlayıcıları başarısız oldu: " + "; ".join(errors))
