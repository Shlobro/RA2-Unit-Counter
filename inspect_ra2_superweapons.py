import ctypes
import struct
import sys
from ctypes import wintypes

import psutil


PROCESS_ALL_ACCESS = 0x1F0FFF
INVALID = 0xFFFFFFFF
MAX_PLAYERS = 8


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


def find_pid():
    for process in psutil.process_iter(["pid", "name"]):
        if (process.info["name"] or "").lower() == "gamemd-spawn.exe":
            return process.info["pid"]
    raise SystemExit("gamemd-spawn.exe is not running")


def player_bases(handle):
    fixed = u32(handle, 0xA8B230)
    class_array = u32(handle, 0xA8022C)
    if fixed is None or class_array is None:
        raise SystemExit("Could not read the game's player tables")
    for slot in range(MAX_PLAYERS):
        class_index = u32(handle, fixed + 1120 * 4 + slot * 4)
        if class_index in (None, INVALID):
            continue
        base = u32(handle, class_array + class_index * 4)
        if base not in (None, 0, INVALID):
            yield slot + 1, base


def plausible_super(handle, pointer):
    if pointer in (None, 0, INVALID) or pointer < 0x10000:
        return None
    data = read(handle, pointer, 0x90)
    if not data or len(data) < 0x7C:
        return None
    owned = data[0x6D]
    ready = data[0x6F]
    charge = struct.unpack_from("<I", data, 0x78)[0]
    if owned in (0, 1) and ready in (0, 1) and (charge <= 1000000 or charge == INVALID):
        return owned, ready, charge
    return None


def ascii_at(handle, pointer, limit=80):
    if pointer in (None, 0, INVALID) or pointer < 0x10000:
        return None
    data = read(handle, pointer, limit)
    if not data:
        return None
    value = data.split(b"\0", 1)[0]
    if len(value) < 3 or any(byte < 32 or byte > 126 for byte in value):
        return None
    return value.decode("ascii", errors="replace")


def pointer_strings(handle, pointer):
    data = read(handle, pointer, 0x90)
    found = []
    if not data:
        return found
    for offset in range(0, len(data) - 3, 4):
        candidate = struct.unpack_from("<I", data, offset)[0]
        direct = ascii_at(handle, candidate)
        if direct:
            found.append((offset, candidate, direct))
        nested_data = read(handle, candidate, 0x40) if candidate not in (0, INVALID) else None
        if nested_data:
            for nested_offset in range(0, len(nested_data) - 3, 4):
                nested_pointer = struct.unpack_from("<I", nested_data, nested_offset)[0]
                nested = ascii_at(handle, nested_pointer)
                if nested and ("Special" in nested or "Chrono" in nested or "Para" in nested):
                    found.append((offset, candidate, f"+0x{nested_offset:X} -> {nested}"))
    return found


def inspect_building_factories(handle, house):
    for label, factory_offset in (("Buildings", 0x53BC), ("Defenses", 0x53CC)):
        factory = u32(handle, house + factory_offset)
        if factory in (None, 0, INVALID):
            print(f"  {label.upper()} FACTORY: idle")
            continue
        progress = u32(handle, factory + 0x24)
        techno = u32(handle, factory + 0x58)
        print(
            f"  {label.upper()} FACTORY +0x{factory_offset:X}: "
            f"FactoryClass=0x{factory:08X} raw_progress={progress} "
            f"TechnoClass=0x{(techno or 0):08X}"
        )
        if techno in (None, 0, INVALID):
            continue
        for offset in range(0, 0x1000, 4):
            type_pointer = u32(handle, techno + offset)
            name = ascii_at(handle, type_pointer + 0x64 if type_pointer else 0, 45)
            if name and any(token in name.lower() for token in ("pill", "prism", "spy", "tesla", "chrono", "iron", "weather", "missile")):
                print(f"    TechnoClass +0x{offset:03X} -> 0x{type_pointer:08X} name={name!r}")


def inspect_vector(handle, house, offset):
    raw = read(handle, house + offset, 0x18)
    if not raw or len(raw) != 0x18:
        return []
    words = struct.unpack("<6I", raw)
    candidates = []
    for ptr_index in range(5):
        pointer = words[ptr_index]
        for count_index in range(6):
            count = words[count_index]
            if pointer in (0, INVALID) or not 1 <= count <= 32:
                continue
            entries = read(handle, pointer, count * 4)
            if not entries or len(entries) != count * 4:
                continue
            statuses = []
            valid = 0
            for index in range(count):
                item = struct.unpack_from("<I", entries, index * 4)[0]
                status = plausible_super(handle, item)
                statuses.append((item, status))
                valid += status is not None
            if valid:
                candidates.append((words, ptr_index, count_index, statuses, valid))
    return candidates


def main():
    pid = find_pid()
    handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not handle:
        raise ctypes.WinError()
    print(f"PID {pid}")
    try:
        for slot, house in player_bases(handle):
            print(f"\nPLAYER {slot} HouseClass=0x{house:08X}")
            inspect_building_factories(handle, house)
            header = read(handle, house + 0x220, 0x90)
            if header:
                for rel in range(0, len(header), 16):
                    vals = struct.unpack_from("<4I", header, rel)
                    print(f"  +0x{0x220 + rel:03X}: " + " ".join(f"{v:08X}" for v in vals))
            seen = set()
            for offset in range(0x220, 0x2C1, 4):
                for words, pi, ci, statuses, valid in inspect_vector(handle, house, offset):
                    key = (words[pi], words[ci], tuple(item for item, _ in statuses))
                    if key in seen:
                        continue
                    seen.add(key)
                    print(f"  VECTOR +0x{offset:03X} word[{pi}]=ptr word[{ci}]=count; valid={valid}/{len(statuses)}")
                    for index, (item, status) in enumerate(statuses):
                        print(f"    [{index:02}] 0x{item:08X} status={status}")
                        if status and status[0]:
                            for field_offset, field_pointer, value in pointer_strings(handle, item):
                                print(f"         +0x{field_offset:02X} -> 0x{field_pointer:08X}: {value}")
    finally:
        kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
