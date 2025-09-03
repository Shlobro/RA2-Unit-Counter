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
    """
    A thread that:
      1) Waits for the game process to start and players to load
      2) Enters a loop reading memory until the game closes
      3) Emits signals to update the HUD and indicate game start/stop
      4) Returns to wait for the next new game (unless stop_event is set externally)
    """
    update_signal = Signal()
    game_started = Signal()
    game_stopped = Signal()

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.stop_event = threading.Event()

    def run(self):
        self.setPriority(QThread.LowPriority)

        # Outer loop: re-check for new games until stop_event is set
        while not self.stop_event.is_set():
            logging.info("Waiting for the game to start and players to load...")
            game_process = run_create_players_in_background(self.stop_event, self.state)
            if game_process is None:
                # No process + players found; wait briefly and try again
                if self.stop_event.is_set():
                    logging.info("Stop event set. Exiting thread.")
                    break
                self.msleep(1000)
                continue

            # We have a valid process + players => emit game_started
            self.game_started.emit()

            # Inner loop: read memory until the game ends or an error occurs
            while not self.stop_event.is_set():
                # If user quits the game, break to the outer loop
                if not game_process.is_running():
                    logging.info("Game process no longer running; stopping updates.")
                    break

                try:
                    # Attempt memory reads for each player
                    for player in self.state.players:
                        player.update_dynamic_data()
                    self.update_signal.emit()

                except ProcessExitedException:
                    # The game memory is gone or invalid
                    logging.error("Caught ProcessExitedException – game ended unexpectedly. Breaking out.")
                    break

                except Exception as e:
                    logging.error(f"Exception during updating player data: {e}")
                    traceback.print_exc()
                    break

                # Sleep per data_update_frequency
                delay = self.state.hud_positions.get('data_update_frequency', 1000)
                self.msleep(delay)

            # Once we exit the inner loop => game is done or we had an error
            self.game_stopped.emit()
            logging.info("Emitted game_stopped signal.")

            # Clean up the process handle + clear old players
            with self.state.data_lock:
                if self.state.process_handle:
                    ctypes.windll.kernel32.CloseHandle(self.state.process_handle)
                    self.state.process_handle = None
                # Clear old player objects so we won't read stale pointers next time
                self.state.players.clear()

            # Brief wait before going back to the outer loop to detect a new game
            self.msleep(1000)

        # If we ever set stop_event externally, we break out of outer loop here
        logging.info("Data update thread has exited.")
