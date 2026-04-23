import ctypes
import sys
from ctypes import wintypes


PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01
READABLE_PROTECTIONS = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


def iter_hits(process_handle):
    targets = build_targets()
    kernel32 = ctypes.windll.kernel32
    mbi = MEMORY_BASIC_INFORMATION()
    address = 0
    max_address = 0x7FFFFFFF

    while address < max_address:
        result = kernel32.VirtualQueryEx(
            process_handle,
            ctypes.c_void_p(address),
            ctypes.byref(mbi),
            ctypes.sizeof(mbi),
        )
        if not result:
            address += 0x1000
            continue

        base = mbi.BaseAddress or 0
        size = mbi.RegionSize
        protection = mbi.Protect & 0xFF
        if (
            mbi.State == MEM_COMMIT
            and not (mbi.Protect & PAGE_GUARD)
            and protection not in (0, PAGE_NOACCESS)
            and protection in READABLE_PROTECTIONS
        ):
            buffer = ctypes.create_string_buffer(size)
            bytes_read = ctypes.c_size_t()
            if kernel32.ReadProcessMemory(
                process_handle,
                ctypes.c_void_p(base),
                buffer,
                size,
                ctypes.byref(bytes_read),
            ):
                data = buffer.raw[: bytes_read.value]
                for label, needle in targets:
                    start = 0
                    while True:
                        index = data.find(needle, start)
                        if index == -1:
                            break
                        yield base + index, label
                        start = index + 1

        if not size:
            address += 0x1000
            continue

        address = base + size


def build_targets():
    if len(sys.argv) > 2:
        search_text = " ".join(sys.argv[2:])
    else:
        search_text = "[8] Desert Island (4v4)"
    short_text = search_text
    if search_text.startswith("[") and "] " in search_text:
        short_text = search_text.split("] ", 1)[1]
    return [
        ("ascii_full", search_text.encode("ascii", errors="ignore")),
        ("ascii_short", short_text.encode("ascii", errors="ignore")),
        ("utf16_full", search_text.encode("utf-16le")),
        ("utf16_short", short_text.encode("utf-16le")),
    ]


def main():
    pid = int(sys.argv[1]) if len(sys.argv) > 1 else 11328
    kernel32 = ctypes.windll.kernel32
    process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not process_handle:
        raise SystemExit(f"OpenProcess failed: {kernel32.GetLastError()}")

    try:
        hits = list(iter_hits(process_handle))
    finally:
        kernel32.CloseHandle(process_handle)

    for hit_address, label in hits[:200]:
        print(hex(hit_address), label)
    print("total_hits", len(hits))


if __name__ == "__main__":
    main()
