"""Versiyon bilgisi modülü"""
from pathlib import Path

# Varsayılan versiyon (geliştirme sırasında)
DEFAULT_VERSION = "dev"


def get_version() -> str:
    """
    Uygulama versiyonunu döndürür.
    
    Build sırasında oluşturulan version.txt dosyasından okur,
    dosya yoksa varsayılan versiyonu döndürür.
    """
    # PyInstaller ile paketlendiğinde veya normal çalıştırmada
    # version.txt dosyasının konumu
    possible_paths = [
        Path(__file__).parent.parent / "version.txt",  # Kaynak kodda: ik_filtresi/version.txt
        Path(__file__).parent / "version.txt",         # app/ içinde
    ]
    
    # PyInstaller _MEIPASS desteği
    import sys
    if hasattr(sys, '_MEIPASS'):
        possible_paths.insert(0, Path(sys._MEIPASS) / "version.txt")
    
    for version_path in possible_paths:
        if version_path.exists():
            try:
                return version_path.read_text(encoding="utf-8").strip()
            except Exception:
                pass
    
    return DEFAULT_VERSION


VERSION = get_version()
