# app_state.py
import os
import threading
import configparser
import logging
import re

from constants import COLOR_NAME_MAPPING


OIL_COUNTS_DIR = "oil counts"
MAP_NAME_FILE = "map_name.txt"


def initialize_oil_count_files():
    folder_name = OIL_COUNTS_DIR
    # Ensure the folder exists.
    os.makedirs(folder_name, exist_ok=True)
    # Loop over all friendly color names and create a file with a default value of 0.
    for friendly_name in COLOR_NAME_MAPPING.values():
        filename = os.path.join(folder_name, f"{friendly_name}_oil_count.txt")
        # Create the file with "0" if it doesn't exist.
        if not os.path.exists(filename):
            with open(filename, 'w') as file:
                file.write("0")
    map_filename = os.path.join(folder_name, MAP_NAME_FILE)
    if not os.path.exists(map_filename):
        with open(map_filename, 'w', encoding='utf-8') as file:
            file.write("")


def normalize_map_name(raw_map_name):
    if not raw_map_name:
        return ""
    return re.sub(r"^\[[^\]]*\]\s*", "", raw_map_name).strip()


def write_map_name_to_file(map_name):
    folder_name = OIL_COUNTS_DIR
    os.makedirs(folder_name, exist_ok=True)
    filename = os.path.join(folder_name, MAP_NAME_FILE)
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(normalize_map_name(map_name))


class AppState:
    def __init__(self):
        self.HUD_POSITION_FILE = 'hud_positions.json'
        self.MATCH_HISTORY_DIR = 'match_history'
        self.players = []           # List to store player objects
        self.hud_windows = []       # List to store HUDWindow objects
        self.selected_units_dict = {}    # For unit selection HUD
        self.data_lock = threading.Lock()
        self.hud_positions = {}     # Stores HUD positions and settings
        self.process_handle = None  # Handle for the game process
        self.process_id = None
        self.control_panel = None   # Reference to the ControlPanel instance
        self.data_update_thread = None  # Reference to the DataUpdateThread instance
        self.game_path = ''         # Game path (empty string by default)
        self.admin = True
        self.scoreboard_window = None
        self.single_window_workspace = None
        self.game_time_window = None
        self.game_time_workspace_item = None
        self.game_time_widget = None
        self.map_name_window = None
        self.map_name_workspace_item = None
        self.map_name_widget = None
        self.post_game_scoreboard_shown = False
        self.last_live_scoreboard_snapshot = None
        self.pending_post_game_scoreboard_payload = None
        self.current_match_timeline = None
        self.completed_match_path = None
        self.player_color_export_cache = {}
        self.current_map_name = ""
        self.map_name_address = None
        initialize_oil_count_files()
        os.makedirs(self.MATCH_HISTORY_DIR, exist_ok=True)


def check_spectator_status(state):
    """
    Check if the player is a spectator by reading spawn.ini from the configured game folder.
    
    Args:
        state: AppState object containing game folder configuration
        
    Returns:
        bool: True if player is spectator, False otherwise
    """
    try:
        # Get the configured game folder
        game_folder = state.hud_positions.get('game_path', '') or state.game_path
        if not game_folder:
            logging.warning("Game folder not configured - cannot check spectator status")
            return False
        
        spawn_ini_path = os.path.join(game_folder, 'spawn.ini')
        
        if not os.path.exists(spawn_ini_path):
            logging.warning(f"spawn.ini not found at {spawn_ini_path}")
            return False
        
        config = configparser.ConfigParser()
        config.read(spawn_ini_path)
        
        logging.info(f"Reading spawn.ini from: {spawn_ini_path}")
        logging.info(f"Sections found: {config.sections()}")
        
        # Check if IsSpectator is True in [Settings] section
        if config.has_section('Settings'):
            if config.has_option('Settings', 'IsSpectator'):
                spectator_value = config.get('Settings', 'IsSpectator')
                logging.info(f"Raw IsSpectator value: '{spectator_value}'")
                
                # Handle both boolean and string representations
                is_spectator = spectator_value.lower() in ['true', '1', 'yes']
                logging.info(f"Parsed IsSpectator={is_spectator} in spawn.ini")
                return is_spectator
            else:
                logging.warning("IsSpectator option not found in Settings section")
                return False
        else:
            logging.warning("Settings section not found in spawn.ini")
            return False
            
    except Exception as e:
        logging.error(f"Error reading spawn.ini: {e}")
        return False

