"""
Filtre modeli - Filtre tanımlarını ve operatörlerini içerir
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, List


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


@dataclass
class FilterModel:
    """
    Tek bir filtre tanımını temsil eder.
    Single Responsibility: Sadece filtre verilerini saklar.
    """
    column_name: str
    operator: FilterOperator
    value: Any = None
    value2: Optional[Any] = None  # BETWEEN operatörü için ikinci değer
    
    @property
    def is_range_filter(self) -> bool:
        """Bu filtre aralık filtresi mi?"""
        return self.operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]
    
    @property
    def is_null_filter(self) -> bool:
        """Bu filtre null kontrolü mü?"""
        return self.operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]
    
    def to_display_string(self) -> str:
        """Kullanıcıya gösterilecek filtre açıklaması"""
        if self.is_null_filter:
            return f"{self.column_name} {self.operator.value}"
        elif self.is_range_filter:
            return f"{self.column_name} {self.value} - {self.value2} {self.operator.value}"
        else:
            return f"{self.column_name} {self.operator.value} {self.value}"
    
    def __repr__(self) -> str:
        return f"FilterModel({self.to_display_string()})"
