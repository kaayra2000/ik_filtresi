"""
Filtre modeli - Filtre tanımlarını ve operatörlerini içerir

Composite Pattern kullanılarak hiyerarşik filtre yapısı desteklenir.
FilterComponent abstract base class'ı, FilterModel (leaf) ve FilterGroup (composite)
tarafından implemente edilir.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional, List, Union
import uuid


# === Serialization Utility Functions ===

def _serialize_value(val: Any) -> Any:
    """Değeri JSON uyumlu formata dönüştürür"""
    if val is None:
        return None
    if isinstance(val, datetime):
        return {"__datetime__": True, "iso": val.isoformat()}
    if isinstance(val, list):
        return [_serialize_value(item) for item in val]
    return val


def _deserialize_value(val: Any) -> Any:
    """JSON formatından orijinal değere dönüştürür"""
    if val is None:
        return None
    if isinstance(val, dict) and val.get("__datetime__"):
        return datetime.fromisoformat(val["iso"])
    if isinstance(val, list):
        return [_deserialize_value(item) for item in val]
    return val


# === Display Format Mapping ===
# Operatör -> format tipi eşleştirmesi (Open/Closed Principle)
_OPERATOR_FORMAT_TYPE: dict['FilterOperator', str] = {}  # Lazy initialization

_DISPLAY_FORMATS = {
    'null': "{prefix}{column} {op}",
    'range': "{prefix}{column} {value} - {value2} {op}",
    'default': "{prefix}{column} {op} {value}"
}


def _get_format_type(operator: 'FilterOperator') -> str:
    """Operatöre göre format tipini döndürür"""
    # Lazy initialization - ilk çağrıda doldur
    if not _OPERATOR_FORMAT_TYPE:
        _OPERATOR_FORMAT_TYPE.update({
            FilterOperator.IS_NULL: 'null',
            FilterOperator.IS_NOT_NULL: 'null',
            FilterOperator.BETWEEN: 'range',
            FilterOperator.NOT_BETWEEN: 'range',
        })
    return _OPERATOR_FORMAT_TYPE.get(operator, 'default')


class LogicalOperator(Enum):
    """Filtre grupları için mantıksal operatörler (AND/OR)"""
    AND = "VE"
    OR = "VEYA"


class FilterOperator(Enum):
    """Filtre operatörleri"""
    # Sayısal ve tarih operatörleri
    EQUALS = "="
    NOT_EQUALS = "≠"
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "≤"
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = "≥"
    BETWEEN = "Arasında"
    NOT_BETWEEN = "Arasında Değil"
    
    # Metin operatörleri
    CONTAINS = "İçerir"
    NOT_CONTAINS = "İçermez"
    STARTS_WITH = "İle Başlar"
    ENDS_WITH = "İle Biter"
    MATCHES = "Eşleşir"
    NOT_MATCHES = "Eşleşmez"
    IN_LIST = "Listede"
    NOT_IN_LIST = "Listede Değil"
    
    # Null kontrolleri
    IS_NULL = "Boş"
    IS_NOT_NULL = "Boş Değil"
    
    @classmethod
    def numeric_operators(cls) -> List['FilterOperator']:
        """Sayısal sütunlar için geçerli operatörler"""
        return [
            cls.EQUALS, cls.NOT_EQUALS,
            cls.LESS_THAN, cls.LESS_THAN_OR_EQUAL,
            cls.GREATER_THAN, cls.GREATER_THAN_OR_EQUAL,
            cls.BETWEEN, cls.NOT_BETWEEN,
            cls.IS_NULL, cls.IS_NOT_NULL
        ]
    
    @classmethod
    def date_operators(cls) -> List['FilterOperator']:
        """Tarih sütunları için geçerli operatörler"""
        return [
            cls.EQUALS, cls.NOT_EQUALS,
            cls.LESS_THAN, cls.LESS_THAN_OR_EQUAL,
            cls.GREATER_THAN, cls.GREATER_THAN_OR_EQUAL,
            cls.BETWEEN, cls.NOT_BETWEEN,
            cls.IS_NULL, cls.IS_NOT_NULL
        ]
    
    @classmethod
    def text_operators(cls) -> List['FilterOperator']:
        """Metin sütunları için geçerli operatörler"""
        return [
            cls.EQUALS, cls.NOT_EQUALS,
            cls.CONTAINS, cls.NOT_CONTAINS,
            cls.STARTS_WITH, cls.ENDS_WITH,
            cls.MATCHES, cls.NOT_MATCHES,
            cls.IN_LIST, cls.NOT_IN_LIST,
            cls.IS_NULL, cls.IS_NOT_NULL
        ]
    
    @classmethod
    def boolean_operators(cls) -> List['FilterOperator']:
        """Boolean sütunları için geçerli operatörler"""
        return [cls.EQUALS, cls.NOT_EQUALS, cls.IS_NULL, cls.IS_NOT_NULL]


class FilterComponent(ABC):
    """
    Composite Pattern - Abstract Component
    Hem tek filtreler (FilterModel) hem de filtre grupları (FilterGroup)
    bu arayüzü implemente eder.
    """
    
    @abstractmethod
    def to_display_string(self, indent: int = 0) -> str:
        """Kullanıcıya gösterilecek filtre açıklaması"""
        pass
    
    @abstractmethod
    def is_empty(self) -> bool:
        """Bu bileşen boş mu?"""
        pass
    
    @abstractmethod
    def to_dict(self) -> dict:
        """Serialization için dictionary'e dönüştür"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> 'FilterComponent':
        """Dictionary'den nesne oluştur"""
        pass


@dataclass
class FilterModel(FilterComponent):
    """
    Composite Pattern - Leaf
    Tek bir filtre tanımını temsil eder.
    Single Responsibility: Sadece filtre verilerini saklar.
    """
    column_name: str
    operator: FilterOperator
    value: Any = None
    value2: Optional[Any] = None  # BETWEEN operatörü için ikinci değer
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    @property
    def is_range_filter(self) -> bool:
        """Bu filtre aralık filtresi mi?"""
        return self.operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]
    
    @property
    def is_null_filter(self) -> bool:
        """Bu filtre null kontrolü mü?"""
        return self.operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]
    
    def is_empty(self) -> bool:
        """Filtre boş değil (her zaman False)"""
        return False
    
    def to_display_string(self, indent: int = 0) -> str:
        """Kullanıcıya gösterilecek filtre açıklaması"""
        prefix = "  " * indent
        format_type = _get_format_type(self.operator)
        return _DISPLAY_FORMATS[format_type].format(
            prefix=prefix,
            column=self.column_name,
            op=self.operator.value,
            value=self.value,
            value2=self.value2
        )
    
    def to_dict(self) -> dict:
        """Serialization için dictionary'e dönüştür"""
        return {
            "type": "filter",
            "id": self.id,
            "column_name": self.column_name,
            "operator": self.operator.name,
            "value": _serialize_value(self.value),
            "value2": _serialize_value(self.value2)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FilterModel':
        """Dictionary'den nesne oluştur"""
        return cls(
            column_name=data["column_name"],
            operator=FilterOperator[data["operator"]],
            value=_deserialize_value(data.get("value")),
            value2=_deserialize_value(data.get("value2")),
            id=data.get("id", str(uuid.uuid4()))
        )
    
    def __repr__(self) -> str:
        return f"FilterModel({self.to_display_string()})"


@dataclass
class FilterItem:
    """
    Bir filtre bileşenini ve önceki operatörünü birlikte tutan veri yapısı.
    
    Single Responsibility: Component ve operator arasındaki ilişkiyi yönetir.
    İlk eleman için preceding_operator None olmalıdır.
    """
    component: FilterComponent
    preceding_operator: Optional[LogicalOperator] = None  # İlk eleman için None
    
    def to_dict(self) -> dict:
        """Serialization için dictionary'e dönüştür"""
        return {
            "component": self.component.to_dict(),
            "preceding_operator": self.preceding_operator.name if self.preceding_operator else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FilterItem':
        """Dictionary'den nesne oluştur"""
        component_data = data["component"]
        if component_data.get("type") == "group":
            component = FilterGroup.from_dict(component_data)
        else:
            component = FilterModel.from_dict(component_data)
        
        op_name = data.get("preceding_operator")
        preceding_operator = LogicalOperator[op_name] if op_name else None
        
        return cls(component=component, preceding_operator=preceding_operator)


class FilterItems:
    """
    FilterItem koleksiyonunu yöneten sınıf.
    
    Single Responsibility: Item listesini tutarlı bir şekilde yönetir.
    Encapsulation: children ve operators arasındaki bağımlılığı gizler.
    """
    
    def __init__(self, items: Optional[List[FilterItem]] = None):
        self._items: List[FilterItem] = items or []
        self._validate()
    
    def _validate(self):
        """İlk elemanın operatörünün None olmasını garanti eder"""
        if self._items and self._items[0].preceding_operator is not None:
            self._items[0].preceding_operator = None
    
    def add(self, component: FilterComponent, operator: LogicalOperator = LogicalOperator.AND) -> None:
        """Yeni bir eleman ekler. İlk eleman için operatör yoksayılır."""
        if not self._items:
            self._items.append(FilterItem(component=component, preceding_operator=None))
        else:
            self._items.append(FilterItem(component=component, preceding_operator=operator))
    
    def remove_at(self, index: int) -> bool:
        """Belirtilen indeksteki elemanı kaldırır"""
        if 0 <= index < len(self._items):
            self._items.pop(index)
            # İlk eleman kaldırıldıysa, yeni ilk elemanın operatörünü None yap
            if index == 0 and self._items:
                self._items[0].preceding_operator = None
            return True
        return False
    
    def remove_by_id(self, component_id: str) -> bool:
        """ID'ye göre elemanı kaldırır"""
        for i, item in enumerate(self._items):
            if item.component.id == component_id:
                return self.remove_at(i)
        return False
    
    def get_operator_at(self, index: int) -> Optional[LogicalOperator]:
        """Belirtilen indeksteki elemanın önceki operatörünü döndürür"""
        if 0 <= index < len(self._items):
            return self._items[index].preceding_operator
        return None
    
    def set_operator_at(self, index: int, operator: LogicalOperator) -> None:
        """Belirtilen indeksteki elemanın önceki operatörünü ayarlar (ilk eleman hariç)"""
        if 0 < index < len(self._items):
            self._items[index].preceding_operator = operator
    
    def find_by_id(self, component_id: str) -> Optional[FilterComponent]:
        """ID'ye göre bir bileşen bulur"""
        for item in self._items:
            if item.component.id == component_id:
                return item.component
        return None
    
    def __len__(self) -> int:
        return len(self._items)
    
    def __iter__(self):
        return iter(self._items)
    
    def __getitem__(self, index: int) -> FilterItem:
        return self._items[index]
    
    @property
    def components(self) -> List[FilterComponent]:
        """Sadece component'lerin listesini döndürür"""
        return [item.component for item in self._items]
    
    def clear(self):
        """Tüm elemanları temizler"""
        self._items.clear()
    
    def is_empty(self) -> bool:
        """Liste boş mu?"""
        return len(self._items) == 0


@dataclass
class FilterGroup(FilterComponent):
    """
    Composite Pattern - Composite
    Birden fazla filtre veya filtre grubunu bir arada tutar.
    
    Her eleman arasında ayrı operatör kullanılabilir:
    Örnek: A VE B VEYA C VE D
    
    FilterItems sınıfı ile component-operator ilişkisi tutarlı yönetilir.
    """
    _items: FilterItems = field(default_factory=FilterItems)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def __post_init__(self):
        """dataclass initialization sonrası FilterItems oluştur"""
        if not isinstance(self._items, FilterItems):
            self._items = FilterItems()
    
    @property
    def items(self) -> FilterItems:
        """FilterItems erişimi"""
        return self._items
    
    @property
    def children(self) -> List[FilterComponent]:
        """Geriye dönük uyumluluk için children property'si"""
        return self._items.components
    
    def add(self, component: FilterComponent, operator: LogicalOperator = LogicalOperator.AND) -> None:
        """Bir filtre veya filtre grubu ekler"""
        self._items.add(component, operator)
    
    def remove(self, component: FilterComponent) -> None:
        """Bir filtre veya filtre grubunu kaldırır"""
        self._items.remove_by_id(component.id)
    
    def remove_by_id(self, component_id: str) -> bool:
        """ID'ye göre bir bileşeni kaldırır (rekürsif)"""
        # Önce doğrudan çocuklarda ara
        if self._items.remove_by_id(component_id):
            return True
        
        # Alt gruplarda rekürsif ara
        for item in self._items:
            if isinstance(item.component, FilterGroup):
                if item.component.remove_by_id(component_id):
                    return True
        return False
    
    def get_operator_at(self, index: int) -> Optional[LogicalOperator]:
        """Belirli indeksteki elemanın önceki operatörünü döndürür"""
        return self._items.get_operator_at(index)
    
    def set_operator_at(self, index: int, operator: LogicalOperator) -> None:
        """Belirli indeksteki elemanın önceki operatörünü ayarlar"""
        self._items.set_operator_at(index, operator)
    
    def find_by_id(self, component_id: str) -> Optional[FilterComponent]:
        """ID'ye göre bir bileşen bulur (rekürsif)"""
        if self.id == component_id:
            return self
        
        # Doğrudan çocuklarda ara
        found = self._items.find_by_id(component_id)
        if found:
            return found
        
        # Alt gruplarda rekürsif ara
        for item in self._items:
            if isinstance(item.component, FilterGroup):
                found = item.component.find_by_id(component_id)
                if found:
                    return found
        return None
    
    def is_empty(self) -> bool:
        """Grup boş mu veya tüm alt elemanları boş mu?"""
        if self._items.is_empty():
            return True
        return all(item.component.is_empty() for item in self._items)
    
    def get_all_filters(self) -> List[FilterModel]:
        """Tüm alt filtreleri düz liste olarak döndürür (sadece FilterModel'ler)"""
        filters = []
        for item in self._items:
            if isinstance(item.component, FilterModel):
                filters.append(item.component)
            elif isinstance(item.component, FilterGroup):
                filters.extend(item.component.get_all_filters())
        return filters
    
    def to_display_string(self, indent: int = 0) -> str:
        """Kullanıcıya gösterilecek grup açıklaması"""
        if self._items.is_empty():
            return "  " * indent + "(Boş Grup)"
        
        prefix = "  " * indent
        format_child = lambda c: f"({c.to_display_string(0)})" if isinstance(c, FilterGroup) else c.to_display_string(0)
        
        parts = []
        for i, item in enumerate(self._items):
            child_str = format_child(item.component)
            if i == 0:
                parts.append(child_str)
            else:
                op = item.preceding_operator or LogicalOperator.AND
                parts.append(f"{op.value} {child_str}")
        
        return prefix + " ".join(parts)
    
    def to_dict(self) -> dict:
        """Serialization için dictionary'e dönüştür"""
        return {
            "type": "group",
            "id": self.id,
            "items": [item.to_dict() for item in self._items]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FilterGroup':
        """Dictionary'den nesne oluştur"""
        group = cls(id=data.get("id", str(uuid.uuid4())))
        
        # Yeni format: items listesi
        if "items" in data:
            for item_data in data["items"]:
                item = FilterItem.from_dict(item_data)
                # İlk eleman için operatör None olmalı
                if group._items.is_empty():
                    group._items.add(item.component, LogicalOperator.AND)
                else:
                    group._items.add(item.component, item.preceding_operator or LogicalOperator.AND)
        
        # Eski format uyumluluğu: children + operators
        elif "children" in data:
            children = []
            for child_data in data.get("children", []):
                if child_data.get("type") == "group":
                    children.append(FilterGroup.from_dict(child_data))
                else:
                    children.append(FilterModel.from_dict(child_data))
            
            # Operatörleri al
            operators_data = data.get("operators", [])
            if not operators_data and "logical_operator" in data:
                # Çok eski format - tek operatör
                old_op = LogicalOperator[data.get("logical_operator", "AND")]
                operators = [old_op] * (len(children) - 1) if len(children) > 1 else []
            else:
                operators = [LogicalOperator[op] for op in operators_data]
            
            # Items'a ekle
            for i, child in enumerate(children):
                op = operators[i - 1] if i > 0 and i - 1 < len(operators) else LogicalOperator.AND
                group._items.add(child, op)
        
        return group
    
    def clear(self) -> None:
        """Tüm elemanları temizler"""
        self._items.clear()
    
    def __repr__(self) -> str:
        return f"FilterGroup({len(self._items)} children)"


def component_from_dict(data: dict) -> FilterComponent:
    """
    Factory function - Dictionary'den uygun FilterComponent türünü oluşturur.
    """
    if data.get("type") == "group":
        return FilterGroup.from_dict(data)
    else:
        return FilterModel.from_dict(data)
