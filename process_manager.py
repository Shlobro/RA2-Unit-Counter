# process_manager.py
import ctypes
import time
import logging
import traceback
from ctypes import wintypes

import psutil
from PySide6.QtCore import QThread

from Player import GameData, initialize_players_after_loading, detect_if_all_players_are_loaded, ProcessExitedException

def find_pid_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    return None

def find_game_process(stop_event):
    logging.info("Waiting for the game to start...")
    while not stop_event.is_set():
        pid = find_pid_by_name("gamemd-spawn.exe")
        if pid is not None:
            logging.info("Game detected")
            return pid
        time.sleep(1)
    return None

def run_create_players_in_background(stop_event, state):
    state.players.clear()
    game_data = GameData()
    pid = find_game_process(stop_event)
    if pid is None or stop_event.is_set():
        return None
    state.process_handle = ctypes.windll.kernel32.OpenProcess(wintypes.DWORD(0x1F0FFF), False, pid)
    if not state.process_handle:
        logging.error("Failed to obtain process handle.")
        return None
    game_process = psutil.Process(pid)
    try:
        while not detect_if_all_players_are_loaded(state.process_handle):
            if stop_event.is_set():
                return None
            if not game_process.is_running():
                logging.info("Game process exited before players were loaded.")
                ctypes.windll.kernel32.CloseHandle(state.process_handle)
                state.process_handle = None
                return None
            QThread.msleep(1000)
        valid_player_count = initialize_players_after_loading(game_data, state.process_handle)
        if valid_player_count > 0:
            state.players[:] = game_data.players
            return game_process
        else:
            logging.warning("No valid players found.")
            return None
    except Exception as e:
        logging.error(f"Exception in run_create_players_in_background: {e}")
        traceback.print_exc()
        return None
