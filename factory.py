import logging
import ctypes

from exceptions import ProcessExitedException
from memory_utils import read_process_memory

from constants import (
    UNITNAMEOFFSET,
    PERCENTAGECOMPLETEOFFSET,
    QUEUEDUNITSAMOUNT,
    QUEUEDUNITSPTROFFSET,
    TECHNOCLASS_TO_TECHNOTYPE_INFANTRY_OFFSET,
    TECHNOCLASS_TO_TECHNOTYPE_UNIT_OFFSET,
    TECHNOCLASS_TO_TECHNOTYPE_BUILDINGS_OFFSET
)


class Factory:
    """
    Base Factory class with shared logic for reading memory
    (pointer, percentage, technoClass pointer).
    """

    def __init__(self, process_handle, realClassBase, factory_name):
        self.process_handle = process_handle
        self.realClassBase = realClassBase
        self.factory_name = factory_name
        self.currently_building_name = ""
        self.percentage_val = 0

    def get_unit_name_from_techno_type(self, techno_type_ptr):
        """
        Safely read up to 45 bytes of the name from techno_type_ptr + UNITNAMEOFFSET.
        Raises ProcessExitedException if read fails entirely.
        Returns the unit name or "" if pointer is zero.
        """
        if techno_type_ptr == 0:
            logging.error(f"Techno type pointer is zero for {self.factory_name}")
            return ""
        string_address = techno_type_ptr + UNITNAMEOFFSET

        data = read_process_memory(self.process_handle, string_address, 45)
        if data is None:
            logging.error(f"Failed to read unit name data at {string_address:#x} for {self.factory_name}")
            # Raise an exception so we stop reading further invalid pointers
            raise ProcessExitedException("Techno type read failed - game likely closed or memory invalid.")

        # Truncate at the first null terminator
        name_str = data.split(b'\x00')[0].decode('utf-8', errors='replace')
        return name_str

    def get_unit_name_from_techno_class(self, techno_class_ptr, techno_offset):
        """
        From a technoClass pointer + offset -> read the technoType pointer -> read the unit name.
        Raises ProcessExitedException if read fails.
        Returns "" if techno_class_ptr or techno_type_ptr is zero.
        """
        if techno_class_ptr == 0:
            logging.error(f"Techno class pointer is zero for {self.factory_name}")
            return ""
        techno_type_ptr_address = techno_class_ptr + techno_offset

        data = read_process_memory(self.process_handle, techno_type_ptr_address, 4)
        if data is None:
            logging.error(f"Failed to read technoType pointer at {techno_type_ptr_address:#x} for {self.factory_name}")
            raise ProcessExitedException("Techno type pointer read failed - memory invalid.")

        techno_type_ptr = ctypes.c_uint32.from_buffer_copy(data).value
        if techno_type_ptr == 0:
            logging.error(f"Techno type pointer is zero for {self.factory_name} (offset {techno_type_ptr_address:#x})")
            return ""

        return self.get_unit_name_from_techno_type(techno_type_ptr)

    def read_common_factory_data(self, factory_offset):
        """
        Reads the base factory pointer + percentage + technoClass pointer.
        - If we can't read the factory pointer, raise ProcessExitedException to stop further reads.
        - If the pointer is zero, we return producing=False.
        - If we can't read percentage or technoClass, return an error but not necessarily raise.
        """
        factory_ptr_address = self.realClassBase + factory_offset
        factory_ptr_data = read_process_memory(self.process_handle, factory_ptr_address, 4)
        if factory_ptr_data is None:
            error_msg = f"Failed to read factory pointer for {self.factory_name} at offset {factory_offset:#x}"
            logging.error(error_msg)
            # Immediately raise the exception so the calling code stops all further reads
            raise ProcessExitedException("Factory pointer read failed — game likely closed or memory invalid.")

        factory_ptr = ctypes.c_uint32.from_buffer_copy(factory_ptr_data).value
        if factory_ptr == 0:
            info_msg = f"Factory pointer is zero for {self.factory_name} at offset {factory_offset:#x}"
            logging.Logger(info_msg)
            return {"error": False, "error_msg": info_msg, "producing": False}

        # Read the "percentage complete"
        pct_address = factory_ptr + PERCENTAGECOMPLETEOFFSET
        pct_data = read_process_memory(self.process_handle, pct_address, 4)
        if pct_data is None:
            msg = (f"Failed to read percentage complete for {self.factory_name} "
                   f"at factory pointer {factory_ptr:#x}")
            logging.error(msg)
            # Return an error dict, which might cause the calling code to skip this read
            return {"error": True, "error_msg": msg, "producing": False}

        raw_pct = ctypes.c_uint32.from_buffer_copy(pct_data).value
        percentage = (100.0 / 54.0) * raw_pct

        # Read the technoClass pointer at offset 0x58
        techno_class_ptr_address = factory_ptr + 0x58
        techno_class_data = read_process_memory(self.process_handle, techno_class_ptr_address, 4)
        if techno_class_data is None:
            msg = (f"Failed to read technoClass pointer for {self.factory_name} "
                   f"at factory pointer {factory_ptr:#x}")
            logging.error(msg)
            return {"error": True, "error_msg": msg, "producing": False}

        techno_class_ptr = ctypes.c_uint32.from_buffer_copy(techno_class_data).value

        return {
            "error": False,
            "error_msg": "",
            "producing": True,
            "factory_ptr": factory_ptr,
            "percentage": percentage,
            "techno_class_ptr": techno_class_ptr
        }


class QueuedFactory(Factory):
    """
    For factories that can queue multiple units (Infantry, Aircraft, Vehicles, Ships).
    """

    def __init__(self, process_handle, realClassBase, factory_name):
        super().__init__(process_handle, realClassBase, factory_name)
        self.queued_units_list = []
        self.queued_units_amount = 0

    def process_factory(self, factory_offset):
        """
        Returns a dict (the "status" of the factory):
          {
            "error": bool,
            "error_msg": str,
            "producing": bool,
            "status": "active"|"idle",
            "currently_building": str,
            "percentage": float,
            "queued_units": list[str],
          }
        If error or not producing, "queued_units" might be missing or empty.
        """
        # 1) Common data
        common_data = self.read_common_factory_data(factory_offset)
        if common_data["error"] or not common_data["producing"]:
            # Return as-is if reading pointer/percentage/technoClass fails
            return common_data

        self.percentage_val = common_data["percentage"]
        factory_ptr = common_data["factory_ptr"]

        # 2) Read queued units amount
        queued_units_address = factory_ptr + QUEUEDUNITSAMOUNT
        data_queued_amt = read_process_memory(self.process_handle, queued_units_address, 4)
        if data_queued_amt is None:
            msg = (f"Failed to read queued units amount for {self.factory_name} "
                   f"@ factory ptr {factory_ptr:#x}")
            logging.error(msg)
            # Instead of raising an exception here, we return an error so the calling code sees "producing=False"
            return {"error": True, "error_msg": msg, "producing": False}

        self.queued_units_amount = ctypes.c_uint32.from_buffer_copy(data_queued_amt).value

        # 3) Check if idle (no progress, no queued units)
        if (self.percentage_val == 0) and (self.queued_units_amount == 0):
            msg = f"{self.factory_name} is idle (0% progress, 0 queued)."
            logging.info(msg)
            return {
                "error": False, "error_msg": msg,
                "producing": False, "status": "idle"
            }

        # 4) Determine offset for reading the unit name
        if self.factory_name == "Infantry":
            techno_offset = TECHNOCLASS_TO_TECHNOTYPE_INFANTRY_OFFSET
        elif self.factory_name in ("Aircraft", "Vehicles", "Ships"):
            techno_offset = TECHNOCLASS_TO_TECHNOTYPE_UNIT_OFFSET
        else:
            msg = f"Invalid factory name for queued factory: {self.factory_name}"
            logging.error(msg)
            return {"error": True, "error_msg": msg, "producing": False}

        # 5) Read currently building
        self.currently_building_name = self.get_unit_name_from_techno_class(
            common_data["techno_class_ptr"], techno_offset
        )
        if not self.currently_building_name:
            msg = f"Failed to read currently building unit name for {self.factory_name}"
            logging.error(msg)
            return {"error": True, "error_msg": msg, "producing": False}

        # 6) Read the pointer to the queued units array
        queued_units_ptr_address = factory_ptr + QUEUEDUNITSPTROFFSET
        data_qptr = read_process_memory(self.process_handle, queued_units_ptr_address, 4)
        if data_qptr is None:
            msg = f"Failed to read queued units pointer for {self.factory_name}"
            logging.error(msg)
            return {"error": True, "error_msg": msg, "producing": False}

        queued_units_ptr = ctypes.c_uint32.from_buffer_copy(data_qptr).value
        if queued_units_ptr == 0:
            # Possibly the game doesn't store a pointer if there's no queue
            logging.warning(f"Queued units pointer is zero for {self.factory_name}.")
            self.queued_units_list = []
        else:
            # 7) Read each queued unit
            self.queued_units_list = []
            for j in range(self.queued_units_amount):
                address_next = queued_units_ptr + j * 4
                data_next = read_process_memory(self.process_handle, address_next, 4)
                if data_next is None:
                    logging.warning(
                        f"Failed to read queued unit #{j} pointer for {self.factory_name}."
                    )
                    self.queued_units_list.append(None)
                    continue
                next_unit_ptr = ctypes.c_uint32.from_buffer_copy(data_next).value
                next_unit_name = self.get_unit_name_from_techno_type(next_unit_ptr)
                self.queued_units_list.append(next_unit_name)

        # 8) Return success
        return {
            "error": False,
            "error_msg": "",
            "producing": True,
            "status": "active",
            "currently_building": self.currently_building_name,
            "percentage": self.percentage_val,
            "queued_units": self.queued_units_list
        }


class BuildingFactory(Factory):
    """
    For factories that build structures (no multi-queue).
    """

    def __init__(self, process_handle, realClassBase, factory_name):
        super().__init__(process_handle, realClassBase, factory_name)

    def process_factory(self, factory_offset):
        """
        For building factories, we just check:
          - is it producing? read the building name
          - or is it idle?
        Returns a dict:
          {
            "error": bool,
            "error_msg": str,
            "producing": bool,
            "status": "active"|"idle",
            "currently_building": str,
            "percentage": float
          }
        """
        common_data = self.read_common_factory_data(factory_offset)
        if common_data["error"] or not common_data["producing"]:
            return common_data  # error or producing=False => just return

        self.percentage_val = common_data["percentage"]
        if self.percentage_val == 0:
            msg = f"{self.factory_name} is idle (0% progress)."
            logging.info(msg)
            return {
                "error": False, "error_msg": msg,
                "producing": False, "status": "idle"
            }

        # For building factories, we use the buildings offset
        building_name = self.get_unit_name_from_techno_class(
            common_data["techno_class_ptr"],
            TECHNOCLASS_TO_TECHNOTYPE_BUILDINGS_OFFSET
        )
        if not building_name:
            msg = f"Failed to read currently building unit name for {self.factory_name}"
            logging.error(msg)
            return {"error": True, "error_msg": msg, "producing": False}
        self.currently_building_name = building_name

        return {
            "error": False,
            "error_msg": "",
            "producing": True,
            "status": "active",
            "currently_building": self.currently_building_name,
            "percentage": self.percentage_val
        }
