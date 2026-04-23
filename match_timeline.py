import json
import logging
import os
import tempfile
import time
from datetime import datetime

from constants import _existing_asset_paths, SUPERCLASS_READY_VALUE
from scoreboard_window import build_post_game_snapshot


CORE_METRIC_ORDER = [
    "income_total",
    "cash",
    "money_spent_total",
    "infantry_built",
    "vehicles_built",
    "navy_built",
    "buildings_built",
    "aircraft_built",
    "units_current_total",
    "units_lost_total",
    "infantry_current",
    "miners_current",
    "vehicles_current",
    "navy_current",
    "buildings_current",
    "aircraft_current",
    "infantry_lost",
    "vehicles_lost",
    "navy_lost",
    "buildings_lost",
    "aircraft_lost",
]

MINIMUM_MATCH_DURATION_MS = 5_000
NAVAL_UNIT_NAMES = {
    "Aegis Cruiser",
    "Aircraft Carrier",
    "Armored Transport",
    "Destroyer",
    "Dolphin",
    "Dreadnought",
    "Giant Squid",
    "Hover Transport Yuri",
    "Landing Craft",
    "Sea Scorpion",
    "Typhoon Attack Sub",
    "Yuri Boomer",
}
MINER_UNIT_NAMES = {
    "War Miner",
    "Chrono Miner",
    "Slave miner",
    "Slave Miner",
    "Slave miner undeployed",
    "Slave Miner Deployed",
}
COUNTRY_TO_FLAG = {
    "British": "RA2_Flag_Britain.png",
    "Confederation": "RA2_Flag_Cuba.png",
    "Germans": "RA2_Flag_Germany.png",
    "Arabs": "RA2_Flag_Iraq.png",
    "French": "RA2_Flag_France.png",
    "Alliance": "RA2_Flag_Korea.png",
    "Africans": "RA2_Flag_Libya.png",
    "Russians": "RA2_Flag_Russia.png",
    "Americans": "RA2_Flag_USA.png",
    "YuriCountry": "RA2_Yuricountry.png",
}
FACTION_TO_FLAG = {
    "Allied": "RA2_Flag_USA.png",
    "Soviet": "RA2_Flag_Russia.png",
    "Yuri": "RA2_Yuricountry.png",
}


def _now_iso():
    return datetime.now().isoformat(timespec="seconds")


def _player_id(player):
    return str(player.index)


def _sum_counts(counts):
    return int(sum(counts.values()))


def _sum_matching_counts(counts, unit_names, include_matches=True):
    total = 0
    for unit_name, count in counts.items():
        is_match = unit_name in unit_names
        if is_match == include_matches:
            total += count
    return int(total)


def _normalize_country_name(country_name):
    return (country_name or "").split("\x00", 1)[0].strip()


def _resolve_flag_asset(country_name, faction_name):
    normalized_country_name = _normalize_country_name(country_name)
    flag_name = COUNTRY_TO_FLAG.get(normalized_country_name)
    if not flag_name:
        flag_name = FACTION_TO_FLAG.get((faction_name or "").strip())
    if not flag_name:
        flag_name = "RA2_Yuricountry.png"

    for candidate in _existing_asset_paths("Flags", "PNG", flag_name):
        return flag_name, candidate
    return flag_name, None


def _build_player_metadata(player):
    color_name = player.color_name if isinstance(player.color_name, str) else player.color_name.name()
    accent_color = player.color.name() if hasattr(player.color, "name") else str(player.color)
    country_name = _normalize_country_name(player.country_name.value.decode("utf-8", errors="ignore"))
    flag_asset_name, flag_asset_path = _resolve_flag_asset(country_name, player.faction)
    return {
        "player_id": _player_id(player),
        "index": player.index,
        "display_slot": getattr(player, "display_slot", player.index),
        "username": player.username.value or f"Player {player.index}",
        "faction": player.faction,
        "country": country_name,
        "color_name": color_name,
        "accent_color": accent_color,
        "flag_file_stem": getattr(player, "post_game_flag_file_stem", ""),
        "flag_asset_name": flag_asset_name,
        "flag_asset_path": flag_asset_path,
        "owned_building_count": int(getattr(player, "owned_building_count", 0)),
    }


def _derive_player_loss_metrics(players):
    if len(players) != 2:
        return {
            _player_id(player): {
                "infantry_lost": _sum_counts(player.lost_infantry_counts),
                "vehicles_lost": _sum_matching_counts(player.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=False),
                "navy_lost": _sum_matching_counts(player.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=True),
                "buildings_lost": _sum_counts(player.lost_building_counts),
                "aircraft_lost": max(_sum_counts(player.lost_aircraft_counts), max(0, _sum_counts(player.built_aircraft_counts) - _sum_counts(player.aircraft_counts))),
            }
            for player in players
        }

    player_a, player_b = players
    return {
        _player_id(player_a): {
            "infantry_lost": _sum_counts(player_b.lost_infantry_counts),
            "vehicles_lost": _sum_matching_counts(player_b.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=False),
            "navy_lost": _sum_matching_counts(player_b.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=True),
            "buildings_lost": _sum_counts(player_b.lost_building_counts),
            "aircraft_lost": max(
                _sum_counts(player_b.lost_aircraft_counts),
                max(0, _sum_counts(player_a.built_aircraft_counts) - _sum_counts(player_a.aircraft_counts)),
            ),
        },
        _player_id(player_b): {
            "infantry_lost": _sum_counts(player_a.lost_infantry_counts),
            "vehicles_lost": _sum_matching_counts(player_a.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=False),
            "navy_lost": _sum_matching_counts(player_a.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=True),
            "buildings_lost": _sum_counts(player_a.lost_building_counts),
            "aircraft_lost": max(
                _sum_counts(player_a.lost_aircraft_counts),
                max(0, _sum_counts(player_b.built_aircraft_counts) - _sum_counts(player_b.aircraft_counts)),
            ),
        },
    }


def _compute_player_metrics(player, player_meta, derived_loss_metrics):
    infantry_built = _sum_counts(player.built_infantry_counts)
    miners_built = _sum_matching_counts(player.built_tank_counts, MINER_UNIT_NAMES, include_matches=True)
    vehicles_built = _sum_matching_counts(player.built_tank_counts, NAVAL_UNIT_NAMES, include_matches=False)
    vehicles_built = max(0, vehicles_built - miners_built)
    navy_built = _sum_matching_counts(player.built_tank_counts, NAVAL_UNIT_NAMES, include_matches=True)
    buildings_built = _sum_counts(player.built_building_counts)
    aircraft_built = _sum_counts(player.built_aircraft_counts)
    infantry_current = _sum_counts(player.infantry_counts)
    miners_current = _sum_matching_counts(player.tank_counts, MINER_UNIT_NAMES, include_matches=True)
    vehicles_current = _sum_matching_counts(player.tank_counts, NAVAL_UNIT_NAMES, include_matches=False)
    vehicles_current = max(0, vehicles_current - miners_current)
    navy_current = _sum_matching_counts(player.tank_counts, NAVAL_UNIT_NAMES, include_matches=True)
    buildings_current = _sum_counts(player.building_counts)
    aircraft_current = _sum_counts(player.aircraft_counts)

    player_id = _player_id(player)
    loss_metrics = derived_loss_metrics.get(
        player_id,
        {
            "infantry_lost": _sum_counts(player.lost_infantry_counts),
            "vehicles_lost": _sum_matching_counts(player.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=False),
            "navy_lost": _sum_matching_counts(player.lost_tank_counts, NAVAL_UNIT_NAMES, include_matches=True),
            "buildings_lost": _sum_counts(player.lost_building_counts),
            "aircraft_lost": _sum_counts(player.lost_aircraft_counts),
        },
    )
    infantry_lost = loss_metrics["infantry_lost"]
    vehicles_lost = loss_metrics["vehicles_lost"]
    navy_lost = loss_metrics.get("navy_lost", 0)
    buildings_lost = loss_metrics["buildings_lost"]
    aircraft_lost = loss_metrics["aircraft_lost"]

    starting_balance = int(player_meta.get("starting_balance", player.balance))
    starting_spent = int(player_meta.get("starting_spent", player.spent_credit))
    income_total = max(0, int(player.spent_credit - starting_spent + player.balance - starting_balance))

    return {
        "income_total": income_total,
        "cash": int(player.balance),
        "money_spent_total": int(player.spent_credit),
        "infantry_built": infantry_built,
        "vehicles_built": vehicles_built,
        "navy_built": navy_built,
        "buildings_built": buildings_built,
        "aircraft_built": aircraft_built,
        "units_current_total": infantry_current + miners_current + vehicles_current + navy_current + buildings_current + aircraft_current,
        "units_lost_total": infantry_lost + vehicles_lost + navy_lost + buildings_lost + aircraft_lost,
        "infantry_current": infantry_current,
        "miners_current": miners_current,
        "vehicles_current": vehicles_current,
        "navy_current": navy_current,
        "buildings_current": buildings_current,
        "aircraft_current": aircraft_current,
        "infantry_lost": infantry_lost,
        "vehicles_lost": vehicles_lost,
        "navy_lost": navy_lost,
        "buildings_lost": buildings_lost,
        "aircraft_lost": aircraft_lost,
    }


def _record_named_count_series(target_bucket, elapsed_ms, counts):
    active_names = set()
    for unit_name, count in counts.items():
        active_names.add(unit_name)
        target_bucket.setdefault(unit_name, []).append({"t_ms": elapsed_ms, "value": int(count)})

    for unit_name, points in target_bucket.items():
        if unit_name in active_names:
            continue
        last_value = int(points[-1]["value"]) if points else 0
        points.append({"t_ms": elapsed_ms, "value": last_value})


def _split_built_tank_counts(counts):
    vehicle_counts = {}
    navy_counts = {}
    for unit_name, count in counts.items():
        if unit_name in NAVAL_UNIT_NAMES:
            navy_counts[unit_name] = count
        elif unit_name not in MINER_UNIT_NAMES:
            vehicle_counts[unit_name] = count
    return vehicle_counts, navy_counts


def _record_unit_series_sample(unit_series, elapsed_ms, player):
    vehicle_counts, navy_counts = _split_built_tank_counts(player.built_tank_counts)
    category_counts = {
        "infantry_built": player.built_infantry_counts,
        "vehicles_built": vehicle_counts,
        "navy_built": navy_counts,
        "buildings_built": player.built_building_counts,
        "aircraft_built": player.built_aircraft_counts,
    }

    for metric_id, counts in category_counts.items():
        target_bucket = unit_series.setdefault(metric_id, {})
        _record_named_count_series(target_bucket, elapsed_ms, counts)


def _record_superweapon_events(player_meta, elapsed_ms, player):
    event_state = player_meta.setdefault("_superweapon_event_state", {})
    superweapon_events = player_meta.setdefault("events", {}).setdefault("superweapons", [])

    for name in player.superweapon_order:
        timer_info = player.superweapon_timers.get(name) or {}
        owned = bool(timer_info.get("owned"))
        raw_value = int(timer_info.get("raw_value", 0) or 0)
        raw_value = max(0, min(raw_value, SUPERCLASS_READY_VALUE))

        state = event_state.setdefault(
            name,
            {
                "prev_owned": False,
                "prev_raw_value": 0,
                "pending_reset": None,
            },
        )

        pending_reset = state.get("pending_reset")
        if pending_reset is not None:
            pending_raw_value = int(pending_reset.get("raw_value", 0))
            if owned and raw_value > pending_raw_value and raw_value < SUPERCLASS_READY_VALUE:
                superweapon_events.append(
                    {
                        "type": "superweapon_used",
                        "superweapon_name": name,
                        "t_ms": int(pending_reset.get("t_ms", elapsed_ms)),
                    }
                )
                pending_reset = None
            elif not owned or raw_value >= SUPERCLASS_READY_VALUE:
                pending_reset = None

        prev_owned = bool(state.get("prev_owned"))
        prev_raw_value = int(state.get("prev_raw_value", 0))
        if (
            prev_owned
            and owned
            and prev_raw_value >= SUPERCLASS_READY_VALUE - 1
            and raw_value <= max(10, SUPERCLASS_READY_VALUE // 3)
            and raw_value < prev_raw_value
        ):
            pending_reset = {"t_ms": elapsed_ms, "raw_value": raw_value}

        state["prev_owned"] = owned
        state["prev_raw_value"] = raw_value
        state["pending_reset"] = pending_reset


def _export_player_timeline_meta(player_meta):
    exported_meta = dict(player_meta)
    exported_meta.pop("_superweapon_event_state", None)
    exported_meta["events"] = {
        "superweapons": list(((player_meta.get("events") or {}).get("superweapons") or [])),
    }
    return exported_meta


def start_match_timeline(state):
    if not state.players:
        return None

    started_at = _now_iso()
    timeline = {
        "schema_version": 1,
        "match_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "started_at": started_at,
        "ended_at": None,
        "duration_ms": 0,
        "sample_interval_ms": int(state.hud_positions.get("data_update_frequency", 1000)),
        "players": {},
        "series": {},
        "_start_perf": time.perf_counter(),
        "_finalized": False,
        "_last_sample_ms": None,
        "_saved_path": None,
    }

    for player in state.players:
        player_id = _player_id(player)
        timeline["players"][player_id] = _build_player_metadata(player)
        timeline["series"][player_id] = {metric_id: [] for metric_id in CORE_METRIC_ORDER}
        timeline["players"][player_id]["unit_series"] = {}
        timeline["players"][player_id]["events"] = {"superweapons": []}
        timeline["players"][player_id]["_superweapon_event_state"] = {}

    state.current_match_timeline = timeline
    state.completed_match_path = None
    record_match_timeline_sample(state)
    logging.info("Started match timeline %s", timeline["match_id"])
    return timeline


def record_match_timeline_sample(state):
    timeline = getattr(state, "current_match_timeline", None)
    if not timeline or timeline.get("_finalized"):
        return
    if not state.players:
        return

    elapsed_ms = max(0, int((time.perf_counter() - timeline["_start_perf"]) * 1000))
    if timeline.get("_last_sample_ms") == elapsed_ms:
        return

    derived_loss_metrics = _derive_player_loss_metrics(state.players)
    for player in state.players:
        player_id = _player_id(player)
        player_meta = timeline["players"].get(player_id, _build_player_metadata(player))
        if "starting_balance" not in player_meta:
            player_meta["starting_balance"] = int(player.balance)
        if "starting_spent" not in player_meta:
            player_meta["starting_spent"] = int(player.spent_credit)
        country_name = _normalize_country_name(player.country_name.value.decode("utf-8", errors="ignore"))
        flag_asset_name, flag_asset_path = _resolve_flag_asset(country_name, player.faction)
        timeline["players"][player_id] = {
            **player_meta,
            "username": player.username.value or f"Player {player.index}",
            "faction": player.faction,
            "country": country_name,
            "flag_file_stem": getattr(player, "post_game_flag_file_stem", timeline["players"].get(player_id, {}).get("flag_file_stem", "")),
            "flag_asset_name": flag_asset_name,
            "flag_asset_path": flag_asset_path,
            "owned_building_count": int(getattr(player, "owned_building_count", 0)),
        }
        series = timeline["series"].setdefault(
            player_id,
            {metric_id: [] for metric_id in CORE_METRIC_ORDER},
        )
        unit_series = timeline["players"][player_id].setdefault("unit_series", {})
        metrics = _compute_player_metrics(player, timeline["players"][player_id], derived_loss_metrics)
        player.derived_income_total = metrics["income_total"]
        for metric_id, value in metrics.items():
            series.setdefault(metric_id, []).append({"t_ms": elapsed_ms, "value": int(value)})
        _record_unit_series_sample(unit_series, elapsed_ms, player)
        _record_superweapon_events(timeline["players"][player_id], elapsed_ms, player)

    timeline["_last_sample_ms"] = elapsed_ms


def _build_completed_payload(state):
    timeline = state.current_match_timeline
    losing_player_ids = {_player_id(player) for player in state.players if player.has_lost_game()}
    players = []
    for player in state.players:
        player_id = _player_id(player)
        player_meta = _export_player_timeline_meta(timeline["players"].get(player_id, _build_player_metadata(player)))
        player_meta.update(
            {
                "result": "DEFEATED" if player_id in losing_player_ids else "WINNER" if losing_player_ids else "WINNER" if player.is_winner else "DEFEATED" if player.is_loser else "ACTIVE",
                "is_winner": bool(player_id not in losing_player_ids and losing_player_ids) or bool(player.is_winner),
                "is_loser": bool(player_id in losing_player_ids) or bool(player.is_loser),
                "owned_building_count": int(getattr(player, "owned_building_count", 0)),
                "series": timeline["series"].get(player_id, {}),
            }
        )
        players.append(player_meta)

    winner_names = [player["username"] for player in players if player["is_winner"]]
    timeline_payload = {
        "schema_version": timeline["schema_version"],
        "match_id": timeline["match_id"],
        "started_at": timeline["started_at"],
        "ended_at": timeline["ended_at"],
        "duration_ms": timeline["duration_ms"],
        "sample_interval_ms": timeline["sample_interval_ms"],
        "winner_names": winner_names,
        "players": players,
    }
    return {
        **timeline_payload,
        "summary": build_post_game_snapshot(state.players, state.hud_positions),
        "timeline": timeline_payload,
    }


def _prune_saved_scoreboards(history_dir, limit):
    if limit is None or int(limit) < 0:
        return set()

    json_paths = [
        os.path.join(history_dir, entry)
        for entry in os.listdir(history_dir)
        if entry.lower().endswith(".json")
    ]
    json_paths.sort(key=os.path.getmtime, reverse=True)
    removed_paths = set()
    for stale_path in json_paths[int(limit):]:
        try:
            os.remove(stale_path)
            removed_paths.add(stale_path)
        except OSError:
            logging.exception("Failed to remove old scoreboard %s", stale_path)
    return removed_paths


def _save_payload(payload, history_dir):
    os.makedirs(history_dir, exist_ok=True)
    winner_stem = "-".join(payload["winner_names"]) if payload["winner_names"] else "no_winner"
    safe_winner_stem = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in winner_stem)[:48]
    filename = f"{payload['match_id']}_{safe_winner_stem}.json"
    final_path = os.path.join(history_dir, filename)

    fd, temp_path = tempfile.mkstemp(prefix="match_", suffix=".json", dir=history_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            json.dump(payload, temp_file, indent=2)
        os.replace(temp_path, final_path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
    return final_path


def finalize_match_timeline(state):
    timeline = getattr(state, "current_match_timeline", None)
    if not timeline:
        return None
    if timeline.get("_finalized"):
        saved_path = timeline.get("_saved_path")
        return saved_path

    record_match_timeline_sample(state)
    timeline["ended_at"] = _now_iso()
    timeline["duration_ms"] = int(timeline.get("_last_sample_ms") or 0)
    losing_player_ids = {_player_id(player) for player in state.players if player.has_lost_game()}
    for player in state.players:
        player_id = _player_id(player)
        timeline["players"][player_id] = {
            **timeline["players"].get(player_id, _build_player_metadata(player)),
            "result": "DEFEATED" if player_id in losing_player_ids else "WINNER" if losing_player_ids else "WINNER" if player.is_winner else "DEFEATED" if player.is_loser else "ACTIVE",
            "is_winner": bool(player_id not in losing_player_ids and losing_player_ids) or bool(player.is_winner),
            "is_loser": bool(player_id in losing_player_ids) or bool(player.is_loser),
            "owned_building_count": int(getattr(player, "owned_building_count", 0)),
        }
    payload = _build_completed_payload(state)
    saved_path = _save_payload(payload, state.MATCH_HISTORY_DIR)
    removed_paths = _prune_saved_scoreboards(
        state.MATCH_HISTORY_DIR,
        state.hud_positions.get("saved_scoreboard_limit", -1),
    )
    if saved_path in removed_paths:
        saved_path = None
    timeline["_finalized"] = True
    timeline["_saved_path"] = saved_path
    state.completed_match_path = saved_path
    logging.info("Finalized match timeline %s at %s", timeline["match_id"], saved_path)
    return saved_path


def build_scoreboard_timeline(state):
    timeline = getattr(state, "current_match_timeline", None)
    if not timeline:
        return None

    if timeline.get("_finalized"):
        players = []
        for player_id, meta in timeline["players"].items():
            players.append(
                {
                    **_export_player_timeline_meta(meta),
                    "series": timeline["series"].get(player_id, {}),
                }
            )
        winner_names = [player["username"] for player in players if player.get("result") == "WINNER" or player.get("is_winner")]
        return {
            "schema_version": timeline["schema_version"],
            "match_id": timeline["match_id"],
            "started_at": timeline["started_at"],
            "ended_at": timeline["ended_at"],
            "duration_ms": timeline["duration_ms"],
            "sample_interval_ms": timeline["sample_interval_ms"],
            "winner_names": winner_names,
            "players": players,
        }

    record_match_timeline_sample(state)
    losing_player_ids = {_player_id(player) for player in state.players if player.has_lost_game()}
    players = []
    for player in state.players:
        player_id = _player_id(player)
        meta = _export_player_timeline_meta(timeline["players"].get(player_id, _build_player_metadata(player)))
        meta.update(
            {
                "result": "DEFEATED" if player_id in losing_player_ids else "WINNER" if losing_player_ids else "WINNER" if player.is_winner else "DEFEATED" if player.is_loser else "ACTIVE",
                "is_winner": bool(player_id not in losing_player_ids and losing_player_ids) or bool(player.is_winner),
                "is_loser": bool(player_id in losing_player_ids) or bool(player.is_loser),
                "owned_building_count": int(getattr(player, "owned_building_count", 0)),
                "series": timeline["series"].get(player_id, {}),
            }
        )
        players.append(meta)

    return {
        "schema_version": timeline["schema_version"],
        "match_id": timeline["match_id"],
        "started_at": timeline["started_at"],
        "ended_at": None,
        "duration_ms": int(timeline.get("_last_sample_ms") or 0),
        "sample_interval_ms": timeline["sample_interval_ms"],
        "winner_names": [player["username"] for player in players if player["is_winner"]],
        "players": players,
    }


def get_match_elapsed_ms(state):
    timeline = getattr(state, "current_match_timeline", None)
    if not timeline:
        return 0
    if timeline.get("_finalized"):
        return int(timeline.get("duration_ms") or 0)
    start_perf = timeline.get("_start_perf")
    if start_perf is None:
        return int(timeline.get("_last_sample_ms") or 0)
    return max(0, int((time.perf_counter() - start_perf) * 1000))
