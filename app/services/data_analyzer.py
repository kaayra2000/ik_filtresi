"""
Veri analiz servisi - DataFrame sütunlarını analiz eder
"""
from typing import List
from datetime import datetime

import pandas as pd
import numpy as np

from app.models.column_info import ColumnInfo, ColumnType


class DataAnalyzer:
    """
    DataFrame'i analiz eder ve sütun bilgilerini çıkarır.
    Single Responsibility: Sadece veri analizi yapar.
    """
    
    def __init__(self, max_unique_values: int = 100):
        """
        Args:
            max_unique_values: Saklanacak maksimum benzersiz değer sayısı
        """
        self._max_unique_values = max_unique_values
    
    def analyze(self, df: pd.DataFrame) -> List[ColumnInfo]:
        """
        DataFrame'in tüm sütunlarını analiz eder.
        
        Args:
            df: Analiz edilecek DataFrame
            
        Returns:
            Sütun bilgilerinin listesi
        """
        column_infos = []
        
        for column in df.columns:
            info = self._analyze_column(df, column)
            column_infos.append(info)
        
        return column_infos
    
    def _analyze_column(self, df: pd.DataFrame, column: str) -> ColumnInfo:
        """Tek bir sütunu analiz eder"""
        series = df[column]
        
        # Tip belirleme
        column_type = self._determine_type(series)
        
        # Boş olmayan değerler
        non_null_series = series.dropna()
        
        # Benzersiz değerler (sınırlı sayıda)
        unique_values = self._get_unique_values(non_null_series, column_type)
        
        # Min/Max değerler
        min_value, max_value = self._get_min_max(non_null_series, column_type)
        
        return ColumnInfo(
            name=column,
            column_type=column_type,
            unique_values=unique_values,
            min_value=min_value,
            max_value=max_value,
            null_count=series.isna().sum(),
            total_count=len(series)
        )
    
    def _determine_type(self, series: pd.Series) -> ColumnType:
        """Sütun tipini belirler"""
        # Boş olmayan değerler
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return ColumnType.UNKNOWN
        
        dtype = series.dtype
        
        # Datetime kontrolü
        if pd.api.types.is_datetime64_any_dtype(dtype):
            return ColumnType.DATE
        
        # Sayısal kontrol
        if pd.api.types.is_numeric_dtype(dtype):
            # Boolean mu kontrol et
            unique = non_null.unique()
            if len(unique) <= 2 and set(unique).issubset({0, 1, True, False}):
                return ColumnType.BOOLEAN
            return ColumnType.NUMERIC
        
        # Boolean kontrol
        if pd.api.types.is_bool_dtype(dtype):
            return ColumnType.BOOLEAN
        
        # Metin benzeri tipler (object, string, category) - tarih olabilir mi kontrol et
        if pd.api.types.is_object_dtype(dtype) or pd.api.types.is_string_dtype(dtype) or pd.api.types.is_categorical_dtype(dtype):
            if self._is_date_column(non_null):
                return ColumnType.DATE

            # Boolean metin kontrolü
            unique_lower = set(str(v).lower() for v in non_null.unique())
            if unique_lower.issubset({'true', 'false', 'evet', 'hayır', 'yes', 'no', '1', '0'}):
                return ColumnType.BOOLEAN
        
        return ColumnType.TEXT
    
    def _is_date_column(self, series: pd.Series) -> bool:
        """Sütunun tarih içerip içermediğini kontrol eder"""
        sample_size = min(100, len(series))
        sample = series.head(sample_size)
        
        date_count = 0
        for value in sample:
            if self._try_parse_date(str(value)):
                date_count += 1
        
        # %80'i tarih ise tarih sütunu kabul et
        return date_count >= sample_size * 0.8
    
    def _try_parse_date(self, value: str) -> bool:
        """Değerin tarih olarak parse edilip edilemeyeceğini kontrol eder"""
        date_formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y',
            '%Y.%m.%d', '%d.%m.%Y', '%m.%d.%Y',
            '%d %B %Y', '%d %b %Y',
            '%Y-%m-%d %H:%M:%S', '%d.%m.%Y %H:%M:%S'
        ]
        
        for fmt in date_formats:
            try:
                datetime.strptime(value.strip(), fmt)
                return True
            except (ValueError, AttributeError):
                continue
        
        return False
    
    def _get_unique_values(self, series: pd.Series, column_type: ColumnType) -> List:
        """Benzersiz değerleri döndürür (sınırlı sayıda)"""
        unique = series.unique()
        
        # Sıralama
        try:
            if column_type == ColumnType.NUMERIC:
                unique = sorted(unique)
            elif column_type == ColumnType.DATE:
                unique = sorted(unique)
            else:
                unique = sorted(unique, key=str)
        except (TypeError, ValueError):
            pass
        
        # Sınırlama
        if len(unique) > self._max_unique_values:
            return list(unique[:self._max_unique_values])
        
        return list(unique)
    
    def _get_min_max(self, series: pd.Series, column_type: ColumnType):
        """Min ve max değerleri döndürür"""
        if len(series) == 0:
            return None, None
        
        if column_type in [ColumnType.NUMERIC, ColumnType.DATE]:
            try:
                return series.min(), series.max()
            except (TypeError, ValueError):
                return None, None
        
        return None, None
    
    def convert_date_columns(self, df: pd.DataFrame, column_infos: List[ColumnInfo]) -> pd.DataFrame:
        """
        Tarih sütunlarını datetime tipine dönüştürür.
        
        Args:
            df: Dönüştürülecek DataFrame
            column_infos: Sütun bilgileri
            
        Returns:
            Dönüştürülmüş DataFrame
        """
        df = df.copy()
        
        for info in column_infos:
            if info.column_type == ColumnType.DATE:
                if not pd.api.types.is_datetime64_any_dtype(df[info.name]):
                    try:
                        df[info.name] = pd.to_datetime(
                            df[info.name], 
                            format='mixed',
                            dayfirst=True
                        )
                    except Exception:
                        pass
        
        return df
