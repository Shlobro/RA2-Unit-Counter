import logging
import os
import shutil


PLAYER_COLOR_SOURCE_DIR = os.path.join("Other", "player colors")
PLAYER_COLOR_EXPORT_DIR = "player number colors"


def use_player_number_mode(hud_positions):
    return bool(hud_positions.get("use_player_numbers", False))


def get_player_number(player):
    return int(getattr(player, "display_slot", getattr(player, "index", 0) + 1))


def get_player_color_name(player):
    color_name = getattr(player, "color_name", "")
    if isinstance(color_name, str):
        return color_name
    return color_name.name()


def get_player_flag_export_stem(player, hud_positions):
    if use_player_number_mode(hud_positions):
        return f"Player {get_player_number(player)}"

    if hasattr(player, "get_normalized_color_name_for_file"):
        return player.get_normalized_color_name_for_file()
    return get_player_color_name(player)


def get_player_flag_legacy_stems(player, hud_positions):
    current_stem = get_player_flag_export_stem(player, hud_positions)
    candidate_stems = [f"Player {get_player_number(player)}"]

    if hasattr(player, "get_normalized_color_name_for_file"):
        candidate_stems.append(player.get_normalized_color_name_for_file())
    else:
        candidate_stems.append(get_player_color_name(player))

    return [stem for stem in candidate_stems if stem and stem != current_stem]


def get_player_display_label(player, hud_positions):
    if use_player_number_mode(hud_positions):
        return f"Player {get_player_number(player)}"
    return f"Player {get_player_color_name(player)}"


def get_combined_hud_title(player, hud_positions):
    if use_player_number_mode(hud_positions):
        return f"Player {get_player_number(player)} Combined HUD"
    return f"{get_player_color_name(player)} Combined HUD"


def get_player_bucket_key(player, hud_positions):
    if use_player_number_mode(hud_positions):
        return f"player_{get_player_number(player)}"
    return get_player_color_name(player)


def get_player_legacy_bucket_keys(player, hud_positions):
    alternate_key = (
        get_player_color_name(player)
        if use_player_number_mode(hud_positions)
        else f"player_{get_player_number(player)}"
    )
    return [alternate_key]


def _find_player_color_source_path(color_name):
    try:
        for entry in os.scandir(PLAYER_COLOR_SOURCE_DIR):
            if not entry.is_file():
                continue
            stem, ext = os.path.splitext(entry.name)
            if ext.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            if stem.lower() == color_name.lower():
                return entry.path
    except FileNotFoundError:
        logging.warning("Player color source folder not found: %s", PLAYER_COLOR_SOURCE_DIR)
        return None

    logging.warning("No player color image found for color '%s'", color_name)
    return None


def sync_player_color_exports(state):
    if not use_player_number_mode(state.hud_positions):
        state.player_color_export_cache = {}
        return

    os.makedirs(PLAYER_COLOR_EXPORT_DIR, exist_ok=True)
    current_cache = {}
    previous_cache = getattr(state, "player_color_export_cache", {})

    for player in state.players:
        player_number = get_player_number(player)
        color_name = get_player_color_name(player)
        source_path = _find_player_color_source_path(color_name)
        if not source_path:
            continue

        destination_path = os.path.join(
            PLAYER_COLOR_EXPORT_DIR,
            f"Player {player_number} Color.jpg",
        )
        cache_key = (color_name.lower(), source_path)
        current_cache[player_number] = cache_key

        if previous_cache.get(player_number) == cache_key and os.path.exists(destination_path):
            continue

        try:
            shutil.copyfile(source_path, destination_path)
        except Exception as exc:
            logging.exception(
                "Failed to export player color image for Player %s from %s: %s",
                player_number,
                source_path,
                exc,
            )

    state.player_color_export_cache = current_cache
