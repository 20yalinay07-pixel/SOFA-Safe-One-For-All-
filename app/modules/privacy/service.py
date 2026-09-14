"""
System & Privacy Helper Module - Servis Katmanı
Kullanıcının yerelde güvenle çalışmasını sağlayan, log tutmayan
yardımcı fonksiyonlar burada toplanır.
"""
import shutil
import tempfile
from pathlib import Path

from app.config import get_settings
from app.utils.logger import get_logger, safe_log_event

logger = get_logger(__name__)

# SOFA'nın kendi geçici dosyaları için ayrılmış, izole klasör.
SOFA_TEMP_DIR = Path(tempfile.gettempdir()) / "sofa_temp"


class PrivacyServiceError(Exception):
    """Gizlilik servisiyle ilgili kullanıcıya gösterilebilir hatalar."""


def ensure_temp_dir() -> Path:
    """SOFA'nın izole geçici klasörünü oluşturur (yoksa)."""
    try:
        SOFA_TEMP_DIR.mkdir(parents=True, exist_ok=True)
        return SOFA_TEMP_DIR
    except OSError as exc:
        raise PrivacyServiceError("Geçici klasör oluşturulamadı.") from exc


def wipe_temp_files() -> int:
    """
    SOFA'ya ait geçici dosyaları güvenle siler.
    Silinen öğe sayısını döndürür; sistemin geri kalanına dokunmaz.
    """
    if not SOFA_TEMP_DIR.exists():
        return 0

    removed = 0
    try:
        for item in SOFA_TEMP_DIR.iterdir():
            try:
                if item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
                removed += 1
            except OSError:
                # Tek bir öğe silinemese bile diğerlerine devam et.
                continue
        safe_log_event(logger, "temp_wipe_success", {"removed": removed})
        return removed
    except Exception as exc:
        raise PrivacyServiceError("Geçici dosyalar temizlenirken hata oluştu.") from exc


def get_privacy_status() -> dict:
    """Uygulamanın anlık gizlilik durumunu döndürür (log modu, geçici dosya sayısı)."""
    settings = get_settings()
    temp_count = sum(1 for _ in SOFA_TEMP_DIR.iterdir()) if SOFA_TEMP_DIR.exists() else 0

    return {
        "no_log_mode": settings.sofa_no_log,
        "temp_files_cleared": temp_count,
        "message": (
            "Log tutmama modu aktif: hiçbir sohbet/medya içeriği diske yazılmıyor."
            if settings.sofa_no_log
            else "Log tutmama modu kapalı: yalnızca içerik barındırmayan olay adları loglanıyor."
        ),
    }
