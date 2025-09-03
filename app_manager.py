# app_manager.py
import time
import logging
import os
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

def on_closing(state):
    logging.info("Closing application...")
    from hud_manager import save_hud_positions
    save_hud_positions(state)
    if hasattr(state, 'data_update_thread') and state.data_update_thread:
        state.data_update_thread.stop_event.set()
        state.data_update_thread.wait()
        logging.info("Data update thread has finished.")
    QApplication.quit()


def wait_for_current_file_path(app, state):
    state.game_path = state.hud_positions.get('game_path', '')
    spawn_ini_path = os.path.join(state.game_path, 'spawn.ini')
    
    logging.debug(f"Checking game path: {state.game_path}")
    
    # Check if path is already valid
    if os.path.exists(spawn_ini_path):
        logging.info(f"Game path confirmed: {state.game_path}")
        return
    
    # Show warning only once if path is invalid
    if state.game_path:  # Only warn if a path was previously set
        logging.warning(f"Invalid game path: {state.game_path}")
        QMessageBox.warning(None, "Game Path Error", "Please choose a valid game file path in the control panel.")
    else:
        logging.info("No game path set, user needs to select one in the control panel")
        QMessageBox.information(None, "Game Path Required", "Please select your game folder path in the control panel to continue.")
    
    # Don't block - let the application continue and let user fix the path through control panel