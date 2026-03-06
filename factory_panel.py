# factory_panel.py
import logging
from collections import Counter
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy, QLayout

from factory_queue_item_widget import FactoryQueueItemWidget
from factory_widget import FactoryWidget

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
            self.main_layout.setAlignment(Qt.AlignTop)
        else:
            self.main_layout = QHBoxLayout()
            self.main_layout.setAlignment(Qt.AlignTop)

        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSizeConstraint(QLayout.SetFixedSize)
        self.setLayout(self.main_layout)
        
        # Set tight size policy for the panel itself
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        self.load_factories_and_create_widgets()

    def get_default_size(self):
        return self.hud_pos.get('factory_size', 100)

    def load_factories_and_create_widgets(self):
        show_frames = self.hud_pos.get('show_factory_frames', True)
        default_size = self.get_default_size()

        for factory_name, factory_obj in self.player.factories.items():
            # Container for this factory's row/column
            container = QWidget(self)
            container.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            if self.layout_type == 'Vertical':
                sub_layout = QHBoxLayout(container)
                sub_layout.setAlignment(Qt.AlignTop)
            else:
                sub_layout = QVBoxLayout(container)
                sub_layout.setAlignment(Qt.AlignTop)

            sub_layout.setSpacing(0)
            sub_layout.setContentsMargins(0, 0, 0, 0)
            container.setLayout(sub_layout)

            # 1) "Currently Building" widget
            current_widget = FactoryWidget(
                factory=factory_obj,
                player=self.player,
                color=self.player.color,
                size=default_size,
                show_frame=show_frames,
                parent=container
            )
            sub_layout.addWidget(current_widget)

            # 2) Queue widgets will be added dynamically in update_labels
            queue_widgets = []

            # Record everything
            self.main_layout.addWidget(container)
            self.factory_data[factory_name] = {
                "container": container,
                "layout": sub_layout,
                "current_widget": current_widget,
                "queue_widgets": queue_widgets
            }

    def update_labels(self):
        self.player.update_factories()
        show_queue = self.hud_pos.get('show_factory_queue', True)
        default_size = self.get_default_size()

        for factory_name, data in self.factory_data.items():
            current_widget = data["current_widget"]
            queue_widgets = data["queue_widgets"]
            sub_layout = data["layout"]

            # Update the main factory widget
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
                    size=default_size // 2,
                    prefer_vet=prefer_vet,
                    parent=data["container"]
                )
                queue_widgets.append(item_widget)
                sub_layout.addWidget(item_widget)

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
        new_main_layout.setSizeConstraint(QLayout.SetFixedSize)

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
