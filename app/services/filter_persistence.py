"""
Filtre kalıcılığı - FilterGroup'u JSON olarak kaydeder ve yükler.
"""

from pathlib import Path
import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.models.filter_model import FilterGroup


class FilterPersistence:
    """
    JSON tabanlı filtre depolama sınıfı.
    FilterGroup composite yapısını kaydeder ve yükler.

    Varsayılan dosya: ~/.ik_filtresi/last_filters.json
    """

    def __init__(self, path: Optional[Path] = None):
        self._dir = Path.home() / ".ik_filtresi"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = Path(path) if path else self._dir / "last_filters.json"

    def save_filter_group(self, group: FilterGroup) -> None:
        """FilterGroup'u JSON dosyasına kaydet"""
        payload = {"version": 2, "format": "composite", "root": group.to_dict()}
        with self._path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    def load_filter_group(self) -> Optional[FilterGroup]:
        """JSON dosyasından FilterGroup yükle"""
        if not self._path.exists():
            return None

        try:
            with self._path.open("r", encoding="utf-8") as fp:
                payload = json.load(fp)
        except Exception:
            return None

        if payload.get("format") == "composite" and "root" in payload:
            return FilterGroup.from_dict(payload["root"])

        return None
