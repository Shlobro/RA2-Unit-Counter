import json
import logging
import os

from constants import (
    DISPLAY_IMAGE_ALIASES,
    SLAVE_MINER_CANONICAL_NAME,
    canonicalize_unit_name,
    names,
)


UNIT_SELECTION_FILE = 'unit_selection.json'
LEGACY_SLAVE_MINER_NAMES = {
    'Slave miner',
    'Slave miner undeployed',
    'Slave Miner Deployed',
    'Yuri Ore Refinery',
}


def _empty_payload():
    return {'selected_units': {}}


def _build_current_unit_lookup():
    lookup = {}
    for faction, unit_types in names.items():
        faction_lookup = lookup.setdefault(faction, {})
        for unit_type, unit_names in unit_types.items():
            faction_lookup[unit_type] = set(unit_names)
    return lookup


CURRENT_UNIT_NAMES = _build_current_unit_lookup()


def _extract_selected_units(raw_data):
    if not isinstance(raw_data, dict):
        return {}, True
    if isinstance(raw_data.get('selected_units'), dict):
        return raw_data['selected_units'], False
    return raw_data, True


def _normalize_position(value):
    if isinstance(value, bool):
        return -1
    try:
        position = int(value)
    except (TypeError, ValueError):
        return -1
    return position if position >= 0 else -1


def _normalize_unit_info(unit_info, faction, unit_type):
    if isinstance(unit_info, bool):
        return {
            'selected': unit_info,
            'locked': False,
            'position': -1,
            'faction': faction,
            'unit_type': unit_type,
        }, True

    if not isinstance(unit_info, dict):
        unit_info = {}
        changed = True
    else:
        unit_info = dict(unit_info)
        changed = False

    normalized = {
        'selected': bool(unit_info.get('selected', False)),
        'locked': bool(unit_info.get('locked', False)),
        'position': _normalize_position(unit_info.get('position', -1)),
        'faction': faction,
        'unit_type': unit_type,
    }
    changed = changed or normalized != unit_info
    return normalized, changed


def _resolve_unit_bucket_and_name(faction, unit_type, unit_name):
    if unit_name in LEGACY_SLAVE_MINER_NAMES:
        return 'Yuri', 'Tank', SLAVE_MINER_CANONICAL_NAME

    canonical_name = canonicalize_unit_name(unit_name)
    if canonical_name in CURRENT_UNIT_NAMES.get(faction, {}).get(unit_type, set()):
        return faction, unit_type, canonical_name

    alias_name = DISPLAY_IMAGE_ALIASES.get(canonical_name, canonical_name)
    if alias_name in CURRENT_UNIT_NAMES.get(faction, {}).get(unit_type, set()):
        return faction, unit_type, alias_name

    return faction, unit_type, unit_name


def _merge_unit_info(existing_info, incoming_info):
    if existing_info is None:
        return dict(incoming_info), True

    merged = dict(existing_info)
    merged['selected'] = existing_info.get('selected', False) or incoming_info.get('selected', False)
    merged['locked'] = existing_info.get('locked', False) or incoming_info.get('locked', False)

    existing_position = existing_info.get('position', -1)
    incoming_position = incoming_info.get('position', -1)
    if existing_position == -1:
        merged['position'] = incoming_position
    elif incoming_position == -1:
        merged['position'] = existing_position
    else:
        merged['position'] = min(existing_position, incoming_position)

    merged['faction'] = incoming_info.get('faction', existing_info.get('faction'))
    merged['unit_type'] = incoming_info.get('unit_type', existing_info.get('unit_type'))
    return merged, merged != existing_info


def enforce_global_selected_unit_positions(selected_units):
    selected_entries = []
    for faction, unit_types in selected_units.items():
        if not isinstance(unit_types, dict):
            continue
        for unit_type, units in unit_types.items():
            if not isinstance(units, dict):
                continue
            for unit_name, unit_info in units.items():
                if not isinstance(unit_info, dict):
                    continue
                if unit_info.get('selected', False):
                    selected_entries.append((faction, unit_type, unit_name, unit_info))

    used_positions = set()
    deferred_entries = []
    changed = False

    for _, _, _, unit_info in selected_entries:
        position = _normalize_position(unit_info.get('position', -1))
        if position != unit_info.get('position', -1):
            unit_info['position'] = position
            changed = True
        if position == -1 or position in used_positions:
            deferred_entries.append(unit_info)
            continue
        used_positions.add(position)

    next_available = 0
    for unit_info in deferred_entries:
        while next_available in used_positions:
            next_available += 1
        if unit_info.get('position', -1) != next_available:
            unit_info['position'] = next_available
            changed = True
        used_positions.add(next_available)
        next_available += 1

    return changed


def normalize_selected_units_payload(raw_data):
    selected_units_data, root_changed = _extract_selected_units(raw_data)
    normalized_payload = _empty_payload()
    changed = root_changed

    if not isinstance(selected_units_data, dict):
        return normalized_payload, True

    for faction, unit_types in selected_units_data.items():
        if not isinstance(unit_types, dict):
            changed = True
            continue
        for unit_type, units in unit_types.items():
            if not isinstance(units, dict):
                changed = True
                continue
            for unit_name, unit_info in units.items():
                target_faction, target_unit_type, target_unit_name = _resolve_unit_bucket_and_name(
                    faction,
                    unit_type,
                    unit_name,
                )
                normalized_info, info_changed = _normalize_unit_info(unit_info, target_faction, target_unit_type)
                changed = changed or info_changed
                if (target_faction, target_unit_type, target_unit_name) != (faction, unit_type, unit_name):
                    changed = True

                target_units = normalized_payload['selected_units'].setdefault(target_faction, {}).setdefault(
                    target_unit_type,
                    {},
                )
                merged_info, merged_changed = _merge_unit_info(target_units.get(target_unit_name), normalized_info)
                target_units[target_unit_name] = merged_info
                changed = changed or merged_changed

    changed = enforce_global_selected_unit_positions(normalized_payload['selected_units']) or changed
    return normalized_payload, changed


def load_selected_units_file(json_file=UNIT_SELECTION_FILE):
    if not os.path.exists(json_file):
        return _empty_payload(), False

    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            raw_data = json.load(file)
    except Exception as exc:
        logging.exception("Failed to load selected units from %s: %s", json_file, exc)
        return _empty_payload(), False

    return normalize_selected_units_payload(raw_data)


def save_selected_units_file(selected_units_data, json_file=UNIT_SELECTION_FILE):
    normalized_payload, _ = normalize_selected_units_payload(selected_units_data)
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(normalized_payload, file, indent=4)
    return normalized_payload
