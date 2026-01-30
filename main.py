#!/usr/bin/env python3
"""
IK Filtresi - Ana uygulama giriş noktası
"""
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QFile, QTextStream

from app.ui.main_window import MainWindow


def load_stylesheet(app: QApplication) -> None:
    """QSS stil dosyasını yükler."""
    style_path = Path(__file__).parent / "style.qss"
    if style_path.exists():
        file = QFile(str(style_path))
        if file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text):
            stream = QTextStream(file)
            app.setStyleSheet(stream.readAll())
            file.close()


def main() -> None:
    """Uygulamayı başlatır."""
    app = QApplication(sys.argv)
    app.setApplicationName("IK Filtresi")
    
    load_stylesheet(app)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
