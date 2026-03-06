from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLayout, QSizePolicy, QVBoxLayout, QWidget

from superweapon_widget import SuperweaponWidget


class SuperweaponTimerPanel(QWidget):
    def __init__(self, player, hud_positions, parent=None):
        super().__init__(parent)
        self.player = player
        self.hud_positions = hud_positions
        self.widgets = {}
        self.layout_type = hud_positions.get('superweapon_layout', 'Horizontal')

        if self.layout_type == 'Vertical':
            self.main_layout = QVBoxLayout()
            self.main_layout.setAlignment(Qt.AlignTop)
        else:
            self.main_layout = QHBoxLayout()
            self.main_layout.setAlignment(Qt.AlignTop)

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.main_layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._build_widgets()

    def _build_widgets(self):
        size = self.hud_positions.get('superweapon_widget_size', 100)
        show_frames = self.hud_positions.get('show_superweapon_frames', True)

        for name in self.player.superweapon_order:
            widget = SuperweaponWidget(
                superweapon_name=name,
                color=self.player.color,
                size=size,
                show_frame=show_frames,
                parent=self,
            )
            widget.setToolTip(name)
            self.main_layout.addWidget(widget)
            self.widgets[name] = widget

        self.update_labels()

    def update_labels(self):
        visible_count = 0
        for name in self.player.superweapon_order:
            widget = self.widgets.get(name)
            if widget is None:
                continue

            info = self.player.superweapon_timers.get(name, {})
            widget.set_status(info)

            if info.get("owned", False):
                visible_count += 1

        self.setVisible(visible_count > 0)
        self.updateGeometry()

    def update_size(self, new_size):
        for widget in self.widgets.values():
            widget.update_size(new_size)
        self.adjustSize()

    def update_show_frame(self, show):
        for widget in self.widgets.values():
            widget.update_show_frame(show)
        self.adjustSize()

    def set_size_for_all(self, new_size):
        self.update_size(new_size)

    def set_show_frames_for_all(self, show):
        self.update_show_frame(show)

    def set_layout_type(self, new_layout_type):
        if new_layout_type == self.layout_type:
            return

        self.layout_type = new_layout_type
        if self.layout_type == 'Vertical':
            new_layout = QVBoxLayout()
            new_layout.setAlignment(Qt.AlignTop)
        else:
            new_layout = QHBoxLayout()
            new_layout.setAlignment(Qt.AlignTop)

        new_layout.setSpacing(0)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSizeConstraint(QLayout.SetFixedSize)

        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget:
                new_layout.addWidget(widget)

        QWidget().setLayout(self.main_layout)
        self.setLayout(new_layout)
        self.main_layout = new_layout
        self.update_labels()
        self.adjustSize()
