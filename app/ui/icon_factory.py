from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QToolButton, QSizePolicy


class IconFactory:
    """Small helper to centralize icon loading and applying for QToolButton.

    Usage:
        IconFactory.apply_icon(tool_button, "save.svg", (18, 18))
        icon = IconFactory.load_icon("save.svg")
    """

    @staticmethod
    def get_icons_dir() -> Path:
        return Path(__file__).resolve().parent / "icons"

    @staticmethod
    def _normalize_size(size: Optional[QSize] = None) -> QSize:
        """Normalize to a QSize. Accepts only QSize; default is 18x18."""
        if isinstance(size, QSize):
            return size
        return QSize(18, 18)

    @staticmethod
    def load_icon(name: str) -> QIcon:
        """Load icon by filename from the package icons folder. Returns a QIcon (empty if not found)."""
        icons_dir = IconFactory.get_icons_dir()
        path = icons_dir / name
        if path.exists():
            return QIcon(str(path))
        # fallback: try common extensions
        for ext in (".svg", ".png", ".ico"):
            p = icons_dir / (name + ext)
            if p.exists():
                return QIcon(str(p))
        return QIcon()

    @staticmethod
    def apply_icon(
        widget: QToolButton,
        name: str,
        size: Optional[QSize] = None,
        text_beside_icon: bool = True,
    ):
        """Set icon on a QToolButton with left alignment.

        Args:
            widget: QToolButton instance
            name: Icon filename
            size: Icon size (default 18x18)
            text_beside_icon: If True, text appears beside icon (default True)
        """
        icon = IconFactory.load_icon(name)

        try:
            widget.setIcon(icon)
        except Exception:
            return

        qsize = IconFactory._normalize_size(size)
        try:
            widget.setIconSize(qsize)
        except Exception:
            pass

        # QToolButton'a özgü: ikon yanında metin göster
        if text_beside_icon:
            try:
                widget.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            except Exception:
                pass

    @staticmethod
    def create_tool_button(
        name: str, text: str = "", size: Optional[QSize] = None, min_width: int = 120
    ) -> QToolButton:
        """Create a left-aligned QToolButton with icon.

        Args:
            name: Icon filename
            text: Button text
            size: Icon size (default 18x18)
            min_width: Minimum button width (default 120)

        Returns:
            Configured QToolButton instance
        """
        button = QToolButton()
        button.setText(text)
        button.setMinimumWidth(min_width)

        # Apply icon and ensure text is beside icon
        IconFactory.apply_icon(button, name, size, text_beside_icon=True)

        # Centralize size policy and baseline styling for all icon buttons
        try:
            button.setSizePolicy(
                QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            )
            # Size policy centralized; visual alignment moved to style.qss
        except Exception:
            pass

        return button
