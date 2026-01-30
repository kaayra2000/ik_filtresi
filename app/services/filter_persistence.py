"""
Filtre kalıcılığı - Son uygulanan filtreleri JSON olarak kaydeder ve yükler.
"""
from pathlib import Path
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.filter_model import FilterModel, FilterOperator
from app.models.column_info import ColumnInfo, ColumnType


class _JSONEncoder(json.JSONEncoder):
    def default(self, o: Any):
        if isinstance(o, datetime):
            return {"__datetime__": True, "iso": o.isoformat()}
        if isinstance(o, FilterOperator):
            return {"__filter_op__": True, "name": o.name}
        return super().default(o)


def _json_object_hook(d: Dict):
    if "__datetime__" in d:
        return datetime.fromisoformat(d["iso"])
    if "__filter_op__" in d:
        return FilterOperator[d["name"]]
    return d


class FilterPersistence:
    """Basit bir JSON tabanlı depolama sınıfı.

    Varsayılan dosya: ~/.ik_filtresi/last_filters.json
   """

    def __init__(self, path: Optional[Path] = None):
        self._dir = Path.home() / ".ik_filtresi"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = Path(path) if path else self._dir / "last_filters.json"

    def save_filters(self, filters: List[FilterModel]) -> None:
        data = []
        for f in filters:
            item = {
                "column_name": f.column_name,
                "operator": f.operator.name,
                "value": self._serialize_value(f.value),
                "value2": self._serialize_value(f.value2),
            }
            data.append(item)
        payload = {"version": 1, "filters": data}
        with self._path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    def load_filters(self) -> Optional[List[FilterModel]]:
        if not self._path.exists():
            return None
        try:
            with self._path.open("r", encoding="utf-8") as fp:
                payload = json.load(fp)
        except Exception:
            return None
        items = payload.get("filters", [])
        filters = []
        for it in items:
            op = FilterOperator[it["operator"]]
            value = self._deserialize_value(it.get("value"))
            value2 = self._deserialize_value(it.get("value2"))
            filters.append(
                FilterModel(
                    column_name=it["column_name"],
                    operator=op,
                    value=value,
                    value2=value2,
                )
            )
        return filters

    def is_compatible(self, filters: List[FilterModel], column_infos: List[ColumnInfo]) -> bool:
        """Basit uyumluluk kontrolü: tüm filtrelerin sütunu mevcut mu ve tipler uyumlu mu?
        Ekstra kontroller: range filtreleri min/max içinde mi, list filtreleri değerleri içeriyor mu.
        """
        cols = {c.name: c for c in column_infos}
        for f in filters:
            col = cols.get(f.column_name)
            if col is None:
                return False
            # operator uyumu: tarih için DATE, sayısal için NUMERIC, boolean için BOOLEAN
            if col.column_type == ColumnType.DATE and f.operator not in FilterOperator.date_operators():
                return False
            if col.column_type == ColumnType.NUMERIC and f.operator not in FilterOperator.numeric_operators():
                return False
            if col.column_type == ColumnType.BOOLEAN and f.operator not in FilterOperator.boolean_operators():
                return False
            # range checks
            if f.operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]:
                if f.value is None or f.value2 is None:
                    return False
                # For numeric/date, check min/max if present
                if col.min_value is not None and col.max_value is not None:
                    try:
                        if col.column_type == ColumnType.NUMERIC:
                            if not (float(col.min_value) <= float(f.value) <= float(col.max_value)):
                                return False
                            if not (float(col.min_value) <= float(f.value2) <= float(col.max_value)):
                                return False
                        elif col.column_type == ColumnType.DATE:
                            if not (isinstance(f.value, datetime) and isinstance(f.value2, datetime)):
                                return False
                            if not (col.min_value <= f.value <= col.max_value):
                                return False
                            if not (col.min_value <= f.value2 <= col.max_value):
                                return False
                    except Exception:
                        return False
            # In-list checks for categorical/text
            if f.operator in [FilterOperator.IN_LIST, FilterOperator.NOT_IN_LIST]:
                if not isinstance(f.value, list):
                    return False
                # If column has unique_values, ensure selected values are subset
                if col.unique_values:
                    if not set(f.value).issubset(set(col.unique_values)):
                        return False
        return True

    def _serialize_value(self, val: Any):
        if val is None:
            return None
        if isinstance(val, datetime):
            return {"__datetime__": True, "iso": val.isoformat()}
        if isinstance(val, list):
            return [self._serialize_value(v) for v in val]
        # basic types
        return val

    def _deserialize_value(self, v: Any):
        if v is None:
            return None
        if isinstance(v, dict) and v.get("__datetime__"):
            return datetime.fromisoformat(v["iso"])
        if isinstance(v, list):
            return [self._deserialize_value(x) for x in v]
        return v
