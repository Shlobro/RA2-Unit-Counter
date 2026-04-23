import threading
import time
import logging
import traceback
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QThread, Signal
import psutil

from process_manager import run_create_players_in_background
from Player import ProcessExitedException
from memory_utils import read_process_memory
from app_state import write_map_name_to_file, normalize_map_name


LIST_MODULES_ALL = 0x03
MAX_MODULE_COUNT = 1024
MAP_NAME_MODULE_OFFSET = 0x68B322
MAP_NAME_BUFFER_SIZE = 128


class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", ctypes.c_void_p),
        ("SizeOfImage", wintypes.DWORD),
        ("EntryPoint", ctypes.c_void_p),
    ]

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

    def _resolve_map_name_address(self):
        if not self.state.process_handle:
            return None
        if self.state.map_name_address is not None:
            return self.state.map_name_address

        psapi = ctypes.windll.psapi
        needed = wintypes.DWORD()
        modules = (ctypes.c_void_p * MAX_MODULE_COUNT)()
        success = psapi.EnumProcessModulesEx(
            self.state.process_handle,
            ctypes.byref(modules),
            ctypes.sizeof(modules),
            ctypes.byref(needed),
            LIST_MODULES_ALL
        )
        if not success:
            logging.warning("Failed to enumerate game modules for map name resolution.")
            return None

        module_count = min(needed.value // ctypes.sizeof(ctypes.c_void_p), MAX_MODULE_COUNT)
        path_buffer = ctypes.create_unicode_buffer(260)
        module_info = MODULEINFO()

        for index in range(module_count):
            module_handle = ctypes.c_void_p(modules[index])
            if not psapi.GetModuleFileNameExW(
                self.state.process_handle,
                module_handle,
                path_buffer,
                len(path_buffer)
            ):
                continue
            module_path = path_buffer.value.lower()
            if not module_path.endswith("gamemd-spawn.exe"):
                continue
            if not psapi.GetModuleInformation(
                self.state.process_handle,
                module_handle,
                ctypes.byref(module_info),
                ctypes.sizeof(module_info)
            ):
                continue
            base_address = module_info.lpBaseOfDll or 0
            self.state.map_name_address = base_address + MAP_NAME_MODULE_OFFSET
            logging.info(
                "Resolved map name address to 0x%X using module base 0x%X",
                self.state.map_name_address,
                base_address
            )
            return self.state.map_name_address

        logging.warning("Failed to find gamemd-spawn.exe module for map name resolution.")
        return None

    def _update_map_name(self):
        if not self.state.process_handle:
            return
        map_name_address = self._resolve_map_name_address()
        if map_name_address is None:
            return

        map_name_data = read_process_memory(
            self.state.process_handle,
            map_name_address,
            MAP_NAME_BUFFER_SIZE
        )
        if not map_name_data:
            return

        raw_map_name = map_name_data.decode("utf-16le", errors="ignore").split("\x00", 1)[0]
        normalized_map_name = normalize_map_name(raw_map_name)
        if normalized_map_name != self.state.current_map_name:
            self.state.current_map_name = normalized_map_name
            write_map_name_to_file(normalized_map_name)

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
                    self._update_map_name()
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
                    self.state.process_id = None
                # Clear old player objects so we won't read stale pointers next time
                self.state.players.clear()
                self.state.current_map_name = ""
                self.state.map_name_address = None
                write_map_name_to_file("")

            # Brief wait before going back to the outer loop to detect a new game
            self.msleep(1000)

        # If we ever set stop_event externally, we break out of outer loop here
        logging.info("Data update thread has exited.")
