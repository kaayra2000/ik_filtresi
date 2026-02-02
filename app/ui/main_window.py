"""
Ana pencere - Uygulamanın ana arayüzü
"""

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFileDialog,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QGroupBox,
    QProgressBar,
    QDialog,
    QPushButton,
    QSizePolicy,
    QApplication,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from PyQt6.QtGui import QAction, QScreen
from pathlib import Path
from typing import Optional, List

import pandas as pd

from app.services.file_handler import FileIORegistry
from app.services.data_analyzer import DataAnalyzer
from app.services.filter_engine import FilterEngine
from app.services.filter_persistence import FilterPersistence
from app.models.column_info import ColumnInfo
from app.models.filter_model import FilterGroup
from app.ui.column_info_widget import ColumnInfoWidget, ColumnInfoDialog
from app.ui.filter_widget import FilterWidget, FilterDialog
from app.ui.icon_factory import IconFactory
from app.ui.data_table_widget import DataTableWidget

# Uygulama ayarları için sabitler
APP_NAME = "IKFiltresi"
APP_ORG = "IKFiltresi"


class FileLoaderThread(QThread):
    """Dosya yükleme için arka plan thread'i"""

    finished = pyqtSignal(pd.DataFrame, list)  # df, column_infos
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_path: Path, parent=None):
        super().__init__(parent)
        self._file_path = file_path
        self._analyzer = DataAnalyzer()

    def run(self):
        try:
            self.progress.emit("Dosya okunuyor...")
            df = FileIORegistry.read_file(self._file_path)

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
        self._current_theme: str = "light"  # Varsayılan tema
        self._settings = QSettings(APP_ORG, APP_NAME)  # Ayarları yükle/kaydet

        self._filter_engine = FilterEngine()
        self._filter_persistence = FilterPersistence()

        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

        # Kaydedilmiş temayı yükle
        self._load_saved_theme()

        # Uygulama açılınca dosya seç
        self._prompt_file_selection()

    def _setup_ui(self):
        """UI bileşenlerini oluşturur"""
        self.setWindowTitle("Excel Filtresi - Veri Filtreleme Aracı")

        # Ekran çözünürlüğüne göre dinamik boyutlandırma
        self._configure_window_size()

        # Central widget
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Başlık ve dosya bilgisi
        header_layout = QHBoxLayout()

        title = QLabel("Excel Filtresi")
        title.setObjectName("titleLabel")
        header_layout.addWidget(title)

        header_layout.addStretch()

        self._file_label = QLabel("Dosya seçilmedi")
        self._file_label.setObjectName("fileLabel")
        self._file_label.setToolTip("Yüklenen veri dosyasının adı")
        header_layout.addWidget(self._file_label)

        main_layout.addLayout(header_layout)

        # Progress bar (gizli)
        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setRange(0, 0)  # Indeterminate
        self._progress_bar.setToolTip("Dosya yükleme işlemi devam ediyor...")
        main_layout.addWidget(self._progress_bar)

        # Compact action buttons above data preview (filter & column analysis)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        # Right-align buttons: add stretch first
        actions_layout.addStretch()

        # Create hidden stateful widgets (manage state, not shown)
        self._filter_widget = FilterWidget()
        self._column_info_widget = ColumnInfoWidget()

        # Use IconFactory to create tool buttons with icons
        self._filter_button = IconFactory.create_tool_button("filter.svg", "Filtreler")
        self._filter_button.setObjectName("filterButton")
        self._filter_button.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self._filter_button.setToolTip("Filtreleri düzenle")
        self._filter_button.clicked.connect(self._open_filter_dialog)
        actions_layout.addWidget(self._filter_button)

        self._colinfo_button = IconFactory.create_tool_button(
            "columns.svg", "Sütun Ayrıntıları"
        )
        self._colinfo_button.setObjectName("colInfoButton")
        self._colinfo_button.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )
        self._colinfo_button.setToolTip(
            "Sütun türlerini, istatistiklerini ve değer aralıklarını görüntüle"
        )
        self._colinfo_button.clicked.connect(self._open_column_info_dialog)
        actions_layout.addWidget(self._colinfo_button)

        main_layout.addLayout(actions_layout)

        # Veri önizleme (ortak alan)
        data_group = QGroupBox("Veri Önizleme")
        data_layout = QVBoxLayout(data_group)
        self._data_table_widget = DataTableWidget()
        data_layout.addWidget(self._data_table_widget)
        main_layout.addWidget(data_group)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Hazır")

    def _configure_window_size(self):
        """
        Ekran çözünürlüğüne göre pencere boyutlarını dinamik olarak ayarlar.
        Çoklu monitör desteği ile o an bulunulan monitöre göre boyutlandırır.
        """
        # Mevcut ekranı al (çoklu monitör desteği)
        screen = self._get_current_screen()
        screen_geometry = screen.availableGeometry()

        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()

        # Minimum boyutları ekran çözünürlüğüne orantılı hesapla
        # Minimum boyut: ekranın %50'si genişlik, %50'si yükseklik
        min_width = int(screen_width * 0.5)
        min_height = int(screen_height * 0.5)

        # Makul minimum sınırlar (çok küçük ekranlar için)
        min_width = max(min_width, 800)
        min_height = max(min_height, 600)

        self.setMinimumSize(min_width, min_height)

        # Başlangıç boyutu: ekranın %75'i genişlik, %80'i yükseklik
        initial_width = int(screen_width * 0.75)
        initial_height = int(screen_height * 0.80)

        self.resize(initial_width, initial_height)

        # Pencereyi ekranın ortasına konumlandır
        self._center_on_screen(screen_geometry)

    def _get_current_screen(self) -> QScreen:
        """
        Mevcut/birincil ekranı döndürür.
        Çoklu monitör durumunda fare imlecinin bulunduğu ekranı tercih eder.
        """
        # Fare imlecinin bulunduğu ekranı bul
        cursor_pos = QApplication.instance().primaryScreen().geometry().center()

        # Tüm ekranları kontrol et
        for screen in QApplication.screens():
            if screen.geometry().contains(cursor_pos):
                return screen

        # Varsayılan olarak birincil ekranı döndür
        return QApplication.primaryScreen()

    def _center_on_screen(self, screen_geometry):
        """Pencereyi verilen ekran geometrisinin ortasına konumlandırır"""
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()
        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def _setup_menu(self):
        """Menü çubuğunu oluşturur"""
        menubar = self.menuBar()

        # Dosya menüsü
        file_menu = menubar.addMenu("&Dosya")

        open_action = QAction("&Aç...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._prompt_file_selection)
        file_menu.addAction(open_action)

        # Kaydet alt menüsü
        save_menu = file_menu.addMenu("&Kaydet")

        # FileIORegistry'den dinamik olarak export seçeneklerini oluştur (OCP uyumlu)
        shortcuts = ["Ctrl+S", "Ctrl+Shift+S"]  # İlk iki format için kısayollar

        for idx, desc in enumerate(FileIORegistry.get_format_descriptors()):
            ext = desc.get("default", "").lstrip(".")
            action_text = f"{ext.upper()} Olarak Kaydet..."
            export_action = QAction(action_text, self)

            # İlk iki format için kısayol ata
            if idx < len(shortcuts):
                export_action.setShortcut(shortcuts[idx])

            # Lambda'da closure problemi için default argument kullan
            export_action.triggered.connect(
                lambda checked, fmt=ext: self._data_table_widget._export_data(fmt)
            )
            save_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("Çı&kış", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tema menüsü
        view_menu = menubar.addMenu("&Tema")

        self._light_theme_action = QAction("☀️ Açık", self)
        self._light_theme_action.setCheckable(True)
        self._light_theme_action.setChecked(True)
        self._light_theme_action.triggered.connect(lambda: self._set_theme("light"))
        view_menu.addAction(self._light_theme_action)

        self._dark_theme_action = QAction("🌙 Koyu", self)
        self._dark_theme_action.setCheckable(True)
        self._dark_theme_action.setChecked(False)
        self._dark_theme_action.triggered.connect(lambda: self._set_theme("dark"))
        view_menu.addAction(self._dark_theme_action)

        # Yardım menüsü
        help_menu = menubar.addMenu("&Yardım")

        usage_action = QAction("📖 &Nasıl Kullanılır?", self)
        usage_action.triggered.connect(self._show_help)
        help_menu.addAction(usage_action)

        help_menu.addSeparator()

        about_action = QAction("ℹ️ &Hakkında", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        """Sinyalleri bağlar"""
        self._filter_widget.filter_group_changed.connect(self._apply_filter_group)
        self._filter_widget.filter_group_changed.connect(
            self._update_filter_button_tooltip
        )

    def _update_filter_button_tooltip(self, group=None):
        """Update filter button tooltip to show current summary."""
        try:
            # Eğer group parametresi verilmişse, ondan özet oluştur
            if group is not None and not group.is_empty():
                summary = group.to_display_string()
            elif group is not None and group.is_empty():
                summary = "Filtre yok"
            else:
                summary = "Filtre yok - düzenlemek için tıklayın"

            # Keep tooltip short
            tooltip = summary if len(summary) <= 300 else summary[:300] + "..."
            self._filter_button.setToolTip(tooltip)
        except Exception:
            self._filter_button.setToolTip("Filtreleri düzenle")

    def _open_filter_dialog(self):
        """Open modal filter dialog from compact button."""
        if not self._column_infos:
            QMessageBox.warning(self, "Uyarı", "Önce bir veri dosyası yükleyin.")
            return

        dialog = FilterDialog(
            self._column_infos, self._filter_widget.get_filter_group(), self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_group = dialog.get_filter_group()
            self._filter_widget.set_filter_group(new_group)
            self._apply_filter_group(new_group)
            self._update_filter_button_tooltip(new_group)

    def _open_column_info_dialog(self):
        """Open column analysis as modal dialog."""
        if not self._column_infos:
            QMessageBox.information(self, "Bilgi", "Önce bir veri dosyası yükleyin.")
            return

        dialog = ColumnInfoDialog(self._column_infos, self)
        dialog.exec()

    def _prompt_file_selection(self):
        """Dosya seçim dialogunu gösterir"""
        file_filter = FileIORegistry.get_file_filter()

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Veri Dosyası Seç", "", file_filter
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

        self._df = df
        self._column_infos = column_infos

        # Widget'ları güncelle
        self._column_info_widget.set_column_infos(column_infos)
        self._filter_widget.set_column_infos(column_infos)
        # Provide column infos to data table for header tooltips
        self._data_table_widget.set_column_infos(column_infos)

        # Kaydedilmiş filtreleri yükle
        saved_group = self._filter_persistence.load_filter_group()
        if saved_group and not saved_group.is_empty():
            # Tabloyu ayarla
            self._data_table_widget.set_dataframe(df)
            # Filtreleri yükle ve uygula
            self._filter_widget.set_filter_group(saved_group)
            self._apply_filter_group(saved_group)
            # Tooltip'i kaydedilmiş filtrelerle güncelle
            self._update_filter_button_tooltip(saved_group)
            self._status_bar.showMessage("Kayıtlı filtreler yüklendi ve uygulandı.")
        else:
            self._data_table_widget.set_dataframe(df)
            # Filtre yoksa tooltip'i güncelle
            self._update_filter_button_tooltip()
            self._status_bar.showMessage(
                f"Dosya yüklendi: {len(df)} satır, {len(df.columns)} sütun"
            )

    def _on_load_error(self, error_message: str):
        """Yükleme hatası"""
        self._progress_bar.setVisible(False)

        QMessageBox.critical(
            self, "Yükleme Hatası", f"Dosya yüklenirken hata oluştu:\n{error_message}"
        )

        self._status_bar.showMessage("Yükleme başarısız")

    def _apply_filter_group(self, group: FilterGroup):
        """FilterGroup ile filtreleme (AND/OR destekli)"""
        if self._df is None:
            return

        if group is None or group.is_empty():
            self._data_table_widget.reset_to_original()
            self._status_bar.showMessage("Filtreler temizlendi")
            # Boş filtre grubunu da kaydet - uygulama yeniden açıldığında eski filtre gelmemesi için
            self._filter_persistence.save_filter_group(FilterGroup())
            return

        try:
            filtered_df = self._filter_engine.apply_filter_component(self._df, group)
            self._data_table_widget.set_filtered_dataframe(filtered_df)

            summary = self._filter_engine.get_component_summary(group)
            self._status_bar.showMessage(
                f"Filtre uygulandı: {len(filtered_df)} sonuç | {summary}"
            )
            self._filter_persistence.save_filter_group(group)
        except Exception as e:
            QMessageBox.warning(
                self, "Filtre Hatası", f"Filtre uygulanırken hata oluştu:\n{str(e)}"
            )

    def _show_help(self):
        """Yardım/Kullanım kılavuzu dialogu"""
        help_path = Path(__file__).parent.parent / "help.md"

        if help_path.exists():
            with open(help_path, "r", encoding="utf-8") as f:
                help_content = f.read()

            # Düz markdown'u olduğu gibi göster
            dialog = QDialog(self)
            dialog.setWindowTitle("Nasıl Kullanılır?")
            dialog.setMinimumSize(600, 500)
            dialog.resize(700, 600)

            layout = QVBoxLayout(dialog)

            from PyQt6.QtWidgets import QTextBrowser

            text_browser = QTextBrowser()
            # Markdown içeriğini işle ve görüntüle
            text_browser.setMarkdown(help_content)
            text_browser.setOpenExternalLinks(True)
            layout.addWidget(text_browser)

            dialog.exec()
        else:
            QMessageBox.warning(
                self,
                "Yardım Dosyası Bulunamadı",
                "Yardım dosyası (help.md) bulunamadı.",
            )

    def _show_about(self):
        """Hakkında dialogu"""
        from app.version import VERSION

        QMessageBox.about(
            self,
            "IK Filtresi Hakkında",
            f"""<h2>IK Filtresi {VERSION}</h2>
            <p>Veri filtreleme ve analiz aracı.</p>
            <p><b>Özellikler:</b></p>
            <ul>
                <li>CSV, Excel (xlsx, xls) dosya desteği</li>
                <li>Otomatik sütun tipi algılama</li>
                <li>Sayısal, tarih ve metin filtreleri</li>
                <li>Çoklu filtre desteği</li>
                <li>Filtrelenmiş veri dışa aktarma</li>
            </ul>
            """,
        )

    def _set_theme(self, theme: str):
        """Tema değiştirir (light/dark)"""
        self._current_theme = theme

        # Menü checkbox'larını güncelle
        self._light_theme_action.setChecked(theme == "light")
        self._dark_theme_action.setChecked(theme == "dark")

        # Uygun stil dosyasını yükle
        self._load_theme_stylesheet(theme)

        # Temayı kaydet
        self._save_theme(theme)

        self._status_bar.showMessage(
            f"{'Koyu' if theme == 'dark' else 'Açık'} tema uygulandı"
        )

    def _load_saved_theme(self):
        """Kaydedilmiş tema tercihini yükler"""
        saved_theme = self._settings.value("theme", "light")
        if saved_theme in ("light", "dark"):
            self._set_theme(saved_theme)

    def _save_theme(self, theme: str):
        """Tema tercihini kaydeder"""
        self._settings.setValue("theme", theme)
        self._settings.sync()  # Hemen diske yaz

    def _load_theme_stylesheet(self, theme: str):
        """Temaya göre uygun stil dosyasını yükler"""
        # Stil dosyalarının yollarını belirle
        base_path = Path(__file__).parent.parent.parent

        if theme == "dark":
            style_path = base_path / "style_dark.qss"
        else:
            style_path = base_path / "style.qss"

        if style_path.exists():
            with open(style_path, "r", encoding="utf-8") as f:
                stylesheet = f.read()

            # Ana uygulamaya stili uygula
            app = QApplication.instance()
            if app:
                app.setStyleSheet(stylesheet)

    def _reload_stylesheet(self):
        """Stil dosyasını yeniden yükler (mevcut tema için)"""
        self._load_theme_stylesheet(self._current_theme)
