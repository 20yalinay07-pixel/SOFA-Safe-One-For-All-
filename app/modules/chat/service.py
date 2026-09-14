"""
Chat & Assistant Module - Servis Katmanı

SOFA, ücretsiz LLM'lere tek tek sağlayıcı hesabı/anahtarı aramak yerine,
yerelde çalışan OpenAI-uyumlu bir "ağ geçidi" (gateway) üzerinden erişir:

  - OmniRoute  (https://github.com/diegosouzapw/OmniRoute)
    Kurulum: `npm install -g omniroute`
    Varsayılan uç: http://localhost:20128/v1  (zero-config, anahtar gerekmez)

  - FreeLLMAPI (https://github.com/tashfeenahmed/freellmapi)
    Kurulum: `curl -fsSL https://freellmapi.co/install.sh | bash`
    Varsayılan uç: http://localhost:3001/v1  (birleşik anahtar gerekir)

Her iki sağlayıcı da OpenAI'nin `/chat/completions` formatını kullandığı
için tek bir generic istemci yeterlidir; hangisinin kullanılacağı
.env dosyasındaki CHAT_PROVIDER ile seçilir.
"""
import httpx

from app.config import get_settings
from app.utils.logger import get_logger, safe_log_event

logger = get_logger(__name__)


class ChatServiceError(Exception):
    """Chat servisiyle ilgili kullanıcıya gösterilebilir (bilinen) hatalar için."""


def _resolve_provider_config(provider: str) -> tuple[str, str]:
    """Seçili sağlayıcı için (base_url, api_key) döndürür."""
    settings = get_settings()

    if provider == "freellmapi":
        if not settings.freellmapi_api_key:
            raise ChatServiceError(
                "FREELLMAPI_API_KEY .env dosyasında tanımlı değil. "
                "FreeLLMAPI kurulum sonrası panelden aldığınız birleşik anahtarı girin."
            )
        return settings.freellmapi_base_url, settings.freellmapi_api_key

    # Varsayılan / "omniroute": zero-config, anahtar zorunlu değil.
    return settings.omniroute_base_url, settings.omniroute_api_key


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
    Sohbet yanıtı üretir. Sağlayıcı .env'deki CHAT_PROVIDER'a göre seçilir.
    Dönüş: (yanit_metni, kullanilan_saglayici, kullanilan_model)
    """
    settings = get_settings()
    provider = settings.chat_provider.lower()
    chosen_model = model or settings.chat_model

    try:
        base_url, api_key = _resolve_provider_config(provider)
        reply = await _call_gateway(base_url, api_key, chosen_model, messages, temperature)
        safe_log_event(logger, "chat_reply_success", {"provider": provider})
        return reply, provider, chosen_model

    except ChatServiceError:
        raise
    except httpx.HTTPStatusError as exc:
        safe_log_event(logger, "chat_http_error", {"status": exc.response.status_code})
        raise ChatServiceError(
            f"{provider} ağ geçidi hata döndürdü (HTTP {exc.response.status_code}). "
            f"{provider.capitalize()} servisinin çalıştığından ve gerekiyorsa "
            "anahtarın doğru girildiğinden emin olun."
        ) from exc
    except httpx.RequestError as exc:
        safe_log_event(logger, "chat_network_error", {})
        raise ChatServiceError(
            f"{provider} servisine ulaşılamadı. Yerel ağ geçidinin çalıştığından emin olun "
            f"(OmniRoute: `omniroute`, FreeLLMAPI: kurulum betiğiyle başlatılan servis)."
        ) from exc
    except (KeyError, IndexError) as exc:
        safe_log_event(logger, "chat_parse_error", {})
        raise ChatServiceError("Sağlayıcıdan beklenmeyen bir yanıt formatı geldi.") from exc
