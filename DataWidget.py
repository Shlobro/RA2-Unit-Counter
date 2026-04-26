# DataWidget.py
import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

from match_timeline import get_match_elapsed_ms

class BaseDataWidget(QWidget):
    def __init__(self, data=None, text_color=Qt.black, size=16, font=None, use_fixed_width=False, max_digits=10, parent=None):
        """
        Base widget to display numerical data with optional fixed width.
        """
        super().__init__(parent)
        self.size = size
        self.value = data if data is not None else 0
        self.custom_font = font if font is not None else QFont()
        self.text_color = text_color
        self.use_fixed_width = use_fixed_width
        self.max_digits = max_digits
        self.background_enabled = False
        self.background_color = QColor(0, 0, 0, 160)
        self.background_width = 0
        self.background_height = 0

        # Create label for displaying data
        self.data_label = QLabel(str(self.value), self)
        if self.use_fixed_width:
            self.data_label.setAlignment(Qt.AlignCenter)
        try:
            self._apply_label_style()
        except Exception as e:
            logging.exception("Error setting stylesheet in BaseDataWidget: %s", e)

        self.update_font_size()

        if self.use_fixed_width:
            self.compute_fixed_width()
            self.data_label.setFixedWidth(self.fixed_width)

        # Create a horizontal layout for the widget
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(1)
        self.layout.addWidget(self.data_label, alignment=Qt.AlignVCenter)
        self.layout.setAlignment(Qt.AlignCenter)

    def configure_background(self, enabled=False, color=None, width=0, height=0):
        self.background_enabled = bool(enabled)
        if color is not None:
            resolved = QColor(color)
            if resolved.isValid():
                self.background_color = resolved
        self.background_width = max(0, int(width or 0))
        self.background_height = max(0, int(height or 0))
        self.update()
        self.adjust_size()

    def _content_size(self):
        return self.layout.sizeHint()

    def _background_size(self, content_width, content_height):
        if not self.background_enabled:
            return content_width, content_height
        return max(content_width, self.background_width), max(content_height, self.background_height)

    def paintEvent(self, event):
        if self.background_enabled:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.fillRect(self.rect(), self.background_color)
        super().paintEvent(event)

    def compute_fixed_width(self):
        """
        Compute a fixed width based on the maximum number of digits.
        """
        try:
            font = self.custom_font
            font.setPointSize(int(self.size * 0.6))
            fm = QFontMetrics(font)
            max_number = '8' * self.max_digits
            self.fixed_width = fm.horizontalAdvance(max_number)
        except Exception as e:
            logging.exception("Error computing fixed width: %s", e)
            self.fixed_width = 50

    def _apply_label_style(self):
        text_color = QColor(self.text_color).name()
        self.data_label.setStyleSheet(f"color: {text_color}; margin-top: -2px;")

    def update_font_size(self):
        """
        Update the label's font size based on the widget size.
        """
        try:
            font = self.custom_font
            font.setPointSize(int(self.size * 0.6))
            self.data_label.setFont(font)
            self.data_label.adjustSize()
        except Exception as e:
            logging.exception("Error updating font size: %s", e)

    def update_font_family(self, family):
        if family:
            self.custom_font.setFamily(family)
        self.update_font_size()
        self.adjust_size()

    def update_data_size(self, new_size):
        """
        Adjust the widget's size (and font) dynamically.
        """
        self.size = new_size
        self.update_font_size()
        if self.use_fixed_width:
            self.compute_fixed_width()
            self.data_label.setFixedWidth(self.fixed_width)
        self.adjust_size()

    def adjust_size(self):
        """
        Recalculate the widget's size.
        """
        content_size = self._content_size()
        total_width, total_height = self._background_size(content_size.width(), content_size.height())
        self.setFixedSize(total_width, total_height)

    def on_value_changed(self, value):
        """
        Slot to update the widget when the value changes.
        """
        try:
            self.value = value
            self.data_label.setText(str(int(value)))
            self.data_label.adjustSize()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error in on_value_changed: %s", e)

    def update_color(self, new_text_color=None):
        """
        Update the text color of the data label.
        """
        try:
            if new_text_color is not None:
                self.text_color = QColor(new_text_color)
                logging.debug(f"update_color: new_text_color: {self.text_color.name()}")
                self._apply_label_style()
                self.data_label.adjustSize()
                self.adjust_size()
        except Exception as e:
            logging.exception("Error updating color: %s", e)

    def update_data(self, new_data):
        """
        Smoothly update the displayed data using QPropertyAnimation.
        """
        try:
            self.on_value_changed(new_data)
        except Exception as e:
            logging.exception("Error updating data with animation: %s", e)


class MoneyWidget(BaseDataWidget):
    def __init__(self, data=None, text_color=Qt.white, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, use_fixed_width=True, max_digits=10, parent=parent)
        self.target_value = int(self.value)
        self.animation_timer = QTimer(self)
        self.animation_timer.setInterval(16)
        self.animation_timer.timeout.connect(self._animate_step)
        self.update_data_label()

    def on_value_changed(self, value):
        try:
            self.value = int(value)
            self.target_value = self.value
            self.update_data_label()
            self.data_label.adjustSize()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error in MoneyWidget.on_value_changed: %s", e)

    def update_data(self, new_data):
        try:
            self.target_value = int(new_data)
            if not self.animation_timer.isActive():
                self.animation_timer.start()
        except Exception as e:
            logging.exception("Error updating money data: %s", e)

    def _animate_step(self):
        try:
            current_value = int(self.value)
            target_value = int(self.target_value)
            delta = target_value - current_value

            if delta == 0:
                self.animation_timer.stop()
                return

            step = max(1, abs(delta) // 5)
            if delta > 0:
                self.value = min(current_value + step, target_value)
            else:
                self.value = max(current_value - step, target_value)

            self.update_data_label()
            self.data_label.adjustSize()
            self.adjust_size()
        except Exception as e:
            self.animation_timer.stop()
            logging.exception("Error animating money widget: %s", e)

    def update_data_label(self):
        try:
            self.data_label.setText(f"${int(self.value)}")
        except Exception as e:
            logging.exception("Error updating data label in MoneyWidget: %s", e)


class PowerWidget(BaseDataWidget):
    def __init__(self, data=None, image_path='icons/bolt.png', image_color=Qt.green, text_color=Qt.green, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, use_fixed_width=False, parent=parent)
        self.image_path = image_path
        self.image_color = image_color
        self.icon_label = QLabel(self)
        self.load_and_set_image()
        self.layout.insertWidget(0, self.icon_label, alignment=Qt.AlignVCenter)
        self.layout.setSpacing(0)
        self.data_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.update_font_size()
        self.adjust_size()

    def load_and_set_image(self):
        try:
            pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            colored_pixmap = QPixmap(pixmap.size())
            colored_pixmap.fill(Qt.transparent)
            painter = QPainter(colored_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(colored_pixmap.rect(), QColor(self.image_color))
            painter.end()
            self.icon_label.setPixmap(colored_pixmap)
            self.icon_label.setFixedSize(colored_pixmap.size())
        except Exception as e:
            logging.exception("Error loading and setting image in PowerWidget: %s", e)

    def update_data_size(self, new_size):
        try:
            self.size = new_size
            self.load_and_set_image()
            self.update_font_size()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error updating data size in PowerWidget: %s", e)

    def adjust_size(self):
        try:
            content_size = self._content_size()
            total_width, total_height = self._background_size(content_size.width(), content_size.height())
            self.setFixedSize(total_width, total_height)
        except Exception as e:
            logging.exception("Error adjusting size in PowerWidget: %s", e)

    def on_value_changed(self, value):
        try:
            self.value = value
            self.data_label.setText(str(int(value)))
            self.data_label.adjustSize()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error in PowerWidget.on_value_changed: %s", e)

    def update_color(self, new_image_color=None, new_text_color=None):
        try:
            if new_image_color is not None:
                self.image_color = QColor(new_image_color)
                self.load_and_set_image()
            super().update_color(new_text_color=new_text_color)
        except Exception as e:
            logging.exception("Error updating color in PowerWidget: %s", e)


class NameWidget(BaseDataWidget):
    def __init__(self, data=None, image_path=None, image_color=None, text_color=Qt.black, size=16, font=None, parent=None):
        super().__init__(data=data, text_color=text_color, size=size, font=font, parent=parent)
        self.image_path = image_path
        self.image_color = image_color
        if self.image_path:
            self.icon_label = QLabel(self)
            self.load_and_set_image()
            self.layout.insertWidget(0, self.icon_label, alignment=Qt.AlignVCenter)
        self.update_font_size()

    def load_and_set_image(self):
        try:
            pixmap = QPixmap(self.image_path).scaled(self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            if self.image_color is not None:
                colored_pixmap = QPixmap(pixmap.size())
                colored_pixmap.fill(Qt.transparent)
                painter = QPainter(colored_pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_Source)
                painter.drawPixmap(0, 0, pixmap)
                painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
                painter.fillRect(colored_pixmap.rect(), QColor(self.image_color))
                painter.end()
                pixmap = colored_pixmap
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setFixedSize(pixmap.size())
        except Exception as e:
            logging.exception("Error loading image in NameWidget: %s", e)

    def update_data_size(self, new_size):
        try:
            self.size = new_size
            if self.image_path:
                self.load_and_set_image()
            self.update_font_size()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error updating data size in NameWidget: %s", e)

    def adjust_size(self):
        try:
            if self.image_path:
                content_size = self._content_size()
                total_width, total_height = self._background_size(content_size.width(), content_size.height())
                self.setFixedSize(total_width, total_height)
            else:
                super().adjust_size()
        except Exception as e:
            logging.exception("Error adjusting size in NameWidget: %s", e)

class FlagWidget(QWidget):
    def __init__(self, image_path=None, size=16, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.size = size
        self.background_enabled = False
        self.background_color = QColor(0, 0, 0, 160)
        self.background_width = 0
        self.background_height = 0

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel(self)
        self.load_and_set_image()
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignVCenter)
        self.adjust_size()

    def configure_background(self, enabled=False, color=None, width=0, height=0):
        self.background_enabled = bool(enabled)
        if color is not None:
            resolved = QColor(color)
            if resolved.isValid():
                self.background_color = resolved
        self.background_width = max(0, int(width or 0))
        self.background_height = max(0, int(height or 0))
        self.update()
        self.adjust_size()

    def paintEvent(self, event):
        if self.background_enabled:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, False)
            painter.fillRect(self.rect(), self.background_color)
        super().paintEvent(event)

    def load_and_set_image(self):
        try:
            pixmap = QPixmap(self.image_path).scaled(
                self.size, self.size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            self.icon_label.setPixmap(pixmap)
            self.icon_label.setFixedSize(pixmap.size())
        except Exception as e:
            logging.exception("Error loading image in FlagWidget: %s", e)

    def update_data_size(self, new_size):
        try:
            self.size = new_size
            self.load_and_set_image()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error updating data size in FlagWidget: %s", e)

    def adjust_size(self):
        try:
            content_size = self.layout.sizeHint()
            width = content_size.width()
            height = content_size.height()
            if self.background_enabled:
                width = max(width, self.background_width)
                height = max(height, self.background_height)
            self.setFixedSize(width, height)
        except Exception as e:
            logging.exception("Error adjusting size in FlagWidget: %s", e)


class MoneySpentWidget(BaseDataWidget):
    def __init__(self, data=None, text_color=Qt.red, size=16, font=None, parent=None):
        # Disable fixed-width so that it can expand dynamically.
        super().__init__(data=data, text_color=text_color, size=size, font=font, use_fixed_width=False, parent=parent)
        self.image_path = 'icons/money_spent_icon.png'
        self.icon_label = QLabel(self)
        # Insert the icon before the data label in the layout.
        self.layout.insertWidget(0, self.icon_label, alignment=Qt.AlignVCenter)
        self.layout.setSpacing(0)  # Remove extra spacing between icon and text.
        self.data_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.load_and_set_image()
        self.update_data_label()
        self.adjust_size()

    def load_and_set_image(self):
        try:
            # Scale the icon using the current widget size (self.size)
            pixmap = QPixmap(self.image_path).scaled(self.size, self.size,
                                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Apply text color to the icon
            colored_pixmap = QPixmap(pixmap.size())
            colored_pixmap.fill(Qt.transparent)
            painter = QPainter(colored_pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.drawPixmap(0, 0, pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(colored_pixmap.rect(), self.text_color)
            painter.end()
            
            self.icon_label.setPixmap(colored_pixmap)
            self.icon_label.setFixedSize(colored_pixmap.size())
        except Exception as e:
            logging.exception("Error loading image in MoneySpentWidget: %s", e)

    def update_data_size(self, new_size):
        # Update the internal size and then refresh both text and icon.
        self.size = new_size
        self.load_and_set_image()  # Reload the icon with the new size.
        self.update_font_size()    # Update the text font size.
        self.adjust_size()

    def on_value_changed(self, value):
        try:
            self.value = value
            self.update_data_label()
            self.data_label.adjustSize()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error in MoneySpentWidget.on_value_changed: %s", e)

    def update_data_label(self):
        try:
            self.data_label.setText(f"{int(self.value)}")
        except Exception as e:
            logging.exception("Error updating data label in MoneySpentWidget: %s", e)

    def adjust_size(self):
        try:
            content_size = self._content_size()
            total_width, total_height = self._background_size(content_size.width(), content_size.height())
            self.setFixedSize(total_width, total_height)
        except Exception as e:
            logging.exception("Error adjusting size in MoneySpentWidget: %s", e)


class GameTimeWidget(BaseDataWidget):
    def __init__(self, state, hud_positions, text_color=Qt.white, size=16, font=None, parent=None):
        super().__init__(
            data=0,
            text_color=text_color,
            size=size,
            font=font,
            use_fixed_width=False,
            parent=parent,
        )
        self.state = state
        self.hud_positions = hud_positions
        self._timer = QTimer(self)
        self._timer.setInterval(250)
        self._timer.timeout.connect(self.refresh_time)
        self.data_label.setAlignment(Qt.AlignCenter)
        self.refresh_time()
        self._timer.start()

    @staticmethod
    def format_elapsed(elapsed_ms):
        total_seconds = max(0, int(elapsed_ms // 1000))
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def refresh_time(self):
        self.update_data(get_match_elapsed_ms(self.state))

    def on_value_changed(self, value):
        try:
            self.value = max(0, int(value))
            self.data_label.setText(self.format_elapsed(self.value))
            self.data_label.adjustSize()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error in GameTimeWidget.on_value_changed: %s", e)

    def update_font_family(self, family):
        try:
            if family:
                self.custom_font.setFamily(family)
            self.update_font_size()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error updating game time font family: %s", e)

    def update_data_size(self, new_size):
        super().update_data_size(new_size)
        self.refresh_time()

    def adjust_size(self):
        try:
            fm = QFontMetrics(self.data_label.font())
            text_width = fm.horizontalAdvance("88:88:88")
            content_width = max(text_width, self.data_label.width()) + 4
            content_height = self.data_label.height()
            total_width, total_height = self._background_size(content_width, content_height)
            self.setFixedSize(total_width, total_height)
        except Exception as e:
            logging.exception("Error adjusting size in GameTimeWidget: %s", e)


class MapNameWidget(BaseDataWidget):
    def __init__(self, state, text_color=Qt.white, size=16, font=None, parent=None):
        super().__init__(
            data="",
            text_color=text_color,
            size=size,
            font=font,
            use_fixed_width=False,
            parent=parent,
        )
        self.state = state
        self._timer = QTimer(self)
        self._timer.setInterval(500)
        self._timer.timeout.connect(self.refresh_map_name)
        self.data_label.setAlignment(Qt.AlignCenter)
        self.refresh_map_name()
        self._timer.start()

    def refresh_map_name(self):
        self.update_data(getattr(self.state, "current_map_name", "") or "")

    def on_value_changed(self, value):
        try:
            self.value = value or ""
            self.data_label.setText(self.value)
            self.data_label.adjustSize()
            self.adjust_size()
        except Exception as e:
            logging.exception("Error in MapNameWidget.on_value_changed: %s", e)

    def adjust_size(self):
        try:
            fm = QFontMetrics(self.data_label.font())
            text_width = fm.horizontalAdvance(self.data_label.text() or "Map Name")
            content_width = max(text_width, self.data_label.width()) + 8
            content_height = self.data_label.height()
            total_width, total_height = self._background_size(content_width, content_height)
            self.setFixedSize(total_width, total_height)
        except Exception as e:
            logging.exception("Error adjusting size in MapNameWidget: %s", e)

