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
    def check_game_path():
        state.game_path = state.hud_positions.get('game_path', '')
        spawn_ini_path = os.path.join(state.game_path, 'spawn.ini')
        logging.debug(f"Checking game path: {state.game_path}")
        if os.path.exists(spawn_ini_path):
            logging.info(f"Game path confirmed: {state.game_path}")
            timer.stop()  # Stop the timer once a valid path is found
        else:
            # Optionally, warn the user once rather than every time
            QMessageBox.warning(None, "Game Path Error", "Please choose a valid game file path.")

    logging.debug("Starting game path check timer")
    timer = QTimer()
    timer.timeout.connect(check_game_path)
    timer.start(1000)  # Check every 1000ms (1 second)

    # Instead of blocking, let the event loop run
    while not os.path.exists(os.path.join(state.hud_positions.get('game_path', ''), 'spawn.ini')):
        app.processEvents()