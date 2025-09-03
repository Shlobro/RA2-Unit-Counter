import logging
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLayout

from CounterWidget import (CounterWidgetImagesAndNumber, CounterWidgetNumberOnly, CounterWidgetImageOnly)
from constants import name_to_path, country_name_to_faction
from DataTracker import ResourceWindow
from factory_panel import FactoryPanel


# =============================================================================
# UnitWindowBase: Shared functionality for unit counter windows.
# =============================================================================
class UnitWindowBase(QMainWindow):
    def __init__(self, player, hud_pos, selected_units_dict, spacing=0):
        super().__init__()
        self.player = player
        self.hud_pos = hud_pos
        self.selected_units = selected_units_dict['selected_units']
        self.unit_info_by_name = {}
        for faction, unit_types in self.selected_units.items():
            for unit_type, units in unit_types.items():
                for unit_name, unit_info in units.items():
                    unit_info['unit_type'] = unit_type
                    self.unit_info_by_name[unit_name] = unit_info
                    unit_info['faction'] = faction
        self.layout_type = hud_pos.get('unit_layout', 'Vertical')
        self.size = self.get_default_size()
        self.show_unit_frames = hud_pos.get('show_unit_frames', True)
        self.counters = {}
        self.spacing = spacing

        # Set geometry and flags.
        pos = self.get_default_position()
        self.setGeometry(pos['x'], pos['y'], 120, 120)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()

        # Create container for counters.
        self.unit_frame = QWidget(self)
        self.set_layout(self.layout_type, self.spacing)
        self.setCentralWidget(self.unit_frame)
        self.load_selected_units_and_create_counters()
        self.show()

    def get_default_size(self):
        raise NotImplementedError("Subclasses must implement get_default_size().")

    def set_layout(self, layout_type, spacing):
        self.layout = QVBoxLayout() if layout_type == 'Vertical' else QHBoxLayout()
        self.layout.setSpacing(spacing)
        self.layout.setContentsMargins(0, 0, 0, 0)
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
        for unit_name, unit_info in self.unit_info_by_name.items():
            is_selected = unit_info.get('selected', False)
            position = unit_info.get('position', -1)
            if is_selected:
                unit_type = unit_info.get('unit_type')
                counter_widget = self.create_counter_widget(unit_name, 0, unit_type)
                counter_widget.hide()
                if position == -1 or position >= self.layout.count():
                    self.layout.addWidget(counter_widget)
                else:
                    self.layout.insertWidget(position, counter_widget)
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
            if (0 < unit_count < 500) or (is_locked and is_selected and (unit_faction == self.player.faction or unit_name == "Blitz oil (psychic sensor)")):
                counter_widget.show()
            else:
                counter_widget.hide()
        self.update_all_counters_size(self.size)

    def get_unit_count(self, unit_type, unit_name):
        if self.player is None:
            logging.warning("Player is None while retrieving unit count.")
            return 0
        try:
            if unit_type == 'Infantry':
                return self.player.infantry_counts.get(unit_name, 0)
            elif unit_type in ('Tank', 'Naval'):
                return self.player.tank_counts.get(unit_name, 0)
            elif unit_type == 'Structure':
                if unit_name in ('Slave Miner Deployed', 'Slave miner undeployed'):
                    return (self.player.building_counts.get('Slave Miner Deployed', 0) +
                            self.player.tank_counts.get('Slave miner undeployed', 0))
                elif unit_name == 'Allied AFC':
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

    def get_default_position(self):
        if not isinstance(self.player.color_name, str):
            player_color_str = self.player.color_name.name()
        else:
            player_color_str = self.player.color_name
        hud_type = self.get_hud_type()
        if player_color_str not in self.hud_pos:
            self.hud_pos[player_color_str] = {}
        if hud_type not in self.hud_pos[player_color_str]:
            default_position = {"x": 100, "y": 100}
            self.hud_pos[player_color_str][hud_type] = default_position
        else:
            default_position = self.hud_pos[player_color_str][hud_type]
        default_position['x'] = int(default_position['x'])
        default_position['y'] = int(default_position['y'])
        return default_position

    def update_hud_position(self, x, y):
        if not isinstance(self.player.color_name, str):
            player_color_str = self.player.color_name.name()
        else:
            player_color_str = self.player.color_name
        hud_type = self.get_hud_type()
        if player_color_str not in self.hud_pos:
            self.hud_pos[player_color_str] = {}
        self.hud_pos[player_color_str][hud_type] = {"x": x, "y": y}

    def get_hud_type(self):
        raise NotImplementedError("Subclasses must implement get_hud_type().")

    def create_counter_widget(self, unit_name, unit_count, unit_type):
        raise NotImplementedError("Subclasses must implement create_counter_widget().")

    def update_selected_widgets(self, faction, unit_type, unit_name, new_state):
        """Update counters when units are selected/deselected from UnitSelectionWindow."""
        if new_state:
            # Unit was selected - add counter widget if not already present
            if unit_name not in self.counters:
                unit_info = self.unit_info_by_name.get(unit_name, {})
                position = unit_info.get('position', -1)
                counter_widget = self.create_counter_widget(unit_name, 0, unit_type)
                counter_widget.hide()  # Will be shown when unit_count > 0
                
                # Insert at specified position or append at end
                if position == -1 or position >= self.layout.count():
                    self.layout.addWidget(counter_widget)
                else:
                    self.layout.insertWidget(position, counter_widget)
                
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

    def update_position_widgets(self, faction, unit_type, unit_name):
        """Update counter position when changed from UnitSelectionWindow."""
        if unit_name in self.counters:
            counter_widget, _ = self.counters[unit_name]
            unit_info = self.unit_info_by_name.get(unit_name, {})
            position = unit_info.get('position', -1)
            
            # Remove from current position
            self.layout.removeWidget(counter_widget)
            
            # Insert at new position
            if position == -1 or position >= self.layout.count():
                self.layout.addWidget(counter_widget)
            else:
                self.layout.insertWidget(position, counter_widget)
            
            self.updateGeometry()

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
        unit_image_path = name_to_path(unit_name)
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
        unit_image_path = name_to_path(unit_name)
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

        self.setWindowTitle(f"{player.color_name} Combined HUD")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()

        self._init_ui()

        # Restore saved position (for combined HUD).
        player_id = (player.color_name.name() if not isinstance(player.color_name, str) else player.color_name)
        if player_id in self.hud_pos and 'combined' in self.hud_pos[player_id]:
            pos = self.hud_pos[player_id]['combined']
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
        player_id = (self.player.color_name.name() if not isinstance(self.player.color_name, str)
                     else self.player.color_name)
        if player_id not in self.hud_pos:
            self.hud_pos[player_id] = {}
        self.hud_pos[player_id]['combined'] = {"x": x, "y": y}

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

        self.setWindowTitle(f"Player {player.color_name} Unit HUD")
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

