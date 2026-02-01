"""
Filtre motoru - Filtreleri DataFrame üzerinde uygular

Composite Pattern desteği ile hem tekil filtreler hem de
hiyerarşik filtre grupları (AND/OR kombinasyonları) uygulanabilir.
"""
import re

import pandas as pd
import numpy as np

from app.models.filter_model import (
    FilterModel, FilterOperator, FilterGroup, 
    FilterComponent, LogicalOperator
)


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
    
    def apply_filter_component(self, df: pd.DataFrame, component: FilterComponent) -> pd.DataFrame:
        """
        Composite Pattern ile filtreleme.
        FilterModel veya FilterGroup kabul eder.
        
        Args:
            df: Filtrelenecek DataFrame
            component: FilterModel veya FilterGroup
            
        Returns:
            Filtrelenmiş DataFrame
        """
        if component is None or component.is_empty():
            return df
        
        mask = self._get_component_mask(df, component)
        return df[mask]
    
    def _get_component_mask(self, df: pd.DataFrame, component: FilterComponent) -> pd.Series:
        """
        Herhangi bir FilterComponent için boolean mask döndürür.
        Rekürsif olarak çalışır.
        """
        if isinstance(component, FilterModel):
            if component.column_name not in df.columns:
                # Sütun yoksa tümünü dahil et
                return pd.Series([True] * len(df), index=df.index)
            return self._apply_filter(df, component)
        
        elif isinstance(component, FilterGroup):
            return self._get_group_mask(df, component)
        
        else:
            raise ValueError(f"Desteklenmeyen bileşen tipi: {type(component)}")
    
    def _get_group_mask(self, df: pd.DataFrame, group: FilterGroup) -> pd.Series:
        """
        FilterGroup için boolean mask döndürür.
        Her eleman çifti arasındaki operatöre göre maskeleri birleştirir.
        """
        if group.items.is_empty():
            # Boş grup - tümünü dahil et
            return pd.Series([True] * len(df), index=df.index)
        
        # İlk elemanın mask'ı ile başla
        first_item = group.items[0]
        result = self._get_component_mask(df, first_item.component)
        
        # Sonraki elemanları operatörlerine göre birleştir
        for item in list(group.items)[1:]:
            child_mask = self._get_component_mask(df, item.component)
            op = item.preceding_operator or LogicalOperator.AND
            
            if op == LogicalOperator.AND:
                result = result & child_mask
            else:  # OR
                result = result | child_mask
        
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
    
    def get_component_summary(self, component: FilterComponent) -> str:
        """Filtre bileşeni özetini string olarak döndürür"""
        if component is None or component.is_empty():
            return "Filtre yok"
        
        return component.to_display_string()
