# data_update_thread.py
import threading
import time
import logging
import traceback
import ctypes

from PySide6.QtCore import QThread, Signal
import psutil

from process_manager import run_create_players_in_background
from Player import ProcessExitedException

class DataUpdateThread(QThread):
    update_signal = Signal()
    game_started = Signal()
    game_stopped = Signal()

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.stop_event = threading.Event()

    def run(self):
        self.setPriority(QThread.LowPriority)
        try:
            while not self.stop_event.is_set():
                logging.info("Waiting for the game to start and players to load...")
                game_process = run_create_players_in_background(self.stop_event, self.state)
                if game_process is None:
                    if self.stop_event.is_set():
                        logging.info("Stop event set. Exiting thread.")
                        break
                    self.msleep(1000)
                    continue

                self.game_started.emit()

                while not self.stop_event.is_set():
                    try:
                        if not game_process.is_running():
                            logging.info("Game process has ended.")
                            break
                    except psutil.NoSuchProcess:
                        logging.warning("Game process no longer exists.")
                        break

                    try:
                        for player in self.state.players:
                            player.update_dynamic_data()
                        self.update_signal.emit()
                    except ProcessExitedException:
                        logging.error("Process has exited. Exiting data update loop.")
                        break
                    except Exception as e:
                        logging.error(f"Exception during updating player data: {e}")
                        traceback.print_exc()
                        break
                    delay = self.state.hud_positions.get('data_update_frequency', 1000)
                    self.msleep(delay)

                self.game_stopped.emit()
                logging.info("Emitted game_stopped signal.")

                with self.state.data_lock:
                    if self.state.process_handle:
                        ctypes.windll.kernel32.CloseHandle(self.state.process_handle)
                        self.state.process_handle = None

                self.msleep(1000)

        except Exception as e:
            logging.error(f"Error in DataUpdateThread: {e}")
            traceback.print_exc()
            self.game_stopped.emit()
        finally:
            with self.state.data_lock:
                if self.state.process_handle:
                    ctypes.windll.kernel32.CloseHandle(self.state.process_handle)
                    self.state.process_handle = None
            logging.info("Data update thread has exited.")
