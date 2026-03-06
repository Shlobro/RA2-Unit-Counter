# factory_queue_item_widget.py
import logging
from PySide6.QtGui import QPixmap, QPainter, QPen, QFontDatabase, QFont
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from constants import get_display_image_name, name_to_path

class FactoryQueueItemWidget(QLabel):
    """
    A small widget that displays a queued unit:
      - The unit's image
      - If count > 1, show the count in the corner
    """
    def __init__(self, unit_name, count, color, size=50, parent=None):
        super().__init__(parent)
        self.unit_name = unit_name
        self.count = count
        self.color = color
        self.size = size
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.scaled_pixmap = QPixmap()
        self.build_pixmap()

    def build_pixmap(self):
        from constants import name_to_path
        path = name_to_path(get_display_image_name(self.unit_name))
        pix = QPixmap(path)
        if pix.isNull():
            logging.warning(f"Image not found for queued unit: {self.unit_name}")
        pix = pix.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.scaled_pixmap = pix
        self.setFixedSize(self.scaled_pixmap.size())

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.scaled_pixmap)

        if self.count > 1:
            # overlay the count in bottom-right
            font_size = int(self.size / 4)
            font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
            font_family = QFontDatabase.applicationFontFamilies(font_id)
            if font_family:
                text_font = QFont(font_family[0], font_size, QFont.Bold)
            else:
                text_font = QFont("Arial", font_size, QFont.Bold)
            painter.setFont(text_font)

            text = str(self.count)
            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(text)
            text_h = fm.ascent()

            x = self.scaled_pixmap.width() - text_w - 2
            y = self.scaled_pixmap.height() - 2

            # black outline
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx != 0 or dy != 0:
                        painter.setPen(Qt.black)
                        painter.drawText(x+dx, y+dy, text)

            painter.setPen(Qt.white)
            painter.drawText(x, y, text)
