"""
Sütun bilgisi modeli - Sütunların tip ve içerik bilgilerini tutar
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional
from datetime import datetime


class ColumnType(Enum):
    """Sütun veri tipleri"""
    NUMERIC = auto()
    DATE = auto()
    TEXT = auto()
    BOOLEAN = auto()
    UNKNOWN = auto()


@dataclass
class ColumnInfo:
    """
    Bir sütunun analiz edilmiş bilgilerini tutar.
    Single Responsibility: Sadece sütun meta verilerini saklar.
    """
    name: str
    column_type: ColumnType
    unique_values: List[Any] = field(default_factory=list)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    null_count: int = 0
    total_count: int = 0
    
    @property
    def unique_count(self) -> int:
        """Benzersiz değer sayısı"""
        return len(self.unique_values)
    
    @property
    def is_categorical(self) -> bool:
        """Kategorik mi? (az sayıda benzersiz değer)"""
        if self.column_type == ColumnType.TEXT:
            # Toplam değerin %50'sinden az benzersiz değer varsa kategorik
            return self.unique_count <= max(20, self.total_count * 0.5)
        return False
    
    def get_display_range(self) -> str:
        """Aralık bilgisini görüntüleme formatında döndürür"""
        if self.min_value is None or self.max_value is None:
            return "N/A"
        
        if self.column_type == ColumnType.DATE:
            min_str = self.min_value.strftime("%d.%m.%Y") if isinstance(self.min_value, datetime) else str(self.min_value)
            max_str = self.max_value.strftime("%d.%m.%Y") if isinstance(self.max_value, datetime) else str(self.max_value)
            return f"{min_str} - {max_str}"
        elif self.column_type == ColumnType.NUMERIC:
            return f"{self.min_value} - {self.max_value}"
        
        return "N/A"
    
    def __repr__(self) -> str:
        return f"ColumnInfo(name='{self.name}', type={self.column_type.name}, unique={self.unique_count})"
