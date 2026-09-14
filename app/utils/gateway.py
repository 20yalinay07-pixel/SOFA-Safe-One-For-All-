"""
Ortak ağ geçidi (gateway) yardımcıları.

SOFA, ücretsiz LLM/medya sağlayıcılarını art arda dener (fallback zinciri):
sıradaki bir sağlayıcı başarısız olursa (ağ hatası, HTTP hatası, eksik
anahtar), otomatik olarak bir sonrakine geçer — kullanıcı hiçbir şey fark
etmez, yalnızca zincirdeki HERKES başarısız olursa hata görür.

Sıra, ilgili modülün `.env`'deki *_PROVIDER_ORDER değişkeniyle belirlenir
(virgülle ayrılmış, örn. "freellmapi,omniroute").
"""
from dataclasses import dataclass

from app.config import get_settings

_KNOWN_PROVIDERS = {"omniroute", "freellmapi"}


@dataclass
class GatewayConfig:
    name: str
    base_url: str
    api_key: str


def parse_provider_order(order_str: str) -> list[str]:
    """'freellmapi, omniroute' -> ['freellmapi', 'omniroute']; bilinmeyen adları atlar."""
    providers = [p.strip().lower() for p in order_str.split(",") if p.strip()]
    known = [p for p in providers if p in _KNOWN_PROVIDERS]
    return known or ["omniroute"]


def get_gateway_config(provider: str) -> GatewayConfig:
    settings = get_settings()
    if provider == "freellmapi":
        return GatewayConfig("freellmapi", settings.freellmapi_base_url, settings.freellmapi_api_key)
    return GatewayConfig("omniroute", settings.omniroute_base_url, settings.omniroute_api_key)


def is_gateway_usable(gateway: GatewayConfig) -> bool:
    """FreeLLMAPI anahtarsız kullanılamaz; OmniRoute zero-config olduğu için anahtarsız da denenebilir."""
    if gateway.name == "freellmapi" and not gateway.api_key:
        return False
    return True


def error_body_snippet(response, limit: int = 200) -> str:
    """
    Bir HTTP hata yanıtının gövdesinden kısa, okunabilir bir özet çıkarır
    (ör. "omniroute: HTTP 400" yerine "omniroute: HTTP 400 - {"error":
    "invalid model"}"). Gövde okunamazsa veya boşsa sessizce boş döner.
    """
    try:
        text = response.text.strip()
    except Exception:
        return ""
    if not text:
        return ""
    return text[:limit] + ("…" if len(text) > limit else "")
