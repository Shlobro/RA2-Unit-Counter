import json
import logging
import os
import tempfile
import time
from datetime import datetime


CORE_METRIC_ORDER = [
    "income_total",
    "cash",
    "money_spent_total",
    "units_current_total",
    "units_lost_total",
    "infantry_current",
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


def _build_player_metadata(player):
    color_name = player.color_name if isinstance(player.color_name, str) else player.color_name.name()
    accent_color = player.color.name() if hasattr(player.color, "name") else str(player.color)
    return {
        "player_id": _player_id(player),
        "index": player.index,
        "display_slot": getattr(player, "display_slot", player.index),
        "username": player.username.value or f"Player {player.index}",
        "faction": player.faction,
        "country": player.country_name.value.decode("utf-8", errors="ignore").split("\x00", 1)[0].strip(),
        "color_name": color_name,
        "accent_color": accent_color,
        "flag_file_stem": getattr(player, "post_game_flag_file_stem", ""),
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
    infantry_current = _sum_counts(player.infantry_counts)
    vehicles_current = _sum_matching_counts(player.tank_counts, NAVAL_UNIT_NAMES, include_matches=False)
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
        "units_current_total": infantry_current + vehicles_current + navy_current + buildings_current + aircraft_current,
        "units_lost_total": infantry_lost + vehicles_lost + navy_lost + buildings_lost + aircraft_lost,
        "infantry_current": infantry_current,
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
        timeline["players"][player_id] = {
            **player_meta,
            "username": player.username.value or f"Player {player.index}",
            "faction": player.faction,
            "flag_file_stem": getattr(player, "post_game_flag_file_stem", timeline["players"].get(player_id, {}).get("flag_file_stem", "")),
            "owned_building_count": int(getattr(player, "owned_building_count", 0)),
        }
        series = timeline["series"].setdefault(
            player_id,
            {metric_id: [] for metric_id in CORE_METRIC_ORDER},
        )
        metrics = _compute_player_metrics(player, timeline["players"][player_id], derived_loss_metrics)
        player.derived_income_total = metrics["income_total"]
        for metric_id, value in metrics.items():
            series.setdefault(metric_id, []).append({"t_ms": elapsed_ms, "value": int(value)})

    timeline["_last_sample_ms"] = elapsed_ms


def _build_completed_payload(state):
    timeline = state.current_match_timeline
    losing_player_ids = {_player_id(player) for player in state.players if player.has_lost_game()}
    players = []
    for player in state.players:
        player_id = _player_id(player)
        player_meta = dict(timeline["players"].get(player_id, _build_player_metadata(player)))
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
                    **meta,
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
        meta = dict(timeline["players"].get(player_id, _build_player_metadata(player)))
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
    return int(timeline.get("_last_sample_ms") or 0)
