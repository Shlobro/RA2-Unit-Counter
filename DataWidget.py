# DataWidget.py
import logging
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor, QPainter, QFont, QFontMetrics
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout

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

        # Create label for displaying data
        self.data_label = QLabel(str(self.value), self)
        if self.use_fixed_width:
            self.data_label.setAlignment(Qt.AlignCenter)
        try:
            self.data_label.setStyleSheet(f"color: {QColor(self.text_color).name()}; margin-top: -2px;")
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
        total_width = self.data_label.width() + 1
        self.setFixedSize(total_width, self.data_label.height())

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
                self.data_label.setStyleSheet(f"color: {self.text_color.name()}; margin-top: -2px;")
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
            total_width = self.icon_label.width() + self.data_label.width()
            total_height = max(self.icon_label.height(), self.data_label.height())
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
                self.setFixedSize(self.icon_label.width() + self.data_label.width() + 1, max(self.icon_label.height(), self.data_label.height()))
            else:
                super().adjust_size()
        except Exception as e:
            logging.exception("Error adjusting size in NameWidget: %s", e)

class FlagWidget(QWidget):
    def __init__(self, image_path=None, size=16, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.size = size

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.icon_label = QLabel(self)
        self.load_and_set_image()
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignVCenter)
        self.adjust_size()

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
            self.setFixedSize(self.icon_label.width(), self.icon_label.height())
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
            # Use QFontMetrics to calculate the current text width
            fm = QFontMetrics(self.data_label.font())
            text_width = fm.horizontalAdvance(self.data_label.text())
            total_width = self.icon_label.width() + text_width + self.layout.spacing()
            total_height = max(self.icon_label.height(), self.data_label.height())
            self.setFixedSize(total_width, total_height)
        except Exception as e:
            logging.exception("Error adjusting size in MoneySpentWidget: %s", e)

