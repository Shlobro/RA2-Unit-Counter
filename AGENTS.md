# Repository Guidelines

## Project Structure & Module Organization
`Main.py` is the desktop entry point for this Windows-only PySide6 application. Core runtime logic lives in top-level modules such as `hud_manager.py`, `data_update_thread.py`, `app_state.py`, `memory_utils.py`, and `process_manager.py`. UI widgets and windows are also kept at the repository root, for example `control_panel.py`, `DataWidget.py`, `CounterWidget.py`, `UnitWindow.py`, and the `factory_*` modules. Static assets live in `cameos/`, `Flags/`, `icons/`, and `Other/`. Generated artifacts belong in `build/`, `dist/`, logs, and `__pycache__/`; avoid mixing new source files into those directories.

## Build, Test, and Development Commands
Run locally with `python Main.py` or `run.bat`. Build a packaged executable with `pyinstaller Main.spec` or `make EXE.bat`. `Main.spec` is the canonical packaging config; keep it aligned with any new runtime assets or hidden imports. There is no dedicated bootstrap command in the repo, so install Python dependencies manually before running.

## Coding Style & Naming Conventions
Follow the existing codebase style: 4-space indentation, module-level constants in `UPPER_SNAKE_CASE`, functions and variables in `snake_case`, and Qt widget classes in `PascalCase`. Preserve the current filename conventions even where they are not pure PEP 8, such as `Main.py`, `Player.py`, and `DataWidget.py`. Keep modules focused; new UI behavior should usually extend an existing widget or manager module instead of introducing another orchestration layer.

## Testing Guidelines
This repository currently has no automated test suite. For behavior changes, verify manually by launching `python Main.py`, attaching to a running RA2/YR process, and exercising the affected HUD or factory window flow. When adding logic that can be isolated from the game process, prefer small pure functions so future unit tests can target them. Document manual verification steps in the PR.

## Commit & Pull Request Guidelines
Recent commits use short, imperative subjects such as `Fixed Yuri Slave miners` and `added new colors`. Keep commit messages concise, specific, and focused on one change. Pull requests should include a short summary, manual test notes, linked issues when applicable, and screenshots or recordings for UI changes.

## Configuration & Data Files
Treat `hud_positions.json`, `unit_selection.json`, and files under `oil counts/` as user or local state. Do not commit machine-specific edits unless the change intentionally updates shared defaults.
