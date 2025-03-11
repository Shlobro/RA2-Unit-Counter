# app_state.py
import os
import threading

from constants import COLOR_NAME_MAPPING


def initialize_oil_count_files():
    folder_name = "oil counts"
    # Ensure the folder exists.
    os.makedirs(folder_name, exist_ok=True)
    # Loop over all friendly color names and create a file with a default value of 0.
    for friendly_name in COLOR_NAME_MAPPING.values():
        filename = os.path.join(folder_name, f"{friendly_name}_oil_count.txt")
        # Create the file with "0" if it doesn't exist.
        if not os.path.exists(filename):
            with open(filename, 'w') as file:
                file.write("0")


class AppState:
    def __init__(self):
        self.HUD_POSITION_FILE = 'hud_positions.json'
        self.players = []           # List to store player objects
        self.hud_windows = []       # List to store HUDWindow objects
        self.selected_units_dict = {}    # For unit selection HUD
        self.data_lock = threading.Lock()
        self.hud_positions = {}     # Stores HUD positions and settings
        self.process_handle = None  # Handle for the game process
        self.control_panel = None   # Reference to the ControlPanel instance
        self.data_update_thread = None  # Reference to the DataUpdateThread instance
        self.game_path = ''         # Game path (empty string by default)
        self.admin = True
        initialize_oil_count_files()

