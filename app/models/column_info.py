"""
Sütun bilgisi modeli - Sütunların tür ve içerik bilgilerini tutar
"""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, List, Optional

from app.models.formatters import FormatterFactory, ValueFormatter


class ColumnType(Enum):
    """Sütun veri türleri"""
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
    Strategy Pattern: Formatlama işleri ValueFormatter'a delege edilir.
    """
    name: str
    column_type: ColumnType
    unique_values: List[Any] = field(default_factory=list)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    null_count: int = 0
    total_count: int = 0
    _formatter: Optional[ValueFormatter] = field(default=None, repr=False, compare=False)
    
    def __post_init__(self) -> None:
        """Dataclass oluşturulduktan sonra formatter'ı ayarla"""
        if self._formatter is None:
            self._formatter = FormatterFactory.get_formatter(self.column_type.name)
    
    @property
    def formatter(self) -> ValueFormatter:
        """Sütun için kullanılan formatter"""
        if self._formatter is None:
            self._formatter = FormatterFactory.get_formatter(self.column_type.name)
        return self._formatter
    
    @formatter.setter
    def formatter(self, value: ValueFormatter) -> None:
        """Özel formatter atama (dependency injection)"""
        self._formatter = value
    
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
        """
        Aralık bilgisini görüntüleme formatında döndürür.
        Strategy Pattern: Formatlama işi formatter'a delege edilir.
        """
        return self.formatter.format_range(self.min_value, self.max_value)
    
    def format_value(self, value: Any) -> str:
        """
        Tek bir değeri görüntüleme formatında döndürür.
        Strategy Pattern: Formatlama işi formatter'a delege edilir.
        """
        return self.formatter.format_value(value)
    
    def __repr__(self) -> str:
        return f"ColumnInfo(name='{self.name}', type={self.column_type.name}, unique={self.unique_count})"
