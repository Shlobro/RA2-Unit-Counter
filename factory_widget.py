import logging
from PySide6.QtGui import QPixmap, QPainter, QPen, QFontDatabase, QFont, QColor
from PySide6.QtCore import Qt, QRectF
from CounterWidget import CounterWidgetBase
from constants import resolve_factory_image_path

class FactoryWidget(CounterWidgetBase):
    def __init__(self, factory, player, color=Qt.red, size=100, show_frame=True, parent=None):
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
        self.player = player
        self.show_frame = show_frame

        # We'll store the current displayed text here, e.g. "40%" or "Ready"
        self.progress_text = ""
        self.queue_count_text = ""
        self.scaled_pixmap = QPixmap()

        # Hide if not producing
        self.hide()

    def set_status(self, status, show_current_queue_count=False):
        """
        status typically has:
          - producing: bool
          - currently_building: str
          - percentage: float (0..100+)
        """
        if not status.get("producing"):
            self.progress_text = ""
            self.queue_count_text = ""
            self.hide()
            return

        self.show()

        # 1) Scale the image
        unit_name = status.get("currently_building", "")
        if show_current_queue_count and "queued_units" in status:
            queued_units = status.get("queued_units") or []
            total_in_batch = 1 + sum(
                1 for queued_unit in queued_units if queued_unit == unit_name
            )
            self.queue_count_text = str(total_in_batch) if total_in_batch > 1 else ""
        else:
            self.queue_count_text = ""
        prefer_vet = (
            (self.factory.factory_name == "Infantry" and self.player.barracks_infiltrated) or
            (self.factory.factory_name == "Vehicles" and self.player.war_factory_infiltrated)
        )
        image_path = resolve_factory_image_path(unit_name, prefer_vet=prefer_vet)
        if not image_path:
            logging.warning("No factory image resolved for unit: %s", unit_name)
            self.scaled_pixmap = QPixmap()
            self.setFixedSize(0, 0)
            self.update()
            return

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            logging.warning("Factory image failed to load for unit '%s' from path '%s'", unit_name, image_path)
            self.scaled_pixmap = QPixmap()
            self.setFixedSize(0, 0)
            self.update()
            return

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
        if self.scaled_pixmap.isNull():
            return
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
            if self.outline_enabled:
                painter.setPen(self.outline_color)
                for dx in range(-self.outline_thickness, self.outline_thickness + 1):
                    for dy in range(-self.outline_thickness, self.outline_thickness + 1):
                        if dx * dx + dy * dy <= self.outline_thickness ** 2 and (dx or dy):
                            painter.drawText(text_x + dx, text_y + dy, self.progress_text)

            # Draw main text in white
            painter.setPen(Qt.white)
            painter.drawText(text_x, text_y, self.progress_text)

        if self.queue_count_text:
            painter.save()
            badge_font = QFont(text_font)
            badge_font.setPointSize(max(7, int(self.size / 9)))
            painter.setFont(badge_font)
            fm = painter.fontMetrics()
            horizontal_padding = max(4, int(self.size / 20))
            vertical_padding = max(2, int(self.size / 40))
            badge_width = fm.horizontalAdvance(self.queue_count_text) + horizontal_padding * 2
            badge_height = fm.height() + vertical_padding * 2
            edge_margin = max(3, int(self.size / 25))
            badge_rect = QRectF(
                self.scaled_pixmap.width() - badge_width - edge_margin,
                self.scaled_pixmap.height() - badge_height - edge_margin,
                badge_width,
                badge_height,
            )

            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(0, 0, 0, 190))
            painter.drawRoundedRect(badge_rect, badge_height / 3, badge_height / 3)
            painter.setPen(Qt.white)
            painter.drawText(badge_rect, Qt.AlignCenter, self.queue_count_text)
            painter.restore()

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
