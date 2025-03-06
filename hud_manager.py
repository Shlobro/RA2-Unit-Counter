# hud_manager.py
import configparser
import json
import logging
import os
import traceback

from PySide6.QtWidgets import QMessageBox

from DataTracker import ResourceWindow
from UnitWindow import UnitWindowWithImages, UnitWindowNumbersOnly, UnitWindowImagesOnly

def load_hud_positions(state):
    """Load HUD positions from a JSON file into the state. Set defaults for missing keys."""
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

    # Set default HUD configuration values
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
        'separate_unit_counters': False
    }
    for key, value in defaults.items():
        state.hud_positions.setdefault(key, value)

def save_hud_positions(state):
    """Save HUD positions and settings to a JSON file."""
    try:
        # Save control panel settings if available
        if hasattr(state, 'control_panel') and state.control_panel:
            cp = state.control_panel
            state.hud_positions['unit_counter_size'] = cp.counter_size_spinbox.value()
            state.hud_positions['image_size'] = cp.image_size_spinbox.value()
            state.hud_positions['number_size'] = cp.number_size_spinbox.value()
            state.hud_positions['distance_between_numbers'] = cp.distance_spinbox.value()
            state.hud_positions['name_widget_size'] = getattr(cp, 'name_size_spinbox', cp).value()  if hasattr(cp, 'name_size_spinbox') else state.hud_positions.get('name_widget_size')
            state.hud_positions['money_widget_size'] = getattr(cp, 'money_size_spinbox', cp).value() if hasattr(cp, 'money_size_spinbox') else state.hud_positions.get('money_widget_size')
            state.hud_positions['power_widget_size'] = getattr(cp, 'power_size_spinbox', cp).value() if hasattr(cp, 'power_size_spinbox') else state.hud_positions.get('power_widget_size')
            state.hud_positions['show_name'] = cp.name_checkbox.isChecked()
            state.hud_positions['show_money'] = cp.money_checkbox.isChecked()
            state.hud_positions['show_power'] = cp.power_checkbox.isChecked()
            state.hud_positions['unit_layout'] = cp.layout_combo.currentText()
            state.hud_positions['show_unit_frames'] = cp.unit_frame_checkbox.isChecked()
            state.hud_positions['money_color'] = cp.color_combo.currentText()
            state.hud_positions['separate_unit_counters'] = cp.separate_units_checkbox.isChecked()

        if hasattr(state, 'control_panel') and state.control_panel and hasattr(state.control_panel, 'path_edit'):
            state.hud_positions['game_path'] = state.control_panel.path_edit.text()

        # Save positions of each HUD window
        for unit_window, resource_window in state.hud_windows:
            # Convert player's color to a string key
            if not isinstance(resource_window.player.color_name, str):
                player_id = resource_window.player.color_name.name()
            else:
                player_id = resource_window.player.color_name
            # Ensure configuration for this player exists
            state.hud_positions.setdefault(player_id, {})

            # Get window positions
            try:
                name_pos = resource_window.windows[0].pos()
                money_pos = resource_window.windows[1].pos()
                power_pos = resource_window.windows[2].pos()
                flag_pos = resource_window.windows[3].pos()
            except Exception as e:
                logging.exception("Error getting window positions for player %s: %s", player_id, e)
                continue

            state.hud_positions[player_id]['flag'] = {"x": flag_pos.x(), "y": flag_pos.y()}
            state.hud_positions[player_id]['name'] = {"x": name_pos.x(), "y": name_pos.y()}
            state.hud_positions[player_id]['money'] = {"x": money_pos.x(), "y": money_pos.y()}
            state.hud_positions[player_id]['power'] = {"x": power_pos.x(), "y": power_pos.y()}

            separate = state.hud_positions.get('separate_unit_counters', False)
            if separate:
                try:
                    unit_window_images, unit_window_numbers = unit_window
                    unit_images_pos = unit_window_images.pos()
                    unit_numbers_pos = unit_window_numbers.pos()
                    state.hud_positions[player_id]['unit_counter_images'] = {"x": unit_images_pos.x(), "y": unit_images_pos.y()}
                    state.hud_positions[player_id]['unit_counter_numbers'] = {"x": unit_numbers_pos.x(), "y": unit_numbers_pos.y()}
                except Exception as e:
                    logging.exception("Error saving separate unit counters for player %s: %s", player_id, e)
            else:
                try:
                    unit_counter_pos = unit_window.pos()
                    state.hud_positions[player_id]['unit_counter_combined'] = {"x": unit_counter_pos.x(), "y": unit_counter_pos.y()}
                except Exception as e:
                    logging.exception("Error saving combined unit counter for player %s: %s", player_id, e)

        with open(state.HUD_POSITION_FILE, 'w') as file:
            json.dump(state.hud_positions, file, indent=4)
        logging.info("HUD positions saved successfully.")
    except Exception as e:
        logging.exception("Error saving HUD positions: %s", e)

def create_unit_windows_in_current_mode(state):
    """Create unit windows based on current HUD settings."""
    try:
        separate = state.hud_positions.get('separate_unit_counters', False)
        for i, (unit_window, resource_window) in enumerate(state.hud_windows):
            player = resource_window.player
            if unit_window:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.close()
                else:
                    unit_window.close()
            if separate:
                unit_window_images = UnitWindowImagesOnly(player, state.hud_positions, state.selected_units_dict)
                unit_window_images.setWindowTitle(f"Player {player.color_name} unit images window")
                unit_window_numbers = UnitWindowNumbersOnly(player, state.hud_positions, state.selected_units_dict)
                unit_window_numbers.setWindowTitle(f"Player {player.color_name} unit numbers window")
                state.hud_windows[i] = ((unit_window_images, unit_window_numbers), resource_window)
            else:
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
                QMessageBox.warning(None, "Spectator Mode Required", "You can only use the Unit counter in Spectator mode.")
                return
        # Close existing windows
        for unit_window, resource_window in state.hud_windows:
            if unit_window:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.close()
                else:
                    unit_window.close()
            for window in resource_window.windows:
                window.close()
        state.hud_windows = []
        if len(state.players) == 0:
            logging.info("No valid players found. HUD will not be displayed.")
            return
        for player in state.players:
            logging.info(f"Creating HUD for {player.username.value} with color {player.color_name}")
            resource_window = ResourceWindow(player, len(state.players), state.hud_positions, player.color_name)
            state.hud_windows.append((None, resource_window))
        create_unit_windows_in_current_mode(state)
    except Exception as e:
        logging.exception("Error creating HUD windows: %s", e)

def update_huds(state):
    """Update all HUD windows with the latest data."""
    if len(state.hud_windows) == 0:
        return
    try:
        for unit_window, resource_window in state.hud_windows:
            if unit_window:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.update_labels()
                else:
                    unit_window.update_labels()
            resource_window.update_labels()
    except Exception as e:
        logging.error(f"Exception in update_huds: {e}")
        traceback.print_exc()

def game_started_handler(state):
    """Handler to run when the game starts."""
    logging.info("Game started handler called")
    with state.data_lock:
        if len(state.players) == 0:
            logging.info("No valid players found. HUD will not be displayed.")
            return
        create_hud_windows(state)
        for unit_window, resource_window in state.hud_windows:
            if unit_window:
                if isinstance(unit_window, tuple):
                    for uw in unit_window:
                        uw.show()
                else:
                    unit_window.show()

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
        for window in resource_window.windows:
            window.close()
    state.hud_windows.clear()
    state.players.clear()
