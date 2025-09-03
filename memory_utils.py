# memory_utils.py
import ctypes
import logging
from exceptions import ProcessExitedException

def read_process_memory(process_handle, address, size):
    buffer = ctypes.create_string_buffer(size)
    bytesRead = ctypes.c_size_t()
    try:
        success = ctypes.windll.kernel32.ReadProcessMemory(
            process_handle, address, buffer, size, ctypes.byref(bytesRead)
        )
        if success:
            return buffer.raw
        else:
            error_code = ctypes.windll.kernel32.GetLastError()
            if error_code == 299:  # ERROR_PARTIAL_COPY
                logging.warning("Memory read incomplete. Game might still be loading.")
                return None
            elif error_code in (5, 6):  # ERROR_ACCESS_DENIED or ERROR_INVALID_HANDLE
                logging.error("Failed to read memory: Process might have exited.")
                raise ProcessExitedException("Process has exited.")
            else:
                logging.error(f"Failed to read memory: Error code {error_code}")
                raise ProcessExitedException("Process has exited.")
    except Exception as e:
        logging.error(f"Exception in read_process_memory: {e}")
        raise ProcessExitedException("Process has exited.")
