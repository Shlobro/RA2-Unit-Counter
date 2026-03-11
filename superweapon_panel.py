from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLayout, QSizePolicy, QVBoxLayout, QWidget, QMenu

from superweapon_widget import SuperweaponWidget
from hud_position_utils import get_player_setting, set_player_setting, get_player_position, set_player_position
from player_identity import get_player_bucket_key, get_player_legacy_bucket_keys


class SuperweaponTimerPanel(QWidget):
    EXPANSION_SETTING_KEY = 'superweapon_expansion_direction'

    def __init__(self, player, hud_positions, parent=None):
        super().__init__(parent)
        self.player = player
        self.hud_positions = hud_positions
        self.widgets = {}
        self.layout_type = hud_positions.get('superweapon_layout', 'Horizontal')
        self.player_bucket_key = get_player_bucket_key(self.player, self.hud_positions)
        self.legacy_player_bucket_keys = get_player_legacy_bucket_keys(self.player, self.hud_positions)

        if self.layout_type == 'Vertical':
            self.main_layout = QVBoxLayout()
            self.main_layout.setAlignment(Qt.AlignTop)
        else:
            self.main_layout = QHBoxLayout()
            self.main_layout.setAlignment(Qt.AlignTop)

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSizeConstraint(QLayout.SetFixedSize)
        self._apply_layout_direction(self.main_layout)
        self.setLayout(self.main_layout)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self._build_widgets()

    def _is_reverse_expansion(self):
        return get_player_setting(
            self.hud_positions,
            self.player_bucket_key,
            self.EXPANSION_SETTING_KEY,
            'forward',
            legacy_bucket_keys=self.legacy_player_bucket_keys,
        ) == 'reverse'

    def _apply_layout_direction(self, layout):
        if self.layout_type == 'Horizontal':
            layout.setDirection(QHBoxLayout.RightToLeft if self._is_reverse_expansion() else QHBoxLayout.LeftToRight)
        else:
            layout.setDirection(QVBoxLayout.BottomToTop if self._is_reverse_expansion() else QVBoxLayout.TopToBottom)

    def _set_expansion_direction(self, direction):
        if hasattr(self, '_container_window') and self._container_window is not None:
            anchor = self.top_left_to_anchor(self._container_window.x(), self._container_window.y(), self._container_window.size(), direction)
        else:
            anchor = None
        set_player_setting(
            self.hud_positions,
            self.player_bucket_key,
            self.EXPANSION_SETTING_KEY,
            direction,
        )
        if anchor is not None:
            self.save_anchor_position(anchor)
        self._apply_layout_direction(self.main_layout)
        self.main_layout.invalidate()
        self.adjustSize()
        self.updateGeometry()
        if hasattr(self, '_container_window') and self._container_window is not None:
            self._container_window.adjustSize()
            self._move_container_to_saved_anchor()

    def get_saved_anchor_position(self):
        return get_player_position(
            self.hud_positions,
            self.player_bucket_key,
            'superweapons',
            legacy_root_keys=['superweapon'],
            legacy_bucket_keys=self.legacy_player_bucket_keys,
        )

    def save_anchor_position(self, anchor):
        set_player_position(self.hud_positions, self.player_bucket_key, 'superweapons', anchor['x'], anchor['y'])

    def top_left_to_anchor(self, x, y, size, direction=None):
        direction = direction or ('reverse' if self._is_reverse_expansion() else 'forward')
        anchor_x = x
        anchor_y = y
        if self.layout_type == 'Horizontal' and direction == 'reverse':
            anchor_x += size.width()
        elif self.layout_type == 'Vertical' and direction == 'reverse':
            anchor_y += size.height()
        return {'x': anchor_x, 'y': anchor_y}

    def anchor_to_top_left(self, anchor, size):
        x = anchor['x']
        y = anchor['y']
        if self.layout_type == 'Horizontal' and self._is_reverse_expansion():
            x -= size.width()
        elif self.layout_type == 'Vertical' and self._is_reverse_expansion():
            y -= size.height()
        return {'x': x, 'y': y}

    def _move_container_to_saved_anchor(self):
        if not hasattr(self, '_container_window') or self._container_window is None:
            return
        anchor = self.get_saved_anchor_position()
        if not anchor:
            return
        pos = self.anchor_to_top_left(anchor, self._container_window.size())
        if pos['x'] != self._container_window.x() or pos['y'] != self._container_window.y():
            self._container_window.move(pos['x'], pos['y'])

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        if self.layout_type == 'Horizontal':
            expand_forward = menu.addAction("Expand Right")
            expand_reverse = menu.addAction("Expand Left")
        else:
            expand_forward = menu.addAction("Expand Down")
            expand_reverse = menu.addAction("Expand Up")
        expand_forward.setCheckable(True)
        expand_reverse.setCheckable(True)
        if self._is_reverse_expansion():
            expand_reverse.setChecked(True)
        else:
            expand_forward.setChecked(True)

        selected_action = menu.exec(event.globalPos())
        if selected_action == expand_forward:
            self._set_expansion_direction('forward')
        elif selected_action == expand_reverse:
            self._set_expansion_direction('reverse')

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
        self._apply_layout_direction(new_layout)

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
