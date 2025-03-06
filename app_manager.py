# app_manager.py
import time
import logging
import os

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
    new = state.game_path
    logging.debug("Waiting for valid game path")
    while not os.path.exists(spawn_ini_path):
        logging.debug(f"Current game path: {state.game_path}")
        old = new
        QMessageBox.warning(None, "Game Path Error", "Please choose a valid game file path.")
        while old == new:
            logging.debug(f"Waiting... current game path: {state.game_path}")
            app.processEvents()
            state.game_path = state.hud_positions.get('game_path', '')
            new = state.game_path
            time.sleep(1)
        spawn_ini_path = os.path.join(state.game_path, 'spawn.ini')
    logging.info(f"Game path confirmed: {state.game_path}")
