import configparser
import json
import logging
import os
import traceback

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QWidget, QVBoxLayout

from DataTracker import ResourceWindow
from UnitWindow import (
    UnitWindowWithImages,
    UnitWindowNumbersOnly,
    UnitWindowImagesOnly,
    CombinedHudWindow,  # Combined HUD window: one window per player.
    CombinedUnitWindow  # Used in separate mode if separate unit counters are enabled.
)
from factory_window import FactoryWindow  # New import for the factory window


# ---------------------------------------------------------------------------
# Load HUD Positions
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

    defaults = {
        'unit_counter_size': 75,
        'image_size': 75,
        'number_size': 75,
        'distance_between_numbers': 0,
        'distance_between_images': 0,
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
        'combined_hud': False,    # False: separate HUD; True: combined HUD.
        # --- New defaults for factory windows ---
        'show_factory_window': True,
        'show_factory_queue': True,
        'factory_size': 100,
        'factory_layout': 'Horizontal',  # Could be Vertical as well.
        'show_factory_frames': True,
        # Toggle to show/hide the entire factory window
        'show_factory_window': True
    }
    for key, value in defaults.items():
        state.hud_positions.setdefault(key, value)


# ---------------------------------------------------------------------------
# Save HUD Positions
# ---------------------------------------------------------------------------
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
                else state.hud_positions.get('name_widget_size'))
            state.hud_positions['money_widget_size'] = (
                cp.money_size_spinbox.value() if hasattr(cp, 'money_size_spinbox')
                else state.hud_positions.get('money_widget_size'))
            state.hud_positions['power_widget_size'] = (
                cp.power_size_spinbox.value() if hasattr(cp, 'power_size_spinbox')
                else state.hud_positions.get('power_widget_size'))
            state.hud_positions['show_name'] = cp.name_checkbox.isChecked()
            state.hud_positions['show_money'] = cp.money_checkbox.isChecked()
            state.hud_positions['show_power'] = cp.power_checkbox.isChecked()
            state.hud_positions['unit_layout'] = cp.layout_combo.currentText()
            state.hud_positions['show_unit_frames'] = cp.unit_frame_checkbox.isChecked()
            state.hud_positions['money_color'] = cp.color_combo.currentText()
            state.hud_positions['separate_unit_counters'] = cp.separate_units_checkbox.isChecked()
            state.hud_positions['show_money_spent'] = cp.money_spent_checkbox.isChecked()
            state.hud_positions['money_spent_widget_size'] = cp.money_spent_size_spinbox.value()
            # --- New factory settings ---
            state.hud_positions['factory_size'] = cp.factory_size_spinbox.value()
            state.hud_positions['show_factory_frames'] = cp.factory_frame_checkbox.isChecked()
            state.hud_positions['factory_layout'] = cp.factory_layout_combo.currentText()
            # If you also added "Show Factory Window" checkbox:
            if hasattr(cp, 'show_factory_checkbox'):
                state.hud_positions['show_factory_window'] = cp.show_factory_checkbox.isChecked()

        if hasattr(state, 'control_panel') and state.control_panel and hasattr(state.control_panel, 'path_edit'):
            state.hud_positions['game_path'] = state.control_panel.path_edit.text()

        # Save positions for each player.
        for unit_window, resource_window in state.hud_windows:
            if resource_window is not None and hasattr(resource_window, 'player'):
                player_id = (resource_window.player.color_name.name()
                             if not isinstance(resource_window.player.color_name, str)
                             else resource_window.player.color_name)
                state.hud_positions.setdefault(player_id, {})
                # In combined HUD mode, unit_window is the CombinedHudWindow.
                if unit_window is not None and hasattr(unit_window, 'pos'):
                    pos = unit_window.pos()
                    state.hud_positions[player_id]['combined'] = {"x": pos.x(), "y": pos.y()}
                # In separate mode, store positions of resource windows.
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
        # Save factory window positions if available.
        if hasattr(state, 'factory_windows'):
            for factory_win in state.factory_windows:
                if factory_win is not None and hasattr(factory_win, 'pos') and factory_win.player:
                    player_id = (factory_win.player.color_name.name()
                                 if not isinstance(factory_win.player.color_name, str)
                                 else factory_win.player.color_name)
                    state.hud_positions.setdefault(player_id, {})
                    pos = factory_win.pos()
                    state.hud_positions[player_id]['factory'] = {"x": pos.x(), "y": pos.y()}
        with open(state.HUD_POSITION_FILE, 'w') as file:
            json.dump(state.hud_positions, file, indent=4)
        logging.info("HUD positions saved successfully.")
    except Exception as e:
        logging.exception("Error saving HUD positions: %s", e)


# ---------------------------------------------------------------------------
# Create Unit Windows in Current Mode
# ---------------------------------------------------------------------------
def create_unit_windows_in_current_mode(state):
    """Create unit windows for separate HUD mode only."""
    if state.hud_positions.get('combined_hud', False):
        return  # never run in combined HUD mode

    try:
        separate = state.hud_positions.get('separate_unit_counters', False)
        for i, (unit_win, res_win) in enumerate(state.hud_windows):
            player = res_win.player

            # close any existing unit_win
            if unit_win:
                if isinstance(unit_win, tuple):
                    for uw in unit_win:
                        uw.close()
                else:
                    unit_win.close()

            # create new unit windows
            if separate:
                # two separate windows
                img_win = UnitWindowImagesOnly(player, state.hud_positions, state.selected_units_dict)
                num_win = UnitWindowNumbersOnly(player, state.hud_positions, state.selected_units_dict)
                img_win.setWindowTitle(f"Player {player.color_name} Unit Images")
                num_win.setWindowTitle(f"Player {player.color_name} Unit Numbers")
                state.hud_windows[i] = ((img_win, num_win), res_win)
            else:
                # single combined unit window
                uw = UnitWindowWithImages(player, state.hud_positions, state.selected_units_dict)
                uw.setWindowTitle(f"Player {player.color_name} Unit Window")
                state.hud_windows[i] = (uw, res_win)

        logging.info("Unit windows created successfully.")
    except Exception as e:
        logging.exception("Error creating unit windows: %s", e)


# ---------------------------------------------------------------------------
# Create Overall HUD Windows
# ---------------------------------------------------------------------------
def create_hud_windows(state):
    """Create all HUD windows based on loaded players and HUD configuration."""
    try:
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
                    for w in resource_window.windows:
                        w.close()
                else:
                    resource_window.close()
        state.hud_windows = []

        # Also close any existing factory windows.
        if hasattr(state, 'factory_windows'):
            for fac_win in state.factory_windows:
                fac_win.close()
        state.factory_windows = []

        if not state.players:
            logging.info("No valid players found. HUD will not be displayed.")
            return

        show_factory = state.hud_positions.get('show_factory_window', True)

        # ----------------------------------------
        # COMBINED HUD MODE
        # ----------------------------------------
        if state.hud_positions.get('combined_hud', False):
            # One combined window per player – includes resources, units, and factory panel.
            for player in state.players:
                logging.info(f"Creating combined HUD for {player.username.value} with color {player.color_name}")
                combined = CombinedHudWindow(player, state.hud_positions, state.selected_units_dict)
                combined.show()
                # We store (combined, None) because there's no separate resource window in combined mode
                state.hud_windows.append((combined, None))

            # IMPORTANT: We do NOT create separate top-level FactoryWindows here,
            # because the CombinedHudWindow already embeds a factory panel internally.
            # So we leave state.factory_windows = [] in combined mode.

        # ----------------------------------------
        # SEPARATE HUD MODE
        # ----------------------------------------
        else:
            # Resource windows + separate unit windows + separate factory windows
            for player in state.players:
                logging.info(f"Creating ResourceWindow for {player.username.value} with color {player.color_name}")
                res_win = ResourceWindow(player, len(state.players), state.hud_positions, player.color_name)
                state.hud_windows.append((None, res_win))

                # Create a separate FactoryWindow for each player.
                # This only happens in separate HUD mode.
                logging.info(f"Creating FactoryWindow for {player.username.value} with color {player.color_name}")
                factory_win = FactoryWindow(player, state.hud_positions)
                factory_win.setWindowTitle(f"Player {player.color_name} Factory Window")
                if show_factory:
                    factory_win.show()
                else:
                    factory_win.hide()
                state.factory_windows.append(factory_win)

            # Now create the separate unit windows (images/numbers).
            create_unit_windows_in_current_mode(state)

    except Exception as e:
        logging.exception("Error creating HUD windows: %s", e)


# ---------------------------------------------------------------------------
# Update HUDs
# ---------------------------------------------------------------------------
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
        # Update factory windows as well.
        if hasattr(state, 'factory_windows'):
            for factory_win in state.factory_windows:
                factory_win.update_labels()
    except Exception as e:
        logging.error(f"Exception in update_huds: {e}")
        traceback.print_exc()


# ---------------------------------------------------------------------------
# Game Started Handler
# ---------------------------------------------------------------------------
def game_started_handler(state):
    """Handler to run when the game starts."""
    logging.info("Game started handler called")
    with state.data_lock:
        if not state.players:
            logging.info("No valid players found. HUD will not be displayed.")
            return
        create_hud_windows(state)
        # Show resource + unit windows if needed
        for unit_window, resource_window in state.hud_windows:
            if unit_window:
                unit_window.show()
            elif resource_window:
                resource_window.show()

        # Also show/hide factory windows depending on user preference
        show_factory = state.hud_positions.get('show_factory_window', True)
        if hasattr(state, 'factory_windows'):
            for factory_win in state.factory_windows:
                if show_factory:
                    factory_win.show()
                else:
                    factory_win.hide()


# ---------------------------------------------------------------------------
# Game Stopped Handler
# ---------------------------------------------------------------------------
def game_stopped_handler(state):
    logging.info("Game stopped handler called")
    # forcibly stop the data update thread:
    if hasattr(state, 'data_update_thread') and state.data_update_thread:
        state.data_update_thread.stop_event.set()
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
    if hasattr(state, 'factory_windows'):
        for factory_win in state.factory_windows:
            factory_win.close()
    state.hud_windows.clear()
    if hasattr(state, 'factory_windows'):
        state.factory_windows.clear()
    state.players.clear()
