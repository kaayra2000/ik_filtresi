"""
Ekran yardımcı fonksiyonları - Çözünürlük ve boyutlandırma işlemleri
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QScreen
from PyQt6.QtCore import QRect


class ScreenUtils:
    """
    Ekran çözünürlüğü ile ilgili yardımcı fonksiyonlar.
    Single Responsibility: Sadece ekran boyutlandırma işlemleri.
    """

    @staticmethod
    def get_current_screen() -> QScreen:
        """
        Mevcut/birincil ekranı döndürür.
        Çoklu monitör durumunda fare imlecinin bulunduğu ekranı tercih eder.
        """
        app = QApplication.instance()
        if not app:
            return QApplication.primaryScreen()

        # Fare imlecinin bulunduğu ekranı bul
        cursor_pos = app.primaryScreen().geometry().center()

        # Tüm ekranları kontrol et
        for screen in QApplication.screens():
            if screen.geometry().contains(cursor_pos):
                return screen

        # Varsayılan olarak birincil ekranı döndür
        return QApplication.primaryScreen()

    @staticmethod
    def get_screen_geometry() -> QRect:
        """Mevcut ekranın kullanılabilir geometrisini döndürür."""
        screen = ScreenUtils.get_current_screen()
        if screen:
            return screen.availableGeometry()
        return QRect(0, 0, 1920, 1080)  # Varsayılan

    @staticmethod
    def get_screen_width() -> int:
        """Mevcut ekranın genişliğini döndürür."""
        return ScreenUtils.get_screen_geometry().width()

    @staticmethod
    def get_screen_height() -> int:
        """Mevcut ekranın yüksekliğini döndürür."""
        return ScreenUtils.get_screen_geometry().height()

    @staticmethod
    def calculate_max_column_width() -> int:
        """
        Ekran çözünürlüğüne göre maksimum sütun genişliğini hesaplar.
        Ekran genişliğinin yaklaşık %15'i olarak belirlenir.
        """
        screen_width = ScreenUtils.get_screen_width()
        # Ekran genişliğinin %15'i, minimum 200, maksimum 400 piksel
        max_width = int(screen_width * 0.15)
        return max(200, min(max_width, 400))

    @staticmethod
    def calculate_window_size(
        width_ratio: float = 0.75, height_ratio: float = 0.80
    ) -> tuple[int, int]:
        """
        Ekran çözünürlüğüne göre pencere boyutunu hesaplar.
        
        Args:
            width_ratio: Ekran genişliğinin yüzdesi (varsayılan %75)
            height_ratio: Ekran yüksekliğinin yüzdesi (varsayılan %80)
        
        Returns:
            (width, height) tuple
        """
        screen_width = ScreenUtils.get_screen_width()
        screen_height = ScreenUtils.get_screen_height()

        width = int(screen_width * width_ratio)
        height = int(screen_height * height_ratio)

        return width, height

    @staticmethod
    def calculate_minimum_size(
        width_ratio: float = 0.5, height_ratio: float = 0.5
    ) -> tuple[int, int]:
        """
        Ekran çözünürlüğüne göre minimum pencere boyutunu hesaplar.
        
        Args:
            width_ratio: Ekran genişliğinin yüzdesi (varsayılan %50)
            height_ratio: Ekran yüksekliğinin yüzdesi (varsayılan %50)
        
        Returns:
            (min_width, min_height) tuple - en az 800x600
        """
        screen_width = ScreenUtils.get_screen_width()
        screen_height = ScreenUtils.get_screen_height()

        min_width = max(int(screen_width * width_ratio), 800)
        min_height = max(int(screen_height * height_ratio), 600)

        return min_width, min_height
