# main.py
import sys
import logging
import argparse
from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QLabel

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


class TooltipOverrideFilter(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.tooltip_label = QLabel()
        self.tooltip_label.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.tooltip_label.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.tooltip_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.tooltip_label.setStyleSheet(
            "QLabel {"
            " color: #000000;"
            " background-color: #ffffff;"
            " border: 1px solid #000000;"
            " padding: 4px 6px;"
            "}"
        )
        self.tooltip_label.hide()

    def eventFilter(self, watched, event):
        event_type = event.type()

        if event_type == QEvent.ToolTip:
            tooltip_text = watched.toolTip() if hasattr(watched, "toolTip") else ""
            if tooltip_text:
                self.tooltip_label.setText(tooltip_text)
                self.tooltip_label.adjustSize()
                global_pos = event.globalPos() if hasattr(event, "globalPos") else self.app.primaryScreen().availableGeometry().topLeft()
                self.tooltip_label.move(global_pos + QPoint(16, 24))
                self.tooltip_label.show()
                return True
            self.tooltip_label.hide()
            return False

        if event_type in (QEvent.Leave, QEvent.Hide, QEvent.WindowDeactivate, QEvent.FocusOut):
            self.tooltip_label.hide()

        return super().eventFilter(watched, event)


def main():
    logging.info("Starting Resource HUD Application")
    app = QApplication(sys.argv)
    tooltip_palette = QPalette(app.palette())
    tooltip_palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    tooltip_palette.setColor(QPalette.ToolTipText, QColor("#000000"))
    tooltip_palette.setColor(QPalette.Base, QColor("#ffffff"))
    tooltip_palette.setColor(QPalette.Text, QColor("#000000"))
    app.setPalette(tooltip_palette)
    app.setStyleSheet(
        "QToolTip {"
        " color: #000000;"
        " background-color: #ffffff;"
        " border: 1px solid #000000;"
        " padding: 4px 6px;"
        "}"
    )
    app.tooltip_override_filter = TooltipOverrideFilter(app)
    app.installEventFilter(app.tooltip_override_filter)
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
