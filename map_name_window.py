from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout

from DataWidget import MapNameWidget
from hud_position_utils import get_global_widget_position, set_global_widget_position


class MapNameWindow(QWidget):
    WIDGET_KEY = "map_name"

    def __init__(self, state, hud_positions):
        super().__init__()
        self.state = state
        self.hud_positions = hud_positions
        self._drag_offset = None

        font = QFont("Arial", 16, QFont.Bold)
        self.map_name_widget = MapNameWidget(
            state=self.state,
            text_color=QColor(self.hud_positions.get("map_name_color", "#FFFFFF")),
            size=self.hud_positions.get("map_name_widget_size", 50),
            font=font,
        )
        self.map_name_widget.setToolTip("Current map name")

        self.setWindowTitle("Map Name")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setToolTip("Current map name")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.map_name_widget)

        self.adjustSize()
        saved_pos = get_global_widget_position(self.hud_positions, self.WIDGET_KEY)
        self.move(saved_pos["x"], saved_pos["y"])

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.pos()

    def mouseMoveEvent(self, event):
        if self._drag_offset is None:
            return
        x = event.globalX() - self._drag_offset.x()
        y = event.globalY() - self._drag_offset.y()
        self.move(x, y)
        set_global_widget_position(self.hud_positions, self.WIDGET_KEY, x, y)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_offset = None
            set_global_widget_position(self.hud_positions, self.WIDGET_KEY, self.x(), self.y())

    def update_widget_size(self, new_size):
        self.map_name_widget.update_data_size(new_size)
        self.adjustSize()

    def update_text_color(self, color):
        self.map_name_widget.update_color(new_text_color=QColor(color))
        self.adjustSize()
