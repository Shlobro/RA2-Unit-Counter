# player.py
import ctypes
import logging
import os
import traceback

from PySide6.QtGui import QColor

# Import mappings from your constants module (instead of common)
from constants import COLOR_SCHEME_MAPPING, country_name_to_faction
from constants import (
    MAXPLAYERS, INVALIDCLASS, INFOFFSET, AIRCRAFTOFFSET, TANKOFFSET, BUILDINGOFFSET,
    CREDITSPENT_OFFSET, BALANCEOFFSET, USERNAMEOFFSET, ISWINNEROFFSET, ISLOSEROFFSET,
    POWEROUTPUTOFFSET, POWERDRAINOFFSET, HOUSETYPECLASSBASEOFFSET, COUNTRYSTRINGOFFSET, COLORSCHEMEOFFSET,
    infantry_offsets, tank_offsets, structure_offsets, aircraft_offsets
)
from memory_utils import read_process_memory
from exceptions import ProcessExitedException

def get_color(color_scheme):
    """Returns a QColor object based on the color scheme value."""
    from constants import COLOR_SCHEME_MAPPING
    return COLOR_SCHEME_MAPPING.get(color_scheme, QColor("black"))

def get_color_name(color_scheme):
    """Returns a color name based on the color scheme value."""
    return COLOR_SCHEME_MAPPING.get(color_scheme, "white")

class Player:
    def __init__(self, index, process_handle, real_class_base):
        self.index = index
        self.process_handle = process_handle
        self.real_class_base = real_class_base

        self.username = ctypes.create_unicode_buffer(0x20)
        self.color = ""
        self.color_name = ''
        self.country_name = ctypes.create_string_buffer(0x40)

        self.faction = 'Unknown'

        self.is_winner = False
        self.is_loser = False

        self.balance = 0
        self.spent_credit = 0
        self.power_output = 0
        self.power_drain = 0
        self.power = self.power_output - self.power_drain

        # Unit counts
        self.infantry_counts = {}
        self.tank_counts = {}
        self.building_counts = {}
        self.aircraft_counts = {}

        # Pointers to arrays in memory
        self.unit_array_ptr = None
        self.building_array_ptr = None
        self.infantry_array_ptr = None
        self.aircraft_array_ptr = None

        # Test addresses for validation
        self.test_addresses = {
            "infantry": self.real_class_base + 0x0b30,
            "unit": self.real_class_base + 0x1338,
            "building": self.real_class_base + 0x1b40,
            "aircraft": self.real_class_base + 0x328
        }
        self.initialize_pointers()

    def initialize_pointers(self):
        tank_offset = TANKOFFSET
        tank_ptr_address = self.real_class_base + tank_offset
        tank_ptr_data = read_process_memory(self.process_handle, tank_ptr_address, 4)
        if tank_ptr_data:
            self.unit_array_ptr = ctypes.c_uint32.from_buffer_copy(tank_ptr_data).value
        logging.debug(f"Initialized unit array pointer: {self.unit_array_ptr}")

        building_offset = BUILDINGOFFSET
        building_ptr_address = self.real_class_base + building_offset
        building_ptr_data = read_process_memory(self.process_handle, building_ptr_address, 4)
        if building_ptr_data:
            self.building_array_ptr = ctypes.c_uint32.from_buffer_copy(building_ptr_data).value
        logging.debug(f"Initialized building array pointer: {self.building_array_ptr}")

        infantry_offset = INFOFFSET
        infantry_ptr_address = self.real_class_base + infantry_offset
        infantry_ptr_data = read_process_memory(self.process_handle, infantry_ptr_address, 4)
        if infantry_ptr_data:
            self.infantry_array_ptr = ctypes.c_uint32.from_buffer_copy(infantry_ptr_data).value
        logging.debug(f"Initialized infantry array pointer: {self.infantry_array_ptr}")

        aircraft_offset = AIRCRAFTOFFSET
        aircraft_ptr_address = self.real_class_base + aircraft_offset
        aircraft_ptr_data = read_process_memory(self.process_handle, aircraft_ptr_address, 4)
        if aircraft_ptr_data:
            self.aircraft_array_ptr = ctypes.c_uint32.from_buffer_copy(aircraft_ptr_data).value
        logging.debug(f"Initialized aircraft array pointer: {self.aircraft_array_ptr}")

    def read_and_store_inf_units_buildings(self, category_dict, array_ptr, count_type):
        try:
            if array_ptr is None:
                return {}
            counts = {}
            for offset, name in category_dict.items():
                specific_address = array_ptr + offset
                test_address = self.test_addresses[count_type] + offset

                count_data = read_process_memory(self.process_handle, specific_address, 4)
                test_data = read_process_memory(self.process_handle, test_address, 4)

                if count_data and test_data:
                    count = int.from_bytes(count_data, byteorder='little')
                    test = int.from_bytes(test_data, byteorder='little')
                    if name == "Blitz oil (psychic sensor)" and 15 > count > 0:
                        counts[name] = count
                    elif name == "Oil":
                        counts[name] = count
                        self.write_oil_count_to_file(count)
                    elif count <= test:
                        counts[name] = count
                    else:
                        counts[name] = 0
                else:
                    logging.warning(f"Failed to read memory for {name}, count_data or test_data is None.")
            return counts
        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in read_and_store_inf_units_buildings for player {self.username.value}: {e}")
            traceback.print_exc()

    def write_oil_count_to_file(self, oil_count):
        try:
            folder_name = "oil counts"
            os.makedirs(folder_name, exist_ok=True)
            filename = os.path.join(folder_name, f"{self.color_name}_oil_count.txt")
            with open(filename, 'w') as file:
                file.write(str(oil_count))
            logging.debug(f"Wrote oil count {oil_count} to file {filename}")
        except Exception as e:
            logging.error(f"Failed to write oil count to file: {e}")

    def update_dynamic_data(self):
        try:
            logging.debug(f"Updating dynamic data for player {self.index}")

            balance_ptr = self.real_class_base + BALANCEOFFSET
            balance_data = read_process_memory(self.process_handle, balance_ptr, 4)
            if balance_data:
                self.balance = ctypes.c_uint32.from_buffer_copy(balance_data).value

            spent_credit_ptr = self.real_class_base + CREDITSPENT_OFFSET
            spent_credit_data = read_process_memory(self.process_handle, spent_credit_ptr, 4)
            if spent_credit_data:
                self.spent_credit = ctypes.c_uint32.from_buffer_copy(spent_credit_data).value

            is_winner_ptr = self.real_class_base + ISWINNEROFFSET
            is_winner_data = read_process_memory(self.process_handle, is_winner_ptr, 1)
            if is_winner_data:
                self.is_winner = bool(ctypes.c_uint8.from_buffer_copy(is_winner_data).value)

            is_loser_ptr = self.real_class_base + ISLOSEROFFSET
            is_loser_data = read_process_memory(self.process_handle, is_loser_ptr, 1)
            if is_loser_data:
                self.is_loser = bool(ctypes.c_uint8.from_buffer_copy(is_loser_data).value)

            power_output_ptr = self.real_class_base + POWEROUTPUTOFFSET
            power_output_data = read_process_memory(self.process_handle, power_output_ptr, 4)
            if power_output_data:
                self.power_output = ctypes.c_uint32.from_buffer_copy(power_output_data).value

            power_drain_ptr = self.real_class_base + POWERDRAINOFFSET
            power_drain_data = read_process_memory(self.process_handle, power_drain_ptr, 4)
            if power_drain_data:
                self.power_drain = ctypes.c_uint32.from_buffer_copy(power_drain_data).value

            self.power = self.power_output - self.power_drain

            if self.infantry_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.infantry_counts = self.read_and_store_inf_units_buildings(
                    infantry_offsets, self.infantry_array_ptr, "infantry"
                )

            if self.unit_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.tank_counts = self.read_and_store_inf_units_buildings(
                    tank_offsets, self.unit_array_ptr, "unit"
                )

            if self.building_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.building_counts = self.read_and_store_inf_units_buildings(
                    structure_offsets, self.building_array_ptr, "building"
                )

            if self.aircraft_array_ptr == 0:
                self.initialize_pointers()
            else:
                self.aircraft_counts = self.read_and_store_inf_units_buildings(
                    aircraft_offsets, self.aircraft_array_ptr, "aircraft"
                )

        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in update_dynamic_data for player {self.username.value}: {e}")
            traceback.print_exc()

class GameData:
    def __init__(self):
        self.players = []

    def add_player(self, player):
        self.players.append(player)

    def update_all_players(self):
        for player in self.players:
            player.update_dynamic_data()

def detect_if_all_players_are_loaded(process_handle):
    try:
        fixedPoint = 0xa8b230
        classBaseArrayPtr = 0xa8022c

        fixedPointData = read_process_memory(process_handle, fixedPoint, 4)
        if fixedPointData is None:
            logging.error("Failed to read memory at fixedPoint.")
            return False

        fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointData).value
        classBaseArray = ctypes.c_uint32.from_buffer_copy(
            read_process_memory(process_handle, classBaseArrayPtr, 4)
        ).value
        classBasePlayer = fixedPointValue + 1120 * 4

        for i in range(MAXPLAYERS):
            player_data = read_process_memory(process_handle, classBasePlayer, 4)
            classBasePlayer += 4
            if player_data is None:
                logging.warning(f"Skipping Player {i} due to incomplete memory read.")
                continue

            classBasePtr = ctypes.c_uint32.from_buffer_copy(player_data).value
            if classBasePtr == INVALIDCLASS:
                logging.info(f"Skipping Player {i} as not fully initialized yet.")
                continue

            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)
            if realClassBaseData is None:
                continue

            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value

            loaded = 0
            right_values = {0x551c: 66, 0x5778: 0, 0x57ac: 90}
            for offset, value in right_values.items():
                ptr = realClassBase + offset
                data = read_process_memory(process_handle, ptr, 4)
                if data and int.from_bytes(data, byteorder='little') == value:
                    loaded += 1

            if loaded >= 2:
                logging.info("Players loaded. Proceeding with players initialization.")
                return True
        return False

    except Exception as e:
        logging.error(f"Exception in detect_if_all_players_are_loaded: {e}")
        traceback.print_exc()
        return False

def initialize_players_after_loading(game_data, process_handle):
    game_data.players.clear()

    fixedPoint = 0xa8b230
    classBaseArrayPtr = 0xa8022c

    fixedPointData = read_process_memory(process_handle, fixedPoint, 4)
    if fixedPointData is None:
        logging.error("Failed to read memory at fixedPoint.")
        return 0

    fixedPointValue = ctypes.c_uint32.from_buffer_copy(fixedPointData).value
    classBaseArray = ctypes.c_uint32.from_buffer_copy(
        read_process_memory(process_handle, classBaseArrayPtr, 4)
    ).value
    classbasearray = fixedPointValue + 1120 * 4
    valid_player_count = 0

    for i in range(MAXPLAYERS):
        memory_data = read_process_memory(process_handle, classbasearray, 4)
        classbasearray += 4

        if memory_data is None:
            logging.warning(f"Skipping player {i} due to incomplete memory read.")
            continue

        classBasePtr = ctypes.c_uint32.from_buffer_copy(memory_data).value
        if classBasePtr != INVALIDCLASS:
            valid_player_count += 1
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)

            if realClassBaseData is None:
                logging.warning(f"Skipping player {i} due to incomplete real class base read.")
                continue

            realClassBase = ctypes.c_uint32.from_buffer_copy(realClassBaseData).value
            player = Player(i + 1, process_handle, realClassBase)

            colorPtr = realClassBase + COLORSCHEMEOFFSET
            color_data = read_process_memory(process_handle, colorPtr, 4)
            if color_data is None:
                logging.warning(f"Skipping color assignment for player {i} due to incomplete memory read.")
                continue
            color_scheme_value = ctypes.c_uint32.from_buffer_copy(color_data).value
            player.color = get_color(color_scheme_value)
            player.color_name = get_color_name(color_scheme_value)
            logging.info(f"Player {i} color: {player.color_name}")

            houseTypeClassBasePtr = realClassBase + HOUSETYPECLASSBASEOFFSET
            houseTypeClassBaseData = read_process_memory(process_handle, houseTypeClassBasePtr, 4)
            if houseTypeClassBaseData is None:
                logging.warning(f"Skipping country name assignment for player {i} due to incomplete memory read.")
                continue
            houseTypeClassBase = ctypes.c_uint32.from_buffer_copy(houseTypeClassBaseData).value
            countryNamePtr = houseTypeClassBase + COUNTRYSTRINGOFFSET
            country_data = read_process_memory(process_handle, countryNamePtr, 25)
            if country_data is None:
                logging.warning(f"Skipping country name assignment for player {i} due to incomplete memory read.")
                continue
            ctypes.memmove(player.country_name, country_data, 25)
            country_name_str = player.country_name.value.decode('utf-8').strip('\x00')
            logging.info(f"Player {i} country name: {country_name_str}")

            player.faction = country_name_to_faction(country_name_str)
            logging.info(f"Player {i} faction: {player.faction}")

            userNamePtr = realClassBase + USERNAMEOFFSET
            username_data = read_process_memory(process_handle, userNamePtr, 0x20)
            if username_data is None:
                logging.warning(f"Skipping username assignment for player {i} due to incomplete memory read.")
                continue
            ctypes.memmove(player.username, username_data, 0x20)
            logging.info(f"Player {i} name: {player.username.value}")

            game_data.add_player(player)

    logging.info(f"Number of valid players: {valid_player_count}")
    return valid_player_count
