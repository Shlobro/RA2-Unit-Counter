# hud_manager.py
import configparser
import json
import logging
import os
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QWidget, QVBoxLayout

from DataTracker import ResourceWindow
from UnitWindow import UnitWindowWithImages, UnitWindowNumbersOnly, UnitWindowImagesOnly


# ---------------------------------------------------------------------------
# CombinedHudWindow: a container widget that embeds both the resource
# window and the unit window in combined mode.
# ---------------------------------------------------------------------------
class CombinedHudWindow(QWidget):
    def __init__(self, player, hud_positions, selected_units_dict):
        """
        Create a combined HUD container for a single player.

        :param player: The player object.
        :param hud_positions: Dictionary with HUD configuration and positions.
        :param selected_units_dict: Dictionary with selected units data.
        """
        super().__init__()
        self.player = player
        self.hud_positions = hud_positions
        self.selected_units_dict = selected_units_dict
        self.setWindowTitle(f"{player.color_name} Combined HUD")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.make_hud_movable()
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        # Create and embed the ResourceWindow.
        self.resource_widget = ResourceWindow(
            self.player,
            len(self.hud_positions),  # you can adjust this value as needed
            self.hud_positions,
            self.player.color_name,
            combined_mode=True  # Tell ResourceWindow it is in combined mode.
        )
        self.resource_widget.setWindowFlags(Qt.Widget)

        # Create and embed the UnitWindowWithImages using the correct selected_units_dict.
        self.unit_widget = UnitWindowWithImages(
            self.player,
            self.hud_positions,
            self.selected_units_dict
        )
        self.unit_widget.setWindowFlags(Qt.Widget)

        layout.addWidget(self.resource_widget)
        layout.addWidget(self.unit_widget)
        self.setLayout(layout)

    def update_labels(self):
        """Update both the resource and unit widgets."""
        self.resource_widget.update_labels()
        self.unit_widget.update_labels()

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
                # TODO : save the position
                # self.update_hud_position(x, y)

        self.mousePressEvent = mouse_press_event
        self.mouseMoveEvent = mouse_move_event


# ---------------------------------------------------------------------------
# HUD Manager Functions
# ---------------------------------------------------------------------------
def load_hud_positions(state):
    """Load HUD positions and settings from a JSON file into the state."""
    try:
        if os.path.exists(state.HUD_POSITION_FILE):
            with open(state.HUD_POSITION_FILE, 'r') as file:
                state.hud_positions = json.load(file)
            logging.info("HUD positions loaded successfully.")
        else:
            state.hud_positions = {}
            logging.info("HUD positions file not found; using empty configuration.")
    except Exception as e:
        logging.exception("Error loading HUD positions: %s", e)
        state.hud_positions = {}

    # Set default configuration values.
    defaults = {
        'unit_counter_size': 75,
        'image_size': 75,
        'number_size': 75,
        'distance_between_numbers': 0,
        'show_name': True,
        'show_money': True,
        'show_power': True,
        'unit_layout': 'Vertical',
        'money_color': 'Use player color',
        'show_flag': True,
        'flag_widget_size': 50,
        'show_unit_frames': True,
        'name_widget_size': 50,
        'money_widget_size': 50,
        'power_widget_size': 50,
        'separate_unit_counters': False,
        'show_money_spent': False,
        'money_spent_widget_size': 50,
        'combined_hud': False  # False = separate windows, True = combined mode.
    }
    for key, value in defaults.items():
        state.hud_positions.setdefault(key, value)


def save_hud_positions(state):
    """Save HUD positions and settings to a JSON file."""
    try:
        if hasattr(state, 'control_panel') and state.control_panel:
            cp = state.control_panel
            state.hud_positions['unit_counter_size'] = cp.counter_size_spinbox.value()
            state.hud_positions['image_size'] = cp.image_size_spinbox.value()
            state.hud_positions['number_size'] = cp.number_size_spinbox.value()
            state.hud_positions['distance_between_numbers'] = cp.distance_spinbox.value()
            state.hud_positions['name_widget_size'] = (
                cp.name_size_spinbox.value() if hasattr(cp, 'name_size_spinbox')
                else state.hud_positions.get('name_widget_size')
            )
            state.hud_positions['money_widget_size'] = (
                cp.money_size_spinbox.value() if hasattr(cp, 'money_size_spinbox')
                else state.hud_positions.get('money_widget_size')
            )
            state.hud_positions['power_widget_size'] = (
                cp.power_size_spinbox.value() if hasattr(cp, 'power_size_spinbox')
                else state.hud_positions.get('power_widget_size')
            )
            state.hud_positions['show_name'] = cp.name_checkbox.isChecked()
            state.hud_positions['show_money'] = cp.money_checkbox.isChecked()
            state.hud_positions['show_power'] = cp.power_checkbox.isChecked()
            state.hud_positions['unit_layout'] = cp.layout_combo.currentText()
            state.hud_positions['show_unit_frames'] = cp.unit_frame_checkbox.isChecked()
            state.hud_positions['money_color'] = cp.color_combo.currentText()
            state.hud_positions['separate_unit_counters'] = cp.separate_units_checkbox.isChecked()
            state.hud_positions['show_money_spent'] = cp.money_spent_checkbox.isChecked()
            state.hud_positions['money_spent_widget_size'] = cp.money_spent_size_spinbox.value()

        if hasattr(state, 'control_panel') and state.control_panel and hasattr(state.control_panel, 'path_edit'):
            state.hud_positions['game_path'] = state.control_panel.path_edit.text()

        # Save window positions per player.
        for unit_window, resource_window in state.hud_windows:
            if resource_window is not None and hasattr(resource_window, 'player'):
                player_id = (
                    resource_window.player.color_name.name()
                    if not isinstance(resource_window.player.color_name, str)
                    else resource_window.player.color_name
                )
                state.hud_positions.setdefault(player_id, {})
                # For combined mode, store the container's position.
                if unit_window and hasattr(unit_window, 'pos'):
                    pos = unit_window.pos()
                    state.hud_positions[player_id]['combined'] = {"x": pos.x(), "y": pos.y()}
                # For separate mode, save each child window's position.
                elif hasattr(resource_window, 'windows') and resource_window.windows:
                    name_pos = resource_window.windows[0].pos()
                    money_pos = resource_window.windows[1].pos()
                    money_spent = resource_window.windows[2].pos()
                    power_pos = resource_window.windows[3].pos()
                    flag_pos = resource_window.windows[4].pos()
                    state.hud_positions[player_id]['flag'] = {"x": flag_pos.x(), "y": flag_pos.y()}
                    state.hud_positions[player_id]['name'] = {"x": name_pos.x(), "y": name_pos.y()}
                    state.hud_positions[player_id]['money'] = {"x": money_pos.x(), "y": money_pos.y()}
                    state.hud_positions[player_id]['power'] = {"x": power_pos.x(), "y": power_pos.y()}
                    state.hud_positions[player_id]['money_spent'] = {"x": money_spent.x(), "y": money_spent.y()}
        with open(state.HUD_POSITION_FILE, 'w') as file:
            json.dump(state.hud_positions, file, indent=4)
        logging.info("HUD positions saved successfully.")
    except Exception as e:
        logging.exception("Error saving HUD positions: %s", e)


def create_unit_windows_in_current_mode(state):
    """Create unit windows based on the current HUD settings."""
    try:
        separate = state.hud_positions.get('separate_unit_counters', False)
        if state.hud_positions.get('combined_hud', False):
            # In combined mode, create a CombinedHudWindow for each player.
            for i, (win, resource_win) in enumerate(state.hud_windows):
                if win:
                    win.close()
                # resource_win holds the original ResourceWindow instance (if any).
                # Replace the tuple with the CombinedHudWindow.
                state.hud_windows[i] = (
                    CombinedHudWindow(resource_win.player, state.hud_positions, state.selected_units_dict),
                    None
                )
        else:
            # In separate mode, create individual unit windows.
            for i, (unit_window, resource_window) in enumerate(state.hud_windows):
                player = resource_window.player
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.close()
                    else:
                        unit_window.close()
                if separate:
                    logging.info("Unit separate.")
                    unit_window_images = UnitWindowImagesOnly(player, state.hud_positions, state.selected_units_dict)
                    unit_window_images.setWindowTitle(f"Player {player.color_name} unit images window")
                    unit_window_numbers = UnitWindowNumbersOnly(player, state.hud_positions, state.selected_units_dict)
                    unit_window_numbers.setWindowTitle(f"Player {player.color_name} unit numbers window")
                    state.hud_windows[i] = ((unit_window_images, unit_window_numbers), resource_window)
                else:
                    logging.info("Unit UnitWindowWithImages.")
                    unit_window = UnitWindowWithImages(player, state.hud_positions, state.selected_units_dict)
                    unit_window.setWindowTitle(f"Player {player.color_name} unit window")
                    state.hud_windows[i] = (unit_window, resource_window)
        logging.info("Unit windows created successfully.")
    except Exception as e:
        logging.exception("Error creating unit windows: %s", e)


def create_hud_windows(state):
    """Create all HUD windows based on loaded players and HUD configuration."""
    try:
        if not state.game_path:
            logging.error("Game path is not defined. Please set a valid game path.")
            return

        spawn_ini_path = os.path.join(state.game_path, 'spawn.ini')
        config = configparser.ConfigParser()
        config.read(spawn_ini_path)
        if not state.admin:
            is_spectator = config.get('Settings', 'IsSpectator', fallback='False').lower() in ['true', 'yes']
            if not is_spectator:
                QMessageBox.warning(None, "Spectator Mode Required",
                                    "You can only use the Unit counter in Spectator mode.")
                return

        # Close existing windows.
        for unit_window, resource_window in state.hud_windows:
            if unit_window:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.close()
                else:
                    unit_window.close()
            if resource_window:
                if hasattr(resource_window, 'windows') and resource_window.windows:
                    for window in resource_window.windows:
                        window.close()
                else:
                    resource_window.close()
        state.hud_windows = []

        if len(state.players) == 0:
            logging.info("No valid players found. HUD will not be displayed.")
            return

        if state.hud_positions.get('combined_hud', False):
            # Combined mode: Create one CombinedHudWindow per player.
            for player in state.players:
                logging.info(f"Creating combined HUD for {player.username.value} with color {player.color_name}")
                combined_window = CombinedHudWindow(player, state.hud_positions, state.selected_units_dict)
                combined_window.show()
                state.hud_windows.append((combined_window, None))
        else:
            # Separate mode: Create a ResourceWindow for each player.
            for player in state.players:
                logging.info(f"Creating HUD for {player.username.value} with color {player.color_name}")
                resource_window = ResourceWindow(player, len(state.players), state.hud_positions, player.color_name)
                state.hud_windows.append((None, resource_window))
            create_unit_windows_in_current_mode(state)
    except Exception as e:
        logging.exception("Error creating HUD windows: %s", e)


def update_huds(state):
    """Update all HUD windows with the latest data."""
    if not state.hud_windows:
        return
    try:
        for unit_window, resource_window in state.hud_windows:
            if unit_window is not None:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.update_labels()
                else:
                    unit_window.update_labels()
            elif resource_window is not None:
                resource_window.update_labels()
    except Exception as e:
        logging.error(f"Exception in update_huds: {e}")
        traceback.print_exc()


def game_started_handler(state):
    """Handler to run when the game starts."""
    logging.info("Game started handler called")
    with state.data_lock:
        if not state.players:
            logging.info("No valid players found. HUD will not be displayed.")
            return
        create_hud_windows(state)
        for unit_window, resource_window in state.hud_windows:
            if unit_window:
                unit_window.show()
            elif resource_window:
                resource_window.show()


def game_stopped_handler(state):
    """Handler to run when the game stops."""
    logging.info("Game stopped handler called")
    save_hud_positions(state)
    for unit_window, resource_window in state.hud_windows:
        if unit_window:
            if isinstance(unit_window, tuple):
                for uw in unit_window:
                    uw.close()
            else:
                unit_window.close()
        if resource_window:
            if hasattr(resource_window, 'windows') and resource_window.windows:
                for window in resource_window.windows:
                    window.close()
            else:
                resource_window.close()
    state.hud_windows.clear()
    state.players.clear()
