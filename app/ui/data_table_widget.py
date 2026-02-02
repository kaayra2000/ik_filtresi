"""
Veri tablosu widget'ı - DataFrame'i görüntüler
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QLabel, QHBoxLayout,
    QToolButton, QFileDialog, QHeaderView, QMessageBox, QComboBox, QPushButton
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant, QSize, QSortFilterProxyModel
from PyQt6.QtGui import QColor, QIcon, QPixmap
from typing import Optional
from pathlib import Path
from app.ui.icon_factory import IconFactory

import pandas as pd
import numpy as np
from app.services.file_handler import FileIORegistry


class PandasTableModel(QAbstractTableModel):
    """
    Pandas DataFrame için Qt tablo modeli.
    Liskov Substitution: QAbstractTableModel'in yerine geçebilir.
    """
    
    def __init__(self, df: pd.DataFrame = None, parent=None):
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()
        self._column_infos = []

    def set_column_infos(self, column_infos):
        """Provide ColumnInfo list for header tooltips."""
        self._column_infos = column_infos or []
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df)
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df.columns)
    
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iloc[index.row(), index.column()]
            
            # Pandas NaT ve NaN kontrolü
            if pd.isna(value):
                return ""
            
            return str(value)
        
        elif role == Qt.ItemDataRole.BackgroundRole:
            # Alternatif satır renklendirmesi
            if index.row() % 2 == 0:
                return QColor(248, 249, 250)
        
        # Sıralama için ham veri döndür
        elif role == Qt.ItemDataRole.UserRole:
            value = self._df.iloc[index.row(), index.column()]
            # NaN/NaT değerleri sıralamada en sona koymak için
            if pd.isna(value):
                return None
            return value
        
        return QVariant()
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        # Display label
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if section < len(self._df.columns):
                    return str(self._df.columns[section])
            else:
                return str(section + 1)

        # Tooltip for header: show column summary if available
        if role == Qt.ItemDataRole.ToolTipRole and orientation == Qt.Orientation.Horizontal:
            if section < len(self._df.columns) and section < len(self._column_infos):
                ci = self._column_infos[section]
                parts = [f"Tür: {ci.column_type.name}"]
                parts.append(f"Boş: {ci.null_count}")
                parts.append(f"Benzersiz: {ci.unique_count}")
                if ci.column_type.name in ("NUMERIC", "DATE"):
                    try:
                        parts.append(f"Aralık: {ci.get_display_range()}")
                    except Exception:
                        pass
                return " | ".join(parts)

        return QVariant()
    
    def set_dataframe(self, df: pd.DataFrame):
        """DataFrame'i günceller"""
        self.beginResetModel()
        self._df = df
        self.endResetModel()
    
    def get_dataframe(self) -> pd.DataFrame:
        """Mevcut DataFrame'i döndürür"""
        return self._df


class PandasSortProxyModel(QSortFilterProxyModel):
    """
    Pandas DataFrame için özelleştirilmiş sıralama proxy modeli.
    Sayısal ve tarih verilerini doğru şekilde sıralar.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSortRole(Qt.ItemDataRole.UserRole)
    
    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """İki değeri karşılaştırır - sayısal ve tarih sıralaması için özelleştirilmiş"""
        left_data = self.sourceModel().data(left, Qt.ItemDataRole.UserRole)
        right_data = self.sourceModel().data(right, Qt.ItemDataRole.UserRole)
        
        # None değerlerini en sona koy
        if left_data is None and right_data is None:
            return False
        if left_data is None:
            return False  # None değerler sonda
        if right_data is None:
            return True   # None olmayan değerler önde
        
        # Aynı tip ise doğrudan karşılaştır
        try:
            # Sayısal karşılaştırma
            if isinstance(left_data, (int, float, np.integer, np.floating)):
                if isinstance(right_data, (int, float, np.integer, np.floating)):
                    return float(left_data) < float(right_data)
            
            # Tarih karşılaştırma
            if isinstance(left_data, (pd.Timestamp, np.datetime64)):
                if isinstance(right_data, (pd.Timestamp, np.datetime64)):
                    return left_data < right_data
            
            # String karşılaştırma (büyük/küçük harf duyarsız)
            if isinstance(left_data, str) and isinstance(right_data, str):
                return left_data.lower() < right_data.lower()
            
            # Genel karşılaştırma
            return str(left_data).lower() < str(right_data).lower()
        except (TypeError, ValueError):
            # Karşılaştırılamayan tipler için string karşılaştırma
            return str(left_data).lower() < str(right_data).lower()


class DataTableWidget(QWidget):
    """
    DataFrame'i görüntüleyen ve dışa aktarma yapabilen widget.
    Single Responsibility: Sadece veri görüntüleme ve export.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_df: Optional[pd.DataFrame] = None
        self._filtered_df: Optional[pd.DataFrame] = None
        self._column_infos = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header - only stats label, no title
        header_layout = QHBoxLayout()
        
        header_layout.addStretch()
        
        self._stats_label = QLabel()
        # use muted property to apply shared style from style.qss
        self._stats_label.setProperty("muted", True)
        self._stats_label.setToolTip("Filtreleme sonucu görüntülenen ve toplam kayıt sayısı")
        header_layout.addWidget(self._stats_label)
        
        layout.addLayout(header_layout)
        
        # Tablo
        self._table_view = QTableView()
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self._table_view.setToolTip("Sütun başlıklarına tıklayarak sıralayabilirsiniz")
        
        # Kaynak model
        self._model = PandasTableModel()
        
        # Sıralama için proxy model
        self._proxy_model = PandasSortProxyModel()
        self._proxy_model.setSourceModel(self._model)
        
        self._table_view.setModel(self._proxy_model)
        # Varsayılan olarak sıralama göstergesini gizle (ilk tıklamada görünür olur)
        self._table_view.horizontalHeader().setSortIndicatorShown(True)
        
        layout.addWidget(self._table_view)
        
        # Export butonları
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self._format_combo = QComboBox()
        # Label for the format combo (placed to the left)
        self._format_label = QLabel("Kaydetme türü:")
        # apply shared muted label style via property
        self._format_label.setProperty("muted", True)
        self._format_label.setContentsMargins(0, 0, 6, 0)
        export_layout.addWidget(self._format_label)

        self._populate_format_combo()
        self._format_combo.setEnabled(False)
        self._format_combo.setToolTip("Dışa aktarılacak dosya biçimini seçin")
        export_layout.addWidget(self._format_combo)
        
        # use a QPushButton with icon for save
        self._save_btn = QPushButton("Kaydet")
        self._save_btn.setIcon(IconFactory.load_icon("save.svg"))
        self._save_btn.setObjectName("saveButton")
        self._save_btn.setToolTip("Filtrelenmiş veriyi seçili biçimde dosyaya kaydet")
        self._save_btn.clicked.connect(self._on_save_clicked)
        self._save_btn.setEnabled(False)
        export_layout.addWidget(self._save_btn)
        
        layout.addLayout(export_layout)
    
    def _populate_format_combo(self):
        """Format combo box'ı FileIORegistry'den dinamik olarak doldurur (SRP)."""
        for desc in FileIORegistry.get_format_descriptors():
            idx = self._format_combo.count()
            self._format_combo.addItem(desc['name'])
            self._format_combo.setItemData(idx, desc, Qt.ItemDataRole.UserRole)
    
    def set_dataframe(self, df: pd.DataFrame):
        """Orijinal DataFrame'i ayarlar"""
        self._original_df = df
        self._filtered_df = df
        self._model.set_dataframe(df)
        self._update_stats()
        self._format_combo.setEnabled(True)
        self._save_btn.setEnabled(True)

    def set_column_infos(self, column_infos):
        """Keep column infos to provide header tooltips via model."""
        self._column_infos = column_infos or []
        try:
            self._model.set_column_infos(self._column_infos)
        except Exception:
            pass
    
    def set_filtered_dataframe(self, df: pd.DataFrame):
        """Filtrelenmiş DataFrame'i ayarlar"""
        self._filtered_df = df
        self._model.set_dataframe(df)
        self._update_stats()
    
    def reset_to_original(self):
        """Orijinal veriyi gösterir"""
        if self._original_df is not None:
            self._filtered_df = self._original_df
            self._model.set_dataframe(self._original_df)
            self._update_stats()
    
    def _update_stats(self):
        """İstatistikleri günceller"""
        if self._filtered_df is None:
            self._stats_label.setText("")
            return
        
        total = len(self._original_df) if self._original_df is not None else 0
        filtered = len(self._filtered_df)
        
        if total == filtered:
            self._stats_label.setText(f"Toplam: {total} kayıt")
        else:
            self._stats_label.setText(f"Gösterilen: {filtered} / {total} kayıt")
    
    def _on_save_clicked(self):
        """Kaydet butonuna tıklandığında"""
        idx = self._format_combo.currentIndex()
        if idx < 0:
            return

        desc = self._format_combo.itemData(idx, Qt.ItemDataRole.UserRole)
        if not desc:
            return

        file_filter = desc.get('filter', '')
        default_suffix = desc.get('default', '')

        self._export_data_with_filter(file_filter, default_suffix)
    
    def _export_data(self, format_type: str):
        """Menüden çağrılan export metodu - format türüne göre kaydetme yapar.
        
        FileIORegistry'den dinamik olarak format bilgilerini alır (OCP uyumlu).
        """
        desc = FileIORegistry.get_descriptor_by_extension(format_type)
        
        if desc:
            self._export_data_with_filter(desc['filter'], desc['default'])
        else:
            QMessageBox.warning(self, "Uyarı", f"Desteklenmeyen format: {format_type}")
    
    def _export_data_with_filter(self, file_filter: str, default_suffix: str):
        """Veriyi dosyaya aktarır"""
        if self._filtered_df is None or len(self._filtered_df) == 0:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak veri yok!")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Dosyayı Kaydet",
            "",
            file_filter
        )
        
        if not file_path:
            return
        
        # Uzantı yoksa ekle
        if not file_path.endswith(default_suffix):
            file_path += default_suffix
        
        try:
            FileIORegistry.write_file(self._filtered_df, Path(file_path))
            
            QMessageBox.information(
                self,
                "Başarılı",
                f"Dosya başarıyla kaydedildi:\n{file_path}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Hata",
                f"Dosya kaydedilemedi:\n{str(e)}"
            )
    
    def get_current_dataframe(self) -> Optional[pd.DataFrame]:
        """Mevcut (filtrelenmiş) DataFrame'i döndürür"""
        return self._filtered_df
