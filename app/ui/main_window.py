"""
Ana pencere - Uygulamanın ana arayüzü
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QMessageBox, QSplitter, QStatusBar,
    QGroupBox, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction
from pathlib import Path
from typing import Optional, List

import pandas as pd

from app.services.file_reader import FileReaderFactory
from app.services.data_analyzer import DataAnalyzer
from app.services.filter_engine import FilterEngine
from app.models.column_info import ColumnInfo
from app.models.filter_model import FilterModel
from app.ui.column_info_widget import ColumnInfoWidget
from app.ui.filter_widget import FilterWidget
from app.ui.data_table_widget import DataTableWidget


class FileLoaderThread(QThread):
    """Dosya yükleme için arka plan thread'i"""
    
    finished = pyqtSignal(pd.DataFrame, list)  # df, column_infos
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, file_path: Path, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._factory = FileReaderFactory()
        self._analyzer = DataAnalyzer()
    
    def run(self):
        try:
            self.progress.emit("Dosya okunuyor...")
            df = self._factory.read_file(self._file_path)
            
            self.progress.emit("Sütunlar analiz ediliyor...")
            column_infos = self._analyzer.analyze(df)
            
            self.progress.emit("Tarih sütunları dönüştürülüyor...")
            df = self._analyzer.convert_date_columns(df, column_infos)
            
            # Tekrar analiz et (dönüştürme sonrası)
            column_infos = self._analyzer.analyze(df)
            
            self.finished.emit(df, column_infos)
            
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """
    Ana uygulama penceresi.
    Interface Segregation: Her widget kendi sorumluluğunu taşır.
    """
    
    def __init__(self):
        super().__init__()
        
        self._file_path: Optional[Path] = None
        self._df: Optional[pd.DataFrame] = None
        self._column_infos: List[ColumnInfo] = []
        
        self._file_reader = FileReaderFactory()
        self._filter_engine = FilterEngine()
        
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()
        
        # Uygulama açılınca dosya seç
        self._prompt_file_selection()
    
    def _setup_ui(self):
        """UI bileşenlerini oluşturur"""
        self.setWindowTitle("IK Filtresi - Veri Filtreleme Aracı")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Başlık ve dosya bilgisi
        header_layout = QHBoxLayout()
        
        title = QLabel("📋 IK Filtresi")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        self._file_label = QLabel("Dosya seçilmedi")
        self._file_label.setStyleSheet("color: #7f8c8d;")
        header_layout.addWidget(self._file_label)
        
        self._load_btn = QPushButton("📂 Dosya Yükle")
        self._load_btn.clicked.connect(self._prompt_file_selection)
        header_layout.addWidget(self._load_btn)
        
        main_layout.addLayout(header_layout)
        
        # Progress bar (gizli)
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setRange(0, 0)  # Indeterminate
        main_layout.addWidget(self._progress_bar)
        
        # Ana splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Sol panel - Sütun bilgileri ve filtreler
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sütun bilgileri
        column_group = QGroupBox("Sütun Analizi")
        column_layout = QVBoxLayout(column_group)
        self._column_info_widget = ColumnInfoWidget()
        column_layout.addWidget(self._column_info_widget)
        left_layout.addWidget(column_group)
        
        # Filtreler
        filter_group = QGroupBox("Filtreler")
        filter_layout = QVBoxLayout(filter_group)
        self._filter_widget = FilterWidget()
        filter_layout.addWidget(self._filter_widget)
        left_layout.addWidget(filter_group)
        
        splitter.addWidget(left_panel)
        
        # Sağ panel - Veri tablosu
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        data_group = QGroupBox("Veri Önizleme")
        data_layout = QVBoxLayout(data_group)
        self._data_table_widget = DataTableWidget()
        data_layout.addWidget(self._data_table_widget)
        right_layout.addWidget(data_group)
        
        splitter.addWidget(right_panel)
        
        # Splitter oranları
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Hazır")
    
    def _setup_menu(self):
        """Menü çubuğunu oluşturur"""
        menubar = self.menuBar()
        
        # Dosya menüsü
        file_menu = menubar.addMenu("&Dosya")
        
        open_action = QAction("&Aç...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._prompt_file_selection)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        export_csv = QAction("CSV Olarak &Kaydet...", self)
        export_csv.setShortcut("Ctrl+S")
        export_csv.triggered.connect(lambda: self._data_table_widget._export_data('csv'))
        file_menu.addAction(export_csv)
        
        export_excel = QAction("&Excel Olarak Kaydet...", self)
        export_excel.setShortcut("Ctrl+Shift+S")
        export_excel.triggered.connect(lambda: self._data_table_widget._export_data('xlsx'))
        file_menu.addAction(export_excel)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Çı&kış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Filtre menüsü
        filter_menu = menubar.addMenu("F&iltre")
        
        add_filter = QAction("Filtre &Ekle", self)
        add_filter.setShortcut("Ctrl+F")
        add_filter.triggered.connect(self._filter_widget._add_filter)
        filter_menu.addAction(add_filter)
        
        clear_filters = QAction("Filtreleri &Temizle", self)
        clear_filters.setShortcut("Ctrl+Shift+F")
        clear_filters.triggered.connect(self._clear_filters)
        filter_menu.addAction(clear_filters)
        
        # Yardım menüsü
        help_menu = menubar.addMenu("&Yardım")
        
        about_action = QAction("&Hakkında", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Sinyalleri bağlar"""
        self._filter_widget.filters_changed.connect(self._apply_filters)
    
    def _prompt_file_selection(self):
        """Dosya seçim dialogunu gösterir"""
        file_filter = self._file_reader.get_file_filter()
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Veri Dosyası Seç",
            "",
            file_filter
        )
        
        if file_path:
            self._load_file(Path(file_path))
    
    def _load_file(self, file_path: Path):
        """Dosyayı yükler"""
        self._file_path = file_path
        self._file_label.setText(f"📄 {file_path.name}")
        
        # Progress göster
        self._progress_bar.setVisible(True)
        self._status_bar.showMessage("Dosya yükleniyor...")
        self._load_btn.setEnabled(False)
        
        # Thread ile yükle
        self._loader_thread = FileLoaderThread(file_path)
        self._loader_thread.finished.connect(self._on_file_loaded)
        self._loader_thread.error.connect(self._on_load_error)
        self._loader_thread.progress.connect(self._on_load_progress)
        self._loader_thread.start()
    
    def _on_load_progress(self, message: str):
        """Yükleme ilerlemesi"""
        self._status_bar.showMessage(message)
    
    def _on_file_loaded(self, df: pd.DataFrame, column_infos: List[ColumnInfo]):
        """Dosya yüklendiğinde"""
        self._progress_bar.setVisible(False)
        self._load_btn.setEnabled(True)
        
        self._df = df
        self._column_infos = column_infos
        
        # Widget'ları güncelle
        self._column_info_widget.set_column_infos(column_infos)
        self._filter_widget.set_column_infos(column_infos)
        self._data_table_widget.set_dataframe(df)
        
        self._status_bar.showMessage(
            f"Dosya yüklendi: {len(df)} satır, {len(df.columns)} sütun"
        )
    
    def _on_load_error(self, error_message: str):
        """Yükleme hatası"""
        self._progress_bar.setVisible(False)
        self._load_btn.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Yükleme Hatası",
            f"Dosya yüklenirken hata oluştu:\n{error_message}"
        )
        
        self._status_bar.showMessage("Yükleme başarısız")
    
    def _apply_filters(self, filters: List[FilterModel]):
        """Filtreleri uygular"""
        if self._df is None:
            return
        
        if not filters:
            self._data_table_widget.reset_to_original()
            self._status_bar.showMessage("Filtreler temizlendi")
            return
        
        try:
            filtered_df = self._filter_engine.apply_filters(self._df, filters)
            self._data_table_widget.set_filtered_dataframe(filtered_df)
            
            summary = self._filter_engine.get_filter_summary(filters)
            self._status_bar.showMessage(
                f"Filtre uygulandı: {len(filtered_df)} sonuç | {summary}"
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Filtre Hatası",
                f"Filtre uygulanırken hata oluştu:\n{str(e)}"
            )
    
    def _clear_filters(self):
        """Filtreleri temizler"""
        self._filter_widget._clear_filters()
        if self._df is not None:
            self._data_table_widget.reset_to_original()
        self._status_bar.showMessage("Filtreler temizlendi")
    
    def _show_about(self):
        """Hakkında dialogu"""
        QMessageBox.about(
            self,
            "IK Filtresi Hakkında",
            """<h2>IK Filtresi v1.0</h2>
            <p>Veri filtreleme ve analiz aracı.</p>
            <p><b>Özellikler:</b></p>
            <ul>
                <li>CSV, Excel (xlsx, xls) dosya desteği</li>
                <li>Otomatik sütun tipi algılama</li>
                <li>Sayısal, tarih ve metin filtreleri</li>
                <li>Çoklu filtre desteği</li>
                <li>Filtrelenmiş veri dışa aktarma</li>
            </ul>
            <p>SOLID prensipleriyle geliştirilmiştir.</p>
            """
        )
