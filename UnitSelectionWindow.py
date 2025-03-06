# UnitSelectionWindow.py
import json
import logging
import os

from PySide6.QtGui import QPixmap, QImage, QAction, QPainter, QFont
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QLabel, QMenu, QInputDialog
from PySide6.QtCore import Qt

# Import immutable definitions from constants
from constants import factions, unit_types, names, name_to_path


class UnitSelectionWindow(QMainWindow):
    def __init__(self, selected_units_dict, hud_windows, parent=None):
        super().__init__(parent)
        self.hud_windows = hud_windows

        # Ensure 'selected_units' key exists in selected_units_dict
        if 'selected_units' not in selected_units_dict:
            selected_units_dict['selected_units'] = {}
        self.units_data = selected_units_dict['selected_units']

        # Migrate units data to new format if necessary
        self.migrate_units_data()

        self.setWindowTitle("Unit Selection")
        self.setGeometry(200, 200, 400, 300)

        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)

        # Create tabs for factions
        self.tab_widget = QTabWidget()
        self.create_faction_tabs()

        # Layout setup
        layout = QVBoxLayout(main_widget)
        layout.addWidget(self.tab_widget)

    def create_faction_tabs(self):
        for faction in factions:
            faction_tab = QWidget()
            faction_layout = QVBoxLayout(faction_tab)

            # Create sub-tabs (Infantry, Structure, Tank, Naval, Aircraft)
            sub_tab_widget = QTabWidget()
            self.create_sub_tabs(faction, sub_tab_widget)

            faction_layout.addWidget(sub_tab_widget)
            self.tab_widget.addTab(faction_tab, faction)

    def create_sub_tabs(self, faction, sub_tab_widget):
        """Create sub-tabs and populate them with units if available."""
        for unit_type in unit_types:
            sub_tab = QWidget()
            sub_layout = QGridLayout(sub_tab)
            sub_layout.setAlignment(Qt.AlignTop)

            # Get units defined for this faction and unit type
            units = names.get(faction, {}).get(unit_type, [])
            row = 0
            col = 0
            for unit in units:
                # Create a vertical layout for each unit (image acts as checkbox)
                unit_layout = QVBoxLayout()
                unit_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

                # Create image label and set it as clickable
                image_label = QLabel()
                image_path = name_to_path(unit)
                image_label.setProperty("image_path", image_path)
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    image_label.setPixmap(pixmap.scaled(50, 50, Qt.KeepAspectRatio))

                # Determine selection, lock state and position
                is_selected = self.is_unit_selected(faction, unit_type, unit)
                is_locked = self.is_unit_locked(faction, unit_type, unit)
                position = self.get_unit_position(faction, unit_type, unit)
                self.update_image_selection(image_label, is_selected, is_locked, position)

                # Set click handler using a lambda that passes parameters (corrected to one line)
                image_label.mousePressEvent = lambda event, f=faction, ut=unit_type, u=unit, label=image_label: self.unit_image_mousePressEvent(event, f, ut, u, label)

                # Add the image label to the unit's layout and grid layout
                unit_layout.addWidget(image_label, alignment=Qt.AlignHCenter)
                sub_layout.addLayout(unit_layout, row, col)

                col += 1
                if col >= 3:
                    col = 0
                    row += 1

            sub_tab_widget.addTab(sub_tab, unit_type)

    def is_unit_selected(self, faction, unit_type, unit):
        unit_info = self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {})
        if isinstance(unit_info, bool):
            # Convert old format to new format
            unit_info = {'selected': unit_info, 'locked': False, 'position': -1}
            self.units_data.setdefault(faction, {}).setdefault(unit_type, {})[unit] = unit_info
        return unit_info.get('selected', False)

    def get_unit_position(self, faction, unit_type, unit):
        unit_info = self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {})
        return unit_info.get('position', -1)

    def is_unit_locked(self, faction, unit_type, unit):
        unit_info = self.units_data.get(faction, {}).get(unit_type, {}).get(unit, {})
        if isinstance(unit_info, bool):
            unit_info = {'selected': unit_info, 'locked': False, 'position': -1}
            self.units_data.setdefault(faction, {}).setdefault(unit_type, {})[unit] = unit_info
        return unit_info.get('locked', False)

    def migrate_units_data(self):
        for faction, unit_types_data in self.units_data.items():
            for unit_type, units in unit_types_data.items():
                for unit_name, unit_info in units.items():
                    if isinstance(unit_info, bool):
                        self.units_data[faction][unit_type][unit_name] = {'selected': unit_info, 'locked': False,
                                                                          'position': -1}
                    else:
                        if 'position' not in unit_info:
                            unit_info['position'] = -1

    def unit_image_mousePressEvent(self, event, faction, unit_type, unit_name, label):
        if event.button() == Qt.LeftButton:
            self.toggle_unit_selection(faction, unit_type, unit_name, label)
        elif event.button() == Qt.RightButton:
            self.show_unit_context_menu(event, faction, unit_type, unit_name, label)

    def show_unit_context_menu(self, event, faction, unit_type, unit_name, label):
        menu = QMenu(self)
        is_locked = self.is_unit_locked(faction, unit_type, unit_name)
        action_text = "Unlock Unit" if is_locked else "Lock Unit"
        lock_action = QAction(action_text, self)
        lock_action.triggered.connect(lambda: self.toggle_unit_lock(faction, unit_type, unit_name, label))
        menu.addAction(lock_action)

        position_action = QAction("Set Position", self)
        position_action.triggered.connect(lambda: self.set_position(faction, unit_type, unit_name, label))
        menu.addAction(position_action)

        menu.exec(event.globalPos())

    def set_position(self, faction, unit_type, unit_name, label):
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        position, ok = QInputDialog.getInt(self, "Set Position " + unit_name, "Enter a positive position (default -1):",
                                           unit_info.get('position', -1))
        if ok:
            self.handle_position_change(position, faction, unit_type, unit_name, label)

    def handle_position_change(self, position, faction, unit_type, unit_name, label):
        try:
            unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
            unit_info['position'] = position
            print(f"Position of {unit_name} in {unit_type} ({faction}) set to: {position}")
            self.update_image_selection(label, self.is_unit_selected(faction, unit_type, unit_name),
                                        self.is_unit_locked(faction, unit_type, unit_name),
                                        self.get_unit_position(faction, unit_type, unit_name))
            for unit_counter, _ in self.hud_windows:
                if hasattr(unit_counter, 'update_position_widgets'):
                    unit_counter.update_position_widgets(faction, unit_type, unit_name)
        except KeyError:
            print(f"Error: Unit '{unit_name}' of type '{unit_type}' in faction '{faction}' not found.")

    def update_image_selection(self, label, is_selected, is_locked, position):
        image_path = label.property("image_path")
        if not image_path:
            return
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return
        image = pixmap.toImage()
        # Modify brightness based on selection state
        for x in range(image.width()):
            for y in range(image.height()):
                color = image.pixelColor(x, y)
                color = color.lighter(150) if is_selected else color.darker(150)
                image.setPixelColor(x, y, color)
        # Overlay a lock icon if locked
        if is_locked:
            painter = QPainter()
            painter.begin(image)
            lock_icon = QPixmap('icons/lock_icon.png')
            lock_icon = lock_icon.scaled(20, 20, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.drawPixmap(0, 0, lock_icon)
            painter.end()
        # Overlay the position text if set
        if position > -1:
            painter = QPainter(image)
            painter.setFont(QFont('Arial', 14))
            painter.setPen(Qt.black if is_selected else Qt.white)
            painter.drawText(1, image.height() - 1, str(position))
            painter.end()
        label.setPixmap(QPixmap.fromImage(image))

    def toggle_unit_lock(self, faction, unit_type, unit_name, label):
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        current_state = unit_info.get('locked', False)
        new_state = not current_state
        unit_info['locked'] = new_state
        logging.debug(f'{unit_name} lock state changed to {new_state}')
        self.update_image_selection(label, self.is_unit_selected(faction, unit_type, unit_name),
                                    new_state, self.get_unit_position(faction, unit_type, unit_name))
        for unit_counter, _ in self.hud_windows:
            if hasattr(unit_counter, 'update_locked_widgets'):
                unit_counter.update_locked_widgets(faction, unit_type, unit_name, new_state)

    def toggle_unit_selection(self, faction, unit_type, unit_name, label):
        current_state = self.is_unit_selected(faction, unit_type, unit_name)
        new_state = not current_state
        logging.debug(f'{unit_name} selection state changed to {new_state}')
        unit_info = self.units_data.setdefault(faction, {}).setdefault(unit_type, {}).setdefault(unit_name, {})
        unit_info['selected'] = new_state
        is_locked = self.is_unit_locked(faction, unit_type, unit_name)
        position = self.get_unit_position(faction, unit_type, unit_name)
        self.update_image_selection(label, new_state, is_locked, position)
        for unit_counter, _ in self.hud_windows:
            if hasattr(unit_counter, 'update_selected_widgets'):
                unit_counter.update_selected_widgets(faction, unit_type, unit_name, new_state)
