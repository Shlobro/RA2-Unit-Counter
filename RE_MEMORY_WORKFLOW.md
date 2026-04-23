# RE Memory Workflow

This project reads live `gamemd-spawn.exe` memory on Windows. The notes below document the exact workflow that worked in this repository and the issues encountered while finding the live map-name address.

## What Worked

The core game-memory access already existed in the repo:

- `memory_utils.py` uses `ctypes.windll.kernel32.ReadProcessMemory`
- `process_manager.py` opens the game process with `OpenProcess`
- `Player.py` and related modules already read known offsets from that process handle

For new values that are not already mapped in the repo, the effective workflow was:

1. Confirm the game process is running with PowerShell:
   ```powershell
   Get-Process gamemd-spawn
   ```
2. Use a small helper script to scan the live process memory for a known string.
3. Read candidate addresses directly to verify the value.
4. Re-check after changing maps to confirm the address updates in place.
5. Only then wire the address into the application update loop.

## Python / Sandbox Issues We Hit

The first attempts to run inline Python failed even though Python was present on the machine.

Problems encountered:

- `python` resolved to a Windows Store path and failed with access errors.
- `py -3` also routed through the blocked WindowsApps interpreter when used inside the sandbox.
- Opening the live game process from the sandbox failed, even when the script itself was correct.

Symptoms looked like:

- `Access is denied` when trying to launch Python via the Windows Store path
- `OpenProcess failed` when trying to inspect the live game process from the sandbox

What fixed it:

- Use the user-provided direct interpreter path:
  `C:\Users\Shlomo\AppData\Local\Programs\Python\Python313\python.exe`
- Request elevated execution permission when the task needs unsandboxed access to the live game process

This matters because there are two separate failure modes:

- Python launch problems
- process-access problems

Fixing only one of them is not enough.

## Practical Pattern For Live Memory Scans

When a new address needs to be discovered:

1. Write a small standalone script in the repo.
2. Run it with the direct Python path.
3. If it needs live process access and sandboxed execution fails, rerun it with permission.

Example command shape:

```powershell
& 'C:\Users\Shlomo\AppData\Local\Programs\Python\Python313\python.exe' .\scan_map_string.py 18920 'Yellow Snow Gardens'
```

## Map Name Discovery Example

We searched for the current map name as a UTF-16LE string in the running process.

Confirmed result:

- process: `gamemd-spawn.exe`
- module: `gamemd-spawn.exe`
- module-relative address: `+0x68B322`
- absolute address in the tested sessions: `0x00A8B322`
- encoding: UTF-16LE

Verified values:

- `[8] Desert Island (4v4)`
- `[8] Yellow Snow Gardens`

After cross-checking on a different live map, the same address updated correctly, which is why it was considered safe enough to integrate.

## Why Cross-Checking Matters

A string found once in memory may only be:

- a heap copy
- a UI cache
- a transient buffer from the current screen

The first scan found multiple copies of the map string. The safer candidate was the one inside the main module image, not the likely heap copy.

We then changed maps and reread the same address. That confirmed the address was live and not just a stale copy.

## Current Helper Scripts

These helper scripts were created during this investigation:

- `scan_map_string.py`
- `inspect_map_address.py`
- `read_process_string.py`

They are useful for future offset discovery and validation.

## Implementation Notes

The app currently reads the map name from:

- absolute address `0x00A8B322`

This corresponds to:

- `gamemd-spawn.exe + 0x68B322`

If game builds diverge later, prefer computing the module base dynamically and adding the relative offset instead of assuming the absolute address remains fixed.
