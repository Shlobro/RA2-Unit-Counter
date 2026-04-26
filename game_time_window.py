from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout

from DataWidget import GameTimeWidget
from hud_position_utils import get_global_widget_position, set_global_widget_position


class GameTimeWindow(QWidget):
    WIDGET_KEY = "game_time"

    def __init__(self, state, hud_positions):
        super().__init__()
        self.state = state
        self.hud_positions = hud_positions
        self._drag_offset = None

        font = QFont(
            self.hud_positions.get("game_time_font_family", "Arial"),
            16,
            QFont.Bold,
        )
        self.game_time_widget = GameTimeWidget(
            state=self.state,
            hud_positions=self.hud_positions,
            text_color=QColor(self.hud_positions.get("game_time_color", "#FFFFFF")),
            size=self.hud_positions.get("game_time_widget_size", 50),
            font=font,
        )
        self.game_time_widget.setToolTip("Game time")
        self._apply_background_settings()

        self.setWindowTitle("Game Time")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setToolTip("Game time")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.game_time_widget)

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
        self.game_time_widget.update_data_size(new_size)
        self.adjustSize()

    def update_text_color(self, color):
        self.game_time_widget.update_color(new_text_color=QColor(color))
        self.adjustSize()

    def update_font_family(self, family):
        self.game_time_widget.update_font_family(family)
        self.adjustSize()

    def _apply_background_settings(self):
        self.game_time_widget.configure_background(
            enabled=self.hud_positions.get('game_time_background_enabled', False),
            color=self.hud_positions.get('game_time_background_color', '#A0000000'),
            width=self.hud_positions.get('game_time_background_width', 0),
            height=self.hud_positions.get('game_time_background_height', 0),
        )
        self.adjustSize()

    def update_background_settings(self):
        self._apply_background_settings()
