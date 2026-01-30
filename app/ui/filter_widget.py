"""
Filtre widget'ı - Filtreleme arayüzü
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QLineEdit, QFrame, QScrollArea, QDateEdit,
    QDoubleSpinBox, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QDoubleValidator
from typing import List, Optional
from datetime import datetime

from app.models.column_info import ColumnInfo, ColumnType
from app.models.filter_model import FilterModel, FilterOperator


class SingleFilterWidget(QFrame):
    """
    Tek bir filtre satırı widget'ı.
    Sütun tipine göre dinamik olarak input alanları oluşturur.
    """
    
    removed = pyqtSignal(object)  # self'i emit eder
    changed = pyqtSignal()
    
    def __init__(self, column_infos: List[ColumnInfo], parent=None):
        super().__init__(parent)
        self.setObjectName("filterFrame")
        self._column_infos = column_infos
        self._current_column_info: Optional[ColumnInfo] = None
        self._setup_ui()
    
    def _setup_ui(self):
        self._main_layout = QHBoxLayout(self)
        self._main_layout.setSpacing(10)
        
        # Sütun seçici
        self._column_combo = QComboBox()
        self._column_combo.setMinimumWidth(150)
        self._column_combo.addItem("Sütun Seçin...", None)
        for info in self._column_infos:
            self._column_combo.addItem(info.name, info)
        self._column_combo.currentIndexChanged.connect(self._on_column_changed)
        self._main_layout.addWidget(self._column_combo)
        
        # Operatör seçici
        self._operator_combo = QComboBox()
        self._operator_combo.setMinimumWidth(120)
        self._operator_combo.setEnabled(False)
        self._operator_combo.currentIndexChanged.connect(self._on_operator_changed)
        self._main_layout.addWidget(self._operator_combo)
        
        # Değer alanı container
        self._value_container = QWidget()
        self._value_layout = QHBoxLayout(self._value_container)
        self._value_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.addWidget(self._value_container)
        
        # Stretch
        self._main_layout.addStretch()
        
        # Kaldır butonu
        remove_btn = QPushButton("✕")
        remove_btn.setObjectName("removeButton")
        remove_btn.setFixedSize(30, 30)
        remove_btn.clicked.connect(lambda: self.removed.emit(self))
        self._main_layout.addWidget(remove_btn)
    
    def _on_column_changed(self, index: int):
        """Sütun değiştiğinde çağrılır"""
        self._current_column_info = self._column_combo.currentData()
        self._update_operators()
        self._update_value_inputs()
        self.changed.emit()
    
    def _update_operators(self):
        """Operatörleri günceller"""
        self._operator_combo.clear()
        
        if self._current_column_info is None:
            self._operator_combo.setEnabled(False)
            return
        
        self._operator_combo.setEnabled(True)
        
        # Tipe göre operatörler
        col_type = self._current_column_info.column_type
        
        if col_type == ColumnType.NUMERIC:
            operators = FilterOperator.numeric_operators()
        elif col_type == ColumnType.DATE:
            operators = FilterOperator.date_operators()
        elif col_type == ColumnType.BOOLEAN:
            operators = FilterOperator.boolean_operators()
        else:
            operators = FilterOperator.text_operators()
        
        for op in operators:
            self._operator_combo.addItem(op.value, op)
    
    def _on_operator_changed(self, index: int):
        """Operatör değiştiğinde çağrılır"""
        self._update_value_inputs()
        self.changed.emit()
    
    def _update_value_inputs(self):
        """Değer giriş alanlarını günceller"""
        # Mevcut widget'ları temizle
        while self._value_layout.count():
            item = self._value_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self._current_column_info is None:
            return
        
        operator = self._operator_combo.currentData()
        if operator is None:
            return
        
        # Null operatörleri için input gerekmez
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            return
        
        col_type = self._current_column_info.column_type
        is_range = operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]
        
        # Tip ve kategorik duruma göre input oluştur
        if col_type == ColumnType.NUMERIC:
            self._create_numeric_inputs(is_range)
        elif col_type == ColumnType.DATE:
            self._create_date_inputs(is_range)
        elif col_type == ColumnType.BOOLEAN:
            self._create_boolean_input()
        elif col_type == ColumnType.TEXT:
            if operator in [FilterOperator.IN_LIST, FilterOperator.NOT_IN_LIST]:
                self._create_list_input()
            elif operator in [FilterOperator.EQUALS, FilterOperator.NOT_EQUALS] and \
                 self._current_column_info.is_categorical:
                self._create_categorical_input()
            else:
                self._create_text_input()
    
    def _create_numeric_inputs(self, is_range: bool):
        """Sayısal değer girişi oluşturur"""
        self._value1_spin = QDoubleSpinBox()
        self._value1_spin.setRange(-999999999, 999999999)
        self._value1_spin.setDecimals(2)
        
        if self._current_column_info.min_value is not None:
            self._value1_spin.setValue(float(self._current_column_info.min_value))
        
        self._value1_spin.valueChanged.connect(self.changed.emit)
        self._value_layout.addWidget(self._value1_spin)
        
        if is_range:
            self._value_layout.addWidget(QLabel("-"))
            
            self._value2_spin = QDoubleSpinBox()
            self._value2_spin.setRange(-999999999, 999999999)
            self._value2_spin.setDecimals(2)
            
            if self._current_column_info.max_value is not None:
                self._value2_spin.setValue(float(self._current_column_info.max_value))
            
            self._value2_spin.valueChanged.connect(self.changed.emit)
            self._value_layout.addWidget(self._value2_spin)
    
    def _create_date_inputs(self, is_range: bool):
        """Tarih girişi oluşturur"""
        self._value1_date = QDateEdit()
        self._value1_date.setCalendarPopup(True)
        self._value1_date.setDisplayFormat("dd.MM.yyyy")
        
        if self._current_column_info.min_value is not None:
            try:
                min_date = self._current_column_info.min_value
                if isinstance(min_date, datetime):
                    self._value1_date.setDate(QDate(min_date.year, min_date.month, min_date.day))
            except Exception:
                self._value1_date.setDate(QDate.currentDate())
        
        self._value1_date.dateChanged.connect(self.changed.emit)
        self._value_layout.addWidget(self._value1_date)
        
        if is_range:
            self._value_layout.addWidget(QLabel("-"))
            
            self._value2_date = QDateEdit()
            self._value2_date.setCalendarPopup(True)
            self._value2_date.setDisplayFormat("dd.MM.yyyy")
            
            if self._current_column_info.max_value is not None:
                try:
                    max_date = self._current_column_info.max_value
                    if isinstance(max_date, datetime):
                        self._value2_date.setDate(QDate(max_date.year, max_date.month, max_date.day))
                except Exception:
                    self._value2_date.setDate(QDate.currentDate())
            
            self._value2_date.dateChanged.connect(self.changed.emit)
            self._value_layout.addWidget(self._value2_date)
    
    def _create_boolean_input(self):
        """Boolean seçici oluşturur"""
        self._value_combo = QComboBox()
        self._value_combo.addItem("Evet / True", True)
        self._value_combo.addItem("Hayır / False", False)
        self._value_combo.currentIndexChanged.connect(self.changed.emit)
        self._value_layout.addWidget(self._value_combo)
    
    def _create_categorical_input(self):
        """Kategorik değer seçici oluşturur"""
        self._value_combo = QComboBox()
        for value in self._current_column_info.unique_values:
            self._value_combo.addItem(str(value), value)
        self._value_combo.currentIndexChanged.connect(self.changed.emit)
        self._value_layout.addWidget(self._value_combo)
    
    def _create_list_input(self):
        """Liste seçici (çoklu seçim) oluşturur"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        # Seçenekleri checkbox olarak göster (max 10)
        self._list_checkboxes = []
        values = self._current_column_info.unique_values[:20]
        
        for value in values:
            cb = QCheckBox(str(value))
            cb.setProperty("value", value)
            cb.stateChanged.connect(self.changed.emit)
            self._list_checkboxes.append(cb)
            layout.addWidget(cb)
        
        self._value_layout.addWidget(container)
    
    def _create_text_input(self):
        """Metin girişi oluşturur"""
        self._value_edit = QLineEdit()
        self._value_edit.setPlaceholderText("Değer girin...")
        self._value_edit.textChanged.connect(self.changed.emit)
        self._value_layout.addWidget(self._value_edit)
    
    def get_filter_model(self) -> Optional[FilterModel]:
        """Mevcut ayarlardan FilterModel oluşturur"""
        if self._current_column_info is None:
            return None
        
        operator = self._operator_combo.currentData()
        if operator is None:
            return None
        
        value = None
        value2 = None
        
        # Null operatörleri
        if operator in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
            pass
        
        # Sayısal
        elif self._current_column_info.column_type == ColumnType.NUMERIC:
            if hasattr(self, '_value1_spin'):
                value = self._value1_spin.value()
            if hasattr(self, '_value2_spin') and operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]:
                value2 = self._value2_spin.value()
        
        # Tarih
        elif self._current_column_info.column_type == ColumnType.DATE:
            if hasattr(self, '_value1_date'):
                qdate = self._value1_date.date()
                value = datetime(qdate.year(), qdate.month(), qdate.day())
            if hasattr(self, '_value2_date') and operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]:
                qdate = self._value2_date.date()
                value2 = datetime(qdate.year(), qdate.month(), qdate.day())
        
        # Boolean veya Kategorik
        elif hasattr(self, '_value_combo'):
            value = self._value_combo.currentData()
        
        # Liste
        elif hasattr(self, '_list_checkboxes'):
            value = [cb.property("value") for cb in self._list_checkboxes if cb.isChecked()]
            if not value:
                return None
        
        # Metin
        elif hasattr(self, '_value_edit'):
            value = self._value_edit.text()
            if not value and operator not in [FilterOperator.IS_NULL, FilterOperator.IS_NOT_NULL]:
                return None
        
        return FilterModel(
            column_name=self._current_column_info.name,
            operator=operator,
            value=value,
            value2=value2
        )


class FilterWidget(QWidget):
    """
    Filtre yönetimi widget'ı.
    Birden fazla filtre eklenmesini ve yönetilmesini sağlar.
    """
    
    filters_changed = pyqtSignal(list)  # List[FilterModel]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._column_infos: List[ColumnInfo] = []
        self._filter_widgets: List[SingleFilterWidget] = []
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Başlık ve ekle butonu
        header_layout = QHBoxLayout()
        
        title = QLabel("🔍 Filtreler")
        title.setObjectName("sectionLabel")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self._add_btn = QPushButton("+ Filtre Ekle")
        self._add_btn.setObjectName("addFilterButton")
        self._add_btn.setEnabled(False)
        self._add_btn.clicked.connect(self._add_filter)
        header_layout.addWidget(self._add_btn)
        
        main_layout.addLayout(header_layout)
        
        # Scroll area for filters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        
        self._filters_container = QWidget()
        self._filters_layout = QVBoxLayout(self._filters_container)
        self._filters_layout.setSpacing(10)
        self._filters_layout.addStretch()
        
        scroll.setWidget(self._filters_container)
        main_layout.addWidget(scroll)
        
        # Filtreleri uygula butonu
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._clear_btn = QPushButton("Temizle")
        self._clear_btn.setObjectName("dangerButton")
        self._clear_btn.clicked.connect(self._clear_filters)
        btn_layout.addWidget(self._clear_btn)
        
        self._apply_btn = QPushButton("Filtreleri Uygula")
        self._apply_btn.setObjectName("primaryButton")
        self._apply_btn.clicked.connect(self._apply_filters)
        btn_layout.addWidget(self._apply_btn)
        
        main_layout.addLayout(btn_layout)
    
    def set_column_infos(self, column_infos: List[ColumnInfo]):
        """Sütun bilgilerini günceller"""
        self._column_infos = column_infos
        self._add_btn.setEnabled(len(column_infos) > 0)
        self._clear_filters()
    
    def _add_filter(self):
        """Yeni filtre ekler"""
        if not self._column_infos:
            return
        
        filter_widget = SingleFilterWidget(self._column_infos)
        filter_widget.removed.connect(self._remove_filter)
        filter_widget.changed.connect(self._on_filter_changed)
        
        self._filter_widgets.append(filter_widget)
        self._filters_layout.insertWidget(self._filters_layout.count() - 1, filter_widget)
    
    def _remove_filter(self, widget: SingleFilterWidget):
        """Filtreyi kaldırır"""
        if widget in self._filter_widgets:
            self._filter_widgets.remove(widget)
            widget.deleteLater()
            self._on_filter_changed()
    
    def _clear_filters(self):
        """Tüm filtreleri temizler"""
        for widget in self._filter_widgets:
            widget.deleteLater()
        self._filter_widgets.clear()
        self.filters_changed.emit([])
    
    def _on_filter_changed(self):
        """Herhangi bir filtre değiştiğinde çağrılır"""
        pass  # Otomatik uygulama istenirse burada yapılabilir
    
    def _apply_filters(self):
        """Filtreleri uygular"""
        filters = self.get_filters()
        self.filters_changed.emit(filters)
    
    def get_filters(self) -> List[FilterModel]:
        """Tüm geçerli filtreleri döndürür"""
        filters = []
        for widget in self._filter_widgets:
            filter_model = widget.get_filter_model()
            if filter_model is not None:
                filters.append(filter_model)
        return filters
