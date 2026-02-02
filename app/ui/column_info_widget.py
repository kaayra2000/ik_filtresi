"""
Sütun bilgi widget'ı - Sütunların özetini görüntüler
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QComboBox,
    QGroupBox,
)
from PyQt6.QtCore import Qt
from typing import List

from app.models.column_info import ColumnInfo, ColumnType


class ColumnInfoCard(QFrame):
    """Tek bir sütunun bilgi kartı"""

    def __init__(self, column_info: ColumnInfo, parent=None):
        super().__init__(parent)
        self.column_info = column_info
        self.setObjectName("columnInfoFrame")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(5)

        # Sütun adı
        name_label = QLabel(f"{self.column_info.name}")
        name_label.setObjectName("sectionLabel")
        name_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        name_label.setToolTip(f"Sütun adı: {self.column_info.name}")
        layout.addWidget(name_label)

        # Tip
        type_icons = {
            ColumnType.NUMERIC: "🔢",
            ColumnType.DATE: "📅",
            ColumnType.TEXT: "📝",
            ColumnType.BOOLEAN: "✓/✗",
            ColumnType.UNKNOWN: "❓",
        }
        type_names = {
            ColumnType.NUMERIC: "Sayısal",
            ColumnType.DATE: "Tarih",
            ColumnType.TEXT: "Metin",
            ColumnType.BOOLEAN: "Mantıksal",
            ColumnType.UNKNOWN: "Bilinmiyor",
        }

        icon = type_icons.get(self.column_info.column_type, "❓")
        type_name = type_names.get(self.column_info.column_type, "Bilinmiyor")
        type_label = QLabel(f"Tür: {icon} {type_name}")
        type_label.setToolTip(
            f"Veri türü: {type_name} - Filtreleme seçenekleri bu türe göre belirlenir"
        )
        layout.addWidget(type_label)

        # İstatistikler
        stats_text = f"Toplam: {self.column_info.total_count} | "
        stats_text += f"Boş: {self.column_info.null_count} | "
        stats_text += f"Benzersiz: {self.column_info.unique_count}"
        stats_label = QLabel(stats_text)
        stats_label.setProperty("muted", True)
        stats_label.setToolTip(
            "Toplam kayıt sayısı, boş değer sayısı ve tekil değer sayısı"
        )
        layout.addWidget(stats_label)

        # Tip'e göre ek bilgiler
        if self.column_info.column_type in [ColumnType.NUMERIC, ColumnType.DATE]:
            range_text = f"Aralık: {self.column_info.get_display_range()}"
            range_label = QLabel(range_text)
            range_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            range_label.setToolTip("Bu sütundaki asgari ve azami değerler")
            layout.addWidget(range_label)

        elif self.column_info.column_type == ColumnType.TEXT:
            if self.column_info.is_categorical and self.column_info.unique_count <= 20:
                # Kategorik değerler için combobox
                values_layout = QHBoxLayout()
                values_label = QLabel("Değerler:")
                values_label.setToolTip("Bu sütundaki tüm tekil değerler")
                values_layout.addWidget(values_label)

                combo = QComboBox()
                combo.setToolTip("Mevcut kategorik değerleri görmek için tıklayın")
                combo.addItems([str(v) for v in self.column_info.unique_values])
                combo.setMaximumWidth(200)
                values_layout.addWidget(combo)
                values_layout.addStretch()

                layout.addLayout(values_layout)
            else:
                unique_label = QLabel(
                    f"Benzersiz değer sayısı: {self.column_info.unique_count}"
                )
                unique_label.setProperty("muted", True)
                unique_label.setToolTip(
                    "Çok fazla tekil değer olduğundan kategorik olarak gösterilemiyor"
                )
                layout.addWidget(unique_label)


class ColumnInfoWidget(QWidget):
    """
    Tüm sütunların bilgilerini görüntüleyen widget.
    Single Responsibility: Sadece sütun bilgilerini görüntüler.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._column_infos: List[ColumnInfo] = []
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Başlık
        title = QLabel("Sütun Bilgileri")
        title.setObjectName("sectionLabel")
        main_layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setSpacing(10)
        self._content_layout.addStretch()

        scroll.setWidget(self._content_widget)
        main_layout.addWidget(scroll)

    def set_column_infos(self, column_infos: List[ColumnInfo]):
        """Sütun bilgilerini günceller"""
        self._column_infos = column_infos
        self._refresh_ui()

    def _refresh_ui(self):
        """UI'ı yeniden oluşturur"""
        # Mevcut kartları temizle
        while self._content_layout.count() > 1:  # Stretch'i koru
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Yeni kartları ekle
        for info in self._column_infos:
            card = ColumnInfoCard(info)
            self._content_layout.insertWidget(self._content_layout.count() - 1, card)

    def get_column_info(self, column_name: str) -> ColumnInfo:
        """Belirtilen sütunun bilgisini döndürür"""
        for info in self._column_infos:
            if info.name == column_name:
                return info
        return None

    @property
    def column_infos(self) -> List[ColumnInfo]:
        return self._column_infos


from PyQt6.QtWidgets import QDialog, QVBoxLayout


class ColumnInfoDialog(QDialog):
    """Modal dialog for showing column analysis."""

    def __init__(self, column_infos: List[ColumnInfo], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sütun Ayrıntıları")
        self.setModal(True)
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        self._widget = ColumnInfoWidget(self)
        layout.addWidget(self._widget)

        # initialize
        self.set_column_infos(column_infos)

    def set_column_infos(self, column_infos: List[ColumnInfo]):
        self._widget.set_column_infos(column_infos)
