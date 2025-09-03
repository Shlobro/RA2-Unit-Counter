# factory_panel.py
import logging
from collections import Counter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from factory_queue_item_widget import FactoryQueueItemWidget
from factory_widget import FactoryWidget

MAX_QUEUE_SLOTS = 5  # Adjust as you like

class FactoryPanel(QWidget):
    def __init__(self, player, hud_pos, parent=None):
        super().__init__(parent)
        self.player = player
        self.hud_pos = hud_pos

        self.factory_data = {}
        self.layout_type = hud_pos.get('factory_layout', 'Horizontal')
        self.show_factory_queue = hud_pos.get('show_factory_queue', True)

        # Main layout for the panel
        if self.layout_type == 'Vertical':
            self.main_layout = QVBoxLayout()
        else:
            self.main_layout = QHBoxLayout()

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.main_layout)

        self.load_factories_and_create_widgets()

    def get_default_size(self):
        return self.hud_pos.get('factory_size', 100)

    def load_factories_and_create_widgets(self):
        show_frames = self.hud_pos.get('show_factory_frames', True)
        default_size = self.get_default_size()

        for factory_name, factory_obj in self.player.factories.items():
            # Container for this factory's row/column
            container = QWidget(self)
            if self.layout_type == 'Vertical':
                sub_layout = QHBoxLayout(container)
            else:
                sub_layout = QVBoxLayout(container)

            sub_layout.setSpacing(0)
            sub_layout.setContentsMargins(0, 0, 0, 0)
            container.setLayout(sub_layout)

            # 1) "Currently Building" widget
            current_widget = FactoryWidget(
                factory=factory_obj,
                color=self.player.color,
                size=default_size,
                show_frame=show_frames,
                parent=container
            )
            sub_layout.addWidget(current_widget)

            # 2) Create a fixed number of placeholders for the queue
            #    We'll store them so we can fill them later.
            queue_placeholders = []
            for i in range(MAX_QUEUE_SLOTS):
                placeholder = QLabel(parent=container)
                # Give it a fixed size, e.g. half the default or whatever you want.
                placeholder.setFixedSize(default_size // 2, default_size // 2)
                # Start out invisible or blank. We can do placeholder.setText("") if we want.
                # But DO NOT hide() it, or the layout will compress it. Keep it shown but blank.
                sub_layout.addWidget(placeholder)
                queue_placeholders.append(placeholder)

            # Record everything
            self.main_layout.addWidget(container)
            self.factory_data[factory_name] = {
                "container": container,
                "layout": sub_layout,
                "current_widget": current_widget,
                "queue_placeholders": queue_placeholders,
                "queue_widgets": []
            }

    def update_labels(self):
        self.player.update_factories()
        show_queue = self.hud_pos.get('show_factory_queue', True)

        for factory_name, data in self.factory_data.items():
            current_widget = data["current_widget"]
            placeholders = data["queue_placeholders"]

            # Update the main factory widget
            status = self.player.factory_status.get(factory_name, {"producing": False})
            current_widget.set_status(status)

            # Fill placeholders
            if show_queue and status.get("producing"):
                queued_list = status.get("queued_units", [])
                c = Counter(queued_list)
                # Flatten the (unit_name, count) pairs
                queue_items = []
                for unit_name, cnt in c.items():
                    queue_items.extend([unit_name] * cnt)
            else:
                queue_items = []

            # Now update exactly MAX_QUEUE_SLOTS placeholders
            for i in range(MAX_QUEUE_SLOTS):
                placeholder = placeholders[i]

                if i < len(queue_items):
                    unit_name = queue_items[i]
                    # Instead of creating or adding a new widget, just set some text or icon
                    # or if you want a real widget, see advanced approach below.
                    placeholder.setText(unit_name)
                    placeholder.setStyleSheet("border: 1px solid red;")  # for example
                else:
                    # No item => blank
                    placeholder.setText("")
                    placeholder.setStyleSheet("border: none;")

        self.layout().update()
        self.updateGeometry()

    def set_layout_type(self, new_layout_type):
        """Same logic as your old set_layout_type, but for QWidget instead of QMainWindow."""
        if new_layout_type == self.layout_type:
            return
        self.layout_type = new_layout_type

        if self.layout_type == 'Vertical':
            new_main_layout = QVBoxLayout()
            new_main_layout.setAlignment(Qt.AlignTop)
        else:
            new_main_layout = QHBoxLayout()
            new_main_layout.setAlignment(Qt.AlignTop)

        new_main_layout.setSpacing(0)
        new_main_layout.setContentsMargins(0, 0, 0, 0)

        # Move each factory container from old layout to new
        while self.main_layout.count():
            item = self.main_layout.takeAt(0)
            w = item.widget()
            if w:
                new_main_layout.addWidget(w)

        # Forcefully detach old layout
        QWidget().setLayout(self.main_layout)

        # Replace layout
        self.setLayout(new_main_layout)
        self.main_layout = new_main_layout

        # Rebuild each sub-layout
        for data in self.factory_data.values():
            container = data["container"]
            old_sub_layout = data["layout"]
            items = []
            while old_sub_layout.count():
                i2 = old_sub_layout.takeAt(0)
                w2 = i2.widget()
                if w2:
                    items.append(w2)

            QWidget().setLayout(old_sub_layout)

            if self.layout_type == 'Vertical':
                new_sub_layout = QHBoxLayout()
                new_sub_layout.setAlignment(Qt.AlignTop)
            else:
                new_sub_layout = QVBoxLayout()
                new_sub_layout.setAlignment(Qt.AlignTop)

            new_sub_layout.setSpacing(0)
            new_sub_layout.setContentsMargins(0, 0, 0, 0)

            container.setLayout(new_sub_layout)
            data["layout"] = new_sub_layout

            for w2 in items:
                new_sub_layout.addWidget(w2)

        # Force update
        self.update_labels()
        self.updateGeometry()

    def set_size_for_all(self, new_size):
        for data in self.factory_data.values():
            data["current_widget"].update_size(new_size)
            for qw in data["queue_widgets"]:
                if hasattr(qw, "update_size"):
                    qw.update_size(new_size)

        # self.main_layout.setSizeConstraint(QLayout.SetFixedSize)  # optional
        self.adjustSize()
        self.show()

    def set_show_frames_for_all(self, show):
        for data in self.factory_data.values():
            data["current_widget"].update_show_frame(show)
            for qw in data["queue_widgets"]:
                if hasattr(qw, "update_show_frame"):
                    qw.update_show_frame(show)
