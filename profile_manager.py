import json
import os
import re
import shutil


PROFILES_DIR = "profiles"
PROFILE_INDEX_FILE = os.path.join(PROFILES_DIR, "profiles.json")
DEFAULT_PROFILE = "Default"


def _safe_directory_name(name):
    value = re.sub(r"[^A-Za-z0-9._ -]+", "_", str(name)).strip(" .")
    return value or "Profile"


def _read_index():
    if os.path.exists(PROFILE_INDEX_FILE):
        try:
            with open(PROFILE_INDEX_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
            profiles = data.get("profiles", [])
            if profiles:
                return data
        except (OSError, ValueError, TypeError):
            pass
    return {"active": DEFAULT_PROFILE, "profiles": [DEFAULT_PROFILE]}


def _write_index(data):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    with open(PROFILE_INDEX_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def profile_directory(name):
    return os.path.join(PROFILES_DIR, _safe_directory_name(name))


def profile_paths(name):
    folder = profile_directory(name)
    return (
        os.path.join(folder, "hud_positions.json"),
        os.path.join(folder, "unit_selection.json"),
    )


def initialize_profiles():
    """Create the registry and migrate legacy settings into Default once."""
    first_run = not os.path.exists(PROFILE_INDEX_FILE)
    data = _read_index()
    os.makedirs(PROFILES_DIR, exist_ok=True)
    if first_run and DEFAULT_PROFILE in data["profiles"]:
        default_hud, default_units = profile_paths(DEFAULT_PROFILE)
        os.makedirs(os.path.dirname(default_hud), exist_ok=True)
        for legacy, destination in (
            ("hud_positions.json", default_hud),
            ("unit_selection.json", default_units),
        ):
            if not os.path.exists(destination) and os.path.exists(legacy):
                shutil.copy2(legacy, destination)
    _write_index(data)
    return data


def list_profiles():
    return list(initialize_profiles()["profiles"])


def active_profile():
    data = initialize_profiles()
    active = data.get("active", DEFAULT_PROFILE)
    return active if active in data["profiles"] else data["profiles"][0]


def activate_profile(name):
    data = initialize_profiles()
    if name not in data["profiles"]:
        raise ValueError(f"Unknown profile: {name}")
    data["active"] = name
    _write_index(data)


def create_profile(name, copy_from=None):
    name = str(name).strip()
    if not name:
        raise ValueError("Profile name cannot be empty.")
    data = initialize_profiles()
    if name.casefold() in {item.casefold() for item in data["profiles"]}:
        raise ValueError("A profile with that name already exists.")
    destination = profile_directory(name)
    os.makedirs(destination, exist_ok=False)
    if copy_from:
        source_hud, source_units = profile_paths(copy_from)
        target_hud, target_units = profile_paths(name)
        for source, target in ((source_hud, target_hud), (source_units, target_units)):
            if os.path.exists(source):
                shutil.copy2(source, target)
    data["profiles"].append(name)
    data["active"] = name
    _write_index(data)
    return name


def rename_profile(old_name, new_name):
    new_name = str(new_name).strip()
    if not new_name:
        raise ValueError("Profile name cannot be empty.")
    data = initialize_profiles()
    if old_name not in data["profiles"]:
        raise ValueError("Profile does not exist.")
    if new_name.casefold() in {item.casefold() for item in data["profiles"] if item != old_name}:
        raise ValueError("A profile with that name already exists.")
    old_dir = profile_directory(old_name)
    new_dir = profile_directory(new_name)
    if os.path.abspath(old_dir) != os.path.abspath(new_dir):
        if os.path.exists(new_dir):
            raise ValueError("A profile folder with that name already exists.")
        os.rename(old_dir, new_dir)
    index = data["profiles"].index(old_name)
    data["profiles"][index] = new_name
    if data.get("active") == old_name:
        data["active"] = new_name
    _write_index(data)
    return new_name


def delete_profile(name):
    data = initialize_profiles()
    if name not in data["profiles"]:
        raise ValueError("Profile does not exist.")
    if len(data["profiles"]) == 1:
        raise ValueError("The last profile cannot be deleted.")
    shutil.rmtree(profile_directory(name), ignore_errors=True)
    data["profiles"].remove(name)
    if data.get("active") == name:
        data["active"] = data["profiles"][0]
    _write_index(data)
    return data["active"]


def configure_state_profile(state, name=None):
    name = name or active_profile()
    hud_file, unit_file = profile_paths(name)
    os.makedirs(os.path.dirname(hud_file), exist_ok=True)
    state.active_profile = name
    state.HUD_POSITION_FILE = hud_file
    state.UNIT_SELECTION_FILE = unit_file
