"""
Veri tablosu widget'ı - DataFrame'i görüntüler
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableView, QLabel, QHBoxLayout,
    QWidget, QVBoxLayout, QTableView, QLabel, QHBoxLayout,
    QPushButton, QFileDialog, QHeaderView, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtGui import QColor
from typing import Optional
from pathlib import Path

import pandas as pd
from app.services.file_writer import FileWriterFactory


class PandasTableModel(QAbstractTableModel):
    """
    Pandas DataFrame için Qt tablo modeli.
    Liskov Substitution: QAbstractTableModel'in yerine geçebilir.
    """
    
    def __init__(self, df: pd.DataFrame = None, parent=None):
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()
    
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
        
        return QVariant()
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return QVariant()
        
        if orientation == Qt.Orientation.Horizontal:
            if section < len(self._df.columns):
                return str(self._df.columns[section])
        else:
            return str(section + 1)
        
        return QVariant()
    
    def set_dataframe(self, df: pd.DataFrame):
        """DataFrame'i günceller"""
        self.beginResetModel()
        self._df = df
        self.endResetModel()
    
    def get_dataframe(self) -> pd.DataFrame:
        """Mevcut DataFrame'i döndürür"""
        return self._df


class DataTableWidget(QWidget):
    """
    DataFrame'i görüntüleyen ve dışa aktarma yapabilen widget.
    Single Responsibility: Sadece veri görüntüleme ve export.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_df: Optional[pd.DataFrame] = None
        self._filtered_df: Optional[pd.DataFrame] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header_layout = QHBoxLayout()
        
        self._title = QLabel("📊 Veri Tablosu")
        self._title.setObjectName("sectionLabel")
        header_layout.addWidget(self._title)
        
        header_layout.addStretch()
        
        self._stats_label = QLabel()
        self._stats_label.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(self._stats_label)
        
        layout.addLayout(header_layout)
        
        # Tablo
        self._table_view = QTableView()
        self._table_view.setAlternatingRowColors(True)
        self._table_view.setSortingEnabled(True)
        self._table_view.horizontalHeader().setStretchLastSection(True)
        self._table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self._table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        
        self._model = PandasTableModel()
        self._table_view.setModel(self._model)
        
        layout.addWidget(self._table_view)
        
        # Export butonları
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        
        self._format_combo = QComboBox()
        self._format_combo.addItems(["Excel Dosyası (*.xlsx)", "CSV Dosyası (*.csv)"])
        self._format_combo.setEnabled(False)
        export_layout.addWidget(self._format_combo)
        
        self._save_btn = QPushButton("Kaydet")
        self._save_btn.clicked.connect(self._on_save_clicked)
        self._save_btn.setEnabled(False)
        export_layout.addWidget(self._save_btn)
        
        layout.addLayout(export_layout)
    
    def set_dataframe(self, df: pd.DataFrame):
        """Orijinal DataFrame'i ayarlar"""
        self._original_df = df
        self._filtered_df = df
        self._model.set_dataframe(df)
        self._update_stats()
        self._format_combo.setEnabled(True)
        self._save_btn.setEnabled(True)
    
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
        selected_index = self._format_combo.currentIndex()
        if selected_index == 0:
            self._export_data('xlsx')
        else:
            self._export_data('csv')

    def _export_data(self, format: str):
        """Veriyi dosyaya aktarır"""
        if self._filtered_df is None or len(self._filtered_df) == 0:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak veri yok!")
            return
        
        if format == 'csv':
            file_filter = "CSV Dosyaları (*.csv)"
            default_suffix = ".csv"
        else:
            file_filter = "Excel Dosyaları (*.xlsx)"
            default_suffix = ".xlsx"
        
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
            writer_factory = FileWriterFactory()
            writer_factory.write_file(self._filtered_df, Path(file_path))
            
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
