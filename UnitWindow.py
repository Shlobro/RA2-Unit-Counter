import ctypes
import logging
from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLayout, QMenu, QLabel
from shiboken6 import isValid

from CounterWidget import (
    CounterWidgetImagesAndNumber,
    CounterWidgetNumberOnly,
    CounterWidgetImageOnly,
    apply_context_menu_style,
)
from constants import (
    name_to_path,
    country_name_to_faction,
    canonicalize_unit_name,
    SLAVE_MINER_CANONICAL_NAME,
    get_display_image_name,
)
from DataTracker import ResourceWindow
from factory_panel import FactoryPanel
from hud_position_utils import (
    get_global_widget_position,
    get_player_position,
    set_global_widget_position,
    set_player_position,
    get_player_setting,
    set_player_setting,
)
from player_identity import (
    build_player_hud_tooltip,
    get_combined_hud_title,
    get_player_bucket_key,
    get_player_display_label,
    get_player_legacy_bucket_keys,
)


def _clamp_half_visible_to_parent(widget, x, y):
    parent = widget.parentWidget()
    if parent is None:
        return x, y
    min_x = -(widget.width() // 2)
    min_y = -(widget.height() // 2)
    max_x = parent.width() - (widget.width() // 2)
    max_y = parent.height() - (widget.height() // 2)
    return max(min_x, min(x, max_x)), max(min_y, min(y, max_y))


# =============================================================================
# UnitWindowBase: Shared functionality for unit counter windows.
# =============================================================================
class UnitWindowBase(QMainWindow):
    EXPANSION_SETTING_KEY = 'unit_expansion_direction'

    def __init__(self, player, hud_pos, selected_units_dict, spacing=0, embedded_mode=False, parent=None):
        super().__init__(parent)
        self.player = player
        self.hud_pos = hud_pos
        self.embedded_mode = embedded_mode
        self.selected_units = selected_units_dict['selected_units']
        self.unit_info_by_name = {}
        self.unit_order_index = {}
        order_index = 0
        for faction, unit_types in self.selected_units.items():
            for unit_type, units in unit_types.items():
                for unit_name, unit_info in units.items():
                    canonical_name = canonicalize_unit_name(unit_name)
                    if canonical_name not in self.unit_order_index:
                        self.unit_order_index[canonical_name] = order_index
                        order_index += 1
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
        self.tooltip_text = build_player_hud_tooltip(self.player, self.hud_pos, "unit counter")

        # Set geometry and flags.
        self.setGeometry(0, 0, 120, 120)
        if self.embedded_mode:
            self.setWindowFlags(Qt.Widget)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_NoSystemBackground, True)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
            self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()

        # Create container for counters.
        self.unit_frame = QWidget(self)
        self.setToolTip(self.tooltip_text)
        self.unit_frame.setToolTip(self.tooltip_text)
        self.set_layout(self.layout_type, self.spacing)
        self.setCentralWidget(self.unit_frame)
        self.load_selected_units_and_create_counters()
        self.adjustSize()
        self._move_to_saved_anchor()
        if not self.embedded_mode:
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
        for unit_name in self.get_selected_counter_names_in_display_order():
            unit_info = self.unit_info_by_name.get(unit_name, {})
            unit_type = unit_info.get('unit_type')
            counter_widget = self.create_counter_widget(unit_name, 0, unit_type)
            counter_widget.setToolTip(self.tooltip_text)
            counter_widget.hide()
            self.layout.addWidget(counter_widget)
            self.counters[unit_name] = (counter_widget, unit_type)

    def get_selected_counter_names_in_display_order(self):
        selected_units = []
        seen_units = set()
        for unit_name, unit_info in self.unit_info_by_name.items():
            canonical_name = canonicalize_unit_name(unit_name)
            if canonical_name in seen_units or not unit_info.get('selected', False):
                continue
            selected_units.append((canonical_name, unit_info))
            seen_units.add(canonical_name)

        def sort_key(item):
            unit_name, unit_info = item
            position = unit_info.get('position', -1)
            has_explicit_position = position != -1
            return (
                0 if has_explicit_position else 1,
                position if has_explicit_position else 0,
                self.unit_order_index.get(unit_name, float('inf')),
                unit_name.casefold(),
            )

        return [unit_name for unit_name, _ in sorted(selected_units, key=sort_key)]

    def rebuild_counter_order(self):
        ordered_names = self.get_selected_counter_names_in_display_order()
        for unit_name in ordered_names:
            counter_widget, _ = self.counters[unit_name]
            self.layout.removeWidget(counter_widget)
        for unit_name in ordered_names:
            counter_widget, _ = self.counters[unit_name]
            self.layout.addWidget(counter_widget)
        self.updateGeometry()

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
                self.raise_()
                self.offset = event.pos()
        def mouse_move_event(event):
            if self.offset is not None:
                if self.parentWidget() is not None and not self.isWindow():
                    x = self.x() + event.pos().x() - self.offset.x()
                    y = self.y() + event.pos().y() - self.offset.y()
                    x, y = self._clamp_to_parent(x, y)
                else:
                    x = event.globalX() - self.offset.x()
                    y = event.globalY() - self.offset.y()
                self.move(x, y)
                self.update_hud_position(x, y)
        def mouse_release_event(event):
            if event.button() == Qt.LeftButton:
                self.offset = None
                self.update_hud_position(self.x(), self.y())
        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event
        self.mouseReleaseEvent = mouse_release_event

    def _clamp_to_parent(self, x, y):
        return _clamp_half_visible_to_parent(self, x, y)

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

    def show_context_menu(self, global_pos):
        menu = apply_context_menu_style(QMenu(self))
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

        workspace = self.window() if hasattr(self.window(), 'add_window_context_actions') else None
        if workspace is not None:
            menu.addSeparator()
            workspace_actions = workspace.add_window_context_actions(menu)
            toggle_window_bar = workspace_actions['toggle_window_bar']
            toggle_always_on_top = workspace_actions['toggle_always_on_top']
        else:
            toggle_window_bar = None
            toggle_always_on_top = None

        selected_action = menu.exec(global_pos)
        if selected_action == expand_forward:
            self._set_expansion_direction('forward')
        elif selected_action == expand_reverse:
            self._set_expansion_direction('reverse')
        elif selected_action in (toggle_window_bar, toggle_always_on_top):
            return

    def contextMenuEvent(self, event):
        self.show_context_menu(event.globalPos())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self.isWindow():
            if self._is_reverse_expansion():
                self._move_to_saved_anchor()
            x, y = self._clamp_to_parent(self.x(), self.y())
            if x != self.x() or y != self.y():
                self.move(x, y)
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
        if self.parentWidget() is not None and not self.isWindow():
            pos['x'], pos['y'] = self._clamp_to_parent(pos['x'], pos['y'])
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
                counter_widget = self.create_counter_widget(unit_name, 0, unit_type)
                counter_widget.setToolTip(self.tooltip_text)
                counter_widget.hide()  # Will be shown when unit_count > 0
                self.counters[unit_name] = (counter_widget, unit_type)
                self.layout.addWidget(counter_widget)
        else:
            # Unit was deselected - remove counter widget
            if unit_name in self.counters:
                counter_widget, _ = self.counters[unit_name]
                self.layout.removeWidget(counter_widget)
                counter_widget.setParent(None)
                del self.counters[unit_name]

        self.rebuild_counter_order()
        self.update_labels()

    def update_position_widgets(self, faction, unit_type, unit_name):
        """Update counter position when changed from UnitSelectionWindow."""
        unit_name = canonicalize_unit_name(unit_name)
        if unit_name in self.counters:
            self.rebuild_counter_order()

    def update_locked_widgets(self, faction, unit_type, unit_name, new_state):
        """Update counter when lock state changes from UnitSelectionWindow."""
        # The lock state affects visibility in update_labels, so just refresh
        self.update_labels()


# =============================================================================
# UnitWindowWithImages: Combined unit window (image and number together).
# =============================================================================
class UnitWindowWithImages(UnitWindowBase):
    def __init__(self, player, hud_pos, selected_units_dict, embedded_mode=False, parent=None):
        self.distance_between_images = hud_pos.get('distance_between_images', 0)
        super().__init__(
            player,
            hud_pos,
            selected_units_dict,
            spacing=self.distance_between_images,
            embedded_mode=embedded_mode,
            parent=parent,
        )
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
    def __init__(self, player, hud_pos, selected_units_dict, embedded_mode=False, parent=None):
        self.distance_between_images = hud_pos.get('distance_between_images', 0)
        super().__init__(
            player,
            hud_pos,
            selected_units_dict,
            spacing=self.distance_between_images,
            embedded_mode=embedded_mode,
            parent=parent,
        )
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
    def __init__(self, player, hud_pos, selected_units_dict, embedded_mode=False, parent=None):
        self.distance_between_numbers = hud_pos.get('distance_between_numbers', 0)
        super().__init__(
            player,
            hud_pos,
            selected_units_dict,
            spacing=self.distance_between_numbers,
            embedded_mode=embedded_mode,
            parent=parent,
        )
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
    def __init__(self, player, hud_pos, selected_units_dict, embedded_mode=False, parent=None):
        """
        Create a combined HUD container for a single player.
        The top section displays resource info.
        The middle section displays unit counters (images/numbers).
        The bottom section displays the factory panel (if show_factory_window is True).
        """
        super().__init__(parent)
        self.player = player
        self.hud_pos = hud_pos
        self.selected_units_dict = selected_units_dict
        self.embedded_mode = embedded_mode
        self.offset = None

        self.setWindowTitle(get_combined_hud_title(player, hud_pos))
        if self.embedded_mode:
            self.setAttribute(Qt.WA_StyledBackground, True)
        else:
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
        self.adjustSize()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        if self.embedded_mode:
            self.drag_handle = QLabel(get_player_display_label(self.player, self.hud_pos), self)
            self.drag_handle.setFixedHeight(22)
            self.drag_handle.setAlignment(Qt.AlignCenter)
            self.drag_handle.setCursor(Qt.SizeAllCursor)
            self.drag_handle.setStyleSheet(
                "background-color: rgba(0, 0, 0, 120);"
                "color: white;"
                "font-weight: bold;"
                "padding: 2px 8px;"
                "border-top-left-radius: 6px;"
                "border-top-right-radius: 6px;"
            )
            main_layout.addWidget(self.drag_handle)
            self.make_embedded_movable()
        else:
            self.drag_handle = None

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
        # We want to remove any existing unit widgets but keep the drag handle
        # (embedded mode), the resource_widget, and the factory_panel if present.
        fixed_items = 1 + (1 if self.drag_handle is not None else 0) + (1 if self.factory_panel else 0)
        while layout.count() > fixed_items:
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
        self.adjustSize()

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

    def make_embedded_movable(self):
        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self.raise_()
                self.offset = event.pos()

        def mouse_move_event(event):
            if self.offset is not None and self.parentWidget() is not None:
                new_x = self.x() + event.pos().x() - self.offset.x()
                new_y = self.y() + event.pos().y() - self.offset.y()
                self.move(new_x, new_y)
                self.update_hud_position(new_x, new_y)

        def mouse_release_event(event):
            if event.button() == Qt.LeftButton:
                self.offset = None
                self.update_hud_position(self.x(), self.y())

        self.drag_handle.mousePressEvent = mouse_press_event
        self.drag_handle.mouseMoveEvent = mouse_move_event
        self.drag_handle.mouseReleaseEvent = mouse_release_event

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


class SingleWindowWorkspace(QMainWindow):
    GEOMETRY_KEY = 'single_window_geometry'
    WINDOW_BAR_KEY = 'single_window_show_window_bar'
    ALWAYS_ON_TOP_KEY = 'single_window_always_on_top'

    def __init__(self, hud_pos):
        super().__init__()
        self.hud_pos = hud_pos
        self.canvas = QWidget(self)
        self.canvas.setObjectName("singleWindowCanvas")
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.setAutoFillBackground(False)
        self.canvas.setAttribute(Qt.WA_OpaquePaintEvent, False)
        self.canvas.setAutoFillBackground(False)
        self.setCentralWidget(self.canvas)
        self.setWindowTitle("Single Window HUD")
        self.setMinimumSize(900, 600)
        self._apply_window_chrome(self.is_window_bar_visible(), keep_geometry=False)
        self._apply_saved_geometry()

    def _get_saved_geometry(self):
        geometry = self.hud_pos.get(self.GEOMETRY_KEY, {})
        if not isinstance(geometry, dict):
            geometry = {}
        return geometry

    def _apply_saved_geometry(self):
        geometry = self._get_saved_geometry()
        width = int(geometry.get('width', 1600))
        height = int(geometry.get('height', 900))
        x = int(geometry.get('x', 50))
        y = int(geometry.get('y', 50))
        maximized = bool(geometry.get('maximized', True))

        self.setGeometry(x, y, width, height)
        if maximized:
            self.showMaximized()

    def save_geometry_to_state(self):
        normal_geometry = self.normalGeometry() if self.isMaximized() else self.geometry()
        self.hud_pos[self.GEOMETRY_KEY] = {
            'x': normal_geometry.x(),
            'y': normal_geometry.y(),
            'width': normal_geometry.width(),
            'height': normal_geometry.height(),
            'maximized': self.isMaximized(),
        }

    def save_layout_to_state(self):
        self.save_geometry_to_state()
        for child in self.canvas.findChildren(QWidget):
            if child.parentWidget() is self.canvas and hasattr(child, 'save_position_to_state'):
                child.save_position_to_state()

    def closeEvent(self, event):
        self.save_layout_to_state()
        super().closeEvent(event)

    def is_window_bar_visible(self):
        return bool(self.hud_pos.get(self.WINDOW_BAR_KEY, False))

    def is_always_on_top(self):
        return bool(self.hud_pos.get(self.ALWAYS_ON_TOP_KEY, True))

    def _apply_window_chrome(self, show_window_bar, keep_geometry=True):
        normal_geometry = self.normalGeometry() if keep_geometry and self.isMaximized() else self.geometry()
        maximized = self.isMaximized() if keep_geometry else False
        was_visible = self.isVisible()
        flags = Qt.Window
        if self.is_always_on_top():
            flags |= Qt.WindowStaysOnTopHint

        if was_visible:
            self.hide()

        if show_window_bar:
            self.setWindowFlags(flags)
            self.setAttribute(Qt.WA_TranslucentBackground, False)
            self.setAttribute(Qt.WA_NoSystemBackground, False)
            self.canvas.setAttribute(Qt.WA_TranslucentBackground, False)
            self.canvas.setAttribute(Qt.WA_NoSystemBackground, False)
            self.canvas.setAutoFillBackground(True)
            self.setAutoFillBackground(True)
            self.setStyleSheet(
                "QMainWindow { background-color: rgba(24, 24, 24, 180); }"
                "QWidget#singleWindowCanvas { background-color: rgba(24, 24, 24, 180); }"
            )
            self.canvas.setStyleSheet("background-color: rgba(24, 24, 24, 180);")
        else:
            # Keep this as a real top-level window so OBS can still enumerate it
            # for window capture while the title bar is hidden.
            self.setWindowFlags(flags | Qt.FramelessWindowHint)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_NoSystemBackground, False)
            self.canvas.setAttribute(Qt.WA_TranslucentBackground, True)
            self.canvas.setAttribute(Qt.WA_NoSystemBackground, False)
            self.canvas.setAutoFillBackground(False)
            self.setAutoFillBackground(False)
            self.setStyleSheet(
                "QMainWindow { background: transparent; border: none; }"
                "QWidget#singleWindowCanvas { background: transparent; border: none; }"
            )
            self.canvas.setStyleSheet("background-color: transparent;")

        if keep_geometry and normal_geometry.isValid():
            self.setGeometry(normal_geometry)
        if was_visible or not keep_geometry:
            self.show()
        if keep_geometry and normal_geometry.isValid():
            self.updateGeometry()
        if maximized:
            self.showMaximized()
        self._sync_native_topmost_state()
        QTimer.singleShot(0, self._sync_native_topmost_state)
        self.canvas.update()
        self.update()

    def _sync_native_topmost_state(self):
        if not hasattr(ctypes, 'windll'):
            return
        hwnd = int(self.winId())
        if not hwnd:
            return
        hwnd_topmost = -1
        hwnd_notopmost = -2
        swp_nosize = 0x0001
        swp_nomove = 0x0002
        swp_noactivate = 0x0010
        swp_showwindow = 0x0040
        insert_after = hwnd_topmost if self.is_always_on_top() else hwnd_notopmost
        ctypes.windll.user32.SetWindowPos(
            hwnd,
            insert_after,
            0,
            0,
            0,
            0,
            swp_nomove | swp_nosize | swp_noactivate | swp_showwindow,
        )

    def set_window_bar_visible(self, visible):
        visible = bool(visible)
        if self.hud_pos.get(self.WINDOW_BAR_KEY, False) == visible:
            return
        self.hud_pos[self.WINDOW_BAR_KEY] = visible
        self._apply_window_chrome(visible)

    def toggle_window_bar_visible(self):
        self.set_window_bar_visible(not self.is_window_bar_visible())

    def set_always_on_top(self, enabled):
        enabled = bool(enabled)
        self.save_layout_to_state()
        self.hud_pos[self.ALWAYS_ON_TOP_KEY] = enabled
        self._apply_window_chrome(self.is_window_bar_visible())

    def toggle_always_on_top(self):
        self.set_always_on_top(not self.is_always_on_top())

    def add_always_on_top_action(self, menu):
        action = menu.addAction("Always On Top")
        action.setCheckable(True)
        action.setChecked(self.is_always_on_top())
        action.triggered.connect(self.toggle_always_on_top)
        return action

    def add_window_bar_toggle_action(self, menu):
        action_text = "Hide Window Bar" if self.is_window_bar_visible() else "Show Window Bar"
        action = menu.addAction(action_text)
        action.triggered.connect(self.toggle_window_bar_visible)
        return action

    def add_window_context_actions(self, menu):
        return {
            'toggle_always_on_top': self.add_always_on_top_action(menu),
            'toggle_window_bar': self.add_window_bar_toggle_action(menu),
        }


class WorkspaceWidgetContainer(QWidget):
    def __init__(self, inner_widget, player, hud_pos, hud_type, parent, legacy_root_keys=None):
        super().__init__(parent)
        self.inner_widget = inner_widget
        self.player = player
        self.hud_pos = hud_pos
        self.hud_type = hud_type
        self.legacy_root_keys = legacy_root_keys or []
        self.player_bucket_key = get_player_bucket_key(self.player, self.hud_pos)
        self.legacy_player_bucket_keys = get_player_legacy_bucket_keys(self.player, self.hud_pos)
        self._drag_offset = None
        self._sync_pending = False
        self._explicitly_hidden = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.inner_widget)

        self.inner_widget.destroyed.connect(self._on_inner_destroyed)

        self._install_drag_filters(self)
        self._install_drag_filters(self.inner_widget)
        self._refresh_geometry_from_saved_position()
        self._sync_to_inner()

    def _has_live_inner_widget(self):
        return self.inner_widget is not None and isValid(self.inner_widget)

    def _on_inner_destroyed(self, *_args):
        self.inner_widget = None
        self._sync_pending = False
        if isValid(self):
            self.hide()

    def _install_drag_filters(self, widget):
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    def _find_workspace(self):
        current = self.parentWidget()
        while current is not None:
            if hasattr(current, 'add_window_context_actions'):
                return current
            current = current.parentWidget()
        return None

    def _inner_widget_has_custom_context_menu(self):
        if not self._has_live_inner_widget():
            return False
        for cls in type(self.inner_widget).mro():
            if 'contextMenuEvent' in cls.__dict__:
                return cls not in (QWidget, QMainWindow)
        return False

    def _event_global_point(self, event):
        if hasattr(event, 'globalPos'):
            return event.globalPos()
        if hasattr(event, 'globalPosition'):
            return event.globalPosition().toPoint()
        return self.mapToGlobal(self.rect().center())

    def _mouse_global_point(self, event):
        if hasattr(event, 'globalPosition'):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def _clamp_to_parent(self, x, y):
        return _clamp_half_visible_to_parent(self, x, y)

    def _get_saved_anchor_position(self):
        if self._has_live_inner_widget() and hasattr(self.inner_widget, 'get_saved_anchor_position'):
            return self.inner_widget.get_saved_anchor_position()
        return get_player_position(
            self.hud_pos,
            self.player_bucket_key,
            self.hud_type,
            legacy_root_keys=self.legacy_root_keys,
            legacy_bucket_keys=self.legacy_player_bucket_keys,
        )

    def _save_position(self, x, y):
        if self._has_live_inner_widget() and hasattr(self.inner_widget, 'top_left_to_anchor') and hasattr(self.inner_widget, 'save_anchor_position'):
            self.inner_widget.save_anchor_position(self.inner_widget.top_left_to_anchor(x, y, self.size()))
        else:
            set_player_position(self.hud_pos, self.player_bucket_key, self.hud_type, x, y)

    def save_position_to_state(self):
        self._save_position(self.x(), self.y())

    def _refresh_geometry_from_saved_position(self):
        anchor = self._get_saved_anchor_position()
        if self._has_live_inner_widget() and hasattr(self.inner_widget, 'anchor_to_top_left'):
            pos = self.inner_widget.anchor_to_top_left(anchor, self.size())
            x = pos['x']
            y = pos['y']
        else:
            x = anchor['x']
            y = anchor['y']
        x, y = self._clamp_to_parent(x, y)
        self.move(x, y)

    def _sync_to_inner(self):
        self._sync_pending = False
        if not isValid(self):
            return
        if not self._has_live_inner_widget():
            self.hide()
            return
        if self._explicitly_hidden:
            self.hide()
            return
        if self.inner_widget.isHidden():
            self.hide()
            return
        hint = self.layout().sizeHint()
        if hint.width() > 0 and hint.height() > 0:
            self.setFixedSize(hint)
        self.show()
        self._refresh_geometry_from_saved_position()

    def set_content_visible(self, visible):
        self._explicitly_hidden = not visible
        if not self._has_live_inner_widget():
            self.hide()
            return
        if visible:
            self.inner_widget.show()
            self._sync_to_inner()
        else:
            self.inner_widget.hide()
            self.hide()

    def _queue_sync_to_inner(self):
        if self._sync_pending or not self._has_live_inner_widget():
            return
        self._sync_pending = True
        QTimer.singleShot(0, self._sync_to_inner)

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type == QEvent.ContextMenu and not self._inner_widget_has_custom_context_menu():
            workspace = self._find_workspace()
            if workspace is not None:
                menu = apply_context_menu_style(QMenu(self))
                workspace.add_window_context_actions(menu)
                menu.exec(self._event_global_point(event))
                return True
        if event_type == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.raise_()
            global_pos = self._mouse_global_point(event)
            self._drag_offset = global_pos - self.mapToGlobal(self.rect().topLeft())
            return False
        if event_type == QEvent.MouseMove and self._drag_offset is not None:
            global_pos = self._mouse_global_point(event)
            new_global_pos = global_pos - self._drag_offset
            parent_pos = self.parentWidget().mapFromGlobal(new_global_pos)
            x, y = self._clamp_to_parent(parent_pos.x(), parent_pos.y())
            self.move(x, y)
            self._save_position(x, y)
            return False
        if event_type == QEvent.MouseButtonRelease and getattr(event, 'button', lambda: None)() == Qt.LeftButton:
            self._drag_offset = None
            self._save_position(self.x(), self.y())
            return False
        if watched is self.inner_widget and event_type in (QEvent.Resize, QEvent.Show, QEvent.Hide, QEvent.LayoutRequest):
            self._queue_sync_to_inner()
        return super().eventFilter(watched, event)


class GlobalWorkspaceWidgetContainer(QWidget):
    def __init__(self, inner_widget, hud_pos, widget_key, parent):
        super().__init__(parent)
        self.inner_widget = inner_widget
        self.hud_pos = hud_pos
        self.widget_key = widget_key
        self._drag_offset = None
        self._sync_pending = False
        self._explicitly_hidden = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.inner_widget)

        self.inner_widget.destroyed.connect(self._on_inner_destroyed)

        self._install_drag_filters(self)
        self._install_drag_filters(self.inner_widget)
        self._refresh_geometry_from_saved_position()
        self._sync_to_inner()

    def _has_live_inner_widget(self):
        return self.inner_widget is not None and isValid(self.inner_widget)

    def _on_inner_destroyed(self, *_args):
        self.inner_widget = None
        self._sync_pending = False
        if isValid(self):
            self.hide()

    def _install_drag_filters(self, widget):
        widget.installEventFilter(self)
        for child in widget.findChildren(QWidget):
            child.installEventFilter(self)

    def _find_workspace(self):
        current = self.parentWidget()
        while current is not None:
            if hasattr(current, 'add_window_context_actions'):
                return current
            current = current.parentWidget()
        return None

    def _inner_widget_has_custom_context_menu(self):
        if not self._has_live_inner_widget():
            return False
        for cls in type(self.inner_widget).mro():
            if 'contextMenuEvent' in cls.__dict__:
                return cls not in (QWidget, QMainWindow)
        return False

    def _event_global_point(self, event):
        if hasattr(event, 'globalPos'):
            return event.globalPos()
        if hasattr(event, 'globalPosition'):
            return event.globalPosition().toPoint()
        return self.mapToGlobal(self.rect().center())

    def _mouse_global_point(self, event):
        if hasattr(event, 'globalPosition'):
            return event.globalPosition().toPoint()
        return event.globalPos()

    def _clamp_to_parent(self, x, y):
        return _clamp_half_visible_to_parent(self, x, y)

    def _get_saved_position(self):
        return get_global_widget_position(self.hud_pos, self.widget_key)

    def _save_position(self, x, y):
        set_global_widget_position(self.hud_pos, self.widget_key, x, y)

    def save_position_to_state(self):
        self._save_position(self.x(), self.y())

    def _refresh_geometry_from_saved_position(self):
        pos = self._get_saved_position()
        x, y = self._clamp_to_parent(pos['x'], pos['y'])
        self.move(x, y)

    def _sync_to_inner(self):
        self._sync_pending = False
        if not isValid(self):
            return
        if not self._has_live_inner_widget():
            self.hide()
            return
        if self._explicitly_hidden:
            self.hide()
            return
        if self.inner_widget.isHidden():
            self.hide()
            return
        hint = self.layout().sizeHint()
        if hint.width() > 0 and hint.height() > 0:
            self.setFixedSize(hint)
        self.show()
        self._refresh_geometry_from_saved_position()

    def set_content_visible(self, visible):
        self._explicitly_hidden = not visible
        if not self._has_live_inner_widget():
            self.hide()
            return
        if visible:
            self.inner_widget.show()
            self._sync_to_inner()
        else:
            self.inner_widget.hide()
            self.hide()

    def _queue_sync_to_inner(self):
        if self._sync_pending or not self._has_live_inner_widget():
            return
        self._sync_pending = True
        QTimer.singleShot(0, self._sync_to_inner)

    def eventFilter(self, watched, event):
        event_type = event.type()
        if event_type == QEvent.ContextMenu and not self._inner_widget_has_custom_context_menu():
            workspace = self._find_workspace()
            if workspace is not None:
                menu = apply_context_menu_style(QMenu(self))
                workspace.add_window_context_actions(menu)
                menu.exec(self._event_global_point(event))
                return True
        if event_type == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
            self.raise_()
            global_pos = self._mouse_global_point(event)
            self._drag_offset = global_pos - self.mapToGlobal(self.rect().topLeft())
            return False
        if event_type == QEvent.MouseMove and self._drag_offset is not None:
            global_pos = self._mouse_global_point(event)
            new_global_pos = global_pos - self._drag_offset
            parent_pos = self.parentWidget().mapFromGlobal(new_global_pos)
            x, y = self._clamp_to_parent(parent_pos.x(), parent_pos.y())
            self.move(x, y)
            self._save_position(x, y)
            return False
        if event_type == QEvent.MouseButtonRelease and getattr(event, 'button', lambda: None)() == Qt.LeftButton:
            self._drag_offset = None
            self._save_position(self.x(), self.y())
            return False
        if watched is self.inner_widget and event_type in (QEvent.Resize, QEvent.Show, QEvent.Hide, QEvent.LayoutRequest):
            self._queue_sync_to_inner()
        return super().eventFilter(watched, event)


class SingleWindowPlayerHud:
    def __init__(self, player, hud_pos, selected_units_dict, workspace):
        self.player = player
        self.hud_pos = hud_pos
        self.selected_units_dict = selected_units_dict
        self.workspace = workspace
        self.resource_widget = ResourceWindow(
            self.player,
            0,
            self.hud_pos,
            self.player.color_name,
            combined_mode=True,
        )
        self.resource_widget.hide()
        self.factory_panel = None
        self.unit_widget = None
        self.unit_widget_images = None
        self.unit_widget_numbers = None
        self.items = {}
        self.unit_items = {}

        self._create_resource_items()
        self._create_unit_items()
        self._create_factory_item()
        self._apply_visibility_settings()

    def _register_item(self, key, item):
        self.items[key] = item
        item.show()

    def _set_workspace_item_visibility(self, item, visible):
        if item is None:
            return
        item.set_content_visible(visible)

    def _create_resource_items(self):
        self._register_item(
            'name_widget',
            WorkspaceWidgetContainer(self.resource_widget.name_widget, self.player, self.hud_pos, 'name', self.workspace.canvas),
        )
        self._register_item(
            'flag_widget',
            WorkspaceWidgetContainer(self.resource_widget.flag_widget, self.player, self.hud_pos, 'flag', self.workspace.canvas),
        )
        self._register_item(
            'money_widget',
            WorkspaceWidgetContainer(self.resource_widget.money_widget, self.player, self.hud_pos, 'money', self.workspace.canvas),
        )
        self._register_item(
            'money_widget_spent',
            WorkspaceWidgetContainer(self.resource_widget.money_spent_widget, self.player, self.hud_pos, 'money_spent', self.workspace.canvas),
        )
        self._register_item(
            'power_widget',
            WorkspaceWidgetContainer(self.resource_widget.power_widget, self.player, self.hud_pos, 'power', self.workspace.canvas),
        )
        self._register_item(
            'superweapon_widget',
            WorkspaceWidgetContainer(
                self.resource_widget.superweapon_widget,
                self.player,
                self.hud_pos,
                'superweapons',
                self.workspace.canvas,
                legacy_root_keys=['superweapon'],
            ),
        )

    def _create_unit_items(self):
        if self.hud_pos.get('separate_unit_counters', False):
            self.unit_widget_images = UnitWindowImagesOnly(
                self.player,
                self.hud_pos,
                self.selected_units_dict,
                embedded_mode=True,
            )
            self.unit_widget_numbers = UnitWindowNumbersOnly(
                self.player,
                self.hud_pos,
                self.selected_units_dict,
                embedded_mode=True,
            )
            self.unit_items['unit_widget_images'] = WorkspaceWidgetContainer(
                self.unit_widget_images,
                self.player,
                self.hud_pos,
                'unit_counter_images',
                self.workspace.canvas,
            )
            self.unit_items['unit_widget_numbers'] = WorkspaceWidgetContainer(
                self.unit_widget_numbers,
                self.player,
                self.hud_pos,
                'unit_counter_numbers',
                self.workspace.canvas,
            )
        else:
            self.unit_widget = UnitWindowWithImages(
                self.player,
                self.hud_pos,
                self.selected_units_dict,
                embedded_mode=True,
            )
            self.unit_items['unit_widget'] = WorkspaceWidgetContainer(
                self.unit_widget,
                self.player,
                self.hud_pos,
                'unit_counter_combined',
                self.workspace.canvas,
                legacy_root_keys=['combined'],
            )

    def _create_factory_item(self):
        if not self.hud_pos.get('show_factory_window', True):
            return
        from factory_window import FactoryWindow
        self.factory_panel = FactoryWindow(
            self.player,
            self.hud_pos,
            embedded_mode=True,
            parent=self.workspace.canvas,
        )
        self.factory_panel.show()

    def _apply_visibility_settings(self):
        self.set_element_visibility('name_widget', self.hud_pos.get('show_name', True))
        self.set_element_visibility('flag_widget', self.hud_pos.get('show_flag', True))
        self.set_element_visibility('money_widget', self.hud_pos.get('show_money', True))
        self.set_element_visibility('money_widget_spent', self.hud_pos.get('show_money_spent', False))
        self.set_element_visibility('power_widget', self.hud_pos.get('show_power', True))
        self.set_element_visibility('superweapon_widget', self.hud_pos.get('show_superweapons', True))

    def set_element_visibility(self, widget_name, visible):
        aliases = {
            'money_spent_widget': 'money_widget_spent',
        }
        widget_name = aliases.get(widget_name, widget_name)
        if widget_name == 'unit_widget':
            for item in self.unit_items.values():
                self._set_workspace_item_visibility(item, visible)
            return
        item = self.items.get(widget_name)
        self._set_workspace_item_visibility(item, visible)

    def update_labels(self):
        self.resource_widget.update_labels()
        if self.unit_widget is not None:
            self.unit_widget.update_labels()
        if self.unit_widget_images is not None:
            self.unit_widget_images.update_labels()
        if self.unit_widget_numbers is not None:
            self.unit_widget_numbers.update_labels()
        if self.factory_panel is not None:
            self.factory_panel.update_labels()

    def update_unit_counters_size(self, new_size, section=None):
        if self.hud_pos.get('separate_unit_counters', False):
            if section in (None, 'images') and self.unit_widget_images is not None:
                self.unit_widget_images.update_all_counters_size(new_size)
            if section in (None, 'numbers') and self.unit_widget_numbers is not None:
                self.unit_widget_numbers.update_all_counters_size(new_size)
        elif self.unit_widget is not None:
            self.unit_widget.update_all_counters_size(new_size)

    def update_show_unit_frames(self, show):
        if self.unit_widget is not None:
            self.unit_widget.update_show_unit_frames(show)
        if self.unit_widget_images is not None:
            self.unit_widget_images.update_show_unit_frames(show)
        if self.unit_widget_numbers is not None:
            self.unit_widget_numbers.update_show_unit_frames(show)

    def update_unit_layout(self, layout_type):
        if self.unit_widget is not None:
            self.unit_widget.update_layout(layout_type)
        if self.unit_widget_images is not None:
            self.unit_widget_images.update_layout(layout_type)
        if self.unit_widget_numbers is not None:
            self.unit_widget_numbers.update_layout(layout_type)

    def update_selected_widgets(self, faction, unit_type, unit_name, new_state):
        for widget in (self.unit_widget, self.unit_widget_images, self.unit_widget_numbers):
            if widget is not None:
                widget.update_selected_widgets(faction, unit_type, unit_name, new_state)

    def update_position_widgets(self, faction, unit_type, unit_name):
        for widget in (self.unit_widget, self.unit_widget_images, self.unit_widget_numbers):
            if widget is not None:
                widget.update_position_widgets(faction, unit_type, unit_name)

    def update_locked_widgets(self, faction, unit_type, unit_name, new_state):
        for widget in (self.unit_widget, self.unit_widget_images, self.unit_widget_numbers):
            if widget is not None:
                widget.update_locked_widgets(faction, unit_type, unit_name, new_state)

    def show(self):
        self._apply_visibility_settings()
        for item in self.unit_items.values():
            self._set_workspace_item_visibility(item, True)
        if self.factory_panel is not None:
            if self.hud_pos.get('show_factory_window', True):
                self.factory_panel.show()
            else:
                self.factory_panel.hide()

    def close(self):
        for item in self.items.values():
            item.close()
        for item in self.unit_items.values():
            item.close()
        for widget in (self.unit_widget, self.unit_widget_images, self.unit_widget_numbers, self.factory_panel):
            if widget is not None:
                widget.close()
        self.resource_widget.close()


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

