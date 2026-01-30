"""
Filtre motoru - Filtreleri DataFrame üzerinde uygular
"""
from typing import List
import re

import pandas as pd
import numpy as np

from app.models.filter_model import FilterModel, FilterOperator
from app.models.column_info import ColumnType


class FilterEngine:
    """
    Filtreleri DataFrame üzerinde uygular.
    Single Responsibility: Sadece filtreleme işlemlerini yapar.
    Open/Closed: Yeni operatörler kolayca eklenebilir.
    """
    
    def __init__(self):
        # Operatör -> uygulama fonksiyonu eşleştirmesi
        self._operators = {
            FilterOperator.EQUALS: self._apply_equals,
            FilterOperator.NOT_EQUALS: self._apply_not_equals,
            FilterOperator.LESS_THAN: self._apply_less_than,
            FilterOperator.LESS_THAN_OR_EQUAL: self._apply_less_than_or_equal,
            FilterOperator.GREATER_THAN: self._apply_greater_than,
            FilterOperator.GREATER_THAN_OR_EQUAL: self._apply_greater_than_or_equal,
            FilterOperator.BETWEEN: self._apply_between,
            FilterOperator.NOT_BETWEEN: self._apply_not_between,
            FilterOperator.CONTAINS: self._apply_contains,
            FilterOperator.NOT_CONTAINS: self._apply_not_contains,
            FilterOperator.STARTS_WITH: self._apply_starts_with,
            FilterOperator.ENDS_WITH: self._apply_ends_with,
            FilterOperator.MATCHES: self._apply_matches,
            FilterOperator.NOT_MATCHES: self._apply_not_matches,
            FilterOperator.IN_LIST: self._apply_in_list,
            FilterOperator.NOT_IN_LIST: self._apply_not_in_list,
            FilterOperator.IS_NULL: self._apply_is_null,
            FilterOperator.IS_NOT_NULL: self._apply_is_not_null,
        }
    
    def apply_filters(self, df: pd.DataFrame, filters: List[FilterModel]) -> pd.DataFrame:
        """
        Tüm filtreleri sırayla uygular (AND mantığı).
        
        Args:
            df: Filtrelenecek DataFrame
            filters: Uygulanacak filtreler
            
        Returns:
            Filtrelenmiş DataFrame
        """
        if not filters:
            return df
        
        result = df.copy()
        
        for filter_model in filters:
            if filter_model.column_name not in result.columns:
                continue
            
            mask = self._apply_filter(result, filter_model)
            result = result[mask]
        
        return result
    
    def _apply_filter(self, df: pd.DataFrame, filter_model: FilterModel) -> pd.Series:
        """Tek bir filtreyi uygular ve boolean mask döndürür"""
        operator_func = self._operators.get(filter_model.operator)
        
        if operator_func is None:
            raise ValueError(f"Desteklenmeyen operatör: {filter_model.operator}")
        
        return operator_func(df, filter_model)
    
    # === Karşılaştırma Operatörleri ===
    
    def _apply_equals(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name] == f.value
    
    def _apply_not_equals(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name] != f.value
    
    def _apply_less_than(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name] < f.value
    
    def _apply_less_than_or_equal(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name] <= f.value
    
    def _apply_greater_than(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name] > f.value
    
    def _apply_greater_than_or_equal(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name] >= f.value
    
    # === Aralık Operatörleri ===
    
    def _apply_between(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return (df[f.column_name] >= f.value) & (df[f.column_name] <= f.value2)
    
    def _apply_not_between(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return (df[f.column_name] < f.value) | (df[f.column_name] > f.value2)
    
    # === Metin Operatörleri ===
    
    def _apply_contains(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name].astype(str).str.contains(
            str(f.value), case=False, na=False, regex=False
        )
    
    def _apply_not_contains(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return ~df[f.column_name].astype(str).str.contains(
            str(f.value), case=False, na=False, regex=False
        )
    
    def _apply_starts_with(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name].astype(str).str.lower().str.startswith(
            str(f.value).lower(), na=False
        )
    
    def _apply_ends_with(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name].astype(str).str.lower().str.endswith(
            str(f.value).lower(), na=False
        )
    
    def _apply_matches(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        """Regex eşleşmesi"""
        try:
            return df[f.column_name].astype(str).str.match(
                str(f.value), case=False, na=False
            )
        except re.error:
            # Geçersiz regex durumunda boş mask döndür
            return pd.Series([False] * len(df))
    
    def _apply_not_matches(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return ~self._apply_matches(df, f)
    
    # === Liste Operatörleri ===
    
    def _apply_in_list(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        values = f.value if isinstance(f.value, list) else [f.value]
        return df[f.column_name].isin(values)
    
    def _apply_not_in_list(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        values = f.value if isinstance(f.value, list) else [f.value]
        return ~df[f.column_name].isin(values)
    
    # === Null Operatörleri ===
    
    def _apply_is_null(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name].isna()
    
    def _apply_is_not_null(self, df: pd.DataFrame, f: FilterModel) -> pd.Series:
        return df[f.column_name].notna()
    
    def get_filter_summary(self, filters: List[FilterModel]) -> str:
        """Filtre özetini string olarak döndürür"""
        if not filters:
            return "Filtre yok"
        
        summaries = [f.to_display_string() for f in filters]
        return " VE ".join(summaries)
