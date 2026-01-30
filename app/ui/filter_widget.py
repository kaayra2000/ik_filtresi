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
from typing import List, Optional, Any
from datetime import datetime

from app.models.column_info import ColumnInfo, ColumnType
from app.models.filter_model import FilterModel, FilterOperator


class FilterValueInput(QWidget):
    """Base class for filter value input widgets"""
    changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)

    def get_value(self) -> Any:
        raise NotImplementedError

    def get_value2(self) -> Any:
        return None

class NumericInput(FilterValueInput):
    def __init__(self, is_range: bool, min_val=None, max_val=None, parent=None):
        super().__init__(parent)
        self.is_range = is_range
        
        self.spin1 = self._create_spinbox(min_val, max_val)
        self.layout.addWidget(self.spin1)
        
        if is_range:
            self.layout.addWidget(QLabel("-"))
            self.spin2 = self._create_spinbox(min_val, max_val)
            # Keep range consistent: start <= end
            self.spin1.valueChanged.connect(lambda v: self.spin2.setMinimum(v))
            self.spin2.valueChanged.connect(lambda v: self.spin1.setMaximum(v))
            self.layout.addWidget(self.spin2)

    def _create_spinbox(self, min_val, max_val):
        spin = QDoubleSpinBox()
        spin.setDecimals(2)
        # Constrain to column min/max if available
        if min_val is not None and max_val is not None:
            spin.setRange(float(min_val), float(max_val))
        elif min_val is not None:
            spin.setMinimum(float(min_val))
        elif max_val is not None:
            spin.setMaximum(float(max_val))
        else:
            spin.setRange(-999999999, 999999999)
        # Set initial value
        if min_val is not None:
            spin.setValue(float(min_val))
        spin.valueChanged.connect(self.changed.emit)
        return spin

    def get_value(self) -> float:
        return self.spin1.value()

    def get_value2(self) -> Optional[float]:
        return self.spin2.value() if self.is_range else None

class DateInput(FilterValueInput):
    def __init__(self, is_range: bool, min_val=None, max_val=None, parent=None):
        super().__init__(parent)
        self.is_range = is_range

        self.date1 = self._create_date_edit(default_val=min_val, min_val=min_val, max_val=max_val)
        self.layout.addWidget(self.date1)

        if is_range:
            self.layout.addWidget(QLabel("-"))
            self.date2 = self._create_date_edit(default_val=max_val, min_val=min_val, max_val=max_val)
            # Ensure start <= end
            self.date1.dateChanged.connect(lambda qd: self.date2.setMinimumDate(qd))
            self.date2.dateChanged.connect(lambda qd: self.date1.setMaximumDate(qd))
            self.layout.addWidget(self.date2)

    def _create_date_edit(self, default_val=None, min_val=None, max_val=None):
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd.MM.yyyy")
        # set allowed range
        if isinstance(min_val, datetime):
            edit.setMinimumDate(QDate(min_val.year, min_val.month, min_val.day))
        if isinstance(max_val, datetime):
            edit.setMaximumDate(QDate(max_val.year, max_val.month, max_val.day))
        # initial date preference: default -> min -> current
        if default_val and isinstance(default_val, datetime):
            edit.setDate(QDate(default_val.year, default_val.month, default_val.day))
        elif isinstance(min_val, datetime):
            edit.setDate(QDate(min_val.year, min_val.month, min_val.day))
        else:
            edit.setDate(QDate.currentDate())
        edit.dateChanged.connect(self.changed.emit)
        return edit

    def get_value(self) -> datetime:
        qdate = self.date1.date()
        return datetime(qdate.year(), qdate.month(), qdate.day())

    def get_value2(self) -> Optional[datetime]:
        if not self.is_range:
            return None
        qdate = self.date2.date()
        return datetime(qdate.year(), qdate.month(), qdate.day())

class BooleanInput(FilterValueInput):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.combo = QComboBox()
        self.combo.addItem("Evet / True", True)
        self.combo.addItem("Hayır / False", False)
        self.combo.currentIndexChanged.connect(self.changed.emit)
        self.layout.addWidget(self.combo)

    def get_value(self) -> bool:
        return self.combo.currentData()

class CategoricalInput(FilterValueInput):
    def __init__(self, unique_values: List[Any], parent=None):
        super().__init__(parent)
        self.combo = QComboBox()
        for val in unique_values:
            self.combo.addItem(str(val), val)
        self.combo.currentIndexChanged.connect(self.changed.emit)
        self.layout.addWidget(self.combo)

    def get_value(self) -> Any:
        return self.combo.currentData()

class ListInput(FilterValueInput):
    def __init__(self, unique_values: List[Any], parent=None):
        super().__init__(parent)
        self.checkboxes = []
        
        container = QWidget()
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(2)
        
        for val in unique_values:
            cb = QCheckBox(str(val))
            cb.setProperty("value", val)
            cb.stateChanged.connect(self.changed.emit)
            self.checkboxes.append(cb)
            v_layout.addWidget(cb)
            
        self.layout.addWidget(container)

    def get_value(self) -> List[Any]:
        return [cb.property("value") for cb in self.checkboxes if cb.isChecked()]

class TextInput(FilterValueInput):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Değer girin...")
        self.edit.textChanged.connect(self.changed.emit)
        self.layout.addWidget(self.edit)

    def get_value(self) -> str:
        return self.edit.text()


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
            self._column_combo.addItem(str(info.name), info)
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
        
        self._current_input: Optional[FilterValueInput] = None
        
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
        
        # Uygun input widget'ını oluştur
        if col_type == ColumnType.NUMERIC:
            self._current_input = NumericInput(is_range, 
                                             self._current_column_info.min_value, 
                                             self._current_column_info.max_value)
        elif col_type == ColumnType.DATE:
            self._current_input = DateInput(is_range, 
                                          self._current_column_info.min_value, 
                                          self._current_column_info.max_value)
        elif col_type == ColumnType.BOOLEAN:
            self._current_input = BooleanInput()
        elif col_type == ColumnType.TEXT:
            if operator in [FilterOperator.IN_LIST, FilterOperator.NOT_IN_LIST]:
                self._current_input = ListInput(self._current_column_info.unique_values)
            elif operator in [FilterOperator.EQUALS, FilterOperator.NOT_EQUALS] and \
                 self._current_column_info.is_categorical:
                self._current_input = CategoricalInput(self._current_column_info.unique_values)
            else:
                self._current_input = TextInput()
        
        if self._current_input:
            self._current_input.changed.connect(self.changed.emit)
            self._value_layout.addWidget(self._current_input)
    
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
        
        elif self._current_input:
            value = self._current_input.get_value()
            value2 = self._current_input.get_value2()
            
            # Değer kontrolü (boş değerleri filtrele)
            if value is None or (isinstance(value, str) and not value):
                # Bazı operatörler boş değere izin verebilir mi? Genelde hayır.
                return None
            
            # Liste boşsa
            if isinstance(value, list) and not value:
                return None
        else:
            # Input yoksa ve null operatörü değilse geçersiz
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
