import logging
from collections import Counter
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLayout, QMenu
)

from factory_queue_item_widget import FactoryQueueItemWidget
from factory_widget import FactoryWidget
from hud_position_utils import get_player_position, set_player_position, get_player_setting, set_player_setting
from player_identity import get_player_bucket_key, get_player_display_label, get_player_legacy_bucket_keys

class FactoryWindow(QMainWindow):
    EXPANSION_SETTING_KEY = 'factory_expansion_direction'

    def __init__(self, player, hud_pos, spacing=0):
        """
        Displays a window for all the player's factory production.
        Each "factory" (Infantry, Vehicles, etc.) gets its own
        container widget, which includes the "currently building" unit
        plus any queued units side-by-side or stacked, depending on the main layout.
        """
        super().__init__()
        self.player = player
        self.hud_pos = hud_pos
        self.spacing = spacing
        self._dragging = False
        self._applying_geometry = False
        self._anchor_refresh_pending = False

        # Each entry: factory_name -> dict with:
        # {
        #   "container": QWidget,
        #   "layout": QBoxLayout,
        #   "current_widget": FactoryWidget,
        #   "queue_widgets": [FactoryQueueItemWidget...]
        # }
        self.factory_data = {}
        self.factory_type_order = []
        self._current_layout_order = []

        # Read layout type from state
        self.layout_type = hud_pos.get('factory_layout', 'Horizontal')
        # Read whether we are showing the queue
        self.show_factory_queue = hud_pos.get('show_factory_queue', False)
        self.player_bucket_key = get_player_bucket_key(self.player, self.hud_pos)
        self.legacy_player_bucket_keys = get_player_legacy_bucket_keys(self.player, self.hud_pos)
        self.setWindowTitle(f"{get_player_display_label(self.player, self.hud_pos)} Factory Window")

        # Set up the window
        self.setWindowFlags(Qt.FramelessWindowHint
                            | Qt.WindowStaysOnTopHint
                            | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()

        # The main container for the entire window
        self.factory_frame = QWidget(self)

        # Create the main layout (vertical or horizontal).
        if self.layout_type == 'Vertical':
            self.main_layout = QVBoxLayout()
            self.main_layout.setAlignment(Qt.AlignTop)
        else:
            self.main_layout = QHBoxLayout()
            self.main_layout.setAlignment(Qt.AlignTop)

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self._apply_layout_direction(self.main_layout)
        self.main_layout.setSizeConstraint(QLayout.SetFixedSize)

        self.factory_frame.setLayout(self.main_layout)
        self.setCentralWidget(self.factory_frame)

        # Create factory widgets
        self.load_factories_and_create_widgets()

        # Default geometry
        default_size = self.get_default_size()
        self.setGeometry(0, 0, default_size, default_size)
        self.update_labels()
        self._apply_layout_and_anchor()
        self.show()
        self._schedule_anchor_refresh()

    # --------------------------------------------------------------------
    # Setup
    # --------------------------------------------------------------------
    def load_factories_and_create_widgets(self):
        """Create a sub-container for each factory (Infantry, Vehicles, etc.)."""
        show_frames = self.hud_pos.get('show_factory_frames', True)
        default_size = self.get_default_size()

        for factory_name, factory_obj in self.player.factories.items():
            self.factory_type_order.append(factory_name)
            # Container for "current" unit + queue
            container = QWidget(self.factory_frame)

            # If the main window is vertical => sub-layout is horizontal
            # If the main window is horizontal => sub-layout is vertical
            if self.layout_type == 'Vertical':
                sub_layout = QHBoxLayout(container)
                sub_layout.setAlignment(Qt.AlignTop)
            else:
                sub_layout = QVBoxLayout(container)
                sub_layout.setAlignment(Qt.AlignTop)

            sub_layout.setSpacing(0)
            sub_layout.setContentsMargins(0, 0, 0, 0)
            container.setLayout(sub_layout)

            current_widget = FactoryWidget(
                factory=factory_obj,
                player=self.player,
                color=self.player.color,
                size=default_size,
                show_frame=show_frames,
                parent=container
            )
            sub_layout.addWidget(current_widget)

            queue_widgets = []

            # Add container to the main layout
            self.main_layout.addWidget(container)

            # Store everything in self.factory_data
            self.factory_data[factory_name] = {
                "container": container,
                "layout": sub_layout,
                "current_widget": current_widget,
                "queue_widgets": queue_widgets
            }

    def get_default_size(self):
        return self.hud_pos.get('factory_size', 100)

    def _is_reverse_expansion(self):
        return get_player_setting(
            self.hud_pos,
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
        anchor = self._get_anchor_position(direction)
        set_player_setting(
            self.hud_pos,
            self.player_bucket_key,
            self.EXPANSION_SETTING_KEY,
            direction,
        )
        set_player_position(
            self.hud_pos,
            self.player_bucket_key,
            'factory',
            anchor['x'],
            anchor['y'],
        )
        self._apply_layout_direction(self.main_layout)
        self.main_layout.invalidate()
        self._refresh_window_size()
        self._move_to_saved_anchor()

    def get_default_position(self):
        anchor = self._get_saved_anchor_position()
        return self._anchor_to_top_left(anchor)

    def _get_saved_anchor_position(self):
        return get_player_position(
            self.hud_pos,
            self.player_bucket_key,
            'factory',
            legacy_root_keys=['factories'],
            legacy_bucket_keys=self.legacy_player_bucket_keys,
        )

    # --------------------------------------------------------------------
    # Movable window
    # --------------------------------------------------------------------
    def make_hud_movable(self):
        self.offset = None

        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self._dragging = True
                self.offset = event.pos()

        def mouse_move_event(event):
            if self.offset is not None:
                new_x = event.globalX() - self.offset.x()
                new_y = event.globalY() - self.offset.y()
                self.move(new_x, new_y)
                self.update_hud_position(new_x, new_y)

        def mouse_release_event(event):
            if event.button() == Qt.LeftButton:
                self._dragging = False
                self.offset = None
                self.update_hud_position(self.x(), self.y())

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event
        self.mouseReleaseEvent = mouse_release_event

    def update_hud_position(self, x, y):
        anchor = self._get_anchor_position(origin_x=x, origin_y=y)
        set_player_position(self.hud_pos, self.player_bucket_key, 'factory', anchor['x'], anchor['y'])

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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._applying_geometry or self._dragging or not self._is_reverse_expansion():
            return
        self._move_to_saved_anchor()

    def _get_anchor_position(self, direction=None, origin_x=None, origin_y=None):
        direction = direction or ('reverse' if self._is_reverse_expansion() else 'forward')
        origin_x = self.x() if origin_x is None else origin_x
        origin_y = self.y() if origin_y is None else origin_y
        size = self.size()

        anchor_x = origin_x
        anchor_y = origin_y
        if self.layout_type == 'Horizontal' and direction == 'reverse':
            anchor_x += size.width()
        elif self.layout_type == 'Vertical' and direction == 'reverse':
            anchor_y += size.height()
        return {'x': anchor_x, 'y': anchor_y}

    def top_left_to_anchor(self, x, y, size, direction=None):
        direction = direction or ('reverse' if self._is_reverse_expansion() else 'forward')
        anchor_x = x
        anchor_y = y
        if self.layout_type == 'Horizontal' and direction == 'reverse':
            anchor_x += size.width()
        elif self.layout_type == 'Vertical' and direction == 'reverse':
            anchor_y += size.height()
        return {'x': anchor_x, 'y': anchor_y}

    def _anchor_to_top_left(self, anchor, size=None):
        x = anchor['x']
        y = anchor['y']
        size = self.size() if size is None else size
        if self.layout_type == 'Horizontal' and self._is_reverse_expansion():
            x -= size.width()
        elif self.layout_type == 'Vertical' and self._is_reverse_expansion():
            y -= size.height()
        return {'x': x, 'y': y}

    def _move_to_saved_anchor(self):
        if self._dragging:
            return
        pos = self.get_default_position()
        if pos['x'] != self.x() or pos['y'] != self.y():
            self.move(pos['x'], pos['y'])

    def _get_target_window_size(self):
        self.main_layout.activate()
        size = self.main_layout.sizeHint()
        return size.expandedTo(self.minimumSizeHint())

    def _apply_window_geometry(self, anchor_to_saved=False):
        target_size = self._get_target_window_size()
        new_x = self.x()
        new_y = self.y()
        if anchor_to_saved:
            saved_anchor = self._get_saved_anchor_position()
            pos = self._anchor_to_top_left(saved_anchor, target_size)
            new_x = pos['x']
            new_y = pos['y']

        self._applying_geometry = True
        try:
            self.setGeometry(new_x, new_y, target_size.width(), target_size.height())
        finally:
            self._applying_geometry = False

    def _refresh_window_size(self):
        self._apply_window_geometry(anchor_to_saved=False)

    def _schedule_anchor_refresh(self):
        if self._anchor_refresh_pending:
            return
        self._anchor_refresh_pending = True
        QTimer.singleShot(0, self._flush_pending_anchor_refresh)

    def _flush_pending_anchor_refresh(self):
        self._anchor_refresh_pending = False
        if self._dragging:
            return
        self._apply_layout_and_anchor()

    def _apply_layout_and_anchor(self):
        self.setUpdatesEnabled(False)
        self.factory_frame.setUpdatesEnabled(False)
        try:
            self._apply_window_geometry(anchor_to_saved=not self._dragging)
            self.main_layout.update()
            self.updateGeometry()
        finally:
            self.factory_frame.setUpdatesEnabled(True)
            self.setUpdatesEnabled(True)
            self.update()
            self.factory_frame.update()

    # --------------------------------------------------------------------
    # Updating
    # --------------------------------------------------------------------
    def update_labels(self):
        """
        Refresh the 'currently building' widget and queue widgets
        for each factory. If 'show_factory_queue' is False or the
        factory is not producing, the queue is hidden/cleared.
        """
        self.player.update_factories()
        show_queue = self.hud_pos.get('show_factory_queue', False)
        currently_visible = set()

        for factory_name, data in self.factory_data.items():
            current_widget = data["current_widget"]
            queue_widgets = data["queue_widgets"]
            sub_layout = data["layout"]
            container = data["container"]

            # Get the current factory production status
            status = self.player.factory_status.get(factory_name, {"producing": False})
            current_widget.set_status(status)

            # Remove old queue widgets
            for qw in queue_widgets:
                sub_layout.removeWidget(qw)
                qw.setParent(None)
                qw.deleteLater()
            queue_widgets.clear()

            # If queue is off or not producing, skip building new queue widgets
            if not show_queue:
                container.setVisible(status.get("producing", False))
                if status.get("producing", False):
                    currently_visible.add(factory_name)
                continue
            if not status.get("producing"):
                container.hide()
                continue

            # Create new queue widgets
            queued_list = status.get("queued_units", [])
            container.show()
            currently_visible.add(factory_name)
            if not queued_list:
                continue

            c = Counter(queued_list)
            prefer_vet = (
                (factory_name == "Infantry" and self.player.barracks_infiltrated) or
                (factory_name == "Vehicles" and self.player.war_factory_infiltrated)
            )
            for unit_name, count in c.items():
                item_widget = FactoryQueueItemWidget(
                    unit_name,
                    count,
                    color=self.player.color,
                    size=self.get_default_size() // 2,
                    prefer_vet=prefer_vet,
                    parent=self
                )
                queue_widgets.append(item_widget)
                sub_layout.addWidget(item_widget)

        self._sync_display_order(currently_visible)
        self._apply_layout_and_anchor()
        self._schedule_anchor_refresh()

    def _sync_display_order(self, currently_visible):
        visible_names = [
            name for name in self.factory_type_order
            if name in currently_visible
        ]
        hidden_names = [
            name for name in self.factory_type_order
            if name not in currently_visible
        ]
        ordered_names = visible_names + hidden_names

        if ordered_names == self._current_layout_order:
            return

        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        for factory_name in ordered_names:
            self.main_layout.addWidget(self.factory_data[factory_name]["container"])

        self._current_layout_order = list(ordered_names)

    # --------------------------------------------------------------------
    # Called by control panel or external code
    # --------------------------------------------------------------------
    def set_show_frames_for_all(self, show):
        """
        Tells each factory's main widget + queue widgets to show/hide frames
        (if they implement update_show_frame).
        """
        for data in self.factory_data.values():
            data["current_widget"].update_show_frame(show)
            for qw in data["queue_widgets"]:
                if hasattr(qw, "update_show_frame"):
                    qw.update_show_frame(show)

    def set_size_for_all(self, new_size):
        """
        Tells each factory's main widget + queue widgets to update_size(new_size).
        """
        for data in self.factory_data.values():
            data["current_widget"].update_size(new_size)
            for qw in data["queue_widgets"]:
                if hasattr(qw, "update_size"):
                    qw.update_size(new_size)

        # If you really want to fix the size to the contents, call:
        # self.main_layout.setSizeConstraint(QLayout.SetFixedSize)
        # but be aware it can collapse to 0×0 if everything is hidden.

        self._refresh_window_size()
        self.show()

    def set_layout_type(self, new_layout_type):
        """
        Switches between:
          - Vertical main layout => sub-layout is horizontal side-by-side
          - Horizontal main layout => sub-layout is vertical stacked
        """
        if new_layout_type == self.layout_type:
            return

        self.layout_type = new_layout_type

        # Build a new main layout
        if self.layout_type == 'Vertical':
            new_main_layout = QVBoxLayout()
            new_main_layout.setAlignment(Qt.AlignTop)
        else:
            new_main_layout = QHBoxLayout()
            new_main_layout.setAlignment(Qt.AlignTop)

        new_main_layout.setSpacing(0)
        new_main_layout.setContentsMargins(0, 0, 0, 0)
        new_main_layout.setSizeConstraint(QLayout.SetFixedSize)
        self._apply_layout_direction(new_main_layout)

        # Remove each factory container from old layout, add to new
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            w = item.widget()
            if w:
                new_main_layout.addWidget(w)

        # Forcefully detach the old main_layout from the widget
        QWidget().setLayout(self.main_layout)

        # Set the new layout on factory_frame
        self.factory_frame.setLayout(new_main_layout)
        self.main_layout = new_main_layout

        # Now rebuild each sub-layout for each factory container
        for data in self.factory_data.values():
            container = data["container"]
            old_sub_layout = data["layout"]

            # Grab existing widgets from the old sub-layout
            items = []
            while old_sub_layout.count():
                i2 = old_sub_layout.takeAt(0)
                w2 = i2.widget()
                if w2:
                    items.append(w2)

            # Forcefully detach the old sub-layout
            QWidget().setLayout(old_sub_layout)

            # Create the new sub-layout for that factory
            if self.layout_type == 'Vertical':
                new_sub_layout = QHBoxLayout()
                new_sub_layout.setAlignment(Qt.AlignTop)
            else:
                new_sub_layout = QVBoxLayout()
                new_sub_layout.setAlignment(Qt.AlignTop)

            new_sub_layout.setSpacing(0)
            new_sub_layout.setContentsMargins(0, 0, 0, 0)

            # Assign the new sub-layout
            container.setLayout(new_sub_layout)
            data["layout"] = new_sub_layout

            # Re-add all previously existing widgets
            for w2 in items:
                new_sub_layout.addWidget(w2)

        # Call update_labels so the queue items (if any) get rebuilt
        self.update_labels()

        # Finally, resize and show
        self._refresh_window_size()
        self.show()

        logging.info(f"Factory layout updated to {new_layout_type}")
