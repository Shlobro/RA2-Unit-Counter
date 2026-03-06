import ctypes
import logging
import os
import traceback

from PySide6.QtGui import QColor

from constants import (
    country_name_to_faction, COLOR_NAME_MAPPING, NUMBEROFWFOFFSET,
    QUEUED_FACTORIES_OFFSETS, BUILDING_FACTORIES_OFFSETS,
    MAXPLAYERS, INVALIDCLASS, INFOFFSET, AIRCRAFTOFFSET, TANKOFFSET, BUILDINGOFFSET,
    CREDITSPENT_OFFSET, BALANCEOFFSET, USERNAMEOFFSET, ISWINNEROFFSET,
    POWEROUTPUTOFFSET, HOUSETYPECLASSBASEOFFSET, COUNTRYSTRINGOFFSET, COLORSCHEMEOFFSET,
    infantry_offsets, tank_offsets, structure_offsets, aircraft_offsets,
    BARRACKS_INFILTRATED_OFFSET, WAR_FACTORY_INFILTRATED_OFFSET
)
from factory import QueuedFactory, BuildingFactory
from memory_utils import read_process_memory
from exceptions import ProcessExitedException

def get_color(color_scheme):
    """Returns a QColor object based on the color scheme value."""
    from constants import COLOR_SCHEME_MAPPING
    return COLOR_SCHEME_MAPPING.get(color_scheme, QColor("black"))

def get_color_name(color_scheme):
    """Returns a friendly color name based on the color scheme value."""
    return COLOR_NAME_MAPPING.get(color_scheme, "white")


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
        self.power = 0
        self.barracks_infiltrated = False
        self.war_factory_infiltrated = False

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

        # Instantiate factory objects for each production type.
        self.factories = {
            "Aircraft": QueuedFactory(process_handle, self.real_class_base, "Aircraft"),
            "Infantry": QueuedFactory(process_handle, self.real_class_base, "Infantry"),
            "Vehicles": QueuedFactory(process_handle, self.real_class_base, "Vehicles"),
            "Ships": QueuedFactory(process_handle, self.real_class_base, "Ships"),
            "Buildings": BuildingFactory(process_handle, self.real_class_base, "Buildings"),
            "Defenses": BuildingFactory(process_handle, self.real_class_base, "Defenses")
        }

    def initialize_pointers(self):
        """
        Read pointers for building, unit (tank), infantry, and aircraft in one contiguous memory chunk.
        """
        start_offset = BUILDINGOFFSET
        end_offset = AIRCRAFTOFFSET + 4  # include 4 bytes for the last pointer
        total_bytes = end_offset - start_offset
        pointers_data = read_process_memory(self.process_handle, self.real_class_base + start_offset, total_bytes)
        if pointers_data and len(pointers_data) >= total_bytes:
            self.building_array_ptr = int.from_bytes(pointers_data[0:4], byteorder='little')
            tank_offset_relative = TANKOFFSET - BUILDINGOFFSET
            self.unit_array_ptr = int.from_bytes(pointers_data[tank_offset_relative:tank_offset_relative+4], byteorder='little')
            infantry_offset_relative = INFOFFSET - BUILDINGOFFSET
            self.infantry_array_ptr = int.from_bytes(pointers_data[infantry_offset_relative:infantry_offset_relative+4], byteorder='little')
            aircraft_offset_relative = AIRCRAFTOFFSET - BUILDINGOFFSET
            self.aircraft_array_ptr = int.from_bytes(pointers_data[aircraft_offset_relative:aircraft_offset_relative+4], byteorder='little')
        logging.debug(f"Initialized unit array pointer: {self.unit_array_ptr}")
        logging.debug(f"Initialized building array pointer: {self.building_array_ptr}")
        logging.debug(f"Initialized infantry array pointer: {self.infantry_array_ptr}")
        logging.debug(f"Initialized aircraft array pointer: {self.aircraft_array_ptr}")

    def read_and_store_inf_units_buildings(self, category_dict, array_ptr, count_type):
        try:
            if array_ptr is None:
                return {}
            counts = {}
            offsets = sorted(category_dict.keys())
            min_offset = offsets[0]
            max_offset = offsets[-1]
            chunk_size = max_offset - min_offset + 4
            # Read one contiguous chunk for count data and test data.
            chunk_data = read_process_memory(self.process_handle, array_ptr + min_offset, chunk_size)
            test_chunk_data = read_process_memory(self.process_handle, self.test_addresses[count_type] + min_offset, chunk_size)
            if not chunk_data or not test_chunk_data:
                logging.warning(f"Failed to read memory chunk for {count_type}.")
                return {}
            for offset in offsets:
                relative_index = offset - min_offset
                count_bytes = chunk_data[relative_index:relative_index + 4]
                test_bytes = test_chunk_data[relative_index:relative_index + 4]
                if count_bytes and test_bytes and len(count_bytes) == 4 and len(test_bytes) == 4:
                    count = int.from_bytes(count_bytes, byteorder='little')
                    test = int.from_bytes(test_bytes, byteorder='little')
                    name = category_dict[offset]
                    if name in ["Allied War Factory", "Soviet War Factory", "Yuri War Factory"]:
                        warFactories_ptr = self.real_class_base + NUMBEROFWFOFFSET
                        warFactories_data = read_process_memory(self.process_handle, warFactories_ptr, 4)
                        if warFactories_data:
                            warFactories = int.from_bytes(warFactories_data, byteorder='little')
                            if count <= test and count <= warFactories:
                                counts[name] = count
                            else:
                                counts[name] = 0
                    elif name == "Psychic Beacon" and 15 > count > 0:
                        counts[name] = count
                    elif name == "Oil":
                        counts[name] = count
                        self.write_oil_count_to_file(count)
                    elif count <= test:
                        counts[name] = count
                    else:
                        counts[name] = 0
                else:
                    logging.warning(f"Failed to extract 4 bytes for offset {offset} in category {count_type}.")
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
                self.balance = int.from_bytes(balance_data, byteorder='little')

            spent_credit_ptr = self.real_class_base + CREDITSPENT_OFFSET
            spent_credit_data = read_process_memory(self.process_handle, spent_credit_ptr, 4)
            if spent_credit_data:
                self.spent_credit = int.from_bytes(spent_credit_data, byteorder='little')

            winners_data = read_process_memory(self.process_handle, self.real_class_base + ISWINNEROFFSET, 2)
            if winners_data and len(winners_data) >= 2:
                self.is_winner = bool(winners_data[0])
                self.is_loser = bool(winners_data[1])

            power_data = read_process_memory(self.process_handle, self.real_class_base + POWEROUTPUTOFFSET, 8)
            if power_data and len(power_data) >= 8:
                self.power_output = int.from_bytes(power_data[0:4], byteorder='little')
                self.power_drain = int.from_bytes(power_data[4:8], byteorder='little')
                self.power = self.power_output - self.power_drain

            infiltration_data = read_process_memory(
                self.process_handle,
                self.real_class_base + BARRACKS_INFILTRATED_OFFSET,
                2
            )
            if infiltration_data and len(infiltration_data) >= 2:
                self.barracks_infiltrated = bool(infiltration_data[0])
                self.war_factory_infiltrated = bool(infiltration_data[1])

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

            # Update factory production data and log each factory's update status.
            self.update_factories()

        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in update_dynamic_data for player {self.username.value}: {e}")
            traceback.print_exc()

    def update_factories(self):
        """
        Populate self.factory_status by processing both queued and building factories.
        """
        self.factory_status = {}

        # A small helper to process a dictionary of offsets,
        # and log either "Queued factory" or "Building factory"
        def process_factory_group(group_label, offsets_dict):
            for factory_name, offset in offsets_dict.items():
                factory = self.factories.get(factory_name)
                if not factory:
                    continue

                status = factory.process_factory(offset)
                self.factory_status[factory_name] = status

                if status.get("producing"):
                    logging.Logger(f"{group_label} factory '{factory_name}' is actively producing: {status}")
                else:
                    logging.Logger(f"{group_label} factory '{factory_name}' is idle or invalid: {status}")

        # Process queued factories
        process_factory_group("Queued", QUEUED_FACTORIES_OFFSETS)

        # Process building factories
        process_factory_group("Building", BUILDING_FACTORIES_OFFSETS)


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

        fixedPointValue = int.from_bytes(fixedPointData, byteorder='little')
        classBaseArray = int.from_bytes(
            read_process_memory(process_handle, classBaseArrayPtr, 4), byteorder='little'
        )
        classBasePlayer = fixedPointValue + 1120 * 4

        for i in range(MAXPLAYERS):
            player_data = read_process_memory(process_handle, classBasePlayer, 4)
            classBasePlayer += 4
            if player_data is None:
                logging.warning(f"Skipping Player {i} due to incomplete memory read.")
                continue

            classBasePtr = int.from_bytes(player_data, byteorder='little')
            if classBasePtr == INVALIDCLASS:
                logging.info(f"Skipping Player {i} as not fully initialized yet.")
                continue

            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)
            if realClassBaseData is None:
                continue

            realClassBase = int.from_bytes(realClassBaseData, byteorder='little')

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

    fixedPointValue = int.from_bytes(fixedPointData, byteorder='little')
    classBaseArray = int.from_bytes(
        read_process_memory(process_handle, classBaseArrayPtr, 4), byteorder='little'
    )
    classbasearray = fixedPointValue + 1120 * 4
    valid_player_count = 0

    for i in range(MAXPLAYERS):
        memory_data = read_process_memory(process_handle, classbasearray, 4)
        classbasearray += 4

        if memory_data is None:
            logging.warning(f"Skipping player {i} due to incomplete memory read.")
            continue

        classBasePtr = int.from_bytes(memory_data, byteorder='little')
        if classBasePtr != INVALIDCLASS:
            valid_player_count += 1
            realClassBasePtr = classBasePtr * 4 + classBaseArray
            realClassBaseData = read_process_memory(process_handle, realClassBasePtr, 4)

            if realClassBaseData is None:
                logging.warning(f"Skipping player {i} due to incomplete real class base read.")
                continue

            realClassBase = int.from_bytes(realClassBaseData, byteorder='little')
            player = Player(i + 1, process_handle, realClassBase)

            colorPtr = realClassBase + COLORSCHEMEOFFSET
            color_data = read_process_memory(process_handle, colorPtr, 4)
            if color_data is None:
                logging.warning(f"Skipping color assignment for player {i} due to incomplete memory read.")
                continue
            color_scheme_value = int.from_bytes(color_data, byteorder='little')
            player.color = get_color(color_scheme_value)
            player.color_name = get_color_name(color_scheme_value)
            logging.info(f"Player {i} color: {player.color_name}")

            houseTypeClassBasePtr = realClassBase + HOUSETYPECLASSBASEOFFSET
            houseTypeClassBaseData = read_process_memory(process_handle, houseTypeClassBasePtr, 4)
            if houseTypeClassBaseData is None:
                logging.warning(f"Skipping country name assignment for player {i} due to incomplete memory read.")
                continue
            houseTypeClassBase = int.from_bytes(houseTypeClassBaseData, byteorder='little')
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

            # Reset oil_count.txt for player initialization.
            player.write_oil_count_to_file(0)

            game_data.add_player(player)

    logging.info(f"Number of valid players: {valid_player_count}")
    return valid_player_count
