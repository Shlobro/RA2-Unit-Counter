import ctypes
import sys
from ctypes import wintypes


PROCESS_ALL_ACCESS = 0x1F0FFF
LIST_MODULES_ALL = 0x03
MAX_PATH = 260


class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", ctypes.c_void_p),
        ("SizeOfImage", wintypes.DWORD),
        ("EntryPoint", ctypes.c_void_p),
    ]


def read_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    success = ctypes.windll.kernel32.ReadProcessMemory(
        process_handle,
        ctypes.c_void_p(address),
        buffer,
        size,
        ctypes.byref(bytes_read),
    )
    if not success:
        raise OSError(ctypes.windll.kernel32.GetLastError())
    return buffer.raw[: bytes_read.value]


def enum_modules(process_handle):
    psapi = ctypes.windll.psapi
    needed = wintypes.DWORD()
    module_array = (ctypes.c_void_p * 1024)()
    if not psapi.EnumProcessModulesEx(
        process_handle,
        ctypes.byref(module_array),
        ctypes.sizeof(module_array),
        ctypes.byref(needed),
        LIST_MODULES_ALL,
    ):
        raise OSError(ctypes.windll.kernel32.GetLastError())

    module_count = needed.value // ctypes.sizeof(ctypes.c_void_p)
    modules = []
    for index in range(module_count):
        module = ctypes.c_void_p(module_array[index])
        path_buffer = ctypes.create_unicode_buffer(MAX_PATH)
        psapi.GetModuleFileNameExW(process_handle, module, path_buffer, MAX_PATH)
        info = MODULEINFO()
        psapi.GetModuleInformation(
            process_handle,
            module,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        modules.append(
            {
                "base": info.lpBaseOfDll or 0,
                "end": (info.lpBaseOfDll or 0) + info.SizeOfImage,
                "size": info.SizeOfImage,
                "path": path_buffer.value,
            }
        )
    return modules


def main():
    pid = int(sys.argv[1])
    address = int(sys.argv[2], 0)
    size = int(sys.argv[3], 0) if len(sys.argv) > 3 else 96

    kernel32 = ctypes.windll.kernel32
    process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not process_handle:
        raise SystemExit(f"OpenProcess failed: {kernel32.GetLastError()}")

    try:
        modules = enum_modules(process_handle)
        print(f"address=0x{address:08X}")
        for module in modules:
            if module["base"] <= address < module["end"]:
                print(
                    "module="
                    f"{module['path']} base=0x{module['base']:08X} "
                    f"end=0x{module['end']:08X} size=0x{module['size']:X}"
                )
                print(f"module_offset=0x{address - module['base']:X}")
                break
        data = read_memory(process_handle, address, size)
        print("raw_hex=", data.hex(" "))
        try:
            print("utf16=", data.decode("utf-16le", errors="ignore").split("\x00")[0])
        except Exception as exc:
            print("utf16_error=", exc)
    finally:
        kernel32.CloseHandle(process_handle)


if __name__ == "__main__":
    main()
