import bisect
import os

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from constants import _existing_asset_paths, resolve_factory_image_path
from player_identity import get_player_flag_export_stem


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

RESULT_LABELS = {
    "WINNER": "Won",
    "DEFEATED": "Lost",
    "ACTIVE": "Still alive",
}

DISPLAY_NAME_ALIASES = {
    "BlackHawk Transport": "Night Hawk Transport",
    "Slave miner": "Slave Miner",
    "Master Mind": "Mastermind",
    "Desolater": "Desolator",
}

METRIC_OPTIONS = [
    {"id": "income_total", "label": "Income", "format": "money"},
    {"id": "cash", "label": "Cash", "format": "money"},
    {"id": "money_spent_total", "label": "Money Spent", "format": "money"},
    {"id": "units_current_total", "label": "Units", "format": "count"},
    {"id": "units_lost_total", "label": "Lost", "format": "count"},
    {"id": "infantry_current", "label": "Infantry", "format": "count"},
    {"id": "vehicles_current", "label": "Vehicles", "format": "count"},
    {"id": "navy_current", "label": "Navy", "format": "count"},
    {"id": "buildings_current", "label": "Buildings", "format": "count"},
    {"id": "aircraft_current", "label": "Aircraft", "format": "count"},
    {"id": "infantry_lost", "label": "Inf Lost", "format": "count"},
    {"id": "vehicles_lost", "label": "Veh Lost", "format": "count"},
    {"id": "navy_lost", "label": "Navy Lost", "format": "count"},
    {"id": "buildings_lost", "label": "Bld Lost", "format": "count"},
    {"id": "aircraft_lost", "label": "Air Lost", "format": "count"},
]

LINE_STYLES = (
    Qt.PenStyle.SolidLine,
    Qt.PenStyle.DashLine,
    Qt.PenStyle.DotLine,
    Qt.PenStyle.DashDotLine,
    Qt.PenStyle.DashDotDotLine,
)


def _load_ra_font(point_size, weight=QFont.Bold, fallback_family="Arial"):
    font_id = QFontDatabase.addApplicationFont(os.path.join("Other", "Futured.ttf"))
    families = QFontDatabase.applicationFontFamilies(font_id)
    if families:
        return QFont(families[0], point_size, weight)
    return QFont(fallback_family, point_size, weight)


def _color_to_hex(color_value):
    if isinstance(color_value, QColor):
        return color_value.name()
    return str(color_value)


def _as_color(color_value, fallback="#d99a4e"):
    color = QColor(color_value)
    if color.isValid():
        return color
    return QColor(fallback)


def _format_money(value):
    return f"${int(value):,}"


def _format_count(value):
    return f"{int(value):,}"


def _format_value(metric_id, value):
    metric = next((item for item in METRIC_OPTIONS if item["id"] == metric_id), None)
    if metric and metric["format"] == "money":
        return _format_money(value)
    return _format_count(value)


def _format_duration(duration_ms):
    total_seconds = max(0, int(duration_ms // 1000))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def _load_pixmap(path, width, height):
    if not path or not os.path.exists(path):
        return None
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return None
    return pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)


def _scoreboard_background_path():
    for parts in (
        ("Other", "scoreboardbackground.png"),
        ("Other", "post_game_background.png"),
    ):
        for candidate in _existing_asset_paths(*parts):
            return candidate.replace("\\", "/")
    return None


def _normalize_country_name(country_name):
    return (country_name or "").split("\x00", 1)[0].strip()


def _country_flag_path(country_name):
    normalized_country_name = _normalize_country_name(country_name)
    flag_name = COUNTRY_TO_FLAG.get(normalized_country_name)
    if not flag_name:
        return None
    for candidate in _existing_asset_paths("Flags", "PNG", flag_name):
        return candidate
    return None


def _faction_flag_path(faction_name):
    flag_name = FACTION_TO_FLAG.get((faction_name or "").strip())
    if not flag_name:
        return None
    for candidate in _existing_asset_paths("Flags", "PNG", flag_name):
        return candidate
    return None


def _player_flag_path(player_snapshot):
    country_flag = _country_flag_path(player_snapshot.get("country"))
    if country_flag:
        return country_flag

    faction_flag = _faction_flag_path(player_snapshot.get("faction"))
    if faction_flag:
        return faction_flag

    flag_file_stem = (player_snapshot.get("flag_file_stem") or "").strip()
    if flag_file_stem:
        filename = f"{flag_file_stem}_flag.png"
        for candidate in _existing_asset_paths("player flags", filename):
            return candidate

    color_name = (player_snapshot.get("color_name") or "").strip().lower()
    if color_name:
        for candidate in _existing_asset_paths("player flags", f"{color_name}_flag.png"):
            return candidate

    return None


def _sort_units(unit_counts):
    return sorted(unit_counts.items(), key=lambda item: (-item[1], item[0]))


def _display_name(name):
    return DISPLAY_NAME_ALIASES.get(name, name)


def _result_rank(result):
    if result == "WINNER":
        return 0
    if result == "DEFEATED":
        return 1
    return 2


def _derive_snapshot_losses(players):
    if len(players) != 2:
        return {
            str(player.index): {
                "infantry_lost": sum(player.lost_infantry_counts.values()),
                "vehicles_lost": sum(player.lost_tank_counts.values()),
                "buildings_lost": sum(player.lost_building_counts.values()),
                "aircraft_lost": max(
                    sum(player.lost_aircraft_counts.values()),
                    max(0, sum(player.built_aircraft_counts.values()) - sum(player.aircraft_counts.values())),
                ),
            }
            for player in players
        }

    player_a, player_b = players
    return {
        str(player_a.index): {
            "infantry_lost": sum(player_b.lost_infantry_counts.values()),
            "vehicles_lost": sum(player_b.lost_tank_counts.values()),
            "buildings_lost": sum(player_b.lost_building_counts.values()),
            "aircraft_lost": max(
                sum(player_b.lost_aircraft_counts.values()),
                max(0, sum(player_a.built_aircraft_counts.values()) - sum(player_a.aircraft_counts.values())),
            ),
        },
        str(player_b.index): {
            "infantry_lost": sum(player_a.lost_infantry_counts.values()),
            "vehicles_lost": sum(player_a.lost_tank_counts.values()),
            "buildings_lost": sum(player_a.lost_building_counts.values()),
            "aircraft_lost": max(
                sum(player_a.lost_aircraft_counts.values()),
                max(0, sum(player_b.built_aircraft_counts.values()) - sum(player_b.aircraft_counts.values())),
            ),
        },
    }


def build_post_game_snapshot(players, hud_positions=None):
    hud_positions = hud_positions or {}
    losing_player_ids = {str(player.index) for player in players if player.has_lost_game()}
    derived_losses = _derive_snapshot_losses(players)
    snapshot_players = []
    for player in players:
        built_units = player.get_built_unit_totals()
        killed_units = player.get_killed_unit_totals()
        current_units = player.get_current_unit_totals()
        player_losses = derived_losses.get(str(player.index), {})
        result = "ACTIVE"
        if str(player.index) in losing_player_ids:
            result = "DEFEATED"
        elif losing_player_ids:
            result = "WINNER"
        elif player.is_winner:
            result = "WINNER"
        elif player.is_loser:
            result = "DEFEATED"

        country_name = _normalize_country_name(player.country_name.value.decode("utf-8", errors="ignore"))
        snapshot_players.append({
            "player_id": str(player.index),
            "username": player.username.value or f"Player {player.index}",
            "faction": player.faction,
            "country": country_name,
            "color_name": player.color_name if isinstance(player.color_name, str) else player.color_name.name(),
            "flag_file_stem": getattr(player, "post_game_flag_file_stem", "") or get_player_flag_export_stem(player, hud_positions),
            "accent_color": _color_to_hex(player.color),
            "result": result,
            "result_label": RESULT_LABELS.get(result, result.title()),
            "money_spent": player.spent_credit,
            "current_balance": player.balance,
            "income_total": int(getattr(player, "derived_income_total", 0)),
            "infantry_built": sum(player.built_infantry_counts.values()),
            "vehicles_built": sum(player.built_tank_counts.values()),
            "buildings_built": sum(player.built_building_counts.values()),
            "aircraft_built": sum(player.built_aircraft_counts.values()),
            "infantry_lost": player_losses.get("infantry_lost", 0),
            "vehicles_lost": player_losses.get("vehicles_lost", 0),
            "buildings_lost": player_losses.get("buildings_lost", 0),
            "aircraft_lost": player_losses.get("aircraft_lost", 0),
            "units_made": _sort_units(built_units),
            "units_killed": _sort_units(killed_units),
            "units_remaining": _sort_units({name: count for name, count in current_units.items() if count > 0}),
        })

    snapshot_players.sort(key=lambda player_data: (_result_rank(player_data["result"]), player_data["username"].lower()))
    return {"players": snapshot_players}


class StatTable(QTableWidget):
    def __init__(self, title, rows):
        super().__init__(0, 2)
        self._title = title
        self.setHorizontalHeaderLabels(["Unit", "Count"])
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setIconSize(QSize(42, 32))
        self.setMinimumHeight(210)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.populate(rows)

    def populate(self, rows):
        table_rows = rows or [("None", 0)]
        self.setRowCount(len(table_rows))
        for row_index, (unit_name, count) in enumerate(table_rows):
            unit_item = QTableWidgetItem(_display_name(unit_name))
            icon_path = resolve_factory_image_path(unit_name)
            pixmap = _load_pixmap(icon_path, 40, 30)
            if pixmap is not None:
                unit_item.setIcon(QIcon(pixmap))
            count_item = QTableWidgetItem(f"{count:,}")
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.setItem(row_index, 0, unit_item)
            self.setItem(row_index, 1, count_item)


class WinnerBadge(QLabel):
    def __init__(self, parent=None):
        super().__init__("WON", parent)
        self.setObjectName("winnerBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._glow_effect = QGraphicsDropShadowEffect(self)
        self._glow_effect.setColor(QColor(96, 220, 128, 190))
        self._glow_effect.setBlurRadius(18)
        self._glow_effect.setOffset(0, 0)
        self.setGraphicsEffect(self._glow_effect)
        self._start_pulse()

    def _start_pulse(self):
        self._pulse_up = True
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse_step)
        self._timer.start(40)
        self._radius = 18

    def _pulse_step(self):
        if self._pulse_up:
            self._radius += 2
            if self._radius >= 36:
                self._pulse_up = False
        else:
            self._radius -= 2
            if self._radius <= 10:
                self._pulse_up = True
        self._glow_effect.setBlurRadius(self._radius)


class FlagBadge(QFrame):
    def __init__(self, flag_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName("flagBadge")
        self.setFixedSize(92, 60)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setStyleSheet("background: transparent; border: none;")
        pixmap = _load_pixmap(flag_path, 84, 56)
        if pixmap is not None:
            self._image_label.setPixmap(pixmap)
        layout.addWidget(self._image_label)


class PlayerReportCard(QFrame):
    def __init__(self, player_snapshot, anim_delay_ms=0):
        super().__init__()
        self.player_snapshot = player_snapshot
        self._anim_delay = anim_delay_ms
        self.setObjectName("playerCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._build_ui()
        self._setup_entry_animation()

    def _setup_entry_animation(self):
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._fade_anim.setDuration(600)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        QTimer.singleShot(self._anim_delay, self._fade_anim.start)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)
        is_winner = self.player_snapshot["result"] == "WINNER"

        header = QHBoxLayout()
        header.setSpacing(18)

        flag_label = FlagBadge(_player_flag_path(self.player_snapshot))
        flag_shadow = QGraphicsDropShadowEffect(flag_label)
        flag_shadow.setBlurRadius(10)
        flag_shadow.setColor(QColor(0, 0, 0, 160))
        flag_shadow.setOffset(2, 2)
        flag_label.setGraphicsEffect(flag_shadow)
        header.addWidget(flag_label)

        title_block = QVBoxLayout()
        title = QLabel(self.player_snapshot["username"])
        title.setObjectName("playerName")
        title.setStyleSheet(f'color: {self.player_snapshot["accent_color"]};')
        title_block.addWidget(title)
        header.addLayout(title_block)
        header.addStretch()

        if self.player_snapshot["result"] != "ACTIVE":
            badge = QLabel(self.player_snapshot["result_label"])
            badge.setObjectName("resultBadge")
            badge.setProperty("result", self.player_snapshot["result"])
            header.addWidget(badge)
        layout.addLayout(header)

        divider = QFrame()
        divider.setObjectName("cardDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        metrics = QHBoxLayout()
        for label_text, value_text in (
            ("Income", _format_money(self.player_snapshot["income_total"])),
            ("Money Spent", _format_money(self.player_snapshot["money_spent"])),
            ("Cash Left", _format_money(self.player_snapshot["current_balance"])),
        ):
            metrics.addWidget(self._make_metric_cell(label_text, value_text))
        metrics.addStretch()
        layout.addLayout(metrics)

        layout.addWidget(self._make_category_breakdown())
        layout.addWidget(self._make_highlight_strip(is_winner))

        tables_container = QFrame()
        tables_layout = QHBoxLayout(tables_container)
        tables_layout.setSpacing(14)
        tables_layout.setContentsMargins(0, 0, 0, 0)
        tables_layout.addWidget(self._make_table_block("Built", self.player_snapshot["units_made"]))
        tables_layout.addWidget(self._make_table_block("Destroyed", self.player_snapshot["units_killed"]))
        if is_winner:
            tables_layout.addWidget(self._make_table_block("Surviving", self.player_snapshot["units_remaining"]))
        layout.addWidget(tables_container, stretch=1)

        accent = self.player_snapshot["accent_color"]
        border_color = "#ffd700" if is_winner else accent
        self.setStyleSheet(
            f"""
            QFrame#playerCard {{
                background: rgba(8, 6, 6, 0.7);
                border: 2px solid {border_color};
                border-radius: 16px;
            }}
            """
        )

    def _make_metric_cell(self, label_text, value_text):
        cell = QFrame()
        cell.setObjectName("metricCell")
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(label_text)
        label.setObjectName("metricLabel")
        value = QLabel(value_text)
        value.setObjectName("metricValue")
        layout.addWidget(label)
        layout.addWidget(value)
        return cell

    def _make_highlight_strip(self, show_remaining):
        strip = QFrame()
        strip.setObjectName("highlightStrip")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)
        sections = [
            ("Built the most", self.player_snapshot["units_made"][:3]),
            ("Destroyed the most", self.player_snapshot["units_killed"][:3]),
        ]
        if show_remaining:
            sections.append(("Still had", self.player_snapshot["units_remaining"][:3]))
        for title, rows in sections:
            layout.addWidget(self._make_icon_group(title, rows))
        return strip

    def _make_category_breakdown(self):
        strip = QFrame()
        strip.setObjectName("highlightStrip")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)
        categories = [
            ("Infantry", self.player_snapshot["infantry_built"], self.player_snapshot["infantry_lost"]),
            ("Vehicles", self.player_snapshot["vehicles_built"], self.player_snapshot["vehicles_lost"]),
            ("Buildings", self.player_snapshot["buildings_built"], self.player_snapshot["buildings_lost"]),
            ("Aircraft", self.player_snapshot["aircraft_built"], self.player_snapshot["aircraft_lost"]),
        ]
        for title, built_count, killed_count in categories:
            block = QFrame()
            block.setObjectName("iconGroup")
            block_layout = QVBoxLayout(block)
            title_label = QLabel(title)
            title_label.setObjectName("iconGroupTitle")
            value_label = QLabel(f"Built {built_count:,} | Lost {killed_count:,}")
            value_label.setObjectName("metricValue")
            block_layout.addWidget(title_label)
            block_layout.addWidget(value_label)
            layout.addWidget(block)
        return strip

    def _make_icon_group(self, title, rows):
        block = QFrame()
        block.setObjectName("iconGroup")
        layout = QVBoxLayout(block)
        title_label = QLabel(title)
        title_label.setObjectName("iconGroupTitle")
        layout.addWidget(title_label)

        row_layout = QHBoxLayout()
        if rows:
            for unit_name, count in rows:
                row_layout.addWidget(self._make_unit_chip(unit_name, count))
        else:
            row_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
            none_label = QLabel("No data")
            none_label.setObjectName("emptyChip")
            row_layout.addWidget(none_label)
            row_layout.addSpacerItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(row_layout)
        return block

    def _make_unit_chip(self, unit_name, count):
        chip = QFrame()
        chip.setObjectName("unitChip")
        layout = QVBoxLayout(chip)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = _load_pixmap(resolve_factory_image_path(unit_name), 68, 50)
        if pixmap is not None:
            icon_label.setPixmap(pixmap)
        else:
            icon_label.setText(unit_name[:2].upper())
            icon_label.setObjectName("fallbackIcon")
        layout.addWidget(icon_label)

        name_label = QLabel(_display_name(unit_name))
        name_label.setObjectName("unitChipName")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        count_label = QLabel(f"x{count:,}")
        count_label.setObjectName("unitChipCount")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(count_label)
        return chip

    def _make_table_block(self, title, rows):
        block = QFrame()
        block.setObjectName("tableBlock")
        layout = QVBoxLayout(block)
        title_label = QLabel(title)
        title_label.setObjectName("tableTitle")
        layout.addWidget(title_label)
        table = StatTable(title, rows)
        layout.addWidget(table, stretch=1)
        return block


class TimelineChartWidget(QWidget):
    hoverTextChanged = Signal(str)

    def __init__(self, timeline, summary_players):
        super().__init__()
        self.timeline = timeline or {"players": []}
        self.summary_players = summary_players or []
        self.metric_id = "income_total"
        self.visible_player_ids = {player["player_id"] for player in self.timeline.get("players", [])}
        self.hover_t_ms = None
        self.setMouseTracking(True)
        self.setMinimumHeight(540)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_metric(self, metric_id):
        self.metric_id = metric_id
        self.hover_t_ms = None
        self.hoverTextChanged.emit(self._default_hover_text())
        self.update()

    def set_player_visible(self, player_id, visible):
        if visible:
            self.visible_player_ids.add(player_id)
        else:
            if len(self.visible_player_ids) <= 1 and player_id in self.visible_player_ids:
                return
            self.visible_player_ids.discard(player_id)
        self.hoverTextChanged.emit(self._hover_text())
        self.update()

    def _player_entries(self):
        players_by_id = {player["player_id"]: player for player in self.timeline.get("players", [])}
        ordered = []
        for player in self.summary_players:
            player_id = player.get("player_id")
            if player_id in players_by_id:
                ordered.append(players_by_id[player_id])
        for player_id, player in players_by_id.items():
            if all(existing["player_id"] != player_id for existing in ordered):
                ordered.append(player)
        return ordered

    def _visible_series(self):
        visible = []
        for player in self._player_entries():
            if player["player_id"] not in self.visible_player_ids:
                continue
            points = player.get("series", {}).get(self.metric_id, [])
            if points:
                visible.append((player, points))
        return visible

    def _plot_rect(self):
        return QRectF(78, 26, max(10.0, self.width() - 120.0), max(10.0, self.height() - 90.0))

    def _max_t_ms(self):
        max_t = int(self.timeline.get("duration_ms") or 0)
        for _, points in self._visible_series():
            if points:
                max_t = max(max_t, int(points[-1]["t_ms"]))
        return max(1, max_t)

    def _max_value(self):
        max_value = 0
        for _, points in self._visible_series():
            for point in points:
                max_value = max(max_value, int(point["value"]))
        return max(1, max_value)

    def _point_to_xy(self, t_ms, value, plot_rect, max_t_ms, max_value):
        x = plot_rect.left() + (t_ms / max_t_ms) * plot_rect.width()
        y = plot_rect.bottom() - (value / max_value) * plot_rect.height()
        return x, y

    def _value_at(self, points, t_ms):
        if not points:
            return 0
        if t_ms <= points[0]["t_ms"]:
            return points[0]["value"]
        if t_ms >= points[-1]["t_ms"]:
            return points[-1]["value"]
        times = [point["t_ms"] for point in points]
        index = bisect.bisect_left(times, t_ms)
        left = points[index - 1]
        right = points[index]
        if right["t_ms"] == left["t_ms"]:
            return right["value"]
        ratio = (t_ms - left["t_ms"]) / (right["t_ms"] - left["t_ms"])
        return int(left["value"] + (right["value"] - left["value"]) * ratio)

    def _default_hover_text(self):
        metric_label = next((item["label"] for item in METRIC_OPTIONS if item["id"] == self.metric_id), self.metric_id)
        return f"{metric_label} over {_format_duration(self.timeline.get('duration_ms') or 0)}"

    def _draw_hover_value(self, painter, x, y, text, color, align_right=False):
        padding_x = 8
        padding_y = 5
        font = QFont("Arial", 9, QFont.Bold)
        painter.setFont(font)
        text_width = painter.fontMetrics().horizontalAdvance(text)
        width = text_width + padding_x * 2
        height = painter.fontMetrics().height() + padding_y * 2
        bubble_x = x - width - 12 if align_right else x + 12
        bubble_y = y - height / 2
        bubble_rect = QRectF(bubble_x, bubble_y, width, height)
        painter.setPen(QPen(QColor(12, 10, 10, 220), 1))
        painter.setBrush(QColor(10, 8, 8, 190))
        painter.drawRoundedRect(bubble_rect, 8, 8)
        painter.setPen(QPen(color))
        painter.drawText(bubble_rect, Qt.AlignmentFlag.AlignCenter, text)

    def _hover_text(self):
        if self.hover_t_ms is None:
            return self._default_hover_text()
        parts = [f"{_format_duration(self.hover_t_ms)}"]
        for player, points in self._visible_series():
            parts.append(f"{player['username']}: {_format_value(self.metric_id, self._value_at(points, self.hover_t_ms))}")
        return "   |   ".join(parts)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        panel_rect = self.rect().adjusted(0, 0, -1, -1)
        painter.setPen(QPen(QColor(196, 109, 50, 160), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(panel_rect, 16, 16)

        visible_series = self._visible_series()
        if not visible_series:
            painter.setPen(QColor("#f7d29d"))
            painter.setFont(_load_ra_font(14))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No timeline data available for this metric.")
            return

        plot_rect = self._plot_rect()
        max_t_ms = self._max_t_ms()
        max_value = self._max_value()

        grid_pen = QPen(QColor(255, 221, 175, 35), 1)
        painter.setPen(grid_pen)
        for step in range(5):
            y = plot_rect.top() + (plot_rect.height() / 4) * step
            painter.drawLine(plot_rect.left(), y, plot_rect.right(), y)
        for step in range(7):
            x = plot_rect.left() + (plot_rect.width() / 6) * step
            painter.drawLine(x, plot_rect.top(), x, plot_rect.bottom())

        painter.setPen(QPen(QColor("#d7b48d")))
        painter.setFont(QFont("Arial", 9, QFont.Bold))
        painter.drawText(QRectF(10, plot_rect.top() - 8, 60, 20), Qt.AlignmentFlag.AlignRight, _format_value(self.metric_id, max_value))
        painter.drawText(QRectF(10, plot_rect.bottom() - 12, 60, 20), Qt.AlignmentFlag.AlignRight, _format_value(self.metric_id, 0))
        painter.drawText(QRectF(plot_rect.left() - 8, plot_rect.bottom() + 8, 80, 20), Qt.AlignmentFlag.AlignLeft, "0:00")
        painter.drawText(QRectF(plot_rect.right() - 80, plot_rect.bottom() + 8, 80, 20), Qt.AlignmentFlag.AlignRight, _format_duration(max_t_ms))

        painter.setClipRect(plot_rect.adjusted(-2, -2, 2, 2))
        for series_index, (player, points) in enumerate(visible_series):
            color = _as_color(player.get("accent_color"))
            path = QPainterPath()
            for index, point in enumerate(points):
                x, y = self._point_to_xy(point["t_ms"], point["value"], plot_rect, max_t_ms, max_value)
                if index == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            line_style = LINE_STYLES[series_index % len(LINE_STYLES)]
            painter.setPen(QPen(QColor(10, 8, 8, 220), 6, line_style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)
            painter.setPen(QPen(color, 3, line_style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.drawPath(path)

        if self.hover_t_ms is not None:
            hover_x, _ = self._point_to_xy(self.hover_t_ms, 0, plot_rect, max_t_ms, max_value)
            painter.setPen(QPen(QColor(255, 238, 210, 140), 1, Qt.PenStyle.DashLine))
            painter.drawLine(hover_x, plot_rect.top(), hover_x, plot_rect.bottom())
            for series_index, (player, points) in enumerate(visible_series):
                value = self._value_at(points, self.hover_t_ms)
                _, hover_y = self._point_to_xy(self.hover_t_ms, value, plot_rect, max_t_ms, max_value)
                player_color = _as_color(player.get("accent_color"))
                painter.setBrush(player_color)
                painter.setPen(QPen(QColor("#0b0908"), 1))
                marker_size = 14 + (series_index % 3) * 2
                painter.drawEllipse(QRectF(hover_x - marker_size / 2, hover_y - marker_size / 2, marker_size, marker_size))
                align_right = hover_x > (plot_rect.left() + plot_rect.width() * 0.72)
                self._draw_hover_value(
                    painter,
                    hover_x,
                    hover_y,
                    _format_value(self.metric_id, value),
                    player_color,
                    align_right=align_right,
                )

    def mouseMoveEvent(self, event):
        plot_rect = self._plot_rect()
        if not plot_rect.contains(event.position()):
            self.hover_t_ms = None
            self.hoverTextChanged.emit(self._default_hover_text())
            self.update()
            return
        ratio = (event.position().x() - plot_rect.left()) / max(1.0, plot_rect.width())
        self.hover_t_ms = int(max(0.0, min(1.0, ratio)) * self._max_t_ms())
        self.hoverTextChanged.emit(self._hover_text())
        self.update()

    def leaveEvent(self, event):
        self.hover_t_ms = None
        self.hoverTextChanged.emit(self._default_hover_text())
        self.update()
        super().leaveEvent(event)


class PostGameScoreboardWindow(QMainWindow):
    def __init__(self, payload):
        super().__init__()
        if "summary" in payload:
            self.summary = payload.get("summary") or {"players": []}
            self.timeline = payload.get("timeline") or {"players": [], "duration_ms": 0}
            self.match_path = payload.get("match_path")
        else:
            self.summary = payload
            self.timeline = {"players": [], "duration_ms": 0}
            self.match_path = None
        self.metric_buttons = {}
        self.legend_buttons = {}
        self.setWindowTitle("Post-Game Scoreboard")
        self.resize(1680, 980)
        self._build_ui()
        self.showMaximized()

    def _build_ui(self):
        title_font = _load_ra_font(34)
        heading_font = _load_ra_font(15)
        background_path = _scoreboard_background_path()

        central = QWidget()
        central.setObjectName("scoreboardCentral")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        banner = QFrame()
        banner.setObjectName("banner")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(28, 18, 28, 18)

        title_block = QVBoxLayout()
        title = QLabel("MATCH TIMELINE")
        title.setFont(title_font)
        title.setObjectName("mainTitle")
        title_shadow = QGraphicsDropShadowEffect(title)
        title_shadow.setColor(QColor(196, 109, 50, 200))
        title_shadow.setBlurRadius(16)
        title_shadow.setOffset(0, 0)
        title.setGraphicsEffect(title_shadow)
        title_block.addWidget(title)
        subtitle = QLabel(self._subtitle_text())
        subtitle.setObjectName("headerSubTitle")
        subtitle.setVisible(bool(subtitle.text()))
        title_block.addWidget(subtitle)
        banner_layout.addLayout(title_block)
        banner_layout.addStretch()
        for pill_text in self._summary_pills():
            banner_layout.addWidget(self._make_header_pill(pill_text))
        root.addWidget(banner)

        tabs = QTabWidget()
        tabs.setObjectName("scoreboardTabs")

        graphs_tab = QWidget()
        graphs_layout = QVBoxLayout(graphs_tab)
        graphs_layout.setContentsMargins(18, 18, 18, 24)
        graphs_layout.addWidget(self._build_graph_panel(), 1)
        breakdown_tab = QWidget()
        breakdown_layout = QVBoxLayout(breakdown_tab)
        breakdown_layout.setContentsMargins(18, 18, 18, 24)
        breakdown_layout.setSpacing(18)
        details_heading = QLabel("PLAYER BREAKDOWN")
        details_heading.setObjectName("sectionHeading")
        breakdown_layout.addWidget(details_heading)

        cards_container = QWidget()
        grid = QGridLayout(cards_container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(16)
        num_players = len(self.summary["players"])
        cols = 2 if num_players > 1 else 1
        for index, player_snapshot in enumerate(self.summary["players"]):
            card = PlayerReportCard(player_snapshot, anim_delay_ms=index * 80)
            grid.addWidget(card, index // cols, index % cols)
        for col in range(cols):
            grid.setColumnStretch(col, 1)
        breakdown_layout.addWidget(cards_container)
        tabs.addTab(breakdown_tab, "Player Breakdown")

        tabs.addTab(graphs_tab, "Graphs")

        root.addWidget(tabs)

        self._banner_opacity = QGraphicsOpacityEffect(banner)
        self._banner_opacity.setOpacity(0.0)
        banner.setGraphicsEffect(self._banner_opacity)
        self._banner_anim = QPropertyAnimation(self._banner_opacity, b"opacity", self)
        self._banner_anim.setDuration(700)
        self._banner_anim.setStartValue(0.0)
        self._banner_anim.setEndValue(1.0)
        self._banner_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._banner_anim.start()

        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: #050404;
                color: #f2e1cd;
            }}
            QWidget#scoreboardCentral {{
                border-image: {"none" if not background_path else f"url({background_path}) 0 0 0 0 stretch stretch"};
            }}
            QTabWidget#scoreboardTabs QWidget {{
                background: transparent;
            }}
            QFrame#banner {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(6, 4, 4, 225), stop:1 rgba(6, 4, 4, 150));
                border-bottom: 1px solid rgba(196, 109, 50, 0.6);
            }}
            QLabel#mainTitle {{
                color: #f7d29d;
                letter-spacing: 4px;
            }}
            QLabel#headerSubTitle {{
                color: rgba(244, 216, 187, 0.85);
                font-size: 17px;
            }}
            QLabel#sectionHeading {{
                color: #f7d29d;
                font-size: 22px;
                font-weight: 800;
                letter-spacing: 2px;
                padding-left: 4px;
            }}
            QFrame#headerPill {{
                background: rgba(18, 12, 10, 0.8);
                border: 1px solid rgba(201, 112, 50, 0.75);
                border-radius: 12px;
            }}
            QLabel#headerPillText {{
                color: #fff1cf;
                font-size: 16px;
                font-weight: 700;
            }}
            QFrame#graphPanel {{
                background: rgba(8, 6, 6, 0.78);
                border: 1px solid rgba(201, 112, 50, 0.7);
                border-radius: 18px;
            }}
            QLabel#graphHeading {{
                color: #f7d29d;
                font-size: 24px;
                font-weight: 800;
                letter-spacing: 2px;
            }}
            QLabel#graphSubText {{
                color: rgba(230, 203, 177, 0.82);
                font-size: 14px;
            }}
            QPushButton#metricButton {{
                background-color: rgba(24, 14, 11, 0.92);
                border: 1px solid rgba(201, 112, 50, 0.6);
                border-radius: 10px;
                padding: 9px 14px;
                color: #f2ddbf;
                font-size: 14px;
                font-weight: 700;
                outline: none;
            }}
            QPushButton#metricButton:hover {{
                background-color: rgba(40, 25, 19, 0.94);
            }}
            QPushButton#metricButton:focus {{
                background-color: rgba(24, 14, 11, 0.92);
                border: 1px solid rgba(201, 112, 50, 0.6);
                outline: none;
            }}
            QPushButton#metricButton:checked {{
                background-color: rgba(160, 77, 33, 0.92);
                border: 1px solid rgba(255, 214, 150, 0.95);
                color: #fff4d3;
                outline: none;
            }}
            QPushButton#legendButton {{
                background: rgba(18, 12, 10, 0.9);
                border: 1px solid rgba(201, 112, 50, 0.55);
                border-radius: 11px;
                padding: 8px 14px;
                color: #f4dfc2;
                font-size: 14px;
                font-weight: 700;
                text-align: left;
            }}
            QPushButton#legendButton:checked {{
                background: rgba(36, 20, 15, 0.95);
                border: 1px solid rgba(255, 214, 150, 0.95);
                color: #fff4d3;
            }}
            QLabel#hoverReadout {{
                color: #fff1cf;
                font-size: 14px;
                font-weight: 700;
            }}
            QFrame#flagBadge {{
                min-width: 92px;
                min-height: 60px;
                background-color: rgba(10, 8, 8, 0.5);
                border: 1px solid rgba(201, 112, 50, 0.5);
                border-radius: 8px;
                color: #ffe7a8;
                font-weight: 800;
                font-size: 22px;
            }}
            QLabel#playerName {{
                color: #ffe7a8;
                font-size: 32px;
                font-weight: 700;
            }}
            QLabel#playerMeta {{
                color: rgba(208, 170, 160, 0.8);
                font-size: 18px;
            }}
            QLabel#winnerBadge {{
                padding: 12px 24px;
                border-radius: 12px;
                font-weight: 900;
                font-size: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(18, 86, 36, 0.94), stop:0.5 rgba(48, 156, 78, 0.98), stop:1 rgba(18, 86, 36, 0.94));
                color: #efffe8;
                border: 2px solid #7ef0a1;
                min-width: 150px;
            }}
            QLabel#resultBadge {{
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: 800;
                font-size: 18px;
                min-width: 120px;
            }}
            QLabel#resultBadge[result="DEFEATED"] {{
                background-color: rgba(70, 10, 10, 0.85);
                color: #ffb4a8;
                border: 1px solid rgba(220, 80, 60, 0.8);
            }}
            QLabel#resultBadge[result="WINNER"] {{
                background-color: rgba(18, 86, 36, 0.95);
                color: #efffe8;
                border: 2px solid rgba(126, 240, 161, 0.95);
            }}
            QFrame#cardDivider {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 transparent, stop:0.1 rgba(201, 112, 50, 0.9), stop:0.9 rgba(201, 112, 50, 0.9), stop:1 transparent);
            }}
            QFrame#metricCell, QFrame#tableBlock, QFrame#highlightStrip, QFrame#iconGroup {{
                background-color: rgba(5, 4, 4, 0.65);
                border: 1px solid rgba(201, 112, 50, 0.6);
                border-radius: 10px;
            }}
            QFrame#unitChip {{
                background-color: rgba(6, 5, 5, 0.65);
                border: 1px solid rgba(201, 112, 50, 0.65);
                border-radius: 8px;
                min-width: 108px;
                max-width: 136px;
            }}
            QLabel#iconGroupTitle {{
                color: rgba(255, 207, 118, 0.85);
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#unitChipName {{
                color: #f4d6ba;
                font-size: 14px;
            }}
            QLabel#unitChipCount, QLabel#metricValue {{
                color: #fff3c6;
                font-size: 20px;
                font-weight: 700;
            }}
            QLabel#metricLabel {{
                color: rgba(211, 172, 139, 0.75);
                font-size: 14px;
            }}
            QLabel#tableTitle {{
                color: rgba(255, 207, 118, 0.9);
                font-size: 18px;
                font-weight: 700;
            }}
            QHeaderView::section {{
                background-color: rgba(60, 20, 10, 0.85);
                color: #ffd486;
                border: none;
                padding: 9px 12px;
                font-weight: 700;
            }}
            QTableWidget {{
                background-color: rgba(5, 4, 4, 0.55);
                alternate-background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(201, 112, 50, 0.6);
                border-radius: 8px;
                gridline-color: transparent;
                color: #f7e4d0;
                font-size: 15px;
            }}
            QTabWidget#scoreboardTabs::pane {{
                background: transparent;
                border: none;
                top: -1px;
            }}
            QTabBar::tab {{
                background: rgba(24, 14, 11, 0.92);
                color: #f2ddbf;
                border: 1px solid rgba(201, 112, 50, 0.6);
                padding: 10px 20px;
                min-width: 160px;
                font-size: 14px;
                font-weight: 700;
            }}
            QTabBar::tab:selected {{
                background: rgba(160, 77, 33, 0.92);
                color: #fff4d3;
                border-color: rgba(255, 214, 150, 0.95);
            }}
            QTabBar::tab:first {{
                border-top-left-radius: 10px;
            }}
            QTabBar::tab:last {{
                border-top-right-radius: 10px;
            }}
            """
        )

        central.setFont(heading_font)

    def _subtitle_text(self):
        return ""

    def _summary_pills(self):
        return [f"Duration {_format_duration(self.timeline.get('duration_ms') or 0)}"]

    def _make_header_pill(self, text):
        frame = QFrame()
        frame.setObjectName("headerPill")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 10, 14, 10)
        label = QLabel(text)
        label.setObjectName("headerPillText")
        layout.addWidget(label)
        return frame

    def _build_graph_panel(self):
        panel = QFrame()
        panel.setObjectName("graphPanel")
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 18)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("TIMELINE GRAPHS")
        title.setObjectName("graphHeading")
        header_row.addWidget(title)
        header_row.addStretch()
        layout.addLayout(header_row)

        metric_grid = QGridLayout()
        metric_grid.setHorizontalSpacing(10)
        metric_grid.setVerticalSpacing(10)
        for index, metric in enumerate(METRIC_OPTIONS):
            button = QPushButton(metric["label"])
            button.setObjectName("metricButton")
            button.setCheckable(True)
            button.setAutoDefault(False)
            button.setDefault(False)
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.clicked.connect(lambda checked, metric_id=metric["id"]: self._set_metric(metric_id))
            self.metric_buttons[metric["id"]] = button
            metric_grid.addWidget(button, index // 5, index % 5)
        layout.addLayout(metric_grid)

        self.chart_widget = TimelineChartWidget(self.timeline, self.summary["players"])
        layout.addWidget(self.chart_widget, 1)

        legend_layout = QHBoxLayout()
        for player in self.summary["players"]:
            button = QPushButton(player["username"])
            button.setObjectName("legendButton")
            button.setCheckable(True)
            button.setChecked(True)
            button.setStyleSheet(f"QPushButton#legendButton {{ border-left: 5px solid {player['accent_color']}; }}")
            button.clicked.connect(lambda checked, player_id=player["player_id"]: self._toggle_player(player_id, checked))
            self.legend_buttons[player["player_id"]] = button
            legend_layout.addWidget(button)
        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        self._set_metric("income_total")
        return panel

    def _set_metric(self, metric_id):
        for button_metric_id, button in self.metric_buttons.items():
            button.setChecked(button_metric_id == metric_id)
        self.chart_widget.set_metric(metric_id)

    def _toggle_player(self, player_id, checked):
        self.chart_widget.set_player_visible(player_id, checked)
        self.legend_buttons[player_id].setChecked(player_id in self.chart_widget.visible_player_ids)


