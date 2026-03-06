from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPainter, QPen, QPixmap

from CounterWidget import CounterWidgetBase


class SuperweaponWidget(CounterWidgetBase):
    def __init__(self, superweapon_name, color=Qt.red, size=100, show_frame=True, parent=None):
        super().__init__(color=color, size=size, parent=parent)
        self.superweapon_name = superweapon_name
        self.show_frame = show_frame
        self.progress_text = ""
        self.image_path = f"cameos/png/{superweapon_name}.png"
        self.scaled_pixmap = QPixmap()
        self.hide()

    def set_status(self, status):
        if not status.get("owned"):
            self.progress_text = ""
            self.hide()
            return

        self.show()

        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            self.scaled_pixmap = QPixmap()
            self.setFixedSize(0, 0)
            self.update()
            return

        self.scaled_pixmap = pixmap.scaled(
            self.size,
            self.size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        percent = int(status.get("percent", 0))
        if percent >= 100:
            self.progress_text = "Ready"
        else:
            self.progress_text = f"{percent}%"

        self.setToolTip(
            f"{self.superweapon_name}\n"
            f"Charge: {self.progress_text} ({status.get('raw_value', 0)}/53)"
        )
        self.setFixedSize(self.scaled_pixmap.size())
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.scaled_pixmap.isNull():
            return

        painter.drawPixmap(0, 0, self.scaled_pixmap)

        if self.progress_text:
            font_size = int(self.size / 6)
            font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
            font_family = QFontDatabase.applicationFontFamilies(font_id)
            if font_family:
                text_font = QFont(font_family[0], font_size, QFont.Bold)
            else:
                text_font = QFont("Arial", font_size, QFont.Bold)
            painter.setFont(text_font)

            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(self.progress_text)
            text_h = fm.height()
            pix_w = self.scaled_pixmap.width()
            pix_h = self.scaled_pixmap.height()
            text_x = (pix_w - text_w) / 2
            text_y = (pix_h - text_h) / 2 + fm.ascent()

            painter.setPen(Qt.black)
            outline_thickness = 2
            for dx in range(-outline_thickness, outline_thickness + 1):
                for dy in range(-outline_thickness, outline_thickness + 1):
                    if dx == 0 and dy == 0:
                        continue
                    painter.drawText(text_x + dx, text_y + dy, self.progress_text)

            painter.setPen(Qt.white)
            painter.drawText(text_x, text_y, self.progress_text)

        if self.show_frame:
            pen = QPen(self.color)
            pen.setWidth(int(self.size / 15))
            painter.setPen(pen)
            painter.drawRoundedRect(
                0,
                0,
                self.scaled_pixmap.width(),
                self.scaled_pixmap.height(),
                10,
                10,
            )

    def update_size(self, new_size):
        super().update_size(new_size)
        if not self.scaled_pixmap.isNull():
            self.scaled_pixmap = self.scaled_pixmap.scaled(
                new_size,
                new_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.setFixedSize(self.scaled_pixmap.size())
        self.update()

    def update_show_frame(self, show_frame):
        self.show_frame = show_frame
        self.update()
