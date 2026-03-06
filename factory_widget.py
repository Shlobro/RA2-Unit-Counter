import logging
from PySide6.QtGui import QPixmap, QPainter, QPen, QFontDatabase, QFont
from PySide6.QtCore import Qt
from CounterWidget import CounterWidgetBase
from constants import get_display_image_name, name_to_path

class FactoryWidget(CounterWidgetBase):
    def __init__(self, factory, color=Qt.red, size=100, show_frame=True, parent=None):
        """
        A factory widget that mirrors your "CounterWidgetImagesAndNumber" style:
          - Draws a scaled image
          - Renders text with black outline + white fill
          - Text is now centered in the image
          - The text is half the old size (i.e., size/6 instead of size/3)
          - Draws a rounded colored frame if show_frame is True
        """
        super().__init__(color=color, size=size, parent=parent)
        self.factory = factory
        self.show_frame = show_frame

        # We'll store the current displayed text here, e.g. "40%" or "Ready"
        self.progress_text = ""
        self.scaled_pixmap = QPixmap()

        # Hide if not producing
        self.hide()

    def set_status(self, status):
        """
        status typically has:
          - producing: bool
          - currently_building: str
          - percentage: float (0..100+)
        """
        if not status.get("producing"):
            self.progress_text = ""
            self.hide()
            return

        self.show()

        # 1) Scale the image
        unit_name = status.get("currently_building", "")
        image_path = name_to_path(get_display_image_name(unit_name))
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            logging.error(f"Image not found for unit: {unit_name}")
        self.scaled_pixmap = pixmap.scaled(
            self.size, self.size,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        # 2) Convert the float to integer, e.g. "40%" or "Ready"
        percentage_float = status.get("percentage", 0.0)
        percentage_int = int(round(percentage_float))
        if percentage_int >= 100:
            self.progress_text = "Ready"
        else:
            self.progress_text = f"{percentage_int}%"

        # Match the widget's size to the scaled pixmap
        self.setFixedSize(self.scaled_pixmap.size())

        # Repaint with new text
        self.update()

    def paintEvent(self, event):
        """
        Draw the scaled pixmap, then center the text with a black outline
        and a white fill. Finally, draw a colored frame if show_frame is True.
        """
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.scaled_pixmap)

        # 1) Use half the old font size: size/6 instead of size/3
        font_size = int(self.size / 6)
        font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        if font_family:
            text_font = QFont(font_family[0], font_size, QFont.Bold)
        else:
            text_font = QFont("Arial", font_size, QFont.Bold)
        painter.setFont(text_font)

        # 2) Center the text
        if self.progress_text:
            fm = painter.fontMetrics()
            text_w = fm.horizontalAdvance(self.progress_text)
            text_h = fm.height()

            pix_w = self.scaled_pixmap.width()
            pix_h = self.scaled_pixmap.height()

            # center X and Y:
            #   baseline is ~ text_h from the top, so we do " (pix_h - text_h)/2 + fm.ascent() "
            text_x = (pix_w - text_w) / 2
            text_y = (pix_h - text_h) / 2 + fm.ascent()

            # Draw black outline behind the text
            outline_thickness = 2
            painter.setPen(Qt.black)
            for dx in range(-outline_thickness, outline_thickness + 1):
                for dy in range(-outline_thickness, outline_thickness + 1):
                    if dx == 0 and dy == 0:
                        continue
                    painter.drawText(text_x + dx, text_y + dy, self.progress_text)

            # Draw main text in white
            painter.setPen(Qt.white)
            painter.drawText(text_x, text_y, self.progress_text)

        # 3) If show_frame, draw a colored rounded frame
        if self.show_frame:
            pen = QPen(self.color)
            pen.setWidth(int(self.size / 15))
            painter.setPen(pen)
            painter.drawRoundedRect(
                0, 0,
                self.scaled_pixmap.width(),
                self.scaled_pixmap.height(),
                10, 10
            )

    def update_size(self, new_size):
        """
        Called when the user updates factory_size in your settings.
        Rescale the image and re-center text accordingly.
        """
        super().update_size(new_size)
        if not self.scaled_pixmap.isNull():
            self.scaled_pixmap = self.scaled_pixmap.scaled(
                new_size, new_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setFixedSize(self.scaled_pixmap.size())
        self.update()

    def update_show_frame(self, show_frame):
        self.show_frame = show_frame
        self.update()
