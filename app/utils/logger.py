"""
Gizlilik-öncelikli logger.
- SOFA_NO_LOG=true iken hiçbir mesaj içeriği/istek gövdesi diske veya
  konsola yazılmaz; sadece kritik hatalar (içeriksiz) görünür.
- API anahtarları ve diğer hassas alanlar hiçbir zaman loglanmaz.
"""
import logging
import sys

from app.config import get_settings

_SENSITIVE_KEYS = {"api_key", "authorization", "token", "password", "key", "secret"}


def _redact(data: dict) -> dict:
    """Sözlük içindeki hassas alanları maskeler."""
    redacted = {}
    for k, v in data.items():
        if any(s in k.lower() for s in _SENSITIVE_KEYS):
            redacted[k] = "***REDACTED***"
        else:
            redacted[k] = v
    return redacted


def get_logger(name: str) -> logging.Logger:
    """Modül bazlı, gizlilik ayarlarına duyarlı bir logger döndürür."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    settings = get_settings()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[SOFA] %(levelname)s - %(name)s - %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

    # No-log modunda yalnızca kritik/hatalı olaylar (içeriksiz) konsola düşer.
    logger.setLevel(logging.WARNING if settings.sofa_no_log else logging.INFO)

    return logger


def safe_log_event(logger: logging.Logger, event: str, meta: dict | None = None) -> None:
    """İçerik barındırmayan, yalnızca olay adı + maskelenmiş meta ile log basar."""
    settings = get_settings()
    if settings.sofa_no_log:
        return
    logger.info("%s | %s", event, _redact(meta or {}))
