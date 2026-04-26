# RA2 Unit Counter

<p align="center">
  <img src="Screenshot%202026-03-08%20003925.png" alt="RA2 Unit Counter screenshot" width="100%" />
</p>

<p align="center">
  <strong>A slick Windows HUD companion for Red Alert 2 / Yuri's Revenge.</strong><br />
  Live unit counts, money, power, game-time/map widgets, factory production, superweapon timers, and a post-game scoreboard for <code>gamemd-spawn.exe</code>.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows-1f6feb?style=for-the-badge" alt="Windows" />
  <img src="https://img.shields.io/badge/UI-PySide6-0f766e?style=for-the-badge" alt="PySide6" />
  <img src="https://img.shields.io/badge/runtime-Python-111827?style=for-the-badge" alt="Python" />
</p>

## What It Does

RA2 Unit Counter attaches to a running Yuri's Revenge / RA2 session, reads live game state from memory, and renders draggable HUD windows for each player.

- Track selected unit counts in real time
- Show player name, flag, money, money spent, power, game time, and map name
- Watch live factory production and queue order
- Display superweapon timers
- Switch between separate windows and a combined HUD layout
- Customize widget fonts, colors, and optional background rectangles for readability
- Save window positions and UI settings between sessions
- Show a styled post-game scoreboard with timeline, graphs, and player breakdown views

## Features

### Modular HUDs

You can run the app in either of these modes:

- `Separate HUD`: resource widgets, unit counters, and factory windows stay independent
- `Combined HUD`: each player gets one compact stacked panel

The control panel lets you resize widgets, swap vertical/horizontal layouts, toggle frames, and choose which units appear.
For the regular Widgets tab items, you can also enable a per-widget background rectangle, choose its color, and set its width and height.

### Widget Coverage

The HUD can show:

- Unit counters
- Player name and flag
- Money and money spent
- Power status
- Game time
- Current map name
- Factory queues
- Superweapon panels

### Styling Controls

Most HUD widgets can be styled from the control panel:

- Change font family per widget
- Choose custom text colors
- Keep default/player-color behavior where applicable
- Add optional solid background rectangles with custom color and size

### Post-Game Scoreboard

When a match ends, the app can open a full post-game scoreboard with:

- A match timeline view
- Per-player breakdown cards
- Graph tabs for score, economy, army, and other tracked metrics
- Inline per-unit graph filtering
- Match event tracking for superweapon use/build progress, radar tech, battle lab tech, special units, and MCV loss
- Saved scoreboard management from the Scoreboard tab

### Built for Live Matches

The app looks for `gamemd-spawn.exe`, waits for players to load, then keeps updating the overlay while the match is running. It also reads `spawn.ini` from your selected game folder, which is why the game path must point to the folder containing that file.

### Persistence

Local state is stored in:

- `hud_positions.json`
- `unit_selection.json`
- `oil counts/`

That means your HUD layout survives restarts instead of needing to be rebuilt every game.

## Requirements

- Windows
- Python 3
- A working RA2 / Yuri's Revenge installation or launcher setup that uses `gamemd-spawn.exe`
- Python packages installed manually, since this repo does not currently ship a `requirements.txt`

At minimum, the codebase expects:

- `PySide6`
- `psutil`
- `pyinstaller` for packaging

## Run It

```powershell
python Main.py
```

Or:

```powershell
run.bat
```

When the app opens:

1. Set the game folder in the control panel.
2. Point it at the directory that contains `spawn.ini`.
3. Launch or join a game.
4. Drag the HUD windows where you want them.
5. If text is hard to read over the map, enable widget backgrounds from the `Widgets` tab.

For reliable overlay behavior:

- Run the app as Administrator
- Use borderless-windowed RA2/YR instead of exclusive fullscreen

## Build An EXE

Canonical spec build:

```powershell
pyinstaller Main.spec
```

Batch helper:

```powershell
make EXE.bat
```

## Project Layout

Core runtime lives at the repo root:

- `Main.py` boots the app
- `hud_manager.py` creates, updates, saves, and restores HUD windows
- `data_update_thread.py` drives live refresh
- `process_manager.py`, `memory_utils.py`, and `Player.py` handle game detection and memory reads
- `control_panel.py` is the main configuration surface
- `factory_*`, `superweapon_*`, `DataWidget.py`, `CounterWidget.py`, and `UnitWindow.py` implement the UI pieces
- `scoreboard_window.py` renders the post-game results screen

Assets live in:

- `cameos/`
- `Flags/`
- `icons/`
- `Other/`

## Manual Testing

There is no automated test suite in this repository yet. The intended verification flow is manual:

1. Start the app with `python Main.py`.
2. Select a valid game folder.
3. Attach to a running match.
4. Verify unit counters, money widgets, factories, superweapons, and scoreboard behavior.

## Notes For Contributors

- Keep new source files at the repo root unless they are clearly assets
- Preserve existing filename conventions like `Main.py`, `Player.py`, and `DataWidget.py`
- Avoid committing accidental edits to local state files unless shared defaults are intentionally changing

---

<p align="center">
  <strong>For spectators who want more signal and less guesswork.</strong>
</p>
