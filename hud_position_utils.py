DEFAULT_HUD_POSITION = {"x": 100, "y": 100}


def _coerce_coordinate(value, fallback):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return fallback


def normalize_position(value, default=None):
    fallback = dict(default or DEFAULT_HUD_POSITION)

    if isinstance(value, dict):
        x = _coerce_coordinate(value.get("x"), fallback["x"])
        y = _coerce_coordinate(value.get("y"), fallback["y"])
        return {"x": x, "y": y}

    if isinstance(value, (list, tuple)) and len(value) >= 2:
        x = _coerce_coordinate(value[0], fallback["x"])
        y = _coerce_coordinate(value[1], fallback["y"])
        return {"x": x, "y": y}

    return fallback


def ensure_player_bucket(hud_positions, player_color):
    bucket = hud_positions.get(player_color)
    if not isinstance(bucket, dict):
        bucket = {}
        hud_positions[player_color] = bucket
    return bucket


def get_player_position(hud_positions, player_color, hud_type, legacy_root_keys=None, default=None):
    bucket = ensure_player_bucket(hud_positions, player_color)
    fallback = dict(default or DEFAULT_HUD_POSITION)
    legacy_root_keys = legacy_root_keys or []

    for key in [hud_type]:
        if key in bucket:
            bucket[hud_type] = normalize_position(bucket[key], fallback)
            return bucket[hud_type]

    for key in legacy_root_keys:
        if key in bucket:
            bucket[hud_type] = normalize_position(bucket[key], fallback)
            return bucket[hud_type]

    for key in [hud_type] + legacy_root_keys:
        if key in hud_positions:
            bucket[hud_type] = normalize_position(hud_positions[key], fallback)
            return bucket[hud_type]

    bucket[hud_type] = fallback
    return bucket[hud_type]


def normalize_hud_positions(hud_positions):
    if not isinstance(hud_positions, dict):
        return {}

    for key in ("factory", "superweapons", "superweapon"):
        if key in hud_positions:
            hud_positions[key] = normalize_position(hud_positions[key])

    for value in hud_positions.values():
        if not isinstance(value, dict):
            continue

        for key in ("factory", "superweapons", "superweapon", "combined", "unit_counter_combined"):
            if key in value:
                value[key] = normalize_position(value[key])

    return hud_positions
