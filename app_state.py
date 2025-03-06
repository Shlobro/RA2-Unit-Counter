# app_state.py
import threading

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
