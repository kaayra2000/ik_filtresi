"""
Filtre widget'ı - Filtreleme arayüzü

Composite Pattern kullanılarak hiyerarşik filtre yapısı desteklenir.
Filtreler ve Filtre Grupları rekürsif olarak eklenebilir.
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QComboBox,
    QLineEdit,
    QFrame,
    QScrollArea,
    QDateEdit,
    QDoubleSpinBox,
    QMessageBox,
    QCheckBox,
    QSizePolicy,
    QDialog,
    QDialogButtonBox,
)
from PyQt6.QtWidgets import QFileDialog, QGridLayout
from PyQt6.QtCore import pyqtSignal, QDate, QSize, Qt
from PyQt6.QtGui import QIcon, QPixmap
from pathlib import Path
from app.ui.icon_factory import IconFactory
from typing import List, Optional, Any
from datetime import datetime

from app.models.column_info import ColumnInfo, ColumnType
from app.models.filter_model import (
    FilterModel,
    FilterOperator,
    FilterGroup,
    FilterComponent,
    LogicalOperator,
    component_from_dict,
)
from app.services.filter_persistence import FilterPersistence


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
        spin.setToolTip("Sayısal değer girin veya okları kullanın")
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

        self.date1 = self._create_date_edit(
            default_val=min_val, min_val=min_val, max_val=max_val
        )
        self.layout.addWidget(self.date1)

        if is_range:
            self.layout.addWidget(QLabel("-"))
            self.date2 = self._create_date_edit(
                default_val=max_val, min_val=min_val, max_val=max_val
            )
            # Ensure start <= end
            self.date1.dateChanged.connect(lambda qd: self.date2.setMinimumDate(qd))
            self.date2.dateChanged.connect(lambda qd: self.date1.setMaximumDate(qd))
            self.layout.addWidget(self.date2)

    def _create_date_edit(self, default_val=None, min_val=None, max_val=None):
        edit = QDateEdit()
        edit.setCalendarPopup(True)
        edit.setDisplayFormat("dd.MM.yyyy")
        edit.setToolTip("Tarih seçmek için tıklayın veya manuel girin (GG.AA.YYYY)")
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
        self.combo.setToolTip("Mantıksal değer seçin (Evet/Hayır)")
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
        self.combo.setToolTip("Mevcut değerlerden birini seçin")
        for val in unique_values:
            self.combo.addItem(str(val), val)
        self.combo.currentIndexChanged.connect(self.changed.emit)
        self.layout.addWidget(self.combo)

    def get_value(self) -> Any:
        return self.combo.currentData()


class ListInput(FilterValueInput):
    """Çok sayıda kategorik değer için geliştirilmiş liste seçici.

    Özellikler:
    - Arama/filtreleme kutusu
    - Kaydırılabilir liste (maksimum yükseklik sınırı)
    - Tümünü Seç / Temizle butonları
    - Seçim sayısı özeti
    """

    MAX_VISIBLE_HEIGHT = 200  # Maksimum liste yüksekliği (piksel)

    def __init__(self, unique_values: List[Any], parent=None):
        super().__init__(parent)
        self.checkboxes = []
        self._unique_values = unique_values

        # Ana container
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        # Üst kısım: Arama ve butonlar
        top_row = QHBoxLayout()
        top_row.setSpacing(5)

        # Arama kutusu
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("🔍 Ara...")
        self._search_edit.setToolTip("Değerleri filtrelemek için arama yapın")
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.textChanged.connect(self._filter_checkboxes)
        self._search_edit.setMaximumWidth(150)
        top_row.addWidget(self._search_edit)

        # Tümünü Seç butonu
        self._select_all_btn = QToolButton()
        self._select_all_btn.setText("✓ Tümü")
        self._select_all_btn.setToolTip("Görünen tüm değerleri seç")
        self._select_all_btn.clicked.connect(self._select_all_visible)
        top_row.addWidget(self._select_all_btn)

        # Temizle butonu
        self._clear_btn = QToolButton()
        self._clear_btn.setText("✗ Temizle")
        self._clear_btn.setToolTip("Tüm seçimleri kaldır")
        self._clear_btn.clicked.connect(self._clear_all)
        top_row.addWidget(self._clear_btn)

        top_row.addStretch()
        main_layout.addLayout(top_row)

        # Checkbox listesi için scroll area
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setMaximumHeight(self.MAX_VISIBLE_HEIGHT)
        self._scroll_area.setMinimumWidth(200)

        # Checkbox container
        checkbox_container = QWidget()
        self._checkbox_layout = QVBoxLayout(checkbox_container)
        self._checkbox_layout.setContentsMargins(5, 5, 5, 5)
        self._checkbox_layout.setSpacing(2)

        # Checkbox'ları oluştur
        for val in unique_values:
            cb = QCheckBox(str(val))
            cb.setProperty("value", val)
            cb.setToolTip(f"'{val}' değerini filtreye dahil et")
            cb.stateChanged.connect(self._on_checkbox_changed)
            self.checkboxes.append(cb)
            self._checkbox_layout.addWidget(cb)

        self._checkbox_layout.addStretch()
        self._scroll_area.setWidget(checkbox_container)
        main_layout.addWidget(self._scroll_area)

        # Alt kısım: Seçim özeti
        self._summary_label = QLabel()
        self._summary_label.setStyleSheet("color: #666; font-size: 11px;")
        main_layout.addWidget(self._summary_label)

        self.layout.addWidget(main_container)
        self._update_summary()

    def _filter_checkboxes(self, search_text: str):
        """Arama metnine göre checkbox'ları filtreler"""
        search_lower = search_text.lower()
        for cb in self.checkboxes:
            val_str = str(cb.property("value")).lower()
            cb.setVisible(search_lower in val_str)

    def _select_all_visible(self):
        """Görünen tüm checkbox'ları seçer"""
        for cb in self.checkboxes:
            if cb.isVisible():
                cb.setChecked(True)

    def _clear_all(self):
        """Tüm seçimleri kaldırır"""
        for cb in self.checkboxes:
            cb.setChecked(False)

    def _on_checkbox_changed(self):
        """Checkbox durumu değiştiğinde çağrılır"""
        self._update_summary()
        self.changed.emit()

    def _update_summary(self):
        """Seçim özetini günceller"""
        selected_count = sum(1 for cb in self.checkboxes if cb.isChecked())
        total_count = len(self.checkboxes)

        if selected_count == 0:
            self._summary_label.setText(f"Seçili: 0 / {total_count}")
        elif selected_count <= 3:
            # Az sayıda seçim varsa isimleri göster
            selected_names = [
                str(cb.property("value")) for cb in self.checkboxes if cb.isChecked()
            ]
            names_str = ", ".join(selected_names)
            if len(names_str) > 40:
                names_str = names_str[:37] + "..."
            self._summary_label.setText(f"Seçili ({selected_count}): {names_str}")
        else:
            self._summary_label.setText(f"Seçili: {selected_count} / {total_count}")

    def get_value(self) -> List[Any]:
        return [cb.property("value") for cb in self.checkboxes if cb.isChecked()]

    def set_selected_values(self, values: List[Any]):
        """Programatik olarak seçili değerleri ayarlar"""
        values_set = set(values)
        for cb in self.checkboxes:
            cb.setChecked(cb.property("value") in values_set)
        self._update_summary()


class TextInput(FilterValueInput):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.edit = QLineEdit()
        self.edit.setPlaceholderText("Değer girin...")
        self.edit.setToolTip("Filtrelemek istediğiniz metin değerini girin")
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
        self._column_combo.setToolTip("Filtrelemek istediğiniz sütunu seçin")
        self._column_combo.addItem("Sütun Seçin...", None)
        for info in self._column_infos:
            self._column_combo.addItem(str(info.name), info)
        self._column_combo.currentIndexChanged.connect(self._on_column_changed)
        self._main_layout.addWidget(self._column_combo)

        # Operatör seçici
        self._operator_combo = QComboBox()
        self._operator_combo.setMinimumWidth(120)
        self._operator_combo.setToolTip(
            "Karşılaştırma operatörünü seçin (eşittir, büyüktür, içerir vb.)"
        )
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

        # Kaldır butonu (küçük toolbutton) - ikon kullan
        remove_btn = IconFactory.create_tool_button("remove.svg")
        remove_btn.setObjectName("removeButton")
        remove_btn.setToolTip("Bu filtreyi kaldır")
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
            self._current_input = NumericInput(
                is_range,
                self._current_column_info.min_value,
                self._current_column_info.max_value,
            )
        elif col_type == ColumnType.DATE:
            self._current_input = DateInput(
                is_range,
                self._current_column_info.min_value,
                self._current_column_info.max_value,
            )
        elif col_type == ColumnType.BOOLEAN:
            self._current_input = BooleanInput()
        elif col_type == ColumnType.TEXT:
            if operator in [FilterOperator.IN_LIST, FilterOperator.NOT_IN_LIST]:
                self._current_input = ListInput(self._current_column_info.unique_values)
            elif (
                operator in [FilterOperator.EQUALS, FilterOperator.NOT_EQUALS]
                and self._current_column_info.is_categorical
            ):
                self._current_input = CategoricalInput(
                    self._current_column_info.unique_values
                )
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
            value2=value2,
        )

    def apply_filter_model(self, filter_model: FilterModel):
        """Programmatically set the widget state from a FilterModel"""
        # Set column
        target_col = filter_model.column_name
        idx = -1
        for i in range(self._column_combo.count()):
            data = self._column_combo.itemData(i)
            if data and getattr(data, "name", None) == target_col:
                idx = i
                break
        if idx >= 0:
            self._column_combo.setCurrentIndex(idx)
        # Set operator
        op = filter_model.operator
        for i in range(self._operator_combo.count()):
            if self._operator_combo.itemData(i) == op:
                self._operator_combo.setCurrentIndex(i)
                break
        # Now inputs should be created
        if self._current_input is None:
            return
        val = filter_model.value
        val2 = filter_model.value2
        # Numeric
        if isinstance(self._current_input, NumericInput):
            try:
                if val is not None:
                    self._current_input.spin1.setValue(float(val))
                if val2 is not None and hasattr(self._current_input, "spin2"):
                    self._current_input.spin2.setValue(float(val2))
            except Exception:
                pass
        # Date
        elif isinstance(self._current_input, DateInput):
            from PyQt6.QtCore import QDate

            try:
                if isinstance(val, datetime):
                    self._current_input.date1.setDate(
                        QDate(val.year, val.month, val.day)
                    )
                if (
                    val2 is not None
                    and isinstance(val2, datetime)
                    and hasattr(self._current_input, "date2")
                ):
                    self._current_input.date2.setDate(
                        QDate(val2.year, val2.month, val2.day)
                    )
            except Exception:
                pass
        # Boolean
        elif isinstance(self._current_input, BooleanInput):
            for i in range(self._current_input.combo.count()):
                if self._current_input.combo.itemData(i) == val:
                    self._current_input.combo.setCurrentIndex(i)
                    break
        # Categorical
        elif isinstance(self._current_input, CategoricalInput):
            for i in range(self._current_input.combo.count()):
                if self._current_input.combo.itemData(i) == val:
                    self._current_input.combo.setCurrentIndex(i)
                    break
        # List
        elif isinstance(self._current_input, ListInput):
            try:
                values = list(val or [])
                self._current_input.set_selected_values(values)
            except Exception:
                pass
        # Text
        elif isinstance(self._current_input, TextInput):
            if val is not None:
                self._current_input.edit.setText(str(val))


class FilterGroupWidget(QFrame):
    """
    Composite Pattern - Bir filtre grubunu temsil eden widget.

    İçinde:
    - Mantıksal operatör seçici (AND/OR)
    - Filtre widget'ları (SingleFilterWidget)
    - Alt grup widget'ları (FilterGroupWidget - rekürsif)

    Bu yapı rekürsif olarak çalışır ve karmaşık filtre ifadeleri oluşturmayı sağlar:
    Örnek: (A OR B) AND (C OR D)
    """

    removed = pyqtSignal(object)  # self'i emit eder
    changed = pyqtSignal()

    # Renk şeması - derinliğe göre farklı renkler
    GROUP_COLORS = [
        "#e3f2fd",  # Mavi - depth 0
        "#fff3e0",  # Turuncu - depth 1
        "#e8f5e9",  # Yeşil - depth 2
        "#fce4ec",  # Pembe - depth 3
        "#f3e5f5",  # Mor - depth 4
    ]

    def __init__(
        self,
        column_infos: List[ColumnInfo],
        depth: int = 0,
        parent_widget: Optional["FilterGroupWidget"] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._column_infos = column_infos
        self._depth = depth
        self._parent_widget = parent_widget
        self._children: List[QWidget] = []  # SingleFilterWidget veya FilterGroupWidget
        self._operator_combos: List[QComboBox] = (
            []
        )  # Her çocuk için önceki operatör (ilk hariç)
        self._group_id = None  # FilterGroup için ID
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("filterGroupFrame")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Derinliğe göre farklı objectName - tema QSS'i bunu kullanacak
        depth_name = f"filterGroupDepth{self._depth % 5}"
        self.setProperty("depth", self._depth % 5)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Üst bar - grup başlığı ve butonlar
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        # Grup ikonu
        group_icon_label = QLabel()
        group_icon_label.setPixmap(IconFactory.load_icon("group.svg").pixmap(18, 18))
        group_icon_label.setToolTip(
            "Filtre grubu - içindeki filtreler VE/VEYA ile birleştirilebilir"
        )
        header_layout.addWidget(group_icon_label)

        # Grup etiketi
        depth_label = QLabel(f"Grup (Seviye {self._depth})")
        depth_label.setObjectName("groupDepthLabel")
        depth_label.setToolTip(
            f"Bu grup {self._depth}. seviyede, iç içe gruplar oluşturabilirsiniz"
        )
        header_layout.addWidget(depth_label)

        header_layout.addStretch()

        # Filtre ekle butonu
        add_filter_btn = IconFactory.create_tool_button("add_filter.svg", "Filtre Ekle")
        add_filter_btn.setToolTip(
            "Bu gruba yeni bir filtre koşulu ekle (sütun, operatör, değer)"
        )
        add_filter_btn.clicked.connect(self._add_filter)
        header_layout.addWidget(add_filter_btn)

        # Alt grup ekle butonu
        add_group_btn = IconFactory.create_tool_button("add_group.svg", "Grup Ekle")
        add_group_btn.setToolTip(
            "Karmaşık filtreler için yeni bir alt grup ekle (örn: (A VE B) VEYA (C VE D))"
        )
        add_group_btn.clicked.connect(self._add_group)
        header_layout.addWidget(add_group_btn)

        # Grubu kaldır butonu (kök grup hariç)
        if self._depth > 0:
            remove_btn = IconFactory.create_tool_button("remove.svg", "Grubu Kaldır")
            remove_btn.setToolTip("Bu grubu ve içindeki tüm filtreleri kaldır")
            remove_btn.setObjectName("removeButton")
            remove_btn.clicked.connect(lambda: self.removed.emit(self))
            header_layout.addWidget(remove_btn)

        main_layout.addLayout(header_layout)

        # Ayırıcı çizgi
        separator = QFrame()
        separator.setObjectName("groupSeparator")
        separator.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(separator)

        # Çocuk elemanlar için container
        self._children_container = QWidget()
        self._children_layout = QVBoxLayout(self._children_container)
        self._children_layout.setSpacing(4)
        self._children_layout.setContentsMargins(0, 0, 0, 0)
        self._children_layout.addStretch()

        main_layout.addWidget(self._children_container)

    def _create_operator_combo(self) -> QComboBox:
        """Operatör seçici oluşturur"""
        combo = QComboBox()
        combo.setObjectName("logicalOperatorCombo")
        combo.setFixedWidth(80)
        combo.addItem("VE", LogicalOperator.AND)
        combo.addItem("VEYA", LogicalOperator.OR)
        combo.setCurrentIndex(0)  # Varsayılan: VE
        combo.setToolTip(
            "VE: Her iki koşul da sağlanmalı | VEYA: Koşullardan biri yeterli"
        )
        combo.currentIndexChanged.connect(self._on_operator_changed)
        return combo

    def _create_operator_row(self) -> QWidget:
        """Operatör satırı oluşturur (VE/VEYA seçici)"""
        row = QWidget()
        row.setObjectName("operatorRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(20, 2, 20, 2)
        row_layout.setSpacing(8)

        # Sol çizgi
        left_line = QFrame()
        left_line.setObjectName("operatorLine")
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFixedHeight(2)
        row_layout.addWidget(left_line, 1)

        # Operatör combo
        combo = self._create_operator_combo()
        row_layout.addWidget(combo)

        # Sağ çizgi
        right_line = QFrame()
        right_line.setObjectName("operatorLine")
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFixedHeight(2)
        row_layout.addWidget(right_line, 1)

        row.operator_combo = combo
        return row

    def _on_operator_changed(self, index: int):
        """Operatör değiştiğinde"""
        self.changed.emit()

    def _add_filter(self):
        """Yeni filtre ekler"""
        if not self._column_infos:
            return

        # İlk eleman değilse önce operatör satırı ekle
        operator_row = None
        if self._children:
            operator_row = self._create_operator_row()
            self._operator_combos.append(operator_row.operator_combo)
            self._children_layout.insertWidget(
                self._children_layout.count() - 1, operator_row
            )

        # Filtre widget'ı
        filter_widget = SingleFilterWidget(self._column_infos)
        filter_widget.removed.connect(
            lambda w: self._remove_child(filter_widget, operator_row)
        )
        filter_widget.changed.connect(self._on_child_changed)

        # Container tuple olarak sakla (widget, operator_row)
        container = QWidget()
        container.filter_widget = filter_widget
        container.operator_row = operator_row

        self._children.append(container)
        self._children_layout.insertWidget(
            self._children_layout.count() - 1, filter_widget
        )
        self.changed.emit()

    def _add_group(self):
        """Yeni alt grup ekler"""
        if not self._column_infos:
            return

        # İlk eleman değilse önce operatör satırı ekle
        operator_row = None
        if self._children:
            operator_row = self._create_operator_row()
            self._operator_combos.append(operator_row.operator_combo)
            self._children_layout.insertWidget(
                self._children_layout.count() - 1, operator_row
            )

        # Grup widget'ı
        group_widget = FilterGroupWidget(
            self._column_infos, depth=self._depth + 1, parent_widget=self
        )
        group_widget.removed.connect(
            lambda w: self._remove_child(group_widget, operator_row)
        )
        group_widget.changed.connect(self._on_child_changed)

        # Container tuple olarak sakla
        container = QWidget()
        container.filter_widget = group_widget
        container.operator_row = operator_row

        self._children.append(container)
        self._children_layout.insertWidget(
            self._children_layout.count() - 1, group_widget
        )
        self.changed.emit()

    def _remove_child(self, widget: QWidget, operator_row: Optional[QWidget]):
        """Çocuk elemanı kaldırır"""
        # Container'ı bul
        container_to_remove = None
        idx = -1
        for i, container in enumerate(self._children):
            if container.filter_widget == widget:
                container_to_remove = container
                idx = i
                break

        if container_to_remove is None:
            return

        self._children.remove(container_to_remove)

        # Operatör satırını kaldır
        if operator_row:
            if operator_row.operator_combo in self._operator_combos:
                self._operator_combos.remove(operator_row.operator_combo)
            operator_row.deleteLater()

        # Widget'ı kaldır
        widget.deleteLater()

        # İlk eleman kaldırıldıysa ve başka eleman varsa, yeni ilk elemanın operatör satırını kaldır
        if idx == 0 and self._children:
            first_container = self._children[0]
            if first_container.operator_row:
                if first_container.operator_row.operator_combo in self._operator_combos:
                    self._operator_combos.remove(
                        first_container.operator_row.operator_combo
                    )
                first_container.operator_row.deleteLater()
                first_container.operator_row = None

        self.changed.emit()

    def _on_child_changed(self):
        """Çocuk değiştiğinde"""
        self.changed.emit()

    def clear(self):
        """Tüm çocukları temizler"""
        # Önce tüm widget'ları ve operatör satırlarını kaldır
        for i in range(self._children_layout.count() - 1, -1, -1):
            item = self._children_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                self._children_layout.removeWidget(widget)
                widget.deleteLater()

        self._children.clear()
        self._operator_combos.clear()

        # Stretch'i yeniden ekle
        self._children_layout.addStretch()
        self.changed.emit()

    def get_filter_group(self) -> FilterGroup:
        """
        Bu widget'tan FilterGroup modeli oluşturur.
        Rekürsif olarak tüm çocukları toplar.
        """
        group = FilterGroup(id=self._group_id or "")

        for i, container in enumerate(self._children):
            child_widget = container.filter_widget

            # Operatörü al (ilk eleman hariç)
            operator = LogicalOperator.AND
            if (
                i > 0
                and container.operator_row
                and container.operator_row.operator_combo
            ):
                operator = container.operator_row.operator_combo.currentData()

            if isinstance(child_widget, SingleFilterWidget):
                filter_model = child_widget.get_filter_model()
                if filter_model is not None:
                    group.add(filter_model, operator)
            elif isinstance(child_widget, FilterGroupWidget):
                child_group = child_widget.get_filter_group()
                if not child_group.is_empty():
                    group.add(child_group, operator)

        return group

    def apply_filter_group(self, group: FilterGroup):
        """
        FilterGroup modelinden widget durumunu ayarlar.
        """
        self.clear()

        self._group_id = group.id

        # Çocukları ekle (FilterItems üzerinden iterasyon)
        for i, item in enumerate(group.items):
            child = item.component
            operator = item.preceding_operator or LogicalOperator.AND

            if isinstance(child, FilterModel):
                # İlk eleman değilse operatör satırı ekle
                operator_row = None
                if self._children:
                    operator_row = self._create_operator_row()
                    # Operatörü ayarla
                    for j in range(operator_row.operator_combo.count()):
                        if operator_row.operator_combo.itemData(j) == operator:
                            operator_row.operator_combo.setCurrentIndex(j)
                            break
                    self._operator_combos.append(operator_row.operator_combo)
                    self._children_layout.insertWidget(
                        self._children_layout.count() - 1, operator_row
                    )

                filter_widget = SingleFilterWidget(self._column_infos)
                filter_widget.removed.connect(
                    lambda w, op_row=operator_row: self._remove_child(w, op_row)
                )
                filter_widget.changed.connect(self._on_child_changed)

                container = QWidget()
                container.filter_widget = filter_widget
                container.operator_row = operator_row

                self._children.append(container)
                self._children_layout.insertWidget(
                    self._children_layout.count() - 1, filter_widget
                )
                filter_widget.apply_filter_model(child)

            elif isinstance(child, FilterGroup):
                # İlk eleman değilse operatör satırı ekle
                operator_row = None
                if self._children:
                    operator_row = self._create_operator_row()
                    # Operatörü ayarla
                    for j in range(operator_row.operator_combo.count()):
                        if operator_row.operator_combo.itemData(j) == operator:
                            operator_row.operator_combo.setCurrentIndex(j)
                            break
                    self._operator_combos.append(operator_row.operator_combo)
                    self._children_layout.insertWidget(
                        self._children_layout.count() - 1, operator_row
                    )

                group_widget = FilterGroupWidget(
                    self._column_infos, depth=self._depth + 1, parent_widget=self
                )
                group_widget.removed.connect(
                    lambda w, op_row=operator_row: self._remove_child(w, op_row)
                )
                group_widget.changed.connect(self._on_child_changed)

                container = QWidget()
                container.filter_widget = group_widget
                container.operator_row = operator_row

                self._children.append(container)
                self._children_layout.insertWidget(
                    self._children_layout.count() - 1, group_widget
                )
                group_widget.apply_filter_group(child)

    def get_display_string(self) -> str:
        """Filtre grubunun görüntüleme metnini döndürür"""
        group = self.get_filter_group()
        return group.to_display_string()


class FilterDialog(QDialog):
    """
    Modal filtre düzenleme penceresi.

    Ana pencereden bağımsız açılır ve modal olarak çalışır
    (açıkken ana pencereyle etkileşim engellenir).
    """

    SUMMARY_MAX_LENGTH = 120  # Özet için maksimum karakter

    def __init__(
        self,
        column_infos: List[ColumnInfo],
        current_group: Optional[FilterGroup] = None,
        parent=None,
    ):
        super().__init__(parent)
        self._column_infos = column_infos
        self._initial_group = current_group
        self._root_group: Optional[FilterGroupWidget] = None
        self._result_group: Optional[FilterGroup] = None

        self.setWindowTitle("🔍 Filtre Düzenleyici")
        self.setModal(True)  # Modal dialog - ana pencere ile etkileşim engellenir
        self.setMinimumSize(700, 500)
        self.resize(800, 600)

        self._setup_ui()
        self._create_root_group()

        # Mevcut filtreleri yükle
        if current_group and not current_group.is_empty():
            self._root_group.apply_filter_group(current_group)

        self._update_summary()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Scroll area for filter groups
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setObjectName("filterScrollArea")

        self._scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(5, 5, 5, 5)
        self._scroll_layout.addStretch()

        self._scroll.setWidget(self._scroll_content)
        layout.addWidget(self._scroll)

        self._summary_label = QLabel("Henüz filtre eklenmedi")
        self._summary_label.setObjectName("summaryContent")
        self._summary_label.setWordWrap(True)
        self._summary_label.setToolTip("Aktif filtrelerin özeti")

        layout.addWidget(self._summary_label)

        # Alt butonlar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        # Kaydet butonu
        self._save_btn = IconFactory.create_tool_button("save_filters.svg", "Kaydet")
        self._save_btn.setObjectName("saveFilterButton")
        self._save_btn.setToolTip("Mevcut filtreleri JSON dosyasına kaydet")
        self._save_btn.clicked.connect(self._save_filters_to_file)
        button_layout.addWidget(self._save_btn)

        # Yükle butonu
        self._load_btn = IconFactory.create_tool_button("load_from_file.svg", "Yükle")
        self._load_btn.setObjectName("loadFilterButton")
        self._load_btn.setToolTip("JSON dosyasından filtre yükle")
        self._load_btn.clicked.connect(self._load_filters_from_file)
        button_layout.addWidget(self._load_btn)

        # Temizle butonu
        self._clear_btn = IconFactory.create_tool_button("clear.svg", "Temizle")
        self._clear_btn.setObjectName("dangerButton")
        self._clear_btn.setToolTip("Tüm filtreleri temizle")
        self._clear_btn.clicked.connect(self._clear_filters)
        button_layout.addWidget(self._clear_btn)

        button_layout.addStretch()

        # İptal butonu
        self._cancel_btn = IconFactory.create_tool_button("clear.svg", "İptal")
        self._cancel_btn.setObjectName("cancelButton")
        self._cancel_btn.setToolTip(
            "Değişiklikleri kaydetmeden pencereyi kapat (Escape)"
        )
        self._cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self._cancel_btn)

        # Uygula butonu
        self._apply_btn = IconFactory.create_tool_button(
            "apply_filters.svg", "Filtreleri Uygula"
        )
        self._apply_btn.setObjectName("primaryButton")
        self._apply_btn.setToolTip("Filtreleri uygula ve pencereyi kapat")
        self._apply_btn.clicked.connect(self._apply_and_close)
        button_layout.addWidget(self._apply_btn)

        layout.addLayout(button_layout)

    def _update_summary(self):
        """Filtre özetini günceller"""
        if not self._root_group:
            summary = "Henüz filtre eklenmedi"
        else:
            group = self._root_group.get_filter_group()
            if group.is_empty():
                summary = "Henüz filtre eklenmedi"
            else:
                summary = group.to_display_string()

        # Özeti kısalt ve tooltip ekle
        (
            self._summary_label.setText(summary[: self.SUMMARY_MAX_LENGTH] + "...")
            if len(summary) > self.SUMMARY_MAX_LENGTH
            else self._summary_label.setText(summary)
        )
        self._summary_label.setToolTip(summary)

    def _create_root_group(self):
        """Kök filtre grubunu oluşturur"""
        if self._root_group:
            self._root_group.deleteLater()

        if not self._column_infos:
            self._root_group = None
            return

        self._root_group = FilterGroupWidget(self._column_infos, depth=0)
        self._root_group.changed.connect(self._update_summary)
        self._scroll_layout.insertWidget(0, self._root_group)

    def _clear_filters(self):
        """Tüm filtreleri temizler"""
        if self._root_group:
            self._root_group.clear()
        self._update_summary()

    def _apply_and_close(self):
        """Filtreleri uygula ve pencereyi kapat"""
        if self._root_group:
            self._result_group = self._root_group.get_filter_group()
        else:
            self._result_group = FilterGroup()
        self.accept()

    def get_filter_group(self) -> FilterGroup:
        """Sonuç filtre grubunu döndürür"""
        return self._result_group if self._result_group else FilterGroup()

    def _save_filters_to_file(self):
        """Filtreleri JSON dosyasına kaydet"""
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Filtreleri Kaydet",
            filter="JSON dosyaları (*.json);;Tüm dosyalar (*)",
        )
        if not path:
            return

        try:
            persistence = FilterPersistence(path=path)
            group = (
                self._root_group.get_filter_group()
                if self._root_group
                else FilterGroup()
            )
            persistence.save_filter_group(group)
            QMessageBox.information(
                self, "Kaydedildi", f"Filtreler kaydedildi:\n{path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Kaydetme Hatası", f"Filtre kaydedilirken hata oluştu:\n{e}"
            )

    def _load_filters_from_file(self):
        """JSON dosyasından filtre yükle"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Filtre Dosyası Seçin",
            filter="JSON dosyaları (*.json);;Tüm dosyalar (*)",
        )
        if not path:
            return

        try:
            persistence = FilterPersistence(path=path)
            group = persistence.load_filter_group()

            if group is None or group.is_empty():
                QMessageBox.warning(
                    self, "Yükleme", "Dosyada geçerli filtre bulunamadı."
                )
                return

            if self._root_group:
                self._root_group.apply_filter_group(group)
            QMessageBox.information(self, "Yüklendi", "Filtreler başarıyla yüklendi.")

        except Exception as e:
            QMessageBox.critical(
                self, "Yükleme Hatası", f"Dosya yüklenirken hata oluştu:\n{e}"
            )


class FilterWidget(QWidget):
    """
    Filtre özet widget'ı - Ana pencerede görüntülenir.

    Tıklandığında modal FilterDialog açılır.
    Sadece filtre özetini ve hızlı uygulama butonunu gösterir.
    """

    filter_group_changed = pyqtSignal(object)  # FilterGroup

    SUMMARY_MAX_LENGTH = 100  # Özet için maksimum karakter

    def __init__(self, parent=None):
        super().__init__(parent)
        self._column_infos: List[ColumnInfo] = []
        self._current_group: FilterGroup = FilterGroup()
        self._current_summary = "Henüz filtre eklenmedi"
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === Tıklanabilir özet paneli ===
        self._summary_frame = QFrame()
        self._summary_frame.setObjectName("filterSummaryPanel")
        self._summary_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        frame_layout = QHBoxLayout(self._summary_frame)
        frame_layout.setContentsMargins(12, 12, 12, 12)
        frame_layout.setSpacing(12)

        # İkon
        icon_label = QLabel("🔍")
        icon_label.setObjectName("filterIcon")
        frame_layout.addWidget(icon_label)

        # Başlık ve özet
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title = QLabel("Filtreler")
        title.setObjectName("filterPanelTitle")
        text_layout.addWidget(title)

        self._summary_label = QLabel(self._current_summary)
        self._summary_label.setObjectName("filterPanelSummary")
        self._summary_label.setWordWrap(True)
        text_layout.addWidget(self._summary_label)

        frame_layout.addLayout(text_layout, 1)

        # Düzenle butonu
        self._edit_btn = IconFactory.create_tool_button("edit.svg", "")
        self._edit_btn.setObjectName("filterEditButton")
        self._edit_btn.setToolTip("Filtreleri düzenle")
        self._edit_btn.setFixedSize(36, 36)
        self._edit_btn.clicked.connect(self._open_filter_dialog)
        frame_layout.addWidget(self._edit_btn)

        # Hızlı uygula butonu
        self._quick_apply_btn = IconFactory.create_tool_button("apply_filters.svg", "")
        self._quick_apply_btn.setObjectName("quickApplyButton")
        self._quick_apply_btn.setToolTip("Filtreleri Uygula")
        self._quick_apply_btn.setFixedSize(36, 36)
        self._quick_apply_btn.clicked.connect(self._apply_filters)
        frame_layout.addWidget(self._quick_apply_btn)

        # Frame tıklama olayı
        self._summary_frame.mousePressEvent = self._on_frame_clicked

        main_layout.addWidget(self._summary_frame)

    def _on_frame_clicked(self, event):
        """Frame'e tıklandığında dialog aç"""
        # Butonlara tıklandığında tetiklenmemesi için pozisyon kontrolü
        click_pos = event.pos()
        edit_btn_rect = self._edit_btn.geometry()
        apply_btn_rect = self._quick_apply_btn.geometry()

        if not edit_btn_rect.contains(click_pos) and not apply_btn_rect.contains(
            click_pos
        ):
            self._open_filter_dialog()

    def _open_filter_dialog(self):
        """Modal filtre dialog'unu aç"""
        if not self._column_infos:
            QMessageBox.warning(self, "Uyarı", "Önce bir veri dosyası yükleyin.")
            return

        dialog = FilterDialog(self._column_infos, self._current_group, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._current_group = dialog.get_filter_group()
            self._update_summary()
            self.filter_group_changed.emit(self._current_group)

    def _apply_filters(self):
        """Mevcut filtreleri uygula"""
        self.filter_group_changed.emit(self._current_group)

    def _update_summary(self):
        """Filtre özetini günceller"""
        if self._current_group.is_empty():
            self._current_summary = "Filtre uygulanmadı - tıklayarak filtre ekleyin"
        else:
            self._current_summary = self._current_group.to_display_string()

        # Özeti kısalt ve tooltip ekle
        display_text = self._current_summary
        if len(display_text) > self.SUMMARY_MAX_LENGTH:
            display_text = display_text[: self.SUMMARY_MAX_LENGTH] + "..."
            self._summary_label.setToolTip(self._current_summary)
        else:
            self._summary_label.setToolTip("")

        self._summary_label.setText(display_text)

    def set_column_infos(self, column_infos: List[ColumnInfo]):
        """Sütun bilgilerini günceller"""
        self._column_infos = column_infos
        self._current_group = FilterGroup()
        self._update_summary()

    def get_filter_group(self) -> FilterGroup:
        """Filtre grubunu döndürür"""
        return self._current_group

    def set_filter_group(self, group: FilterGroup):
        """Filtre grubunu ayarlar"""
        self._current_group = group
        self._update_summary()
