import ctypes
import struct
from ctypes import wintypes

import psutil


PROCESS_ALL_ACCESS = 0x1F0FFF
INVALID = 0xFFFFFFFF
MAX_PLAYERS = 8

PLAYER_TABLE = 0xA8B230
CLASS_ARRAY = 0xA8022C
HOUSE_STRIDE = 1120 * 4

TANK_COUNTER = 0x5568
PRESENT_COUNTER_DELTA = 0x64
VEHICLE_FACTORY = 0x53B4
QUEUED_ITEMS = 0x44
QUEUED_COUNT = 0x50
CURRENT_TECHNO = 0x58
TECHNO_TYPE_FROM_UNIT = 0x6C4
TYPE_NAME_OFFSET = 0x64


kernel32 = ctypes.windll.kernel32
kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.ReadProcessMemory.restype = wintypes.BOOL


def read(handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    count = ctypes.c_size_t()
    if not kernel32.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(count)):
        return None
    return buffer.raw[:count.value]


def u32(handle, address):
    data = read(handle, address, 4)
    return struct.unpack("<I", data)[0] if data and len(data) == 4 else None


def ascii_at(handle, address, limit=80):
    data = read(handle, address, limit)
    if not data:
        return None
    raw = data.split(b"\0", 1)[0]
    if not raw or any(value < 32 or value > 126 for value in raw):
        return None
    return raw.decode("ascii", errors="replace")


def type_name(handle, type_pointer):
    if type_pointer in (None, 0, INVALID):
        return None
    return ascii_at(handle, type_pointer + TYPE_NAME_OFFSET)


def techno_name(handle, techno_pointer):
    if techno_pointer in (None, 0, INVALID):
        return None
    return type_name(handle, u32(handle, techno_pointer + TECHNO_TYPE_FROM_UNIT))


def player_bases(handle):
    fixed = u32(handle, PLAYER_TABLE)
    class_array = u32(handle, CLASS_ARRAY)
    for slot in range(MAX_PLAYERS):
        class_index = u32(handle, fixed + HOUSE_STRIDE + slot * 4)
        if class_index in (None, INVALID):
            continue
        base = u32(handle, class_array + class_index * 4)
        if base not in (None, 0, INVALID):
            yield slot + 1, base


def dump_counter(handle, house, label, header_offset):
    items = u32(handle, house + header_offset)
    capacity = u32(handle, house + header_offset + 4)
    print(f"  {label}: ptr=0x{(items or 0):08X} capacity={capacity}")
    if items in (None, 0, INVALID) or not capacity or capacity > 4096:
        return
    values = read(handle, items, capacity * 4)
    if not values or len(values) != capacity * 4:
        return
    for index in range(capacity):
        value = struct.unpack_from("<I", values, index * 4)[0]
        if value:
            marker = "  <== candidate" if value == 10 else ""
            print(f"    index={index:3d} offset=0x{index * 4:03X} value={value}{marker}")


def dump_vehicle_factory(handle, house):
    factory = u32(handle, house + VEHICLE_FACTORY)
    if factory in (None, 0, INVALID):
        print("  Vehicle factory: idle")
        return
    queued_ptr = u32(handle, factory + QUEUED_ITEMS)
    queued_count = u32(handle, factory + QUEUED_COUNT)
    current = techno_name(handle, u32(handle, factory + CURRENT_TECHNO))
    print(
        f"  Vehicle factory: ptr=0x{factory:08X} current={current!r} "
        f"queue_ptr=0x{(queued_ptr or 0):08X} queue_count={queued_count}"
    )
    if queued_ptr in (None, 0, INVALID) or not queued_count or queued_count > 100:
        return
    for index in range(queued_count):
        pointer = u32(handle, queued_ptr + index * 4)
        print(f"    queue[{index}] type=0x{(pointer or 0):08X} name={type_name(handle, pointer)!r}")


def dump_score_slots(handle, house):
    for label, offset in (("built", 0x13AC), ("lost", 0x33CC)):
        print(f"  Tesla Tank {label} score slot +0x{offset:X}: {u32(handle, house + offset)}")


def main():
    pid = next(
        (process.info["pid"] for process in psutil.process_iter(["pid", "name"])
         if (process.info["name"] or "").lower() == "gamemd-spawn.exe"),
        None,
    )
    if pid is None:
        raise SystemExit("gamemd-spawn.exe is not running")
    handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not handle:
        raise SystemExit("OpenProcess failed")
    try:
        print(f"PID {pid}")
        for slot, house in player_bases(handle):
            print(f"PLAYER {slot}: house=0x{house:08X}")
            dump_counter(handle, house, "OwnedUnitTypes", TANK_COUNTER)
            dump_counter(handle, house, "OwnedUnitTypes1/present", TANK_COUNTER + PRESENT_COUNTER_DELTA)
            dump_vehicle_factory(handle, house)
            dump_score_slots(handle, house)
    finally:
        kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
