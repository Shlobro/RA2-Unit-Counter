import os

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPixmap, QIcon
from PySide6.QtWidgets import (
    QFrame,
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

from constants import resolve_factory_image_path


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
    candidate = os.path.join("Other", "post_game_background.png")
    if os.path.exists(candidate):
        return candidate.replace("\\", "/")
    return None


def _country_flag_path(country_name):
    flag_name = COUNTRY_TO_FLAG.get(country_name)
    if not flag_name:
        return None
    return os.path.join("Flags", "PNG", flag_name)


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
        total_cash_seen = player.balance + player.spent_credit

        result = "ACTIVE"
        if player.is_winner:
            result = "WINNER"
        elif player.is_loser:
            result = "DEFEATED"

        snapshot_players.append({
            "username": player.username.value or f"Player {player.index}",
            "faction": player.faction,
            "country": player.country_name.value.decode("utf-8", errors="ignore").strip("\x00"),
            "color_name": player.color_name if isinstance(player.color_name, str) else player.color_name.name(),
            "accent_color": _color_to_hex(player.color),
            "result": result,
            "result_label": RESULT_LABELS.get(result, result.title()),
            "money_spent": player.spent_credit,
            "money_mined": player.harvested_credits,
            "money_from_captures": player.captured_building_credits,
            "total_cash_seen": total_cash_seen,
            "current_balance": player.balance,
            "total_units_made": sum(built_units.values()),
            "total_units_killed": sum(killed_units.values()),
            "total_units_remaining": sum(current_units.values()),
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
        self.setIconSize(QSize(36, 28))
        self.setMinimumHeight(150)
        self.setMaximumHeight(220)
        self.populate(rows)

    def populate(self, rows):
        table_rows = rows or [("None", 0)]
        self.setRowCount(len(table_rows))
        for row_index, (unit_name, count) in enumerate(table_rows):
            unit_item = QTableWidgetItem(_display_name(unit_name))
            icon_path = resolve_factory_image_path(unit_name)
            pixmap = _load_pixmap(icon_path, 34, 26)
            if pixmap is not None:
                unit_item.setIcon(QIcon(pixmap))
            count_item = QTableWidgetItem(f"{count:,}")
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.setItem(row_index, 0, unit_item)
            self.setItem(row_index, 1, count_item)


class PlayerReportCard(QFrame):
    def __init__(self, player_snapshot):
        super().__init__()
        self.player_snapshot = player_snapshot
        self.setObjectName("playerCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        identity = QHBoxLayout()
        identity.setSpacing(12)

        flag_label = QLabel()
        flag_label.setObjectName("flagBadge")
        flag_pixmap = _load_pixmap(_country_flag_path(self.player_snapshot["country"]), 56, 38)
        if flag_pixmap is not None:
            flag_label.setPixmap(flag_pixmap)
        else:
            flag_label.setText(self.player_snapshot["faction"][:2].upper())
            flag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        identity.addWidget(flag_label)

        title_block = QVBoxLayout()
        title = QLabel(self.player_snapshot["username"])
        title.setObjectName("playerName")
        title.setStyleSheet(f'color: {self.player_snapshot["accent_color"]};')
        title_block.addWidget(title)

        subtitle = QLabel(
            f'{self.player_snapshot["result_label"]} | {self.player_snapshot["faction"]} | {self.player_snapshot["color_name"]}'
        )
        subtitle.setObjectName("playerMeta")
        title_block.addWidget(subtitle)
        identity.addLayout(title_block)
        header.addLayout(identity)
        header.addStretch()

        if self.player_snapshot["result"] != "ACTIVE":
            badge = QLabel(self.player_snapshot["result_label"])
            badge.setObjectName("resultBadge")
            badge.setProperty("result", self.player_snapshot["result"])
            header.addWidget(badge)
        layout.addLayout(header)

        layout.addWidget(self._make_highlight_strip())

        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(10)
        summary_items = [
            ("Money mined", _format_money(self.player_snapshot["money_mined"])),
            ("Money from captures", _format_money(self.player_snapshot["money_from_captures"])),
            ("Money spent", _format_money(self.player_snapshot["money_spent"])),
            ("Cash left", _format_money(self.player_snapshot["current_balance"])),
            ("Total cash seen", _format_money(self.player_snapshot["total_cash_seen"])),
            ("Built", f'{self.player_snapshot["total_units_made"]:,}'),
            ("Destroyed", f'{self.player_snapshot["total_units_killed"]:,}'),
            ("Still alive", f'{self.player_snapshot["total_units_remaining"]:,}'),
            ("Country", self.player_snapshot["country"] or "Unknown"),
        ]
        for index, (label_text, value_text) in enumerate(summary_items):
            cell = self._make_metric_cell(label_text, value_text)
            metrics.addWidget(cell, index // 3, index % 3)
        layout.addLayout(metrics)
        layout.addWidget(self._make_category_breakdown())

        tables_layout = QHBoxLayout()
        tables_layout.setSpacing(12)
        tables_layout.addWidget(self._make_table_block("Built", self.player_snapshot["units_made"]))
        tables_layout.addWidget(self._make_table_block("Destroyed", self.player_snapshot["units_killed"]))
        tables_layout.addWidget(self._make_table_block("Still Alive", self.player_snapshot["units_remaining"]))
        layout.addLayout(tables_layout)

        accent = self.player_snapshot["accent_color"]
        self.setStyleSheet(
            f"""
            QFrame#playerCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(34, 7, 7, 235),
                    stop:1 rgba(13, 7, 7, 245));
                border: 2px solid {accent};
                border-radius: 14px;
            }}
            """
        )

    def _make_metric_cell(self, label_text, value_text):
        cell = QFrame()
        cell.setObjectName("metricCell")
        layout = QVBoxLayout(cell)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        label = QLabel(label_text)
        label.setObjectName("metricLabel")
        value = QLabel(value_text)
        value.setObjectName("metricValue")
        layout.addWidget(label)
        layout.addWidget(value)
        return cell

    def _make_highlight_strip(self):
        strip = QFrame()
        strip.setObjectName("highlightStrip")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        sections = [
            ("Built the most", self.player_snapshot["units_made"][:3]),
            ("Destroyed the most", self.player_snapshot["units_killed"][:3]),
            ("Still had", self.player_snapshot["units_remaining"][:3]),
        ]

        for title, rows in sections:
            layout.addWidget(self._make_icon_group(title, rows))

        return strip

    def _make_category_breakdown(self):
        strip = QFrame()
        strip.setObjectName("highlightStrip")
        layout = QHBoxLayout(strip)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

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
            block_layout.setContentsMargins(8, 8, 8, 8)
            block_layout.setSpacing(4)

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
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("iconGroupTitle")
        layout.addWidget(title_label)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(8)
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
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = _load_pixmap(resolve_factory_image_path(unit_name), 58, 42)
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
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title_label = QLabel(title)
        title_label.setObjectName("tableTitle")
        layout.addWidget(title_label)
        layout.addWidget(StatTable(title, rows))
        return block


class PostGameScoreboardWindow(QMainWindow):
    def __init__(self, snapshot):
        super().__init__()
        self.snapshot = snapshot
        self.setWindowTitle("Post-Game Scoreboard")
        self.resize(1600, 920)
        self._build_ui()

    def _build_ui(self):
        title_font = _load_ra_font(24)
        heading_font = _load_ra_font(12)
        body_font = QFont("Segoe UI", 10)
        background_path = _scoreboard_background_path()

        central = QWidget()
        central.setObjectName("scoreboardCentral")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        banner = QFrame()
        banner.setObjectName("banner")
        banner_layout = QVBoxLayout(banner)
        banner_layout.setContentsMargins(18, 14, 18, 14)
        banner_layout.setSpacing(4)

        title = QLabel("MATCH SUMMARY")
        title.setFont(title_font)
        title.setObjectName("mainTitle")
        banner_layout.addWidget(title)

        subtitle = QLabel("")
        subtitle.setObjectName("subTitle")
        subtitle.setFont(body_font)
        banner_layout.addWidget(subtitle)
        root.addWidget(banner)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setObjectName("scoreboardScroll")

        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)

        for index, player_snapshot in enumerate(self.snapshot["players"]):
            card = PlayerReportCard(player_snapshot)
            grid.addWidget(card, index // 2, index % 2)

        scroll.setWidget(content)
        root.addWidget(scroll)

        self.setStyleSheet(
            f"""
            QMainWindow, QWidget {{
                background-color: #090707;
                color: #f6dcc2;
            }}
            QWidget#scoreboardCentral {{
                background-image: {"none" if not background_path else f"url({background_path})"};
                background-position: center;
                background-repeat: no-repeat;
            }}
            QFrame#banner {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2b0909,
                    stop:0.5 #5c120f,
                    stop:1 #210707);
                border: 2px solid #d88f3f;
                border-radius: 16px;
            }}
            QLabel#mainTitle {{
                color: #ffd486;
                letter-spacing: 2px;
            }}
            QLabel#subTitle {{
                color: #d7b59a;
            }}
            QLabel#flagBadge {{
                min-width: 64px;
                min-height: 44px;
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(216, 143, 63, 0.55);
                border-radius: 8px;
                color: #ffe7a8;
                font-weight: 800;
            }}
            QLabel#playerName {{
                color: #ffe7a8;
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#playerMeta {{
                color: #d0aaa0;
                font-size: 11px;
                text-transform: uppercase;
            }}
            QLabel#resultBadge {{
                padding: 8px 12px;
                border-radius: 10px;
                font-weight: 800;
                min-width: 88px;
                text-align: center;
            }}
            QLabel#resultBadge[result="WINNER"] {{
                background-color: #214d21;
                color: #aff0a7;
                border: 1px solid #66c766;
            }}
            QLabel#resultBadge[result="DEFEATED"] {{
                background-color: #5a1111;
                color: #ffb0a4;
                border: 1px solid #ff6f61;
            }}
            QLabel#resultBadge[result="ACTIVE"] {{
                background-color: #40351a;
                color: #f7df9a;
                border: 1px solid #d8b65c;
            }}
            QFrame#metricCell, QFrame#tableBlock {{
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(216, 143, 63, 0.35);
                border-radius: 10px;
            }}
            QFrame#highlightStrip {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 196, 80, 0.10),
                    stop:0.5 rgba(255, 120, 84, 0.08),
                    stop:1 rgba(255, 196, 80, 0.10));
                border: 1px solid rgba(216, 143, 63, 0.35);
                border-radius: 10px;
            }}
            QFrame#iconGroup {{
                background-color: rgba(0, 0, 0, 0.12);
                border: 1px solid rgba(216, 143, 63, 0.25);
                border-radius: 10px;
            }}
            QLabel#iconGroupTitle {{
                color: #ffcf76;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
            }}
            QFrame#unitChip {{
                background-color: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(216, 143, 63, 0.30);
                border-radius: 8px;
                min-width: 86px;
                max-width: 100px;
            }}
            QLabel#unitChipName {{
                color: #f4d6ba;
                font-size: 10px;
            }}
            QLabel#unitChipCount {{
                color: #fff3c6;
                font-size: 12px;
                font-weight: 800;
            }}
            QLabel#emptyChip, QLabel#fallbackIcon {{
                color: #f0d0a6;
                font-weight: 700;
            }}
            QLabel#metricLabel {{
                color: #d3ac8b;
                font-size: 10px;
                text-transform: uppercase;
            }}
            QLabel#metricValue {{
                color: #fff3c6;
                font-size: 16px;
                font-weight: 700;
            }}
            QLabel#tableTitle {{
                color: #ffcf76;
                font-size: 12px;
                font-weight: 700;
                padding-left: 2px;
            }}
            QHeaderView::section {{
                background-color: #5b140f;
                color: #ffd486;
                border: none;
                padding: 6px;
                font-weight: 700;
            }}
            QTableWidget {{
                background-color: rgba(0, 0, 0, 0.15);
                alternate-background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(216, 143, 63, 0.25);
                border-radius: 8px;
                gridline-color: transparent;
                color: #f7e4d0;
                padding: 4px;
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QScrollArea#scoreboardScroll {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: #1a0b0b;
                width: 12px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: #7f2318;
                min-height: 30px;
                border-radius: 6px;
            }}
            """
        )

        central.setFont(heading_font)
