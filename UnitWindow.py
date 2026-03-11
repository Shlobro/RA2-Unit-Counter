import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLayout, QMenu

from CounterWidget import (CounterWidgetImagesAndNumber, CounterWidgetNumberOnly, CounterWidgetImageOnly)
from constants import (
    name_to_path,
    country_name_to_faction,
    canonicalize_unit_name,
    SLAVE_MINER_CANONICAL_NAME,
    get_display_image_name,
)
from DataTracker import ResourceWindow
from factory_panel import FactoryPanel
from hud_position_utils import get_player_position, set_player_position, get_player_setting, set_player_setting
from player_identity import (
    get_combined_hud_title,
    get_player_bucket_key,
    get_player_display_label,
    get_player_legacy_bucket_keys,
)


# =============================================================================
# UnitWindowBase: Shared functionality for unit counter windows.
# =============================================================================
class UnitWindowBase(QMainWindow):
    EXPANSION_SETTING_KEY = 'unit_expansion_direction'

    def __init__(self, player, hud_pos, selected_units_dict, spacing=0):
        super().__init__()
        self.player = player
        self.hud_pos = hud_pos
        self.selected_units = selected_units_dict['selected_units']
        self.unit_info_by_name = {}
        for faction, unit_types in self.selected_units.items():
            for unit_type, units in unit_types.items():
                for unit_name, unit_info in units.items():
                    canonical_name = canonicalize_unit_name(unit_name)
                    unit_info['unit_type'] = unit_type
                    unit_info['faction'] = faction
                    existing_info = self.unit_info_by_name.get(canonical_name)
                    if existing_info is None or unit_info.get('selected', False):
                        self.unit_info_by_name[canonical_name] = unit_info
        self.layout_type = hud_pos.get('unit_layout', 'Vertical')
        self.size = self.get_default_size()
        self.show_unit_frames = hud_pos.get('show_unit_frames', True)
        self.counters = {}
        self.spacing = spacing
        self.player_bucket_key = get_player_bucket_key(self.player, self.hud_pos)
        self.legacy_player_bucket_keys = get_player_legacy_bucket_keys(self.player, self.hud_pos)

        # Set geometry and flags.
        self.setGeometry(0, 0, 120, 120)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()

        # Create container for counters.
        self.unit_frame = QWidget(self)
        self.set_layout(self.layout_type, self.spacing)
        self.setCentralWidget(self.unit_frame)
        self.load_selected_units_and_create_counters()
        self.adjustSize()
        self._move_to_saved_anchor()
        self.show()

    def get_default_size(self):
        raise NotImplementedError("Subclasses must implement get_default_size().")

    def set_layout(self, layout_type, spacing):
        self.layout = QVBoxLayout() if layout_type == 'Vertical' else QHBoxLayout()
        self.layout.setSpacing(spacing)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self._apply_layout_direction(self.layout)
        self.unit_frame.setLayout(self.layout)

    def update_show_unit_frames(self, show_frame):
        self.show_unit_frames = show_frame
        for counter_widget, _ in self.counters.values():
            counter_widget.update_show_frame(show_frame)

    def update_layout(self, layout_type, spacing=None):
        if self.layout_type != layout_type or (spacing is not None and self.layout.spacing() != spacing):
            self.layout_type = layout_type
            new_layout = QVBoxLayout() if layout_type == 'Vertical' else QHBoxLayout()
            new_layout.setSpacing(spacing if spacing is not None else self.layout.spacing())
            new_layout.setContentsMargins(0, 0, 0, 0)
            self._apply_layout_direction(new_layout)
            for counter_widget, _ in self.counters.values():
                self.layout.removeWidget(counter_widget)
                new_layout.addWidget(counter_widget)
            QWidget().setLayout(self.layout)
            self.unit_frame.setLayout(new_layout)
            self.layout = new_layout
            self.updateGeometry()

    def update_spacing(self, new_spacing):
        self.layout.setSpacing(new_spacing)
        self.layout.update()

    def load_selected_units_and_create_counters(self):
        # First pass: collect all selected units with their positions
        selected_units_with_positions = []
        seen_units = set()
        for unit_name, unit_info in self.unit_info_by_name.items():
            canonical_name = canonicalize_unit_name(unit_name)
            if canonical_name in seen_units:
                continue
            is_selected = unit_info.get('selected', False)
            if is_selected:
                position = unit_info.get('position', -1)
                unit_type = unit_info.get('unit_type')
                selected_units_with_positions.append((canonical_name, unit_info, unit_type, position))
                seen_units.add(canonical_name)
        
        # Sort by position: numbered positions first (0,1,2...), then -1 positions at end
        selected_units_with_positions.sort(key=lambda x: (x[3] == -1, x[3] if x[3] != -1 else float('inf')))
        
        # Second pass: create and add widgets in the correct order
        for unit_name, unit_info, unit_type, position in selected_units_with_positions:
            counter_widget = self.create_counter_widget(unit_name, 0, unit_type)
            counter_widget.hide()
            self.layout.addWidget(counter_widget)  # Always add to end since we're adding in sorted order
            self.counters[unit_name] = (counter_widget, unit_type)

    def update_all_counters_size(self, new_size):
        self.size = new_size
        for counter_widget, _ in self.counters.values():
            counter_widget.update_size(new_size)
        self.layout.setSizeConstraint(QLayout.SetFixedSize)
        self.updateGeometry()

    def update_labels(self):
        for unit_name, (counter_widget, unit_type) in self.counters.items():
            unit_count = self.get_unit_count(unit_type, unit_name)
            counter_widget.update_count(unit_count)
            unit_info = self.unit_info_by_name.get(unit_name, {})
            is_locked = unit_info.get('locked', False)
            unit_faction = unit_info.get('faction', None)
            is_selected = unit_info.get('selected', False)
            if (is_selected and unit_count > 0) or (is_locked and is_selected and (unit_faction == self.player.faction or unit_faction == "Other")):
                counter_widget.show()
            else:
                counter_widget.hide()
        self.update_all_counters_size(self.size)

    def get_unit_count(self, unit_type, unit_name):
        if self.player is None:
            logging.warning("Player is None while retrieving unit count.")
            return 0
        try:
            if canonicalize_unit_name(unit_name) == SLAVE_MINER_CANONICAL_NAME:
                return (self.player.building_counts.get('Yuri Ore Refinery', 0) +
                        self.player.building_counts.get('Slave Miner Deployed', 0) +
                        self.player.tank_counts.get('Slave miner', 0) +
                        self.player.tank_counts.get('Slave miner undeployed', 0))
            if unit_type == 'Infantry':
                return self.player.infantry_counts.get(unit_name, 0)
            elif unit_type in ('Tank', 'Naval'):
                return self.player.tank_counts.get(unit_name, 0)
            elif unit_type == 'Structure':
                if unit_name == 'Allied AFC':
                    return (self.player.building_counts.get('Allied AFC', 0) +
                            self.player.building_counts.get('American AFC', 0))
                else:
                    return self.player.building_counts.get(unit_name, 0)
            else:
                return 0
        except AttributeError as e:
            logging.error(f"Error retrieving unit count for {unit_name}: {e}")
            return 0

    def make_hud_movable(self):
        self.offset = None
        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self.offset = event.pos()
        def mouse_move_event(event):
            if self.offset is not None:
                x = event.globalX() - self.offset.x()
                y = event.globalY() - self.offset.y()
                self.move(x, y)
                self.update_hud_position(x, y)
        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event

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
            self.get_hud_type(),
            anchor['x'],
            anchor['y'],
        )
        self._apply_layout_direction(self.layout)
        self.layout.invalidate()
        self.adjustSize()
        if self.isWindow():
            self._move_to_saved_anchor()

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
        if not self.isWindow():
            return
        self._move_to_saved_anchor()

    def get_default_position(self):
        anchor = self._get_saved_anchor_position()
        return self._anchor_to_top_left(anchor)

    def update_hud_position(self, x, y):
        anchor = self._get_anchor_position(origin_x=x, origin_y=y)
        set_player_position(
            self.hud_pos,
            self.player_bucket_key,
            self.get_hud_type(),
            anchor['x'],
            anchor['y'],
        )

    def _get_saved_anchor_position(self):
        return get_player_position(
            self.hud_pos,
            self.player_bucket_key,
            self.get_hud_type(),
            legacy_bucket_keys=self.legacy_player_bucket_keys,
        )

    def _get_anchor_position(self, direction=None, origin_x=None, origin_y=None):
        direction = direction or ('reverse' if self._is_reverse_expansion() else 'forward')
        origin_x = self.x() if origin_x is None else origin_x
        origin_y = self.y() if origin_y is None else origin_y

        anchor_x = origin_x
        anchor_y = origin_y
        if self.layout_type == 'Horizontal' and direction == 'reverse':
            anchor_x += self.width()
        elif self.layout_type == 'Vertical' and direction == 'reverse':
            anchor_y += self.height()
        return {'x': anchor_x, 'y': anchor_y}

    def _anchor_to_top_left(self, anchor):
        x = anchor['x']
        y = anchor['y']
        if self.layout_type == 'Horizontal' and self._is_reverse_expansion():
            x -= self.width()
        elif self.layout_type == 'Vertical' and self._is_reverse_expansion():
            y -= self.height()
        return {'x': x, 'y': y}

    def _move_to_saved_anchor(self):
        pos = self.get_default_position()
        if pos['x'] != self.x() or pos['y'] != self.y():
            self.move(pos['x'], pos['y'])

    def get_hud_type(self):
        raise NotImplementedError("Subclasses must implement get_hud_type().")

    def create_counter_widget(self, unit_name, unit_count, unit_type):
        raise NotImplementedError("Subclasses must implement create_counter_widget().")

    def update_selected_widgets(self, faction, unit_type, unit_name, new_state):
        """Update counters when units are selected/deselected from UnitSelectionWindow."""
        unit_name = canonicalize_unit_name(unit_name)
        if new_state:
            # Unit was selected - add counter widget if not already present
            if unit_name not in self.counters:
                unit_info = self.unit_info_by_name.get(unit_name, {})
                position = unit_info.get('position', -1)
                counter_widget = self.create_counter_widget(unit_name, 0, unit_type)
                counter_widget.hide()  # Will be shown when unit_count > 0
                
                # Find correct insertion point based on position
                insert_index = self.find_insertion_index(position)
                self.layout.insertWidget(insert_index, counter_widget)
                self.counters[unit_name] = (counter_widget, unit_type)
        else:
            # Unit was deselected - remove counter widget
            if unit_name in self.counters:
                counter_widget, _ = self.counters[unit_name]
                self.layout.removeWidget(counter_widget)
                counter_widget.setParent(None)
                del self.counters[unit_name]
        
        # Update layout and visibility
        self.updateGeometry()
        self.update_labels()

    def find_insertion_index(self, target_position):
        """Find the correct index to insert a widget based on position values."""
        if target_position == -1:
            return self.layout.count()  # Insert at end
        
        # Find the correct insertion point by comparing positions
        insert_index = 0
        for i in range(self.layout.count()):
            widget = self.layout.itemAt(i).widget()
            if widget is None:
                continue
                
            # Find the unit name for this widget
            widget_unit_name = None
            for unit_name, (counter_widget, _) in self.counters.items():
                if counter_widget == widget:
                    widget_unit_name = unit_name
                    break
            
            if widget_unit_name:
                widget_unit_info = self.unit_info_by_name.get(widget_unit_name, {})
                widget_position = widget_unit_info.get('position', -1)
                
                # Logic: positioned units (0,1,2...) come first, -1 positions go to end
                # Insert before widgets that:
                # 1. Have -1 position (target has numbered position)
                # 2. Have higher numbered position than target
                if widget_position == -1 or (widget_position > target_position):
                    break
                insert_index = i + 1
        
        return insert_index

    def update_position_widgets(self, faction, unit_type, unit_name):
        """Update counter position when changed from UnitSelectionWindow."""
        unit_name = canonicalize_unit_name(unit_name)
        if unit_name in self.counters:
            counter_widget, _ = self.counters[unit_name]
            unit_info = self.unit_info_by_name.get(unit_name, {})
            position = unit_info.get('position', -1)
            
            # Remove from current position
            self.layout.removeWidget(counter_widget)
            
            # Find correct insertion index based on position
            insert_index = self.find_insertion_index_for_reposition(position, unit_name)
            self.layout.insertWidget(insert_index, counter_widget)
            
            self.updateGeometry()
            print(f"Repositioned {unit_name} to position {position} (index {insert_index})")

    def find_insertion_index_for_reposition(self, target_position, target_unit_name):
        """Find insertion index when repositioning an existing widget."""
        if target_position == -1:
            return self.layout.count()  # Insert at end
        
        # Get all units with their positions (excluding the target unit)
        other_units = []
        for unit_name, (counter_widget, _) in self.counters.items():
            if unit_name == target_unit_name:
                continue  # Skip the unit being repositioned
                
            unit_info = self.unit_info_by_name.get(unit_name, {})
            widget_position = unit_info.get('position', -1)
            other_units.append((unit_name, widget_position))
        
        # Sort other units by position (numbered positions first, then -1)
        other_units.sort(key=lambda x: (x[1] == -1, x[1] if x[1] != -1 else float('inf')))
        
        # Find insertion point: count units that should come before target position
        insert_index = 0
        for unit_name, widget_position in other_units:
            if widget_position == -1 or widget_position > target_position:
                break
            insert_index += 1
        
        return insert_index

    def update_locked_widgets(self, faction, unit_type, unit_name, new_state):
        """Update counter when lock state changes from UnitSelectionWindow."""
        # The lock state affects visibility in update_labels, so just refresh
        self.update_labels()


# =============================================================================
# UnitWindowWithImages: Combined unit window (image and number together).
# =============================================================================
class UnitWindowWithImages(UnitWindowBase):
    def __init__(self, player, hud_pos, selected_units_dict):
        self.distance_between_images = hud_pos.get('distance_between_images', 0)
        super().__init__(player, hud_pos, selected_units_dict, spacing=self.distance_between_images)
    def get_default_size(self):
        return self.hud_pos.get('unit_counter_size', 100)
    def get_hud_type(self):
        return 'unit_counter_combined'
    def create_counter_widget(self, unit_name, unit_count, unit_type):
        unit_image_path = name_to_path(get_display_image_name(unit_name))
        return CounterWidgetImagesAndNumber(
            count=unit_count,
            image_path=unit_image_path,
            color=self.player.color,
            size=self.size,
            show_frame=self.show_unit_frames
        )
    def get_unit_count(self, unit_type, unit_name):
        return super().get_unit_count(unit_type, unit_name)


# =============================================================================
# UnitWindowImagesOnly: Displays only unit images.
# =============================================================================
class UnitWindowImagesOnly(UnitWindowBase):
    def __init__(self, player, hud_pos, selected_units_dict):
        self.distance_between_images = hud_pos.get('distance_between_images', 0)
        super().__init__(player, hud_pos, selected_units_dict, spacing=self.distance_between_images)
    def get_default_size(self):
        return self.hud_pos.get('image_size', 75)
    def get_hud_type(self):
        return 'unit_counter_images'
    def create_counter_widget(self, unit_name, unit_count, unit_type):
        unit_image_path = name_to_path(get_display_image_name(unit_name))
        return CounterWidgetImageOnly(
            image_path=unit_image_path,
            color=self.player.color,
            size=self.size,
            show_frame=self.show_unit_frames
        )
    def get_unit_count(self, unit_type, unit_name):
        return super().get_unit_count(unit_type, unit_name)


# =============================================================================
# UnitWindowNumbersOnly: Displays only unit numbers.
# =============================================================================
class UnitWindowNumbersOnly(UnitWindowBase):
    def __init__(self, player, hud_pos, selected_units_dict):
        self.distance_between_numbers = hud_pos.get('distance_between_numbers', 0)
        super().__init__(player, hud_pos, selected_units_dict, spacing=self.distance_between_numbers)
    def get_default_size(self):
        return self.hud_pos.get('number_size', 75)
    def get_hud_type(self):
        return 'unit_counter_numbers'
    def create_counter_widget(self, unit_name, unit_count, unit_type):
        return CounterWidgetNumberOnly(
            count=unit_count,
            color=self.player.color,
            size=self.size
        )
    def update_spacing(self, new_spacing):
        self.layout.setSpacing(new_spacing)
        self.updateGeometry()
    def get_unit_count(self, unit_type, unit_name):
        return super().get_unit_count(unit_type, unit_name)

# =============================================================================
# CombinedHudWindow: Used in Combined HUD mode.
# This container embeds the ResourceWindow and the unit counters in one window,
# plus the FactoryPanel if "show_factory_window" is True.
# =============================================================================
class CombinedHudWindow(QWidget):
    def __init__(self, player, hud_pos, selected_units_dict):
        """
        Create a combined HUD container for a single player.
        The top section displays resource info.
        The middle section displays unit counters (images/numbers).
        The bottom section displays the factory panel (if show_factory_window is True).
        """
        super().__init__()
        self.player = player
        self.hud_pos = hud_pos
        self.selected_units_dict = selected_units_dict

        self.setWindowTitle(get_combined_hud_title(player, hud_pos))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()

        self._init_ui()

        # Restore saved position (for combined HUD).
        player_id = get_player_bucket_key(player, self.hud_pos)
        pos = get_player_position(
            self.hud_pos,
            player_id,
            'combined',
            legacy_bucket_keys=get_player_legacy_bucket_keys(player, self.hud_pos),
        )
        self.move(pos['x'], pos['y'])

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # First define self.factory_panel = None so it exists for the while-loop check.
        self.factory_panel = None

        # (1) Resource widget
        self.resource_widget = ResourceWindow(
            self.player,
            len(self.hud_pos),
            self.hud_pos,
            self.player.color_name,
            combined_mode=True
        )
        self.resource_widget.setWindowFlags(Qt.Widget)
        main_layout.addWidget(self.resource_widget)

        # (2) Factory panel if "show_factory_window" is True - create before unit section
        if self.hud_pos.get('show_factory_window', True):
            from factory_panel import FactoryPanel  # or wherever your FactoryPanel is
            self.factory_panel = FactoryPanel(self.player, self.hud_pos, parent=self)

        # (3) Unit counters - now factory_panel is properly set
        self.update_unit_section(self.hud_pos.get('separate_unit_counters', False))

        # (4) Add factory panel to layout if it was created
        if self.factory_panel:
            main_layout.addWidget(self.factory_panel)

        self.setLayout(main_layout)

    def update_unit_section(self, separate: bool):
        """
        Rebuild just the unit‐counter portion of this combined HUD.
        :param separate: True to split into images-only + numbers-only,
                         False for a single combined widget.
        """
        layout = self.layout()
        # We want to remove any existing unit widgets but keep the resource_widget
        # (index 0) and the factory_panel if it exists (usually at the bottom).
        while layout.count() > (2 if self.factory_panel else 1):
            # The item at the bottom might be the old unit container or the factory panel.
            item = layout.itemAt(layout.count() - 1)
            w = item.widget()
            if w is not None and w is self.factory_panel:
                break  # do not remove the factory panel
            layout.removeItem(item)
            if w is not None:
                w.setParent(None)

        # Clean up existing widget references before creating new ones
        if hasattr(self, 'unit_widget'):
            self.unit_widget = None
        if hasattr(self, 'unit_widget_images'):
            self.unit_widget_images = None
        if hasattr(self, 'unit_widget_numbers'):
            self.unit_widget_numbers = None

        # Now add a fresh unit section
        if separate:
            # Two embedded widgets - layout depends on unit_layout setting
            container = QWidget()
            unit_layout_type = self.hud_pos.get('unit_layout', 'Vertical')
            if unit_layout_type == 'Horizontal':
                # In horizontal mode: numbers below images
                container_layout = QVBoxLayout()
            else:
                # In vertical mode: numbers to the right of images
                container_layout = QHBoxLayout()
            container_layout.setContentsMargins(0, 0, 0, 0)
            container.setLayout(container_layout)

            self.unit_widget_images = UnitWindowImagesOnly(self.player, self.hud_pos, self.selected_units_dict)
            self.unit_widget_numbers = UnitWindowNumbersOnly(self.player, self.hud_pos, self.selected_units_dict)
            self.unit_widget_images.setWindowFlags(Qt.Widget)
            self.unit_widget_numbers.setWindowFlags(Qt.Widget)

            container_layout.addWidget(self.unit_widget_images)
            container_layout.addWidget(self.unit_widget_numbers)
            layout.addWidget(container)
        else:
            # Single combined unit widget
            self.unit_widget = UnitWindowWithImages(self.player, self.hud_pos, self.selected_units_dict)
            self.unit_widget.setWindowFlags(Qt.Widget)
            layout.addWidget(self.unit_widget)

    def update_labels(self):
        """
        Update resource widget, unit widgets, and factory panel if present.
        """
        self.resource_widget.update_labels()

        # If separate_unit_counters is True, we have unit_widget_images + unit_widget_numbers
        if self.hud_pos.get('separate_unit_counters', False):
            self.unit_widget_images.update_labels()
            self.unit_widget_numbers.update_labels()
        else:
            self.unit_widget.update_labels()

        # Also update factory panel
        if self.factory_panel:
            self.factory_panel.update_labels()

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
        set_player_position(
            self.hud_pos,
            get_player_bucket_key(self.player, self.hud_pos),
            'combined',
            x,
            y,
        )

    def update_unit_counters_size(self, new_size, section=None):
        """
        Update the size of the unit counters in the Combined HUD.
        If separate_unit_counters is enabled:
          - If section=='images', update only the images widget.
          - If section=='numbers', update only the numbers widget.
          - Otherwise, update both.
        If not enabled, update the single combined unit window.
        """
        if self.hud_pos.get('separate_unit_counters', False):
            if section == 'images':
                self.unit_widget_images.update_all_counters_size(new_size)
            elif section == 'numbers':
                self.unit_widget_numbers.update_all_counters_size(new_size)
            else:
                self.unit_widget_images.update_all_counters_size(new_size)
                self.unit_widget_numbers.update_all_counters_size(new_size)
        else:
            if hasattr(self, 'unit_widget'):
                self.unit_widget.update_all_counters_size(new_size)

    def update_show_unit_frames(self, show: bool):
        """
        Show or hide frames around unit counters in combined HUD mode.
        """
        if self.hud_pos.get('separate_unit_counters', False):
            if hasattr(self, 'unit_widget_images'):
                self.unit_widget_images.update_show_unit_frames(show)
            if hasattr(self, 'unit_widget_numbers'):
                self.unit_widget_numbers.update_show_unit_frames(show)
        else:
            if hasattr(self, 'unit_widget'):
                self.unit_widget.update_show_unit_frames(show)

    def update_unit_layout(self, layout_type):
        """
        Update the layout of unit counters in Combined HUD mode.
        """
        if self.hud_pos.get('separate_unit_counters', False):
            # When separate unit counters are enabled, we need to rebuild the container
            # with the appropriate layout (vertical for horizontal mode, horizontal for vertical mode)
            
            # First, properly clean up existing unit widgets
            if hasattr(self, 'unit_widget_images'):
                self.unit_widget_images.setParent(None)
                delattr(self, 'unit_widget_images')
            if hasattr(self, 'unit_widget_numbers'):
                self.unit_widget_numbers.setParent(None) 
                delattr(self, 'unit_widget_numbers')
                
            # Now rebuild with the new layout
            self.update_unit_section(True)
        else:
            # Single combined unit widget
            if hasattr(self, 'unit_widget'):
                self.unit_widget.update_layout(layout_type)

    def update_selected_widgets(self, faction, unit_type, unit_name, new_state):
        """Update counters when units are selected/deselected from UnitSelectionWindow."""
        if self.hud_pos.get('separate_unit_counters', False):
            # Update both image and number widgets
            if hasattr(self, 'unit_widget_images'):
                self.unit_widget_images.update_selected_widgets(faction, unit_type, unit_name, new_state)
            if hasattr(self, 'unit_widget_numbers'):
                self.unit_widget_numbers.update_selected_widgets(faction, unit_type, unit_name, new_state)
        else:
            # Update single combined unit widget
            if hasattr(self, 'unit_widget'):
                self.unit_widget.update_selected_widgets(faction, unit_type, unit_name, new_state)

    def update_position_widgets(self, faction, unit_type, unit_name):
        """Update counter position when changed from UnitSelectionWindow."""
        if self.hud_pos.get('separate_unit_counters', False):
            if hasattr(self, 'unit_widget_images'):
                self.unit_widget_images.update_position_widgets(faction, unit_type, unit_name)
            if hasattr(self, 'unit_widget_numbers'):
                self.unit_widget_numbers.update_position_widgets(faction, unit_type, unit_name)
        else:
            if hasattr(self, 'unit_widget'):
                self.unit_widget.update_position_widgets(faction, unit_type, unit_name)

    def update_locked_widgets(self, faction, unit_type, unit_name, new_state):
        """Update counter when lock state changes from UnitSelectionWindow."""
        if self.hud_pos.get('separate_unit_counters', False):
            if hasattr(self, 'unit_widget_images'):
                self.unit_widget_images.update_locked_widgets(faction, unit_type, unit_name, new_state)
            if hasattr(self, 'unit_widget_numbers'):
                self.unit_widget_numbers.update_locked_widgets(faction, unit_type, unit_name, new_state)
        else:
            if hasattr(self, 'unit_widget'):
                self.unit_widget.update_locked_widgets(faction, unit_type, unit_name, new_state)



# =============================================================================
# CombinedUnitWindow: Used in Separate HUD mode when separate unit counters are enabled.
# This container embeds two separate unit windows in one top-level window.
# =============================================================================
class CombinedUnitWindow(QMainWindow):
    def __init__(self, player, hud_pos, selected_units_dict):
        super().__init__()
        self.player = player
        self.hud_pos = hud_pos
        self.selected_units_dict = selected_units_dict

        self.setWindowTitle(f"{get_player_display_label(player, hud_pos)} Unit HUD")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        central = QWidget(self)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        central.setLayout(layout)
        self.setCentralWidget(central)

        self.images_only = UnitWindowImagesOnly(player, hud_pos, selected_units_dict)
        self.numbers_only = UnitWindowNumbersOnly(player, hud_pos, selected_units_dict)
        self.images_only.setWindowFlags(Qt.Widget)
        self.numbers_only.setWindowFlags(Qt.Widget)
        layout.addWidget(self.images_only)
        layout.addWidget(self.numbers_only)
        self.show()

    def update_labels(self):
        self.images_only.update_labels()
        self.numbers_only.update_labels()

    def update_all_counters_size(self, new_size):
        self.images_only.update_all_counters_size(new_size)
        self.numbers_only.update_all_counters_size(new_size)

