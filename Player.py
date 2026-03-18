import ctypes
from datetime import datetime
import logging
import os
import traceback

from PySide6.QtGui import QColor

from constants import (
    country_name_to_faction, COLOR_NAME_MAPPING, NUMBEROFWFOFFSET,
    QUEUED_FACTORIES_OFFSETS, BUILDING_FACTORIES_OFFSETS,
    MAXPLAYERS, INVALIDCLASS, INFOFFSET, AIRCRAFTOFFSET, TANKOFFSET, BUILDINGOFFSET,
    CREDITSPENT_OFFSET, HARVESTED_CREDITS_OFFSET, CAPTURED_BUILDING_CREDITS_OFFSET, OWNED_BUILDING_COUNT_OFFSET,
    BALANCEOFFSET, USERNAMEOFFSET, ISWINNEROFFSET, ISLOSEROFFSET, ISDEFEATEDFLAGOFFSET,
    POST_GAME_TRIGGER_WIN_OFFSET, POST_GAME_TRIGGER_LOSS_OFFSET,
    POWEROUTPUTOFFSET, HOUSETYPECLASSBASEOFFSET, COUNTRYSTRINGOFFSET, COLORSCHEMEOFFSET,
    infantry_offsets, tank_offsets, structure_offsets, aircraft_offsets,
    BARRACKS_INFILTRATED_OFFSET, WAR_FACTORY_INFILTRATED_OFFSET,
    BUILT_INFANTRY_TOTAL_OFFSETS, BUILT_UNIT_TOTAL_OFFSETS, BUILT_BUILDING_TOTAL_OFFSETS,
    BUILT_AIRCRAFT_TOTAL_OFFSETS, LOST_INFANTRY_TOTAL_OFFSETS, LOST_UNIT_TOTAL_OFFSETS,
    LOST_BUILDING_TOTAL_OFFSETS, LOST_AIRCRAFT_TOTAL_OFFSETS, SUPERS_VECTOR_OFFSET,
    SUPERS_DVC_ITEMS_PTR_OFFSET, SUPERS_DVC_COUNT_OFFSET,
    SUPERCLASS_NOT_OWNED, SUPERCLASS_READY_VALUE, SUPERWEAPON_ORDER,
    SUPERS_DVC_LEGACY_ITEMS_PTR_OFFSET, SUPERS_DVC_LEGACY_COUNT_OFFSET,
    HOUSE_SUPERS_ITEMS_PTR_OFFSET, HOUSE_SUPERS_COUNT_OFFSET,
    SUPERCLASS_OWNERSHIP_OFFSET, SUPERCLASS_READY_OFFSET, SUPERCLASS_CHARGE_OFFSET
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

OIL_DERRICK_NAMES = {"Oil", "Oil Derrick", "Tech Oil Derrick"}
PRESENT_COUNT_POINTER_OFFSET_DELTA = 0x50
COUNTER_CLASS_SIZE = 0x14
TRACKED_MISMATCH_UNITS = {
    "Chrono Legionnaire": ("infantry", 0x3C),
    "Rocketeer": ("infantry", 0x10),
    "Mirage Tank": ("unit", 0x94),
}
MCV_UNIT_NAMES = (
    "Allied Construction Vehicle",
    "Soviet Construction Vehicle",
    "Yuri Construction Vehicle",
)


class Player:
    mismatch_logger = None
    mismatch_log_path = None

    def __init__(self, index, process_handle, real_class_base):
        self.index = index
        self.display_slot = index + 1
        self.process_handle = process_handle
        self.real_class_base = real_class_base

        self.username = ctypes.create_unicode_buffer(0x20)
        self.color = ""
        self.color_name = ''
        self.country_name = ctypes.create_string_buffer(0x40)

        self.faction = 'Unknown'

        self.is_winner = False
        self.is_loser = False
        self.is_defeated_flag = False
        self.post_game_triggered = False

        self.balance = 0
        self.spent_credit = 0
        self.harvested_credits = 0
        self.captured_building_credits = 0
        self.owned_building_count = 0
        self.power_output = 0
        self.power_drain = 0
        self.power = 0
        self.barracks_infiltrated = False
        self.war_factory_infiltrated = False
        self.superweapon_order = list(SUPERWEAPON_ORDER)
        self.superweapon_timers = {
            name: {"owned": False, "raw_value": SUPERCLASS_NOT_OWNED, "percent": 0}
            for name in self.superweapon_order
        }

        # Unit counts
        self.infantry_counts = {}
        self.tank_counts = {}
        self.building_counts = {}
        self.aircraft_counts = {}
        self.built_infantry_counts = {}
        self.built_tank_counts = {}
        self.built_building_counts = {}
        self.built_aircraft_counts = {}
        self.lost_infantry_counts = {}
        self.lost_tank_counts = {}
        self.lost_building_counts = {}
        self.lost_aircraft_counts = {}

        # Pointers to arrays in memory
        self.unit_array_ptr = None
        self.building_array_ptr = None
        self.infantry_array_ptr = None
        self.aircraft_array_ptr = None
        self.unit_array_capacity = 0
        self.building_array_capacity = 0
        self.infantry_array_capacity = 0
        self.aircraft_array_capacity = 0
        self.unit_present_array_ptr = None
        self.building_present_array_ptr = None
        self.infantry_present_array_ptr = None
        self.aircraft_present_array_ptr = None
        self.unit_present_array_capacity = 0
        self.building_present_array_capacity = 0
        self.infantry_present_array_capacity = 0
        self.aircraft_present_array_capacity = 0
        self._last_mismatch_states = {}

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

    @classmethod
    def _get_mismatch_logger(cls):
        if cls.mismatch_logger is not None:
            return cls.mismatch_logger

        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cls.mismatch_log_path = os.path.join(log_dir, f"count_mismatch_{timestamp}.log")

        logger = logging.getLogger("count_mismatch")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if not logger.handlers:
            handler = logging.FileHandler(cls.mismatch_log_path, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
            logger.addHandler(handler)

        cls.mismatch_logger = logger
        logging.info("Count mismatch log file initialized at %s", cls.mismatch_log_path)
        return cls.mismatch_logger

    def initialize_pointers(self):
        """
        Read CounterClass headers for building, unit (tank), infantry, and aircraft.
        """
        start_offset = BUILDINGOFFSET
        end_offset = AIRCRAFTOFFSET + COUNTER_CLASS_SIZE
        total_bytes = end_offset - start_offset
        pointers_data = read_process_memory(self.process_handle, self.real_class_base + start_offset, total_bytes)
        if pointers_data and len(pointers_data) >= total_bytes:
            self.building_array_ptr = int.from_bytes(pointers_data[0:4], byteorder='little')
            self.building_array_capacity = int.from_bytes(pointers_data[4:8], byteorder='little')
            tank_offset_relative = TANKOFFSET - BUILDINGOFFSET
            self.unit_array_ptr = int.from_bytes(
                pointers_data[tank_offset_relative:tank_offset_relative + 4],
                byteorder='little'
            )
            self.unit_array_capacity = int.from_bytes(
                pointers_data[tank_offset_relative + 4:tank_offset_relative + 8],
                byteorder='little'
            )
            infantry_offset_relative = INFOFFSET - BUILDINGOFFSET
            self.infantry_array_ptr = int.from_bytes(
                pointers_data[infantry_offset_relative:infantry_offset_relative + 4],
                byteorder='little'
            )
            self.infantry_array_capacity = int.from_bytes(
                pointers_data[infantry_offset_relative + 4:infantry_offset_relative + 8],
                byteorder='little'
            )
            aircraft_offset_relative = AIRCRAFTOFFSET - BUILDINGOFFSET
            self.aircraft_array_ptr = int.from_bytes(
                pointers_data[aircraft_offset_relative:aircraft_offset_relative + 4],
                byteorder='little'
            )
            self.aircraft_array_capacity = int.from_bytes(
                pointers_data[aircraft_offset_relative + 4:aircraft_offset_relative + 8],
                byteorder='little'
            )
        logging.debug(f"Initialized unit array pointer: {self.unit_array_ptr}")
        logging.debug(f"Initialized building array pointer: {self.building_array_ptr}")
        logging.debug(f"Initialized infantry array pointer: {self.infantry_array_ptr}")
        logging.debug(f"Initialized aircraft array pointer: {self.aircraft_array_ptr}")
        present_start_offset = BUILDINGOFFSET + PRESENT_COUNT_POINTER_OFFSET_DELTA
        present_end_offset = AIRCRAFTOFFSET + PRESENT_COUNT_POINTER_OFFSET_DELTA + COUNTER_CLASS_SIZE
        present_total_bytes = present_end_offset - present_start_offset
        present_pointers_data = read_process_memory(
            self.process_handle,
            self.real_class_base + present_start_offset,
            present_total_bytes
        )
        if present_pointers_data and len(present_pointers_data) >= present_total_bytes:
            self.building_present_array_ptr = int.from_bytes(present_pointers_data[0:4], byteorder='little')
            self.building_present_array_capacity = int.from_bytes(present_pointers_data[4:8], byteorder='little')
            tank_offset_relative = TANKOFFSET - BUILDINGOFFSET
            self.unit_present_array_ptr = int.from_bytes(
                present_pointers_data[tank_offset_relative:tank_offset_relative + 4],
                byteorder='little'
            )
            self.unit_present_array_capacity = int.from_bytes(
                present_pointers_data[tank_offset_relative + 4:tank_offset_relative + 8],
                byteorder='little'
            )
            infantry_offset_relative = INFOFFSET - BUILDINGOFFSET
            self.infantry_present_array_ptr = int.from_bytes(
                present_pointers_data[infantry_offset_relative:infantry_offset_relative + 4],
                byteorder='little'
            )
            self.infantry_present_array_capacity = int.from_bytes(
                present_pointers_data[infantry_offset_relative + 4:infantry_offset_relative + 8],
                byteorder='little'
            )
            aircraft_offset_relative = AIRCRAFTOFFSET - BUILDINGOFFSET
            self.aircraft_present_array_ptr = int.from_bytes(
                present_pointers_data[aircraft_offset_relative:aircraft_offset_relative + 4],
                byteorder='little'
            )
            self.aircraft_present_array_capacity = int.from_bytes(
                present_pointers_data[aircraft_offset_relative + 4:aircraft_offset_relative + 8],
                byteorder='little'
            )
        logging.debug(f"Initialized present unit array pointer: {self.unit_present_array_ptr}")
        logging.debug(f"Initialized present building array pointer: {self.building_present_array_ptr}")
        logging.debug(f"Initialized present infantry array pointer: {self.infantry_present_array_ptr}")
        logging.debug(f"Initialized present aircraft array pointer: {self.aircraft_present_array_ptr}")

    def read_and_store_inf_units_buildings(
        self,
        category_dict,
        array_ptr,
        array_capacity,
        present_array_ptr,
        present_array_capacity,
        count_type
    ):
        try:
            if array_ptr is None:
                return {}
            counts = {}
            for offset, name in category_dict.items():
                if array_capacity <= 0 or offset >= array_capacity * 4:
                    logging.debug(
                        "Skipping %s for player %s because offset 0x%x exceeds %s capacity %s",
                        name,
                        self.username.value,
                        offset,
                        count_type,
                        array_capacity,
                    )
                    counts[name] = 0
                    continue
                count_bytes = read_process_memory(self.process_handle, array_ptr + offset, 4)
                present_count_bytes = None
                if present_array_ptr not in (None, 0) and present_array_capacity > 0 and offset < present_array_capacity * 4:
                    present_count_bytes = read_process_memory(self.process_handle, present_array_ptr + offset, 4)
                test_bytes = read_process_memory(
                    self.process_handle,
                    self.test_addresses[count_type] + offset,
                    4
                )
                if count_bytes and test_bytes and len(count_bytes) == 4 and len(test_bytes) == 4:
                    count = int.from_bytes(count_bytes, byteorder='little')
                    test = int.from_bytes(test_bytes, byteorder='little')
                    present_count = None
                    if present_count_bytes and len(present_count_bytes) == 4:
                        present_count = int.from_bytes(present_count_bytes, byteorder='little')
                        if present_count < count:
                            logging.warning(
                                "%s present-on-map count %s is lower than owned count %s for player %s",
                                name,
                                present_count,
                                count,
                                self.username.value,
                            )

                    if name in ["Allied War Factory", "Soviet War Factory", "Yuri War Factory"]:
                        warFactories_ptr = self.real_class_base + NUMBEROFWFOFFSET
                        warFactories_data = read_process_memory(self.process_handle, warFactories_ptr, 4)
                        if warFactories_data:
                            warFactories = int.from_bytes(warFactories_data, byteorder='little')
                            if count <= test and count <= warFactories:
                                counts[name] = count
                            else:
                                counts[name] = 0
                        else:
                            counts[name] = 0
                    elif name == "Psychic Beacon" and 15 > count > 0:
                        counts[name] = count
                    elif name in OIL_DERRICK_NAMES:
                        # Oil derricks are capturable tech buildings, so built totals are not authoritative.
                        counts[name] = count
                        self.write_oil_count_to_file(count)
                    else:
                        if count <= test:
                            counts[name] = count
                        else:
                            counts[name] = 0
                            if count > test:
                                logging.debug(
                                    "Rejected %s count %s for player %s because it exceeded total made %s",
                                    name,
                                    count,
                                    self.username.value,
                                    test,
                                )
                else:
                    logging.warning(f"Failed to read 4 bytes for {name} in category {count_type}.")
            return counts
        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in read_and_store_inf_units_buildings for player {self.username.value}: {e}")
            traceback.print_exc()

    def read_score_struct_counts(self, category_dict):
        try:
            if not category_dict:
                return {}

            counts = {}
            offsets = sorted(category_dict.keys())
            min_offset = offsets[0]
            max_offset = offsets[-1]
            chunk_size = max_offset - min_offset + 4
            chunk_data = read_process_memory(self.process_handle, self.real_class_base + min_offset, chunk_size)
            if not chunk_data:
                logging.warning(f"Failed to read score struct chunk for player {self.username.value}")
                return {}

            for offset in offsets:
                relative_index = offset - min_offset
                count_bytes = chunk_data[relative_index:relative_index + 4]
                if len(count_bytes) != 4:
                    continue
                count = int.from_bytes(count_bytes, byteorder='little')
                if count > 0:
                    counts[category_dict[offset]] = count
            return counts
        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in read_score_struct_counts for player {self.username.value}: {e}")
            traceback.print_exc()
            return {}

    def _get_counter_context(self, count_type):
        if count_type == "infantry":
            return {
                "owned_ptr": self.infantry_array_ptr,
                "owned_capacity": self.infantry_array_capacity,
                "present_ptr": self.infantry_present_array_ptr,
                "present_capacity": self.infantry_present_array_capacity,
                "built_counts": self.built_infantry_counts,
                "lost_counts": self.lost_infantry_counts,
            }
        if count_type == "unit":
            return {
                "owned_ptr": self.unit_array_ptr,
                "owned_capacity": self.unit_array_capacity,
                "present_ptr": self.unit_present_array_ptr,
                "present_capacity": self.unit_present_array_capacity,
                "built_counts": self.built_tank_counts,
                "lost_counts": self.lost_tank_counts,
            }
        return None

    def _log_tracked_count_mismatches(self):
        mismatch_logger = None
        for unit_name, (count_type, offset) in TRACKED_MISMATCH_UNITS.items():
            context = self._get_counter_context(count_type)
            if context is None:
                continue

            owned_count = None
            if (
                context["owned_ptr"] not in (None, 0)
                and context["owned_capacity"] > 0
                and offset < context["owned_capacity"] * 4
            ):
                owned_bytes = read_process_memory(self.process_handle, context["owned_ptr"] + offset, 4)
                if owned_bytes and len(owned_bytes) == 4:
                    owned_count = int.from_bytes(owned_bytes, byteorder="little")

            present_count = None
            if (
                context["present_ptr"] not in (None, 0)
                and context["present_capacity"] > 0
                and offset < context["present_capacity"] * 4
            ):
                present_bytes = read_process_memory(self.process_handle, context["present_ptr"] + offset, 4)
                if present_bytes and len(present_bytes) == 4:
                    present_count = int.from_bytes(present_bytes, byteorder="little")

            built_count = context["built_counts"].get(unit_name, 0)
            lost_count = context["lost_counts"].get(unit_name, 0)
            displayed_count = None
            if count_type == "infantry":
                displayed_count = self.infantry_counts.get(unit_name, 0)
            elif count_type == "unit":
                displayed_count = self.tank_counts.get(unit_name, 0)

            mismatch = (
                owned_count is not None and present_count is not None and owned_count != present_count
            )
            state = (
                owned_count,
                present_count,
                built_count,
                lost_count,
                displayed_count,
                context["owned_ptr"],
                context["owned_capacity"],
                context["present_ptr"],
                context["present_capacity"],
            )

            if not mismatch:
                self._last_mismatch_states.pop(unit_name, None)
                continue

            if self._last_mismatch_states.get(unit_name) == state:
                continue

            self._last_mismatch_states[unit_name] = state
            mismatch_logger = mismatch_logger or self._get_mismatch_logger()
            mismatch_logger.info(
                (
                    "player=%s slot=%s unit=%s type=%s displayed=%s owned=%s present=%s "
                    "built=%s lost=%s owned_ptr=0x%08X owned_capacity=%s "
                    "present_ptr=0x%08X present_capacity=%s offset=0x%X"
                ),
                self.username.value or "<empty>",
                self.display_slot,
                unit_name,
                count_type,
                displayed_count,
                owned_count,
                present_count,
                built_count,
                lost_count,
                context["owned_ptr"] or 0,
                context["owned_capacity"],
                context["present_ptr"] or 0,
                context["present_capacity"],
                offset,
            )

    @staticmethod
    def merge_counts(*count_dicts):
        merged = {}
        for count_dict in count_dicts:
            for unit_name, count in count_dict.items():
                merged[unit_name] = merged.get(unit_name, 0) + count
        return merged

    def get_current_unit_totals(self):
        return self.merge_counts(
            self.infantry_counts,
            self.tank_counts,
            self.building_counts,
            self.aircraft_counts
        )

    def get_built_unit_totals(self):
        return self.merge_counts(
            self.built_infantry_counts,
            self.built_tank_counts,
            self.built_building_counts,
            self.built_aircraft_counts
        )

    def get_killed_unit_totals(self):
        return self.merge_counts(
            self.lost_infantry_counts,
            self.lost_tank_counts,
            self.lost_building_counts,
            self.lost_aircraft_counts
        )

    def get_lost_unit_totals(self):
        return self.get_killed_unit_totals()

    def get_mcv_count(self):
        return sum(self.tank_counts.get(unit_name, 0) for unit_name in MCV_UNIT_NAMES)

    def has_lost_game(self):
        return self.owned_building_count == 0 and self.get_mcv_count() == 0

    def _normalize_color_name_for_oil_file(self):
        if isinstance(self.color_name, str) and self.color_name in COLOR_NAME_MAPPING.values():
            return self.color_name

        color_value = self.color_name if not isinstance(self.color_name, str) else self.color
        if hasattr(color_value, "name"):
            try:
                normalized_hex = color_value.name().lower()
                for scheme_id, mapped_name in COLOR_NAME_MAPPING.items():
                    mapped_color = get_color(scheme_id)
                    if mapped_color.name().lower() == normalized_hex:
                        return mapped_name
            except Exception:
                pass

        if isinstance(self.color_name, str) and self.color_name:
            logging.warning(
                f"Unexpected color_name {self.color_name!r} for player {self.username.value}; "
                "falling back to white oil count file."
            )
        return "white"

    def get_normalized_color_name_for_file(self):
        return self._normalize_color_name_for_oil_file()

    def write_oil_count_to_file(self, oil_count):
        try:
            folder_name = "oil counts"
            os.makedirs(folder_name, exist_ok=True)
            normalized_color_name = self.get_normalized_color_name_for_file()
            filename = os.path.join(folder_name, f"{normalized_color_name}_oil_count.txt")
            with open(filename, 'w') as file:
                file.write(str(oil_count))
            logging.debug(f"Wrote oil count {oil_count} to file {filename}")
        except Exception as e:
            logging.error(f"Failed to write oil count to file: {e}")

    def update_dynamic_data(self):
        try:
            logging.debug(f"Updating dynamic data for player {self.index}")

            resource_start = CREDITSPENT_OFFSET
            resource_size = OWNED_BUILDING_COUNT_OFFSET - CREDITSPENT_OFFSET + 4
            resource_data = read_process_memory(
                self.process_handle,
                self.real_class_base + resource_start,
                resource_size
            )
            if resource_data and len(resource_data) >= resource_size:
                spent_index = CREDITSPENT_OFFSET - resource_start
                harvested_index = HARVESTED_CREDITS_OFFSET - resource_start
                captured_index = CAPTURED_BUILDING_CREDITS_OFFSET - resource_start
                self.spent_credit = int.from_bytes(resource_data[spent_index:spent_index + 4], byteorder='little')
                self.harvested_credits = int.from_bytes(
                    resource_data[harvested_index:harvested_index + 4],
                    byteorder='little'
                )
                self.captured_building_credits = int.from_bytes(
                    resource_data[captured_index:captured_index + 4],
                    byteorder='little'
                )
                owned_building_index = OWNED_BUILDING_COUNT_OFFSET - resource_start
                self.owned_building_count = int.from_bytes(
                    resource_data[owned_building_index:owned_building_index + 4],
                    byteorder='little'
                )

            balance_ptr = self.real_class_base + BALANCEOFFSET
            balance_data = read_process_memory(self.process_handle, balance_ptr, 4)
            if balance_data:
                self.balance = int.from_bytes(balance_data, byteorder='little')

            winner_data = read_process_memory(self.process_handle, self.real_class_base + ISWINNEROFFSET, 1)
            if winner_data and len(winner_data) >= 1:
                self.is_winner = bool(winner_data[0])

            loser_data = read_process_memory(self.process_handle, self.real_class_base + ISLOSEROFFSET, 1)
            if loser_data and len(loser_data) >= 1:
                self.is_loser = bool(loser_data[0])

            defeated_flag_data = read_process_memory(self.process_handle, self.real_class_base + ISDEFEATEDFLAGOFFSET, 1)
            if defeated_flag_data and len(defeated_flag_data) >= 1:
                self.is_defeated_flag = bool(defeated_flag_data[0])

            post_game_trigger_data = read_process_memory(
                self.process_handle,
                self.real_class_base + POST_GAME_TRIGGER_WIN_OFFSET,
                2
            )
            if post_game_trigger_data and len(post_game_trigger_data) >= 2:
                win_trigger = bool(post_game_trigger_data[0])
                loss_trigger = bool(post_game_trigger_data[1])
                self.post_game_triggered = win_trigger or loss_trigger

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

            self.initialize_pointers()

            if self.infantry_array_ptr not in (None, 0):
                self.infantry_counts = self.read_and_store_inf_units_buildings(
                    infantry_offsets,
                    self.infantry_array_ptr,
                    self.infantry_array_capacity,
                    self.infantry_present_array_ptr,
                    self.infantry_present_array_capacity,
                    "infantry"
                )

            if self.unit_array_ptr not in (None, 0):
                self.tank_counts = self.read_and_store_inf_units_buildings(
                    tank_offsets,
                    self.unit_array_ptr,
                    self.unit_array_capacity,
                    self.unit_present_array_ptr,
                    self.unit_present_array_capacity,
                    "unit"
                )

            if self.building_array_ptr not in (None, 0):
                self.building_counts = self.read_and_store_inf_units_buildings(
                    structure_offsets,
                    self.building_array_ptr,
                    self.building_array_capacity,
                    self.building_present_array_ptr,
                    self.building_present_array_capacity,
                    "building"
                )

            if self.aircraft_array_ptr not in (None, 0):
                self.aircraft_counts = self.read_and_store_inf_units_buildings(
                    aircraft_offsets,
                    self.aircraft_array_ptr,
                    self.aircraft_array_capacity,
                    self.aircraft_present_array_ptr,
                    self.aircraft_present_array_capacity,
                    "aircraft"
                )

            self.built_infantry_counts = self.read_score_struct_counts(BUILT_INFANTRY_TOTAL_OFFSETS)
            self.built_tank_counts = self.read_score_struct_counts(BUILT_UNIT_TOTAL_OFFSETS)
            built_buildings = self.read_score_struct_counts(BUILT_BUILDING_TOTAL_OFFSETS)
            self.built_building_counts = built_buildings
            self.built_aircraft_counts = self.read_score_struct_counts(BUILT_AIRCRAFT_TOTAL_OFFSETS)

            self.lost_infantry_counts = self.read_score_struct_counts(LOST_INFANTRY_TOTAL_OFFSETS)
            self.lost_tank_counts = self.read_score_struct_counts(LOST_UNIT_TOTAL_OFFSETS)
            lost_buildings = self.read_score_struct_counts(LOST_BUILDING_TOTAL_OFFSETS)
            self.lost_building_counts = lost_buildings
            self.lost_aircraft_counts = self.read_score_struct_counts(LOST_AIRCRAFT_TOTAL_OFFSETS)
            self._log_tracked_count_mismatches()
            self.update_superweapon_timers()

            # Update factory production data and log each factory's update status.
            self.update_factories()

        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in update_dynamic_data for player {self.username.value}: {e}")
            traceback.print_exc()

    def update_superweapon_timers(self):
        try:
            results = {
                name: {"owned": False, "raw_value": SUPERCLASS_NOT_OWNED, "percent": 0}
                for name in self.superweapon_order
            }

            direct_header = read_process_memory(
                self.process_handle,
                self.real_class_base + HOUSE_SUPERS_ITEMS_PTR_OFFSET,
                8
            )
            items_ptr = 0
            super_count = 0
            if direct_header and len(direct_header) >= 8:
                items_ptr = int.from_bytes(direct_header[0:4], byteorder='little')
                super_count = int.from_bytes(direct_header[4:8], byteorder='little')

            if (
                items_ptr in (0, INVALIDCLASS)
                or super_count <= 0
                or super_count > len(self.superweapon_order)
            ):
                count_data = read_process_memory(
                    self.process_handle,
                    self.real_class_base + HOUSE_SUPERS_COUNT_OFFSET,
                    4
                )
                if count_data and len(count_data) >= 4:
                    super_count = int.from_bytes(count_data, byteorder='little')

            vector_size = max(
                SUPERS_DVC_ITEMS_PTR_OFFSET + 4,
                SUPERS_DVC_COUNT_OFFSET + 4,
                SUPERS_DVC_LEGACY_ITEMS_PTR_OFFSET + 4,
                SUPERS_DVC_LEGACY_COUNT_OFFSET + 4
            )
            vector_data = read_process_memory(
                self.process_handle,
                self.real_class_base + SUPERS_VECTOR_OFFSET,
                vector_size
            )
            if not vector_data or len(vector_data) < vector_size:
                return

            items_ptr = int.from_bytes(
                vector_data[SUPERS_DVC_ITEMS_PTR_OFFSET:SUPERS_DVC_ITEMS_PTR_OFFSET + 4],
                byteorder='little'
            )
            super_count = int.from_bytes(
                vector_data[SUPERS_DVC_COUNT_OFFSET:SUPERS_DVC_COUNT_OFFSET + 4],
                byteorder='little'
            )
            legacy_items_ptr = int.from_bytes(
                vector_data[SUPERS_DVC_LEGACY_ITEMS_PTR_OFFSET:SUPERS_DVC_LEGACY_ITEMS_PTR_OFFSET + 4],
                byteorder='little'
            )
            legacy_super_count = int.from_bytes(
                vector_data[SUPERS_DVC_LEGACY_COUNT_OFFSET:SUPERS_DVC_LEGACY_COUNT_OFFSET + 4],
                byteorder='little'
            )

            if (
                items_ptr in (0, INVALIDCLASS)
                or super_count <= 0
                or super_count > len(self.superweapon_order)
            ):
                items_ptr = legacy_items_ptr
                super_count = legacy_super_count

            if (
                items_ptr in (0, INVALIDCLASS)
                or super_count <= 0
                or super_count > len(self.superweapon_order)
            ):
                # The superweapon list is fixed-size in practice; use the full known order
                # if the count field is unreliable but the items array pointer is valid.
                if items_ptr not in (0, INVALIDCLASS):
                    super_count = len(self.superweapon_order)
                else:
                    self.superweapon_timers = results
                    return

            array_size = min(super_count, len(self.superweapon_order)) * 4
            pointer_data = read_process_memory(self.process_handle, items_ptr, array_size)
            if not pointer_data or len(pointer_data) < array_size:
                self.superweapon_timers = results
                return

            for index, name in enumerate(self.superweapon_order):
                if index * 4 + 4 > len(pointer_data):
                    break

                super_ptr = int.from_bytes(pointer_data[index * 4:index * 4 + 4], byteorder='little')
                if super_ptr in (0, INVALIDCLASS):
                    continue

                status_size = (SUPERCLASS_CHARGE_OFFSET - SUPERCLASS_OWNERSHIP_OFFSET) + 4
                status_data = read_process_memory(
                    self.process_handle,
                    super_ptr + SUPERCLASS_OWNERSHIP_OFFSET,
                    status_size
                )
                if not status_data or len(status_data) < status_size:
                    continue

                owned_value = status_data[0]
                if owned_value == 0:
                    continue

                ready_index = SUPERCLASS_READY_OFFSET - SUPERCLASS_OWNERSHIP_OFFSET
                is_ready = status_data[ready_index] != 0
                charge_index = SUPERCLASS_CHARGE_OFFSET - SUPERCLASS_OWNERSHIP_OFFSET
                raw_value = int.from_bytes(
                    status_data[charge_index:charge_index + 4],
                    byteorder='little'
                )
                if is_ready:
                    clamped_value = SUPERCLASS_READY_VALUE
                elif raw_value == SUPERCLASS_NOT_OWNED:
                    clamped_value = 0
                else:
                    clamped_value = max(0, min(raw_value, SUPERCLASS_READY_VALUE))
                percent = round((clamped_value / SUPERCLASS_READY_VALUE) * 100)
                results[name] = {
                    "owned": True,
                    "raw_value": clamped_value,
                    "percent": percent,
                }

            self.superweapon_timers = results
        except ProcessExitedException:
            raise
        except Exception as e:
            logging.error(f"Exception in update_superweapon_timers for player {self.username.value}: {e}")
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
