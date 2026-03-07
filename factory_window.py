import logging
from collections import Counter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QLayout
)

from factory_queue_item_widget import FactoryQueueItemWidget
from factory_widget import FactoryWidget
from hud_position_utils import ensure_player_bucket, get_player_position

class FactoryWindow(QMainWindow):
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

        # Each entry: factory_name -> dict with:
        # {
        #   "container": QWidget,
        #   "layout": QBoxLayout,
        #   "current_widget": FactoryWidget,
        #   "queue_widgets": [FactoryQueueItemWidget...]
        # }
        self.factory_data = {}

        # Read layout type from state
        self.layout_type = hud_pos.get('factory_layout', 'Horizontal')
        # Read whether we are showing the queue
        self.show_factory_queue = hud_pos.get('show_factory_queue', False)

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
        # REMOVE the fixed-size constraint so the layout can expand/shrink properly:
        # self.main_layout.setSizeConstraint(QLayout.SetFixedSize)

        self.factory_frame.setLayout(self.main_layout)
        self.setCentralWidget(self.factory_frame)

        # Create factory widgets
        self.load_factories_and_create_widgets()

        # Default geometry
        pos = self.get_default_position()
        default_size = self.get_default_size()
        self.setGeometry(pos['x'], pos['y'], default_size, default_size)
        self.show()

    # --------------------------------------------------------------------
    # Setup
    # --------------------------------------------------------------------
    def load_factories_and_create_widgets(self):
        """Create a sub-container for each factory (Infantry, Vehicles, etc.)."""
        show_frames = self.hud_pos.get('show_factory_frames', True)
        default_size = self.get_default_size()

        for factory_name, factory_obj in self.player.factories.items():
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

    def _get_player_color_key(self):
        if isinstance(self.player.color_name, str):
            return self.player.color_name
        return self.player.color_name.name()

    def get_default_position(self):
        return get_player_position(
            self.hud_pos,
            self._get_player_color_key(),
            'factory',
            legacy_root_keys=['factories'],
        )

    # --------------------------------------------------------------------
    # Movable window
    # --------------------------------------------------------------------
    def make_hud_movable(self):
        self.offset = None

        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self.offset = event.pos()

        def mouse_move_event(event):
            if self.offset is not None:
                new_x = event.globalX() - self.offset.x()
                new_y = event.globalY() - self.offset.y()
                self.move(new_x, new_y)
                self.update_hud_position(new_x, new_y)

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event

    def update_hud_position(self, x, y):
        player_bucket = ensure_player_bucket(self.hud_pos, self._get_player_color_key())
        player_bucket['factory'] = {"x": int(x), "y": int(y)}

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

        for factory_name, data in self.factory_data.items():
            current_widget = data["current_widget"]
            queue_widgets = data["queue_widgets"]
            sub_layout = data["layout"]

            # Get the current factory production status
            status = self.player.factory_status.get(factory_name, {"producing": False})
            current_widget.set_status(status)

            # Remove old queue widgets
            for qw in queue_widgets:
                qw.setParent(None)
                qw.deleteLater()
            queue_widgets.clear()

            # If queue is off or not producing, skip building new queue widgets
            if not show_queue:
                continue
            if not status.get("producing"):
                continue

            # Create new queue widgets
            queued_list = status.get("queued_units", [])
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

        # Force a re-layout
        self.main_layout.update()
        self.updateGeometry()

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

        self.adjustSize()
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
        self.adjustSize()
        self.show()

        logging.info(f"Factory layout updated to {new_layout_type}")
