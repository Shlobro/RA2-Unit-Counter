import os

from PySide6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QTimer, QSequentialAnimationGroup, QParallelAnimationGroup, QPoint, QRect
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPixmap, QIcon, QPainter, QLinearGradient, QPen, QBrush, QRadialGradient
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from constants import _existing_asset_paths, resolve_factory_image_path


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


def _format_money(value):
    return f"${value:,}"


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


def _player_flag_path(player_snapshot):
    color_name = (player_snapshot.get("color_name") or "").strip()
    if color_name:
        filename = f"{color_name}_flag.png"
        for candidate in _existing_asset_paths("player flags", filename):
            return candidate
    return _country_flag_path(player_snapshot.get("country"))


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


def build_post_game_snapshot(players):
    snapshot_players = []
    for player in players:
        built_units = player.get_built_unit_totals()
        killed_units = player.get_killed_unit_totals()
        current_units = player.get_current_unit_totals()
        result = "ACTIVE"
        if player.is_winner:
            result = "WINNER"
        elif player.is_loser:
            result = "DEFEATED"

        country_name = _normalize_country_name(player.country_name.value.decode("utf-8", errors="ignore"))
        snapshot_players.append({
            "username": player.username.value or f"Player {player.index}",
            "faction": player.faction,
            "country": country_name,
            "color_name": player.color_name if isinstance(player.color_name, str) else player.color_name.name(),
            "accent_color": _color_to_hex(player.color),
            "result": result,
            "result_label": RESULT_LABELS.get(result, result.title()),
            "money_spent": player.spent_credit,
            "current_balance": player.balance,
            "infantry_built": sum(player.built_infantry_counts.values()),
            "vehicles_built": sum(player.built_tank_counts.values()),
            "buildings_built": sum(player.built_building_counts.values()),
            "aircraft_built": sum(player.built_aircraft_counts.values()),
            "infantry_killed": sum(player.lost_infantry_counts.values()),
            "vehicles_killed": sum(player.lost_tank_counts.values()),
            "buildings_killed": sum(player.lost_building_counts.values()),
            "aircraft_killed": sum(player.lost_aircraft_counts.values()),
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
    """Animated winner badge with glow pulse effect."""
    def __init__(self, parent=None):
        super().__init__("VICTORY", parent)
        self.setObjectName("winnerBadge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._glow_effect = QGraphicsDropShadowEffect(self)
        self._glow_effect.setColor(QColor(255, 215, 0, 200))
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

        # Header row
        header = QHBoxLayout()
        header.setSpacing(18)

        flag_label = QLabel()
        flag_label.setObjectName("flagBadge")
        flag_pixmap = _load_pixmap(_player_flag_path(self.player_snapshot), 84, 56)
        if flag_pixmap is not None:
            flag_label.setPixmap(flag_pixmap)
        else:
            flag_label.setText(self.player_snapshot["faction"][:2].upper())
            flag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flag_shadow = QGraphicsDropShadowEffect(flag_label)
        flag_shadow.setBlurRadius(10)
        flag_shadow.setColor(QColor(0, 0, 0, 160))
        flag_shadow.setOffset(2, 2)
        flag_label.setGraphicsEffect(flag_shadow)
        header.addWidget(flag_label)

        title_block = QVBoxLayout()
        title_block.setSpacing(4)
        title = QLabel(self.player_snapshot["username"])
        title.setObjectName("playerName")
        title.setStyleSheet(f'color: {self.player_snapshot["accent_color"]};')
        title_block.addWidget(title)
        header.addLayout(title_block)
        header.addStretch()

        if self.player_snapshot["result"] == "WINNER":
            badge = WinnerBadge()
            header.addWidget(badge)
        elif self.player_snapshot["result"] != "ACTIVE":
            badge = QLabel(self.player_snapshot["result_label"])
            badge.setObjectName("resultBadge")
            badge.setProperty("result", self.player_snapshot["result"])
            header.addWidget(badge)
        layout.addLayout(header)

        # Divider
        divider = QFrame()
        divider.setObjectName("cardDivider")
        divider.setFixedHeight(1)
        layout.addWidget(divider)

        # Money metrics row
        metrics = QHBoxLayout()
        metrics.setSpacing(14)
        summary_items = [
            ("Money Spent", _format_money(self.player_snapshot["money_spent"])),
            ("Cash Left", _format_money(self.player_snapshot["current_balance"])),
        ]
        for label_text, value_text in summary_items:
            metrics.addWidget(self._make_metric_cell(label_text, value_text))
        metrics.addStretch()
        layout.addLayout(metrics)

        # Category breakdown
        layout.addWidget(self._make_category_breakdown())

        # Highlight icon strip
        layout.addWidget(self._make_highlight_strip(is_winner))

        # Unit tables — stretch to fill remaining card space
        tables_container = QFrame()
        tables_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
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
        bg_alpha = "50" if is_winner else "40"
        self.setStyleSheet(
            f"""
            QFrame#playerCard {{
                background: rgba(8, 6, 6, 0.{bg_alpha});
                border: 2px solid {border_color};
                border-radius: 16px;
            }}
            """
        )

        if is_winner:
            glow = QGraphicsDropShadowEffect(self)
            glow.setColor(QColor(255, 215, 0, 80))
            glow.setBlurRadius(30)
            glow.setOffset(0, 0)
            # Note: can't combine with opacity effect, apply after fade-in is done
            QTimer.singleShot(self._anim_delay + 650, lambda: self.setGraphicsEffect(glow))

    def _make_metric_cell(self, label_text, value_text):
        cell = QFrame()
        cell.setObjectName("metricCell")
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

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
            ("Infantry", self.player_snapshot["infantry_built"], self.player_snapshot["infantry_killed"]),
            ("Vehicles", self.player_snapshot["vehicles_built"], self.player_snapshot["vehicles_killed"]),
            ("Buildings", self.player_snapshot["buildings_built"], self.player_snapshot["buildings_killed"]),
            ("Aircraft", self.player_snapshot["aircraft_built"], self.player_snapshot["aircraft_killed"]),
        ]

        for title, built_count, killed_count in categories:
            block = QFrame()
            block.setObjectName("iconGroup")
            block_layout = QVBoxLayout(block)
            block_layout.setContentsMargins(10, 10, 10, 10)
            block_layout.setSpacing(6)

            title_label = QLabel(title)
            title_label.setObjectName("iconGroupTitle")
            block_layout.addWidget(title_label)

            value_label = QLabel(f"Built {built_count:,} | Destroyed {killed_count:,}")
            value_label.setObjectName("metricValue")
            block_layout.addWidget(value_label)
            layout.addWidget(block)

        return strip

    def _make_icon_group(self, title, rows):
        block = QFrame()
        block.setObjectName("iconGroup")
        layout = QVBoxLayout(block)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("iconGroupTitle")
        layout.addWidget(title_label)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(10)
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
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

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
        block.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(block)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("tableTitle")
        layout.addWidget(title_label)
        table = StatTable(title, rows)
        layout.addWidget(table, stretch=1)
        return block


class PostGameScoreboardWindow(QMainWindow):
    def __init__(self, snapshot):
        super().__init__()
        self.snapshot = snapshot
        self.setWindowTitle("Post-Game Scoreboard")
        self.resize(1600, 920)
        self._build_ui()
        self.showMaximized()

    def _build_ui(self):
        title_font = _load_ra_font(38)
        heading_font = _load_ra_font(16)
        background_path = _scoreboard_background_path()

        central = QWidget()
        central.setObjectName("scoreboardCentral")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Top banner
        banner = QFrame()
        banner.setObjectName("banner")
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(32, 16, 32, 16)

        title = QLabel("MATCH SUMMARY")
        title.setFont(title_font)
        title.setObjectName("mainTitle")
        title_shadow = QGraphicsDropShadowEffect(title)
        title_shadow.setColor(QColor(196, 109, 50, 200))
        title_shadow.setBlurRadius(16)
        title_shadow.setOffset(0, 0)
        title.setGraphicsEffect(title_shadow)
        banner_layout.addWidget(title)
        banner_layout.addStretch()
        root.addWidget(banner)

        # Scroll area fills remaining space
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("scoreboardScroll")

        content = QWidget()
        content.setObjectName("scoreboardContent")
        grid = QGridLayout(content)
        grid.setContentsMargins(16, 16, 16, 16)
        grid.setSpacing(16)

        num_players = len(self.snapshot["players"])
        cols = 2 if num_players > 1 else 1
        for index, player_snapshot in enumerate(self.snapshot["players"]):
            delay = index * 120
            card = PlayerReportCard(player_snapshot, anim_delay_ms=delay)
            grid.addWidget(card, index // cols, index % cols)

        # Make columns and rows fill the window equally
        for col in range(cols):
            grid.setColumnStretch(col, 1)
        num_rows = (num_players + cols - 1) // cols
        for row in range(num_rows):
            grid.setRowStretch(row, 1)

        scroll.setWidget(content)
        root.addWidget(scroll)

        # Animate the banner fading in
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
            QWidget#scoreboardContent, QScrollArea#scoreboardScroll, QScrollArea#scoreboardScroll > QWidget > QWidget {{
                background: transparent;
            }}
            QFrame#banner {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(6, 4, 4, 210),
                    stop:1 rgba(6, 4, 4, 140));
                border-bottom: 1px solid rgba(196, 109, 50, 0.6);
            }}
            QLabel#mainTitle {{
                color: #f7d29d;
                letter-spacing: 4px;
            }}
            QLabel#flagBadge {{
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
                letter-spacing: 1px;
            }}
            QLabel#winnerBadge {{
                padding: 12px 24px;
                border-radius: 12px;
                font-weight: 900;
                font-size: 20px;
                letter-spacing: 2px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(120, 90, 0, 0.9),
                    stop:0.5 rgba(200, 160, 20, 0.95),
                    stop:1 rgba(120, 90, 0, 0.9));
                color: #fff8dc;
                border: 2px solid #ffd700;
                min-width: 150px;
            }}
            QLabel#resultBadge {{
                padding: 12px 20px;
                border-radius: 10px;
                font-weight: 800;
                font-size: 18px;
                min-width: 120px;
                letter-spacing: 1px;
            }}
            QLabel#resultBadge[result="DEFEATED"] {{
                background-color: rgba(70, 10, 10, 0.85);
                color: #ffb4a8;
                border: 1px solid rgba(220, 80, 60, 0.8);
            }}
            QLabel#resultBadge[result="ACTIVE"] {{
                background-color: rgba(50, 40, 10, 0.85);
                color: #f7df9a;
                border: 1px solid rgba(200, 170, 60, 0.8);
            }}
            QFrame#cardDivider {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 transparent,
                    stop:0.1 rgba(201, 112, 50, 0.9),
                    stop:0.9 rgba(201, 112, 50, 0.9),
                    stop:1 transparent);
            }}
            QFrame#metricCell {{
                background-color: rgba(5, 4, 4, 0.65);
                border: 1px solid rgba(201, 112, 50, 0.7);
                border-radius: 10px;
            }}
            QFrame#tableBlock {{
                background-color: rgba(5, 4, 4, 0.65);
                border: 1px solid rgba(201, 112, 50, 0.7);
                border-radius: 10px;
            }}
            QFrame#highlightStrip {{
                background: rgba(20, 10, 8, 0.55);
                border: 1px solid rgba(201, 112, 50, 0.6);
                border-radius: 10px;
            }}
            QFrame#iconGroup {{
                background-color: rgba(8, 6, 6, 0.55);
                border: 1px solid rgba(201, 112, 50, 0.55);
                border-radius: 8px;
            }}
            QLabel#iconGroupTitle {{
                color: rgba(255, 207, 118, 0.85);
                font-size: 16px;
                font-weight: 700;
                letter-spacing: 1px;
            }}
            QFrame#unitChip {{
                background-color: rgba(6, 5, 5, 0.65);
                border: 1px solid rgba(201, 112, 50, 0.65);
                border-radius: 8px;
                min-width: 108px;
                max-width: 136px;
            }}
            QLabel#unitChipName {{
                color: #f4d6ba;
                font-size: 14px;
            }}
            QLabel#unitChipCount {{
                color: #fff3c6;
                font-size: 18px;
                font-weight: 800;
            }}
            QLabel#emptyChip, QLabel#fallbackIcon {{
                color: #f0d0a6;
                font-weight: 700;
                font-size: 15px;
            }}
            QLabel#metricLabel {{
                color: rgba(211, 172, 139, 0.75);
                font-size: 14px;
                letter-spacing: 1px;
            }}
            QLabel#metricValue {{
                color: #fff3c6;
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#tableTitle {{
                color: rgba(255, 207, 118, 0.9);
                font-size: 18px;
                font-weight: 700;
                letter-spacing: 1px;
                padding-left: 2px;
            }}
            QHeaderView::section {{
                background-color: rgba(60, 20, 10, 0.85);
                color: #ffd486;
                border: none;
                padding: 9px 12px;
                font-weight: 700;
                letter-spacing: 1px;
                font-size: 15px;
            }}
            QTableWidget {{
                background-color: rgba(5, 4, 4, 0.55);
                alternate-background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(201, 112, 50, 0.6);
                border-radius: 8px;
                gridline-color: transparent;
                color: #f7e4d0;
                font-size: 15px;
                padding: 2px;
            }}
            QTableWidget::item {{
                padding: 7px 10px;
                background: transparent;
            }}
            QScrollArea#scoreboardScroll {{
                background: transparent;
                border: none;
            }}
            QScrollArea#scoreboardScroll QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: rgba(10, 4, 4, 0.6);
                width: 8px;
                margin: 0;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(127, 35, 24, 0.8);
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            """
        )

        central.setFont(heading_font)
