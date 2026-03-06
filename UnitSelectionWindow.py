# UnitSelectionWindow.py
import json
import logging
import os

from PySide6.QtGui import QPixmap, QImage, QAction, QPainter, QFont
from PySide6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QGridLayout, QLabel, QMenu, QInputDialog
from PySide6.QtCore import Qt

# Import immutable definitions from constants
from constants import (
    factions,
    unit_types,
    names,
    name_to_path,
    SLAVE_MINER_CANONICAL_NAME,
)


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
        
        # Validate position data integrity on startup
        self.validate_position_data()

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
        self.migrate_slave_miner_selection()
        for faction, unit_types_data in self.units_data.items():
            for unit_type, units in unit_types_data.items():
                for unit_name, unit_info in units.items():
                    if isinstance(unit_info, bool):
                        self.units_data[faction][unit_type][unit_name] = {'selected': unit_info, 'locked': False,
                                                                          'position': -1}
                    else:
                        if 'position' not in unit_info:
                            unit_info['position'] = -1

    def migrate_slave_miner_selection(self):
        yuri_units = self.units_data.setdefault('Yuri', {})
        tank_units = yuri_units.setdefault('Tank', {})
        structure_units = yuri_units.setdefault('Structure', {})

        canonical_info = tank_units.get(SLAVE_MINER_CANONICAL_NAME)
        merged_info = self._normalize_unit_info(canonical_info)

        for legacy_name in ('Slave miner undeployed', 'Slave Miner Deployed', 'Yuri Ore Refinery'):
            legacy_group = tank_units if legacy_name == 'Slave miner undeployed' else structure_units
            legacy_info = legacy_group.pop(legacy_name, None)
            if legacy_info is not None:
                merged_info = self._merge_unit_info(merged_info, self._normalize_unit_info(legacy_info))

        if merged_info:
            merged_info['unit_type'] = 'Tank'
            merged_info['faction'] = 'Yuri'
            tank_units[SLAVE_MINER_CANONICAL_NAME] = merged_info

    def _normalize_unit_info(self, unit_info):
        if unit_info is None:
            return None
        if isinstance(unit_info, bool):
            return {'selected': unit_info, 'locked': False, 'position': -1}
        normalized = dict(unit_info)
        normalized.setdefault('selected', False)
        normalized.setdefault('locked', False)
        normalized.setdefault('position', -1)
        return normalized

    def _merge_unit_info(self, base_info, incoming_info):
        if base_info is None:
            return incoming_info
        if incoming_info is None:
            return base_info
        merged = dict(base_info)
        merged['selected'] = base_info.get('selected', False) or incoming_info.get('selected', False)
        merged['locked'] = base_info.get('locked', False) or incoming_info.get('locked', False)

        base_position = base_info.get('position', -1)
        incoming_position = incoming_info.get('position', -1)
        if base_position == -1:
            merged['position'] = incoming_position
        elif incoming_position == -1:
            merged['position'] = base_position
        else:
            merged['position'] = min(base_position, incoming_position)
        return merged

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
        current_position = unit_info.get('position', -1)
        
        # Get the maximum valid position based on selected units
        max_position = self.get_max_valid_position(faction, unit_type)
        
        position, ok = QInputDialog.getInt(
            self, 
            f"Set Position - {unit_name}", 
            f"Enter position (0-{max_position}, or -1 for end):",
            current_position,
            -1,  # minimum value
            max_position  # maximum value
        )
        if ok:
            # Validate and handle position conflicts
            validated_position = self.validate_and_resolve_position(position, faction, unit_type, unit_name)
            self.handle_position_change(validated_position, faction, unit_type, unit_name, label)

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
            # Save the updated positions to JSON immediately
            self.save_unit_positions()
        except KeyError:
            print(f"Error: Unit '{unit_name}' of type '{unit_type}' in faction '{faction}' not found.")

    def get_max_valid_position(self, faction, unit_type):
        """Get the maximum valid position - allow positioning up to total available units."""
        units = self.units_data.get(faction, {}).get(unit_type, {})
        total_units = len(units)
        
        # Allow positions from 0 to total_units-1, with minimum of 10 for flexibility
        # This allows users to set positions even for units not yet selected
        max_reasonable_position = max(10, total_units - 1)
        return max_reasonable_position

    def validate_and_resolve_position(self, requested_position, faction, unit_type, target_unit_name):
        """Validate position and resolve conflicts by adjusting other units' positions."""
        if requested_position == -1:
            return -1  # -1 means "end of list"
        
        # Get all selected units in this category with their positions
        units = self.units_data.get(faction, {}).get(unit_type, {})
        selected_units = {}
        for unit_name, unit_info in units.items():
            if unit_info.get('selected', False):
                selected_units[unit_name] = unit_info.get('position', -1)
        
        # If no conflict, return the requested position
        conflict_unit = None
        for unit_name, position in selected_units.items():
            if unit_name != target_unit_name and position == requested_position and position != -1:
                conflict_unit = unit_name
                break
        
        if conflict_unit is None:
            return requested_position
        
        # Resolve conflict by pushing other units down
        self.resolve_position_conflict(requested_position, faction, unit_type, target_unit_name)
        return requested_position

    def resolve_position_conflict(self, target_position, faction, unit_type, target_unit_name):
        """Resolve position conflicts by shifting other units' positions."""
        units = self.units_data.get(faction, {}).get(unit_type, {})
        
        # Get all units that need to be shifted (position >= target_position, excluding target unit)
        units_to_shift = []
        for unit_name, unit_info in units.items():
            if unit_name != target_unit_name and unit_info.get('selected', False):
                current_pos = unit_info.get('position', -1)
                if current_pos >= target_position and current_pos != -1:
                    units_to_shift.append((unit_name, current_pos))
        
        # Sort by current position and shift each one down by 1
        units_to_shift.sort(key=lambda x: x[1])
        for unit_name, old_position in units_to_shift:
            new_position = old_position + 1
            units[unit_name]['position'] = new_position
            print(f"Shifted {unit_name} from position {old_position} to {new_position}")
            
            # Update the visual representation for shifted units
            for hud_window, _ in self.hud_windows:
                if hasattr(hud_window, 'update_position_widgets'):
                    hud_window.update_position_widgets(faction, unit_type, unit_name)

    def save_unit_positions(self):
        """Save the current unit selection data to JSON file immediately."""
        try:
            with open('unit_selection.json', 'w') as f:
                json.dump({'selected_units': self.units_data}, f, indent=4)
            print("Unit positions saved to unit_selection.json")
        except Exception as e:
            print(f"Error saving unit positions: {e}")

    def validate_position_data(self):
        """Validate and fix position data integrity issues."""
        print("Validating position data integrity...")
        changes_made = False
        
        for faction, unit_types in self.units_data.items():
            for unit_type, units in unit_types.items():
                for unit_name, unit_info in units.items():
                    # Fix missing unit_type and faction fields
                    if 'unit_type' not in unit_info:
                        unit_info['unit_type'] = unit_type
                        changes_made = True
                        print(f"Fixed missing unit_type for {unit_name}")
                    
                    if 'faction' not in unit_info:
                        unit_info['faction'] = faction
                        changes_made = True
                        print(f"Fixed missing faction for {unit_name}")
                    
                    # Fix missing position field
                    if 'position' not in unit_info:
                        unit_info['position'] = -1
                        changes_made = True
                        print(f"Fixed missing position for {unit_name}")
                    
                    # Fix missing locked field
                    if 'locked' not in unit_info:
                        unit_info['locked'] = False
                        changes_made = True
                        print(f"Fixed missing locked field for {unit_name}")
                    
                    # Fix missing selected field
                    if 'selected' not in unit_info:
                        unit_info['selected'] = False
                        changes_made = True
                        print(f"Fixed missing selected field for {unit_name}")
                
                # Get all selected units with their positions
                selected_units = [(name, info) for name, info in units.items() 
                                if info.get('selected', False)]
                
                if not selected_units:
                    continue
                
                # Check for position conflicts and gaps
                positions_used = {}
                units_to_fix = []
                
                for unit_name, unit_info in selected_units:
                    position = unit_info.get('position', -1)
                    if position != -1:
                        if position in positions_used:
                            # Duplicate position found
                            print(f"Conflict detected: {unit_name} and {positions_used[position]} both have position {position}")
                            units_to_fix.append((unit_name, unit_info))
                        else:
                            positions_used[position] = unit_name
                    else:
                        units_to_fix.append((unit_name, unit_info))
                
                # Fix conflicts by reassigning positions
                if units_to_fix:
                    next_available = 0
                    sorted_positions = sorted(positions_used.keys())
                    
                    for unit_name, unit_info in units_to_fix:
                        # Find next available position
                        while next_available in positions_used:
                            next_available += 1
                        
                        unit_info['position'] = next_available
                        positions_used[next_available] = unit_name
                        print(f"Fixed position for {unit_name}: assigned position {next_available}")
                        changes_made = True
                        next_available += 1
        
        if changes_made:
            self.save_unit_positions()
            print("Position data validation complete - changes saved.")
        else:
            print("Position data validation complete - no issues found.")

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
            # Use larger, bold font for better visibility
            font = QFont('Arial', 16, QFont.Bold)
            painter.setFont(font)
            
            # Create background circle for position number
            fm = painter.fontMetrics()
            text = str(position)
            text_width = fm.horizontalAdvance(text)
            text_height = fm.height()
            
            # Position circle in top-right corner
            circle_size = max(text_width + 8, text_height + 4)
            circle_x = image.width() - circle_size - 2
            circle_y = 2
            
            # Draw background circle
            painter.setPen(Qt.black)
            painter.setBrush(Qt.yellow if is_selected else Qt.lightGray)
            painter.drawEllipse(circle_x, circle_y, circle_size, circle_size)
            
            # Draw position number
            painter.setPen(Qt.black)
            text_x = circle_x + (circle_size - text_width) // 2
            text_y = circle_y + (circle_size + text_height) // 2 - fm.descent()
            painter.drawText(text_x, text_y, text)
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
        
        # Save changes immediately
        self.save_unit_positions()

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
        
        # Save changes immediately
        self.save_unit_positions()
