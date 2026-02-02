"""
Sütun değer formatlayıcıları - Strategy Pattern implementasyonu
Her sütun tipi için ayrı formatlama stratejisi sağlar.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class ValueFormatter(ABC):
    """
    Değer formatlama için Strategy interface.
    Open/Closed Principle: Yeni tipler eklemek için yeni sınıf türetilir.
    """

    @abstractmethod
    def format_range(self, min_value: Optional[Any], max_value: Optional[Any]) -> str:
        """Aralık bilgisini görüntüleme formatında döndürür"""
        pass

    @abstractmethod
    def format_value(self, value: Any) -> str:
        """Tek bir değeri görüntüleme formatında döndürür"""
        pass


class DateFormatter(ValueFormatter):
    """Tarih değerleri için formatlayıcı"""

    def __init__(self, date_format: str = "%d.%m.%Y"):
        self._date_format = date_format

    def format_range(self, min_value: Optional[Any], max_value: Optional[Any]) -> str:
        """Tarih aralığını formatlar"""
        if min_value is None or max_value is None:
            return "N/A"

        min_str = self._format_date(min_value)
        max_str = self._format_date(max_value)
        return f"{min_str} - {max_str}"

    def format_value(self, value: Any) -> str:
        """Tek bir tarih değerini formatlar"""
        return self._format_date(value)

    def _format_date(self, value: Any) -> str:
        """Tarih değerini string'e çevirir"""
        if isinstance(value, datetime):
            return value.strftime(self._date_format)
        return str(value)


class NumericFormatter(ValueFormatter):
    """Sayısal değerler için formatlayıcı"""

    def __init__(self, decimal_places: Optional[int] = None):
        self._decimal_places = decimal_places

    def format_range(self, min_value: Optional[Any], max_value: Optional[Any]) -> str:
        """Sayısal aralığı formatlar"""
        if min_value is None or max_value is None:
            return "N/A"

        min_str = self.format_value(min_value)
        max_str = self.format_value(max_value)
        return f"{min_str} - {max_str}"

    def format_value(self, value: Any) -> str:
        """Tek bir sayısal değeri formatlar"""
        if value is None:
            return "N/A"
        if self._decimal_places is not None and isinstance(value, float):
            return f"{value:.{self._decimal_places}f}"
        return str(value)


class TextFormatter(ValueFormatter):
    """Metin değerleri için formatlayıcı"""

    def format_range(self, min_value: Optional[Any], max_value: Optional[Any]) -> str:
        """Metin için aralık desteklenmez"""
        return "N/A"

    def format_value(self, value: Any) -> str:
        """Tek bir metin değerini formatlar"""
        if value is None:
            return ""
        return str(value)


class BooleanFormatter(ValueFormatter):
    """Boolean değerler için formatlayıcı"""

    def __init__(self, true_label: str = "Evet", false_label: str = "Hayır"):
        self._true_label = true_label
        self._false_label = false_label

    def format_range(self, min_value: Optional[Any], max_value: Optional[Any]) -> str:
        """Boolean için aralık desteklenmez"""
        return "N/A"

    def format_value(self, value: Any) -> str:
        """Boolean değeri formatlar"""
        if value is None:
            return "N/A"
        return self._true_label if value else self._false_label


class UnknownFormatter(ValueFormatter):
    """Bilinmeyen tip değerler için varsayılan formatlayıcı"""

    def format_range(self, min_value: Optional[Any], max_value: Optional[Any]) -> str:
        """Bilinmeyen tip için aralık"""
        return "N/A"

    def format_value(self, value: Any) -> str:
        """Değeri string olarak döndürür"""
        if value is None:
            return "N/A"
        return str(value)


class FormatterFactory:
    """
    Sütun tipine göre uygun formatter döndüren Factory.
    Factory Pattern: Nesne oluşturma mantığını merkezi bir yerde toplar.
    """

    _formatters = {
        "NUMERIC": NumericFormatter,
        "DATE": DateFormatter,
        "TEXT": TextFormatter,
        "BOOLEAN": BooleanFormatter,
        "UNKNOWN": UnknownFormatter,
    }

    @classmethod
    def get_formatter(cls, column_type_name: str, **kwargs) -> ValueFormatter:
        """
        Sütun tipine göre uygun formatter instance'ı döndürür.

        Args:
            column_type_name: ColumnType enum değerinin adı (örn: "DATE", "NUMERIC")
            **kwargs: Formatter'a özel parametreler

        Returns:
            İlgili ValueFormatter instance'ı
        """
        formatter_class = cls._formatters.get(column_type_name, UnknownFormatter)
        return formatter_class(**kwargs) if kwargs else formatter_class()

    @classmethod
    def register_formatter(cls, type_name: str, formatter_class: type) -> None:
        """
        Yeni bir formatter tipi kaydet.
        Open/Closed Principle: Mevcut kodu değiştirmeden yeni tipler eklenebilir.

        Args:
            type_name: Tip adı
            formatter_class: ValueFormatter'dan türetilmiş sınıf
        """
        if not issubclass(formatter_class, ValueFormatter):
            raise TypeError("formatter_class must be a subclass of ValueFormatter")
        cls._formatters[type_name] = formatter_class
