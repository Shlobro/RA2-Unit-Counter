import ctypes
import sys


PROCESS_ALL_ACCESS = 0x1F0FFF


def main():
    pid = int(sys.argv[1])
    address = int(sys.argv[2], 0)
    size = int(sys.argv[3], 0) if len(sys.argv) > 3 else 128
    encoding = sys.argv[4] if len(sys.argv) > 4 else "utf-16le"

    kernel32 = ctypes.windll.kernel32
    process_handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not process_handle:
        raise SystemExit(f"OpenProcess failed: {kernel32.GetLastError()}")

    try:
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()
        success = kernel32.ReadProcessMemory(
            process_handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read),
        )
        if not success:
            raise SystemExit(f"ReadProcessMemory failed: {kernel32.GetLastError()}")

        data = buffer.raw[: bytes_read.value]
        print("raw_hex=", data.hex(" "))
        text = data.decode(encoding, errors="ignore").split("\x00")[0]
        print("text=", text)
    finally:
        kernel32.CloseHandle(process_handle)


if __name__ == "__main__":
    main()
