# factory_queue_item_widget.py
import logging
from PySide6.QtGui import QPixmap, QPainter, QPen, QFontDatabase, QFont
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import Qt
from constants import resolve_factory_image_path

class FactoryQueueItemWidget(QLabel):
    """
    A small widget that displays a queued unit:
      - The unit's image
      - If count > 1, show the count in the corner
    """
    def __init__(self, unit_name, count, color, size=50, prefer_vet=False, parent=None):
        super().__init__(parent)
        self.unit_name = unit_name
        self.count = count
        self.color = color
        self.size = size
        self.prefer_vet = prefer_vet
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.scaled_pixmap = QPixmap()
        self.build_pixmap()

    def build_pixmap(self):
        path = resolve_factory_image_path(self.unit_name, prefer_vet=self.prefer_vet)
        if not path:
            logging.warning("No queue image resolved for unit: %s", self.unit_name)
            self.scaled_pixmap = QPixmap()
            self.setFixedSize(0, 0)
            return
        pix = QPixmap(path)
        if pix.isNull():
            logging.warning("Queue image failed to load for unit '%s' from path '%s'", self.unit_name, path)
            self.scaled_pixmap = QPixmap()
            self.setFixedSize(0, 0)
            return
        pix = pix.scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.scaled_pixmap = pix
        self.setFixedSize(self.scaled_pixmap.size())

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.scaled_pixmap.isNull():
            return
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
