# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is RA2-Viewer, a Python application that provides a real-time HUD overlay for Command & Conquer: Red Alert 2. It reads game memory to display player resources, unit counts, and other game statistics in customizable overlay windows that stay on top of the game.

## Key Architecture

### Memory Reading System
- **memory_utils.py**: Windows-specific memory reading using ctypes and kernel32.dll
- **process_manager.py**: Handles game process detection and management
- **DataTracker.py**: Main resource window implementation with combined/separated HUD modes
- **Player.py**: Player data structure for storing game state (credits, power, units, etc.)

### Data Flow
1. **Main.py** initializes the Qt application and starts the data update thread
2. **data_update_thread.py** continuously reads memory from the game process
3. **hud_manager.py** manages HUD window creation, positioning, and updates
4. **app_state.py** maintains global application state including player data and settings

### Widget System
- **DataWidget.py**: Contains specialized widget classes (MoneyWidget, PowerWidget, NameWidget, etc.)
- **CounterWidget.py**: Handles unit counter displays with images and numbers
- **UnitWindow.py** & **UnitSelectionWindow.py**: Unit tracking interface components

### Configuration & Persistence
- **hud_positions.json**: Stores HUD window positions and visibility settings
- **unit_selection.json**: Stores selected units for tracking
- **constants.py**: Game-specific offsets, unit mappings, and faction definitions

## Common Development Commands

### Building Executable
```bash
# Build standalone executable using PyInstaller
make EXE.bat
# Or directly:
pyinstaller --onefile --windowed main.py
```

### Running the Application
```bash
python Main.py
```

## Memory Architecture Details

The application uses Windows process memory reading to extract real-time game data:

- **Base Process Detection**: Finds gamemd.exe or ra2md.exe processes
- **Memory Offsets**: Defined in constants.py for different game data (credits, power, unit counts)
- **Player Data Structure**: Each player has offsets for resources, units, country, color scheme
- **Unit Tracking**: Separate offset arrays for infantry, tanks, aircraft, and buildings

## HUD System

### Display Modes
- **Combined Mode**: All widgets in a single movable window per player
- **Separated Mode**: Individual movable windows for each widget type (money, power, name, etc.)

### Widget Types
- Money display with player color or white text options
- Power display with bolt icon (red when negative, green when positive)
- Player name with faction flag
- Unit counters with cameo images
- Money spent tracking

## File Structure Notes

- **cameos/**: Contains unit/building images for the UI
- **Flags/**: Country flag images for player identification  
- **icons/**: UI element images (bolt, money, lock icons)
- **oil counts/**: Text files storing oil derrick counts per player color

## Error Handling

The application includes comprehensive error handling for:
- Game process termination (ProcessExitedException in exceptions.py)
- Memory read failures with detailed error codes
- Qt window management issues
- File I/O operations for settings persistence

## Logging

Structured logging is configured in logging_config.py with file rotation and appropriate log levels for debugging memory operations and UI updates.