# main.py
import sys
import logging
import argparse
from PySide6.QtWidgets import QApplication

from logging_config import setup_logging
from hud_manager import (
    load_hud_positions,
    save_hud_positions,
    update_huds,
    game_started_handler,
    game_stopped_handler
)
from control_panel import ControlPanel, save_selected_units
from app_manager import wait_for_current_file_path
from data_update_thread import DataUpdateThread
from app_state import AppState


def main():
    logging.info("Starting Resource HUD Application")
    app = QApplication(sys.argv)
    state = AppState()

    data_thread = None  # Initialize data_thread here
    try:
        logging.info("Loading HUD positions")
        load_hud_positions(state)
        logging.info("Creating control panel")
        control_panel = ControlPanel(state)
        control_panel.show()
        logging.info("Waiting for a valid game path to be selected")
        wait_for_current_file_path(app, state)
        logging.info("Starting data update thread")
        data_thread = DataUpdateThread(state)
        data_thread.update_signal.connect(lambda: update_huds(state))
        data_thread.game_started.connect(lambda: game_started_handler(state))
        data_thread.game_stopped.connect(lambda: game_stopped_handler(state))
        data_thread.start()
        logging.info("Entering application event loop")
        app.exec()
    except Exception as e:
        logging.exception("Unhandled exception occurred: %s", e)
    finally:
        logging.info("Exiting application, stopping data update thread")
        try:
            if data_thread is not None:
                data_thread.stop_event.set()
                data_thread.wait()
        except Exception as thread_error:
            logging.exception("Error stopping data update thread: %s", thread_error)
        logging.info("Saving selected units and HUD positions")
        try:
            save_selected_units(state)
            save_hud_positions(state)
        except Exception as save_error:
            logging.exception("Error saving settings: %s", save_error)

if __name__ == '__main__':
    main()