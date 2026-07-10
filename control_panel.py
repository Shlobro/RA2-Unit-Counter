import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QFormLayout, QGroupBox,
    QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox,
    QColorDialog, QFontComboBox, QScrollArea, QSizePolicy, QTextEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase
import logging
import os

from UnitWindow import CombinedHudWindow
from hud_position_utils import normalize_position
from scoreboard_window import PostGameScoreboardWindow, load_scoreboard_payload_from_file
from selected_units_utils import load_selected_units_file, save_selected_units_file


def _load_futured_family():
    font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
    families = QFontDatabase.applicationFontFamilies(font_id)
    return families[0] if families else 'Arial'


class ControlPanel(QMainWindow):
    DEFAULT_COLOR_LABELS = {
        'name': 'Default (Player color)',
        'money': 'Default (Use player color)',
        'money_spent': 'Default (#76b5c5)',
        'power_good': 'Default (Green)',
        'power_low': 'Default (Red)',
        'game_time': 'Default (#ffffff)',
        'map_name': 'Default (#ffffff)',
    }
    BACKGROUND_WIDGET_LABELS = {
        'name': 'Name',
        'flag': 'Flag',
        'money': 'Money',
        'money_spent': 'Money Spent',
        'power': 'Power',
        'game_time': 'Game Time',
        'map_name': 'Map Name',
    }
    BACKGROUND_DEFAULT_SIZES = {
        'name': (240, 48),
        'flag': (64, 48),
        'money': (200, 48),
        'money_spent': (220, 48),
        'power': (180, 48),
        'game_time': (180, 48),
        'map_name': (300, 48),
    }
    DEFAULT_BACKGROUND_COLOR = '#A0000000'

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.default_color_settings = self._capture_default_color_settings()
        # Load selected units into state.
        self.state.selected_units_dict = self.load_selected_units()

        self.setWindowTitle("HUD Control Panel")
        self.setGeometry(100, 100, 620, 650)
        self.restore_saved_position()
        self._apply_dark_theme()

        # Create a tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create individual tabs
        self.create_general_settings_tab()
        self.create_name_flag_money_tab()
        self.create_unit_settings_tab()
        self.create_factory_settings_tab()
        self.create_superweapon_settings_tab()
        self.create_scoreboard_settings_tab()
        self.create_help_tab()

        self.unit_selection_window = None

        # Store reference in state so other modules can access control panel settings.
        self.state.control_panel = self

    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 13px;
            }
            QTabWidget::pane {
                border: 1px solid #2d2d4e;
                background-color: #16213e;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #0f3460;
                color: #a0a0c0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #e94560;
                color: #ffffff;
                font-weight: 700;
            }
            QTabBar::tab:hover:!selected {
                background-color: #1a4a8a;
                color: #e0e0e0;
            }
            QGroupBox {
                border: 1px solid #2d2d4e;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: 600;
                color: #c0c0e0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 6px;
                color: #e94560;
            }
            QLabel {
                color: #c0c0e0;
            }
            QSpinBox, QComboBox, QLineEdit, QFontComboBox {
                background-color: #0f3460;
                color: #e0e0e0;
                border: 1px solid #2d2d4e;
                border-radius: 5px;
                padding: 4px 8px;
                min-height: 24px;
            }
            QSpinBox:focus, QComboBox:focus, QLineEdit:focus, QFontComboBox:focus {
                border: 1px solid #e94560;
            }
            QSpinBox:disabled, QComboBox:disabled, QLineEdit:disabled, QFontComboBox:disabled {
                background-color: #12122a;
                color: #444466;
                border-color: #1e1e38;
            }
            QCheckBox:disabled {
                color: #444466;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #1a4a8a;
                border-top-right-radius: 5px;
                border-bottom-right-radius: 5px;
                width: 24px;
            }
            QComboBox QAbstractItemView {
                background-color: #0f3460;
                color: #e0e0e0;
                selection-background-color: #e94560;
                border: 1px solid #2d2d4e;
            }
            QPushButton {
                background-color: #0f3460;
                color: #e0e0e0;
                border: 1px solid #2d2d4e;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 500;
                min-height: 28px;
            }
            QPushButton:hover {
                background-color: #e94560;
                color: #ffffff;
                border-color: #e94560;
            }
            QPushButton:pressed {
                background-color: #c73652;
            }
            QCheckBox {
                color: #c0c0e0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #2d2d4e;
                background-color: #0f3460;
            }
            QCheckBox::indicator:checked {
                background-color: #e94560;
                border-color: #e94560;
                image: url(none);
            }
            QCheckBox::indicator:hover {
                border-color: #e94560;
            }
            QScrollArea {
                background-color: #16213e;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background-color: #0f3460;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #e94560;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: #1a1a2e;
                height: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal {
                background-color: #0f3460;
                border-radius: 5px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: #e94560;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)

    def _get_futured_family(self):
        if not hasattr(self, '_futured_family'):
            self._futured_family = _load_futured_family()
        return self._futured_family

    def _create_font_control_row(self, combo_attr, state_key, update_handler):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        combo = QFontComboBox()
        combo.setEditable(True)
        combo.lineEdit().setPlaceholderText("Search fonts...")
        saved = self.state.hud_positions.get(state_key, self._get_futured_family())
        combo.setCurrentFont(QFont(saved))
        combo.currentFontChanged.connect(lambda f: update_handler(f.family()))
        setattr(self, combo_attr, combo)
        layout.addWidget(combo)

        default_btn = QPushButton("Default")
        default_btn.clicked.connect(lambda: self._reset_font(combo_attr, state_key, update_handler))
        layout.addWidget(default_btn)

        return row

    def _reset_font(self, combo_attr, state_key, update_handler):
        family = self._get_futured_family()
        self.state.hud_positions[state_key] = family
        combo = getattr(self, combo_attr)
        combo.blockSignals(True)
        combo.setCurrentFont(QFont(family))
        combo.blockSignals(False)
        update_handler(family)

    def _wrap_in_scroll_area(self, widget):
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        return scroll

    def restore_saved_position(self):
        saved_position = self.state.hud_positions.get('control_panel_position')
        if not saved_position:
            return

        normalized_position = normalize_position(saved_position)
        self.move(normalized_position['x'], normalized_position['y'])

    def _capture_default_color_settings(self):
        return {
            'name': {
                'mode': self.state.hud_positions.get('name_color_mode', 'default'),
                'color': self.state.hud_positions.get('name_color'),
            },
            'money': {
                'mode': self.state.hud_positions.get('money_color_mode', 'default'),
                'color': self.state.hud_positions.get('money_custom_color'),
                'legacy_mode': self.state.hud_positions.get('money_color', 'Use player color'),
            },
            'money_spent': {
                'mode': self.state.hud_positions.get('money_spent_color_mode', 'default'),
                'color': self.state.hud_positions.get('money_spent_color'),
            },
            'power': {
                'mode': self.state.hud_positions.get('power_color_mode', 'default'),
                'color': self.state.hud_positions.get('power_custom_color'),
            },
            'game_time': {
                'mode': self.state.hud_positions.get('game_time_color_mode', 'custom'),
                'color': self.state.hud_positions.get('game_time_color', '#FFFFFF'),
            },
            'map_name': {
                'mode': self.state.hud_positions.get('map_name_color_mode', 'custom'),
                'color': self.state.hud_positions.get('map_name_color', '#FFFFFF'),
            },
        }

    def _get_default_setting(self, key):
        return self.default_color_settings.get(key, {})

    def _make_help_badge(self, tooltip):
        help_label = QLabel("?")
        help_label.setToolTip(tooltip)
        help_label.setFixedSize(18, 18)
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet(
            "QLabel { background-color: #0f3460; color: #a0a0c0; border: 1px solid #2d2d4e;"
            " border-radius: 9px; font-size: 11px; font-weight: bold; }"
            "QLabel:hover { background-color: #e94560; color: #ffffff; }"
        )
        return help_label

    def _with_help(self, widget, tooltip):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(widget)
        help_label = QLabel("?")
        help_label.setToolTip(tooltip)
        help_label.setFixedSize(18, 18)
        help_label.setAlignment(Qt.AlignCenter)
        help_label.setStyleSheet(
            "QLabel { background-color: #0f3460; color: #a0a0c0; border: 1px solid #2d2d4e;"
            " border-radius: 9px; font-size: 11px; font-weight: bold; }"
            "QLabel:hover { background-color: #e94560; color: #ffffff; }"
        )
        layout.addWidget(help_label)
        layout.addStretch()
        return row

    def _create_color_control_row(self, button_attr, choose_handler, reset_handler):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        color_button = QPushButton()
        color_button.clicked.connect(choose_handler)
        setattr(self, button_attr, color_button)
        layout.addWidget(color_button)

        default_button = QPushButton("Default")
        default_button.clicked.connect(reset_handler)
        layout.addWidget(default_button)

        return row

    def _set_color_button_state(self, button, color_value, default_label, custom_mode):
        if custom_mode:
            color = QColor(color_value)
            if not color.isValid():
                color = QColor('#FFFFFF')
            color_name = self._color_to_storage(color)
            button.setProperty('selected_color', color_name)
            button.setProperty('custom_mode', True)
            button.setText(color_name)
            button.setStyleSheet(
                f"background-color: {color_name}; color: {'#000000' if color.lightness() > 128 else '#FFFFFF'};"
            )
            return

        button.setProperty('selected_color', '')
        button.setProperty('custom_mode', False)
        button.setText(default_label)
        button.setStyleSheet("")

    def _color_to_storage(self, color):
        if isinstance(color, QColor):
            return color.name(QColor.HexArgb)
        resolved = QColor(color)
        return resolved.name(QColor.HexArgb) if resolved.isValid() else self.DEFAULT_BACKGROUND_COLOR

    def _get_background_default_size(self, prefix):
        return self.BACKGROUND_DEFAULT_SIZES.get(prefix, (180, 48))

    def _set_background_color_button(self, prefix):
        button = getattr(self, f'{prefix}_background_color_button')
        color_value = self.state.hud_positions.get(f'{prefix}_background_color', self.DEFAULT_BACKGROUND_COLOR)
        self._set_color_button_state(
            button,
            color_value,
            f"Default ({self.DEFAULT_BACKGROUND_COLOR})",
            True,
        )

    def _sync_background_controls_enabled(self, prefix):
        enabled = self.state.hud_positions.get(f'{prefix}_background_enabled', False)
        for attr in (
            f'{prefix}_background_color_button',
            f'{prefix}_background_width_spinbox',
            f'{prefix}_background_height_spinbox',
        ):
            widget = getattr(self, attr, None)
            if widget is not None:
                widget.setEnabled(enabled)

    def _choose_background_color(self, prefix):
        initial = QColor(self.state.hud_positions.get(f'{prefix}_background_color', self.DEFAULT_BACKGROUND_COLOR))
        color = QColorDialog.getColor(initial, self, f"Select {self.BACKGROUND_WIDGET_LABELS[prefix]} Background Color", QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self._update_background_color(prefix, color)

    def _reset_background_color(self, prefix):
        self.state.hud_positions[f'{prefix}_background_color'] = self.DEFAULT_BACKGROUND_COLOR
        self._set_background_color_button(prefix)
        self._apply_background_settings(prefix)

    def _update_background_color(self, prefix, color_value):
        color = QColor(color_value)
        if not color.isValid():
            return
        self.state.hud_positions[f'{prefix}_background_color'] = self._color_to_storage(color)
        self._set_background_color_button(prefix)
        self._apply_background_settings(prefix)

    def _update_background_dimension(self, prefix, dimension, value):
        self.state.hud_positions[f'{prefix}_background_{dimension}'] = int(value)
        self._apply_background_settings(prefix)

    def _toggle_background_enabled(self, prefix, state_val):
        enabled = (state_val == 2)
        self.state.hud_positions[f'{prefix}_background_enabled'] = enabled
        self._sync_background_controls_enabled(prefix)
        self._apply_background_settings(prefix)

    def _apply_player_widget_background(self, prefix):
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                if hasattr(combined_window, 'resource_widget'):
                    combined_window.resource_widget.apply_widget_background(prefix)
        else:
            for _, resource_window in self.state.hud_windows:
                if resource_window is not None:
                    resource_window.apply_widget_background(prefix)

    def _apply_global_widget_background(self, prefix):
        widget_attr = f'{prefix}_widget'
        workspace_attr = f'{prefix}_workspace_item'
        window_attr = f'{prefix}_window'
        if self.state.hud_positions.get('combined_hud', False):
            widget = getattr(self.state, widget_attr, None)
            if widget is not None and hasattr(widget, 'configure_background'):
                widget.configure_background(
                    enabled=self.state.hud_positions.get(f'{prefix}_background_enabled', False),
                    color=self.state.hud_positions.get(f'{prefix}_background_color', self.DEFAULT_BACKGROUND_COLOR),
                    width=self.state.hud_positions.get(f'{prefix}_background_width', 0),
                    height=self.state.hud_positions.get(f'{prefix}_background_height', 0),
                )
            item = getattr(self.state, workspace_attr, None)
            if item is not None and hasattr(item, '_queue_sync_to_inner'):
                item._queue_sync_to_inner()
        else:
            window = getattr(self.state, window_attr, None)
            if window is not None and hasattr(window, 'update_background_settings'):
                window.update_background_settings()

    def _apply_background_settings(self, prefix):
        if prefix in ('game_time', 'map_name'):
            self._apply_global_widget_background(prefix)
        else:
            self._apply_player_widget_background(prefix)

    def _add_background_controls(self, form_layout, prefix):
        width_default, height_default = self._get_background_default_size(prefix)
        self.state.hud_positions.setdefault(f'{prefix}_background_enabled', False)
        self.state.hud_positions.setdefault(f'{prefix}_background_color', self.DEFAULT_BACKGROUND_COLOR)
        self.state.hud_positions.setdefault(f'{prefix}_background_width', width_default)
        self.state.hud_positions.setdefault(f'{prefix}_background_height', height_default)

        checkbox = QCheckBox("Show Background")
        checkbox.setChecked(self.state.hud_positions.get(f'{prefix}_background_enabled', False))
        checkbox.stateChanged.connect(lambda state_val, p=prefix: self._toggle_background_enabled(p, state_val))
        setattr(self, f'{prefix}_background_checkbox', checkbox)
        form_layout.addRow(self._with_help(
            checkbox,
            "Draw a solid rectangle behind this widget so text and numbers remain readable over the game."
        ))

        color_row = self._create_color_control_row(
            f'{prefix}_background_color_button',
            lambda p=prefix: self._choose_background_color(p),
            lambda p=prefix: self._reset_background_color(p),
        )
        self._set_background_color_button(prefix)
        form_layout.addRow("Background Color:", color_row)

        width_spinbox = QSpinBox()
        width_spinbox.setRange(1, 1200)
        width_spinbox.setValue(self.state.hud_positions.get(f'{prefix}_background_width', width_default))
        width_spinbox.valueChanged.connect(lambda value, p=prefix: self._update_background_dimension(p, 'width', value))
        setattr(self, f'{prefix}_background_width_spinbox', width_spinbox)
        form_layout.addRow("Background Width:", width_spinbox)

        height_spinbox = QSpinBox()
        height_spinbox.setRange(1, 1200)
        height_spinbox.setValue(self.state.hud_positions.get(f'{prefix}_background_height', height_default))
        height_spinbox.valueChanged.connect(lambda value, p=prefix: self._update_background_dimension(p, 'height', value))
        setattr(self, f'{prefix}_background_height_spinbox', height_spinbox)
        form_layout.addRow("Background Height:", height_spinbox)

        self._sync_background_controls_enabled(prefix)

    def _get_first_resource_window(self):
        for _, resource_window in self.state.hud_windows:
            if resource_window is not None:
                return resource_window
        return None

    def _get_live_widget_color(self, attr_name, fallback):
        resource_window = self._get_first_resource_window()
        if resource_window is not None and hasattr(resource_window, attr_name):
            widget = getattr(resource_window, attr_name)
            color = getattr(widget, 'text_color', None)
            if color is not None:
                resolved = QColor(color)
                if resolved.isValid():
                    return resolved
        return QColor(fallback)

    def _get_name_picker_initial_color(self):
        custom_color = self.state.hud_positions.get('name_color')
        if self.state.hud_positions.get('name_color_mode') == 'custom' and custom_color:
            return QColor(custom_color)
        return self._get_live_widget_color('name_widget', '#FFFFFF')

    def _get_money_picker_initial_color(self):
        custom_color = self.state.hud_positions.get('money_custom_color')
        if self.state.hud_positions.get('money_color_mode') == 'custom' and custom_color:
            return QColor(custom_color)
        return self._get_live_widget_color('money_widget', '#FFFFFF')

    def _get_money_spent_picker_initial_color(self):
        custom_color = self.state.hud_positions.get('money_spent_color')
        if self.state.hud_positions.get('money_spent_color_mode') == 'custom' and custom_color:
            return QColor(custom_color)
        return self._get_live_widget_color('money_spent_widget', '#76B5C5')

    def _get_power_picker_initial_color(self):
        custom_color = self.state.hud_positions.get('power_custom_color')
        if self.state.hud_positions.get('power_color_mode') == 'custom' and custom_color:
            return QColor(custom_color)
        return self._get_live_widget_color('power_widget', '#00FF00')

    def create_unit_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        separate = self.state.hud_positions.get('separate_unit_counters', False)

        # ── General ──────────────────────────────────────────────
        general_group = QGroupBox("General")
        general_layout = QFormLayout()

        self.unit_frame_checkbox = QCheckBox("Show Unit Frames")
        self.unit_frame_checkbox.setChecked(self.state.hud_positions.get('show_unit_frames', True))
        self.unit_frame_checkbox.stateChanged.connect(self.toggle_unit_frames)
        general_layout.addRow(self._with_help(self.unit_frame_checkbox,
            "Show a decorative border/frame around each unit cameo image in the counter.\n"
            "The frame color matches the player's in-game color."))

        layout_label = QLabel("Layout:")
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Vertical", "Horizontal"])
        self.layout_combo.setCurrentText(self.state.hud_positions.get('unit_layout', 'Vertical'))
        self.layout_combo.currentTextChanged.connect(self.update_layout)
        general_layout.addRow(layout_label, self.layout_combo)

        distance_images_label = QLabel("Spacing Between Images:")
        self.distance_images_spinbox = QSpinBox()
        self.distance_images_spinbox.setRange(0, 150)
        self.distance_images_spinbox.setValue(self.state.hud_positions.get('distance_between_images', 0))
        self.distance_images_spinbox.valueChanged.connect(self.update_distance_between_images)
        general_layout.addRow(distance_images_label, self.distance_images_spinbox)

        selection_button = QPushButton("Select Units")
        selection_button.clicked.connect(self.open_unit_selection)
        general_layout.addRow(selection_button)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # ── Combined Mode ─────────────────────────────────────────
        self.combined_mode_group = QGroupBox("Combined Counter Mode")
        combined_layout = QFormLayout()

        counter_size = self.state.hud_positions.get('unit_counter_size', 75)
        self.counter_size_spinbox = QSpinBox()
        self.counter_size_spinbox.setRange(5, 250)
        self.counter_size_spinbox.setValue(counter_size)
        self.counter_size_spinbox.valueChanged.connect(self.update_unit_window_size)
        combined_layout.addRow("Counter Size:", self.counter_size_spinbox)

        self.combined_mode_group.setLayout(combined_layout)
        layout.addWidget(self.combined_mode_group)

        # ── Separate Mode ─────────────────────────────────────────
        self.separate_mode_group = QGroupBox("Separate Counter Mode")
        separate_layout = QFormLayout()

        image_size = self.state.hud_positions.get('image_size', 75)
        self.image_size_spinbox = QSpinBox()
        self.image_size_spinbox.setRange(5, 250)
        self.image_size_spinbox.setValue(image_size)
        self.image_size_spinbox.valueChanged.connect(self.update_image_size)
        separate_layout.addRow("Image Size:", self.image_size_spinbox)

        number_size = self.state.hud_positions.get('number_size', 75)
        self.number_size_spinbox = QSpinBox()
        self.number_size_spinbox.setRange(5, 250)
        self.number_size_spinbox.setValue(number_size)
        self.number_size_spinbox.valueChanged.connect(self.update_number_size)
        separate_layout.addRow("Number Size:", self.number_size_spinbox)

        distance = self.state.hud_positions.get('distance_between_numbers', 0)
        self.distance_spinbox = QSpinBox()
        self.distance_spinbox.setRange(0, 150)
        self.distance_spinbox.setValue(distance)
        self.distance_spinbox.valueChanged.connect(self.update_distance_between_numbers)
        separate_layout.addRow("Spacing Between Numbers:", self.distance_spinbox)

        self.separate_units_checkbox = QCheckBox("Separate Unit Counters")
        self.separate_units_checkbox.setChecked(separate)
        self.separate_units_checkbox.stateChanged.connect(self.toggle_separate_unit_counters)
        separate_layout.insertRow(0, self._with_help(self.separate_units_checkbox,
            "Split the unit counter into two separate windows: one for unit images and one for numbers.\n"
            "Enables independent sizing of images and numbers."))

        self.separate_mode_group.setLayout(separate_layout)
        layout.addWidget(self.separate_mode_group)

        layout.addStretch()
        tab.setLayout(layout)
        self.tabs.addTab(self._wrap_in_scroll_area(tab), "Units")

        self._update_unit_mode_groups(separate)

    def update_image_size(self):
        new_size = self.image_size_spinbox.value()
        self.state.hud_positions['image_size'] = new_size
        logging.info(f"Updated image size to {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                # Assume your combined window has an update_unit_counters_size method.
                combined_window.update_unit_counters_size(new_size, section='images')
        else:
            for unit_window, _ in self.state.hud_windows:
                if unit_window:
                    if isinstance(unit_window, tuple):
                        img_win, _ = unit_window
                        img_win.update_all_counters_size(new_size)
                    else:
                        unit_window.update_all_counters_size(new_size)

    def update_number_size(self):
        new_size = self.number_size_spinbox.value()
        self.state.hud_positions['number_size'] = new_size
        logging.info(f"Updated number size to {new_size}")
        # Update number counters in all HUD windows.
        for unit_window, resource_window in self.state.hud_windows:
            if unit_window and isinstance(unit_window, tuple):
                # Separate mode: the tuple holds (image_window, number_window)
                _, num_win = unit_window
                num_win.update_all_counters_size(new_size)
            elif unit_window:
                # Combined mode or single unit window
                if hasattr(unit_window, 'update_unit_counters_size'):
                    unit_window.update_unit_counters_size(new_size, section='numbers')
                else:
                    unit_window.update_all_counters_size(new_size)

    def toggle_unit_frames(self, state_val):
        self.state.hud_positions['show_unit_frames'] = (state_val != 0)
        logging.info(f"Toggled show_unit_frames to: {self.state.hud_positions['show_unit_frames']}")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                for combined_window, _ in self.state.hud_windows:
                    combined_window.update_show_unit_frames(self.state.hud_positions['show_unit_frames'])
            else:
                for unit_window, _ in self.state.hud_windows:
                    if unit_window:
                        if isinstance(unit_window, tuple):
                            for uw in unit_window:
                                uw.update_show_unit_frames(self.state.hud_positions['show_unit_frames'])
                        else:
                            unit_window.update_show_unit_frames(self.state.hud_positions['show_unit_frames'])

    def toggle_combined_hud(self, state_val):
        self.state.hud_positions['combined_hud'] = (state_val != 0)
        logging.info(f"Toggled combined_hud to: {self.state.hud_positions['combined_hud']}")

        if self.state.hud_windows:
            for unit_window, resource_window in self.state.hud_windows:
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.close()
                    else:
                        unit_window.close()
                if resource_window:
                    if hasattr(resource_window, 'windows') and resource_window.windows:
                        for window in resource_window.windows:
                            window.close()
                    else:
                        resource_window.close()

        from hud_manager import create_hud_windows
        create_hud_windows(self.state)

    def toggle_single_window_always_on_top(self, state_val):
        enabled = (state_val != 0)
        self.state.hud_positions['single_window_always_on_top'] = enabled
        logging.info(f"Toggled single_window_always_on_top to: {enabled}")

        workspace = getattr(self.state, 'single_window_workspace', None)
        if workspace is not None and hasattr(workspace, 'save_layout_to_state'):
            workspace.save_layout_to_state()

        try:
            from hud_manager import save_hud_positions
            save_hud_positions(self.state)
        except Exception as save_error:
            logging.exception("Error saving HUD positions before topmost toggle: %s", save_error)

        if workspace is not None and hasattr(workspace, 'set_always_on_top'):
            workspace.set_always_on_top(enabled)

    def toggle_player_number_mode(self, state_val):
        enabled = (state_val != 0)
        self.state.hud_positions['use_player_numbers'] = enabled
        logging.info(f"Toggled use_player_numbers to: {enabled}")

        from hud_manager import create_hud_windows
        create_hud_windows(self.state)

    def update_reserved_player_name(self, slot, text):
        key = f'player_{slot}_name'
        value = text.strip()
        self.state.hud_positions[key] = value
        logging.info(f"Updated reserved player name for Player {slot}: {value!r}")

        if self.state.hud_windows:
            from hud_manager import create_hud_windows
            create_hud_windows(self.state)

    def update_flag_widget_size(self):
        new_size = self.flag_size_spinbox.value()
        self.state.hud_positions['flag_widget_size'] = new_size
        logging.info(f"Updated flag widget size: {new_size}")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                for combined_window, _ in self.state.hud_windows:
                    combined_window.resource_widget.flag_widget.update_data_size(new_size)
                    combined_window.resource_widget.export_flag_image_if_needed()
            else:
                for _, resource_window in self.state.hud_windows:
                    resource_window.flag_widget.update_data_size(new_size)
                    resource_window.export_flag_image_if_needed()



    def _update_unit_mode_groups(self, separate):
        self.combined_mode_group.setEnabled(not separate)
        for w in (self.image_size_spinbox, self.number_size_spinbox, self.distance_spinbox):
            w.setEnabled(separate)
        self.combined_mode_group.setStyleSheet(
            "QGroupBox { color: #e94560; }" if not separate
            else "QGroupBox { color: #555577; border-color: #2a2a3e; } QGroupBox * { color: #555577; }"
        )
        self.separate_mode_group.setStyleSheet(
            "QGroupBox { color: #e94560; }" if separate
            else "QGroupBox { color: #555577; border-color: #2a2a3e; } QGroupBox * { color: #555577; }"
        )

    def toggle_separate_unit_counters(self, state_val):

        separate = (state_val != 0)
        self.state.hud_positions['separate_unit_counters'] = separate
        logging.info(f"Toggled separate_unit_counters to: {separate}")
        self._update_unit_mode_groups(separate)

        # Do a full recreation in both modes to avoid duplicates (same as combined toggle):
        from hud_manager import create_hud_windows
        # Close and recreate everything
        if self.state.hud_windows:
            for unit_window, resource_window in self.state.hud_windows:
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.close()
                    else:
                        unit_window.close()
                if resource_window:
                    if hasattr(resource_window, 'windows') and resource_window.windows:
                        for window in resource_window.windows:
                            window.close()
                    else:
                        resource_window.close()
        
        create_hud_windows(self.state)

    def create_name_flag_money_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Name Settings
        name_group = QGroupBox("Player Name Settings")
        name_layout = QFormLayout()
        self.name_checkbox = QCheckBox("Show Name")
        self.name_checkbox.setChecked(self.state.hud_positions.get('show_name', True))
        self.name_checkbox.stateChanged.connect(self.toggle_name)
        name_layout.addRow(self._with_help(self.name_checkbox,
            "Show the player's in-game name on the HUD overlay."))
        name_size_label = QLabel("Player Name Size:")
        name_size = self.state.hud_positions.get('name_widget_size', 50)
        self.name_size_spinbox = QSpinBox()
        self.name_size_spinbox.setRange(5, 500)
        self.name_size_spinbox.setValue(name_size)
        self.name_size_spinbox.valueChanged.connect(self.update_name_widget_size)
        name_layout.addRow(name_size_label, self.name_size_spinbox)
        name_layout.addRow("Font:", self._create_font_control_row('name_font_combo', 'name_font_family', self.update_name_font))
        self.name_color_row = self._create_color_control_row(
            'name_color_button',
            self.choose_name_color,
            self.reset_name_color,
        )
        self._set_name_color_button()
        name_layout.addRow("Name Color:", self.name_color_row)
        self._add_background_controls(name_layout, 'name')
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        # Flag Settings
        flag_group = QGroupBox("Flag Settings")
        flag_layout = QFormLayout()
        self.flag_checkbox = QCheckBox("Show Flag")
        self.flag_checkbox.setChecked(self.state.hud_positions.get('show_flag', True))
        self.flag_checkbox.stateChanged.connect(self.toggle_flag)
        flag_layout.addRow(self._with_help(self.flag_checkbox,
            "Show the player's country/faction flag next to their name on the HUD."))
        flag_size_label = QLabel("Flag Size:")
        flag_size = self.state.hud_positions.get('flag_widget_size', 50)
        self.flag_size_spinbox = QSpinBox()
        self.flag_size_spinbox.setRange(5, 500)
        self.flag_size_spinbox.setValue(flag_size)
        self.flag_size_spinbox.valueChanged.connect(self.update_flag_widget_size)
        flag_layout.addRow(flag_size_label, self.flag_size_spinbox)
        self._add_background_controls(flag_layout, 'flag')
        flag_group.setLayout(flag_layout)
        layout.addWidget(flag_group)

        # Money Settings
        money_group = QGroupBox("Money Settings")
        money_layout = QFormLayout()
        self.money_checkbox = QCheckBox("Show Money")
        self.money_checkbox.setChecked(self.state.hud_positions.get('show_money', True))
        self.money_checkbox.stateChanged.connect(self.toggle_money)
        money_layout.addRow(self._with_help(self.money_checkbox,
            "Show the player's current credit balance on the HUD."))
        money_size_label = QLabel("Money Size:")
        money_size = self.state.hud_positions.get('money_widget_size', 50)
        self.money_size_spinbox = QSpinBox()
        self.money_size_spinbox.setRange(5, 500)
        self.money_size_spinbox.setValue(money_size)
        self.money_size_spinbox.valueChanged.connect(self.update_money_widget_size)
        money_layout.addRow(money_size_label, self.money_size_spinbox)
        money_layout.addRow("Font:", self._create_font_control_row('money_font_combo', 'money_font_family', self.update_money_font))
        self.money_color_row = self._create_color_control_row(
            'money_color_button',
            self.choose_money_color,
            self.reset_money_color,
        )
        self._set_money_color_button()
        money_layout.addRow("Money Color:", self.money_color_row)
        self._add_background_controls(money_layout, 'money')
        money_group.setLayout(money_layout)
        layout.addWidget(money_group)

        # Money Spent Settings
        money_spent_group = QGroupBox("Money Spent Settings")
        money_spent_layout = QFormLayout()
        self.money_spent_checkbox = QCheckBox("Show Money Spent")
        self.money_spent_checkbox.setChecked(self.state.hud_positions.get('show_money_spent', True))
        self.money_spent_checkbox.stateChanged.connect(self.toggle_money_spent)
        money_spent_layout.addRow(self._with_help(self.money_spent_checkbox,
            "Show a running total of how much money the player has spent during the match."))
        money_spent_size_label = QLabel("Money Spent Size:")
        money_spent_size = self.state.hud_positions.get('money_spent_widget_size', 50)
        self.money_spent_size_spinbox = QSpinBox()
        self.money_spent_size_spinbox.setRange(5, 500)
        self.money_spent_size_spinbox.setValue(money_spent_size)
        self.money_spent_size_spinbox.valueChanged.connect(self.update_money_spent_widget_size)
        money_spent_layout.addRow(money_spent_size_label, self.money_spent_size_spinbox)
        money_spent_layout.addRow("Font:", self._create_font_control_row('money_spent_font_combo', 'money_spent_font_family', self.update_money_spent_font))
        self.money_spent_color_row = self._create_color_control_row(
            'money_spent_color_button',
            self.choose_money_spent_color,
            self.reset_money_spent_color,
        )
        self._set_money_spent_color_button()
        money_spent_layout.addRow("Money Spent Color:", self.money_spent_color_row)
        self._add_background_controls(money_spent_layout, 'money_spent')
        money_spent_group.setLayout(money_spent_layout)
        layout.addWidget(money_spent_group)

        # Power Settings
        power_group = QGroupBox("Power Settings")
        power_layout = QFormLayout()
        self.power_checkbox = QCheckBox("Show Power")
        self.power_checkbox.setChecked(self.state.hud_positions.get('show_power', True))
        self.power_checkbox.stateChanged.connect(self.toggle_power)
        power_layout.addRow(self._with_help(self.power_checkbox,
            "Show the player's power balance (produced vs consumed).\n"
            "Turns red when the player is low on power."))
        power_size_label = QLabel("Power Size:")
        power_size = self.state.hud_positions.get('power_widget_size', 50)
        self.power_size_spinbox = QSpinBox()
        self.power_size_spinbox.setRange(5, 500)
        self.power_size_spinbox.setValue(power_size)
        self.power_size_spinbox.valueChanged.connect(self.update_power_widget_size)
        power_layout.addRow(power_size_label, self.power_size_spinbox)
        power_layout.addRow("Font:", self._create_font_control_row('power_font_combo', 'power_font_family', self.update_power_font))
        self.power_good_color_row = self._create_color_control_row(
            'power_good_color_button',
            self.choose_power_good_color,
            self.reset_power_good_color,
        )
        self._set_power_good_color_button()
        power_layout.addRow("Good Power Color:", self.power_good_color_row)

        self.power_low_color_row = self._create_color_control_row(
            'power_low_color_button',
            self.choose_power_low_color,
            self.reset_power_low_color,
        )
        self._set_power_low_color_button()
        power_layout.addRow("Low Power Color:", self.power_low_color_row)
        self._add_background_controls(power_layout, 'power')
        power_group.setLayout(power_layout)
        layout.addWidget(power_group)

        game_time_group = QGroupBox("Game Time Settings")
        game_time_layout = QFormLayout()
        self.game_time_checkbox = QCheckBox("Show Game Time")
        self.game_time_checkbox.setChecked(self.state.hud_positions.get('show_game_time', True))
        self.game_time_checkbox.stateChanged.connect(self.toggle_game_time)
        game_time_layout.addRow(self._with_help(self.game_time_checkbox,
            "Show the elapsed game time as a clock on the HUD overlay."))

        game_time_size_label = QLabel("Game Time Size:")
        game_time_size = self.state.hud_positions.get('game_time_widget_size', 50)
        self.game_time_size_spinbox = QSpinBox()
        self.game_time_size_spinbox.setRange(5, 500)
        self.game_time_size_spinbox.setValue(game_time_size)
        self.game_time_size_spinbox.valueChanged.connect(self.update_game_time_widget_size)
        game_time_layout.addRow(game_time_size_label, self.game_time_size_spinbox)

        game_time_layout.addRow("Font:", self._create_font_control_row('game_time_font_combo', 'game_time_font_family', self._update_game_time_font_family))

        self.game_time_color_row = self._create_color_control_row(
            'game_time_color_button',
            self.choose_game_time_color,
            self.reset_game_time_color,
        )
        self._set_game_time_color_button()
        game_time_layout.addRow("Game Time Color:", self.game_time_color_row)
        self._add_background_controls(game_time_layout, 'game_time')

        game_time_group.setLayout(game_time_layout)
        layout.addWidget(game_time_group)

        map_name_group = QGroupBox("Map Name Settings")
        map_name_layout = QFormLayout()
        self.map_name_checkbox = QCheckBox("Show Map Name")
        self.map_name_checkbox.setChecked(self.state.hud_positions.get('show_map_name', True))
        self.map_name_checkbox.stateChanged.connect(self.toggle_map_name)
        map_name_layout.addRow(self._with_help(self.map_name_checkbox,
            "Show the current map name on the HUD overlay."))

        map_name_size_label = QLabel("Map Name Size:")
        map_name_size = self.state.hud_positions.get('map_name_widget_size', 50)
        self.map_name_size_spinbox = QSpinBox()
        self.map_name_size_spinbox.setRange(5, 500)
        self.map_name_size_spinbox.setValue(map_name_size)
        self.map_name_size_spinbox.valueChanged.connect(self.update_map_name_widget_size)
        map_name_layout.addRow(map_name_size_label, self.map_name_size_spinbox)
        map_name_layout.addRow("Font:", self._create_font_control_row('map_name_font_combo', 'map_name_font_family', self.update_map_name_font))

        self.map_name_color_row = self._create_color_control_row(
            'map_name_color_button',
            self.choose_map_name_color,
            self.reset_map_name_color,
        )
        self._set_map_name_color_button()
        map_name_layout.addRow(QLabel("Map Name Color:"), self.map_name_color_row)
        self._add_background_controls(map_name_layout, 'map_name')

        map_name_group.setLayout(map_name_layout)
        layout.addWidget(map_name_group)

        tab.setLayout(layout)
        self.tabs.addTab(self._wrap_in_scroll_area(tab), "Widgets")

    def update_distance_between_numbers(self):
        new_distance = self.distance_spinbox.value()
        self.state.hud_positions['distance_between_numbers'] = new_distance
        logging.info(f"Updated distance between numbers: {new_distance}")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                for combined_window, _ in self.state.hud_windows:
                    # Only apply distance setting when separate unit counters are enabled
                    if self.state.hud_positions.get('separate_unit_counters', False):
                        if hasattr(combined_window, 'unit_widget_numbers'):
                            combined_window.unit_widget_numbers.update_spacing(new_distance)
            else:
                for unit_window, _ in self.state.hud_windows:
                    if unit_window and isinstance(unit_window, tuple):
                        _, unit_window_numbers = unit_window
                        unit_window_numbers.update_spacing(new_distance)

    def update_distance_between_images(self):
        new_distance = self.distance_images_spinbox.value()
        self.state.hud_positions['distance_between_images'] = new_distance
        logging.info(f"Updated distance between images: {new_distance}")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                for combined_window, _ in self.state.hud_windows:
                    if self.state.hud_positions.get('separate_unit_counters', False):
                        # Separate unit counters: apply to images widget only
                        if hasattr(combined_window, 'unit_widget_images'):
                            combined_window.unit_widget_images.update_spacing(new_distance)
                    else:
                        # Single combined unit widget: apply spacing to the combined widget
                        if hasattr(combined_window, 'unit_widget'):
                            combined_window.unit_widget.update_spacing(new_distance)
            else:
                for unit_window, _ in self.state.hud_windows:
                    if unit_window and isinstance(unit_window, tuple):
                        img_win, _ = unit_window
                        img_win.update_spacing(new_distance)
                    elif unit_window:
                        # Single unit window (non-separate mode)
                        unit_window.update_spacing(new_distance)

    # ------------------------- Factory stuff ------------------------------
    def create_factory_settings_tab(self):
        tab = QWidget()
        layout = QFormLayout()


        self.show_factory_queue_checkbox = QCheckBox("Show Factory Queue")
        show_factory_queue = self.state.hud_positions.get("show_factory_queue", True)
        self.show_factory_queue_checkbox.setChecked(show_factory_queue)
        self.show_factory_queue_checkbox.stateChanged.connect(self.toggle_factory_queue)
        layout.addRow(self._with_help(self.show_factory_queue_checkbox,
            "Show what unit is currently being built in each factory.\n"
            "Displays a queue of upcoming units with a progress indicator."))


        self.show_factory_checkbox = QCheckBox("Show Factory Window")
        show_factory_window = self.state.hud_positions.get("show_factory_window", True)
        self.show_factory_checkbox.setChecked(show_factory_window)
        self.show_factory_checkbox.stateChanged.connect(self.toggle_factory_window)
        layout.addRow(self._with_help(self.show_factory_checkbox,
            "Show the factory window panel on the HUD overlay.\n"
            "Displays each player's active production buildings."))


        factory_size_label = QLabel("Factory Size:")
        factory_size = self.state.hud_positions.get('factory_size', 100)
        self.factory_size_spinbox = QSpinBox()
        self.factory_size_spinbox.setRange(5, 250)
        self.factory_size_spinbox.setValue(factory_size)
        self.factory_size_spinbox.valueChanged.connect(self.update_factory_widget_size)
        layout.addRow(factory_size_label, self.factory_size_spinbox)


        factory_frame_label = QLabel("Show Factory Frames:")
        self.factory_frame_checkbox = QCheckBox()
        self.factory_frame_checkbox.setChecked(self.state.hud_positions.get('show_factory_frames', True))
        self.factory_frame_checkbox.stateChanged.connect(self.toggle_factory_frames)
        layout.addRow(factory_frame_label, self._with_help(self.factory_frame_checkbox,
            "Show a decorative border/frame around each factory cameo in the factory panel.\n"
            "The frame color matches the player's in-game color."))


        factory_layout_label = QLabel("Select Factory Layout:")
        self.factory_layout_combo = QComboBox()
        self.factory_layout_combo.addItems(["Vertical", "Horizontal"])
        factory_layout_type = self.state.hud_positions.get('factory_layout', 'Horizontal')
        self.factory_layout_combo.setCurrentText(factory_layout_type)
        self.factory_layout_combo.currentTextChanged.connect(self.update_factory_layout)
        layout.addRow(factory_layout_label, self.factory_layout_combo)

        tab.setLayout(layout)
        self.tabs.addTab(self._wrap_in_scroll_area(tab), "Factory")

    def create_superweapon_settings_tab(self):
        tab = QWidget()
        layout = QFormLayout()

        self.show_superweapon_panel_checkbox = QCheckBox("Show Superweapon Counters")
        show_superweapons = self.state.hud_positions.get("show_superweapons", True)
        self.show_superweapon_panel_checkbox.setChecked(show_superweapons)
        self.show_superweapon_panel_checkbox.stateChanged.connect(self.toggle_superweapons)
        layout.addRow(self._with_help(self.show_superweapon_panel_checkbox,
            "Show the superweapon panel on the HUD overlay.\n"
            "Displays each player's available superweapons and their cooldown timers."))

        superweapon_size_label = QLabel("Superweapon Size:")
        superweapon_size = self.state.hud_positions.get('superweapon_widget_size', 100)
        self.superweapon_size_spinbox = QSpinBox()
        self.superweapon_size_spinbox.setRange(5, 250)
        self.superweapon_size_spinbox.setValue(superweapon_size)
        self.superweapon_size_spinbox.valueChanged.connect(self.update_superweapon_widget_size)
        layout.addRow(superweapon_size_label, self.superweapon_size_spinbox)

        superweapon_frame_label = QLabel("Show Superweapon Frames:")
        self.superweapon_frame_checkbox = QCheckBox()
        self.superweapon_frame_checkbox.setChecked(self.state.hud_positions.get('show_superweapon_frames', True))
        self.superweapon_frame_checkbox.stateChanged.connect(self.toggle_superweapon_frames)
        layout.addRow(superweapon_frame_label, self._with_help(self.superweapon_frame_checkbox,
            "Show a decorative border/frame around each superweapon cameo in the panel.\n"
            "The frame color matches the player's in-game color."))

        superweapon_layout_label = QLabel("Select Superweapon Layout:")
        self.superweapon_layout_combo = QComboBox()
        self.superweapon_layout_combo.addItems(["Vertical", "Horizontal"])
        superweapon_layout_type = self.state.hud_positions.get('superweapon_layout', 'Horizontal')
        self.superweapon_layout_combo.setCurrentText(superweapon_layout_type)
        self.superweapon_layout_combo.currentTextChanged.connect(self.update_superweapon_layout)
        layout.addRow(superweapon_layout_label, self.superweapon_layout_combo)

        tab.setLayout(layout)
        self.tabs.addTab(self._wrap_in_scroll_area(tab), "Superweapons")

    def toggle_factory_queue(self, state_val):
        show_queue = (state_val != 0)
        self.state.hud_positions["show_factory_queue"] = show_queue
        logging.info(f"Set show_factory_queue to {show_queue}")

        # Do a full recreation in both modes to fix spacing issues (same approach as other toggles)
        from hud_manager import create_hud_windows
        create_hud_windows(self.state)

    def toggle_factory_window(self, state_val):
        show = (state_val != 0)
        self.state.hud_positions["show_factory_window"] = show
        logging.info(f"Set show_factory_window to {show}")

        # In separate HUD mode, we have top-level factory windows
        if not self.state.hud_positions.get('combined_hud', False):
            if hasattr(self.state, "factory_windows"):
                for factory_win in self.state.factory_windows:
                    if show:
                        factory_win.show()
                    else:
                        factory_win.hide()
        else:
            # In combined HUD mode, each CombinedHudWindow may or may not have a factory panel,
            # but "show_factory_window" toggles whether we create or destroy the panel.
            # The simplest approach is to close and rebuild the entire combined HUD so
            # the panel is added/removed.  Or you can dynamically create/destroy the
            # panel in each CombinedHudWindow. For now, let's do a full rebuild:
            from hud_manager import create_hud_windows
            create_hud_windows(self.state)

    def update_factory_widget_size(self):
        new_size = self.factory_size_spinbox.value()
        self.state.hud_positions['factory_size'] = new_size
        logging.info(f"Updated factory widget size to {new_size}")

        if not self.state.hud_positions.get('combined_hud', False):
            # Separate mode: update each FactoryWindow
            if hasattr(self.state, 'factory_windows'):
                for factory_win in self.state.factory_windows:
                    factory_win.set_size_for_all(new_size)
        else:
            # Combined mode: update each CombinedHudWindow's factory_panel
            for combined_window, _ in self.state.hud_windows:
                if hasattr(combined_window, 'factory_panel') and combined_window.factory_panel:
                    combined_window.factory_panel.set_size_for_all(new_size)

    def toggle_factory_frames(self, state_val):
        show = (state_val != 0)
        self.state.hud_positions['show_factory_frames'] = show
        logging.info(f"Toggled show_factory_frames to: {show}")

        if not self.state.hud_positions.get('combined_hud', False):
            if hasattr(self.state, 'factory_windows'):
                for factory_win in self.state.factory_windows:
                    factory_win.set_show_frames_for_all(show)
        else:
            for combined_window, _ in self.state.hud_windows:
                if hasattr(combined_window, 'factory_panel') and combined_window.factory_panel:
                    combined_window.factory_panel.set_show_frames_for_all(show)

    def update_factory_layout(self, layout_type):
        self.state.hud_positions['factory_layout'] = layout_type
        logging.info(f"Updated factory layout to: {layout_type}")

        if not self.state.hud_positions.get('combined_hud', False):
            # Separate HUD
            if hasattr(self.state, 'factory_windows'):
                for factory_win in self.state.factory_windows:
                    factory_win.set_layout_type(layout_type)
                    factory_win.update_labels()
        else:
            # Combined HUD
            for combined_window, _ in self.state.hud_windows:
                if hasattr(combined_window, 'factory_panel') and combined_window.factory_panel:
                    combined_window.factory_panel.set_layout_type(layout_type)
                    combined_window.factory_panel.update_labels()

    def create_general_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Game Path
        path_group = QGroupBox("Game Path")
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        game_path_val = self.state.hud_positions.get('game_path', '')
        self.path_edit.setText(game_path_val)
        self.path_edit.setPlaceholderText("Select the game folder")
        path_layout.addWidget(self.path_edit)
        self.path_button = QPushButton("Browse")
        self.path_button.clicked.connect(self.select_game_path)
        path_layout.addWidget(self.path_button)
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # HUD Mode
        hud_mode_group = QGroupBox("HUD Mode")
        hud_mode_layout = QFormLayout()
        self.combined_hud_checkbox = QCheckBox("Use Single Window Mode")
        self.combined_hud_checkbox.setChecked(self.state.hud_positions.get('combined_hud', False))
        self.combined_hud_checkbox.stateChanged.connect(self.toggle_combined_hud)
        hud_mode_layout.addRow(self._with_help(self.combined_hud_checkbox,
            "Merge all HUD elements for each player into a single movable window.\n"
            "When off, each element (name, money, units, etc.) is its own separate draggable window."))
        self.single_window_always_on_top_checkbox = QCheckBox("Single Window Always On Top")
        self.single_window_always_on_top_checkbox.setChecked(
            self.state.hud_positions.get('single_window_always_on_top', True)
        )
        self.single_window_always_on_top_checkbox.stateChanged.connect(self.toggle_single_window_always_on_top)
        hud_mode_layout.addRow(self._with_help(self.single_window_always_on_top_checkbox,
            "Keep the single-window HUD above other windows.\n"
            "Turn this off when you want the game to cover the HUD while OBS can still capture the HUD window."))
        self.use_player_numbers_checkbox = QCheckBox("Use Player Numbers Instead of Colors")
        self.use_player_numbers_checkbox.setChecked(self.state.hud_positions.get('use_player_numbers', False))
        self.use_player_numbers_checkbox.stateChanged.connect(self.toggle_player_number_mode)
        hud_mode_layout.addRow(self._with_help(self.use_player_numbers_checkbox,
            "Identify players by slot number (Player 1–8) instead of their in-game color.\n"
            "Use this when players are set to random colors, so the HUD can still track them reliably."))
        for slot in range(1, 9):
            reserved_name_edit = QLineEdit()
            reserved_name_edit.setPlaceholderText(f"Reserved name for Player {slot}")
            reserved_name_edit.setText(self.state.hud_positions.get(f'player_{slot}_name', ''))
            reserved_name_edit.textChanged.connect(
                lambda text, current_slot=slot: self.update_reserved_player_name(current_slot, text)
            )
            setattr(self, f'player_{slot}_name_edit', reserved_name_edit)
            hud_mode_layout.addRow(f"Player {slot} Name:", reserved_name_edit)
        hud_mode_group.setLayout(hud_mode_layout)
        layout.addWidget(hud_mode_group)

        # Data Update Settings
        data_update_group = QGroupBox("Data Update Settings")
        data_update_layout = QFormLayout()
        default_freq = self.state.hud_positions.get('data_update_frequency', 1000)
        self.update_frequency_spinbox = QSpinBox()
        self.update_frequency_spinbox.setRange(100, 10000)
        self.update_frequency_spinbox.setValue(default_freq)
        self.update_frequency_spinbox.valueChanged.connect(self.update_data_update_frequency)
        freq_row = QWidget()
        freq_row_layout = QHBoxLayout(freq_row)
        freq_row_layout.setContentsMargins(0, 0, 0, 0)
        freq_row_layout.setSpacing(6)
        freq_row_layout.addWidget(self.update_frequency_spinbox)
        freq_row_layout.addWidget(self._make_help_badge(
            "How often the app reads data from the game (in milliseconds).\n"
            "Lower = updates more frequently and feels more responsive.\n"
            "Higher = less frequent updates but uses less CPU.\n"
            "Warning: setting it too low can cause lag in the game or on your PC.\n"
            "1000 ms (1 second) is the recommended default."
        ))
        data_update_layout.addRow("Update Frequency (ms):", freq_row)
        data_update_group.setLayout(data_update_layout)
        layout.addWidget(data_update_group)

        tab.setLayout(layout)
        self.tabs.addTab(self._wrap_in_scroll_area(tab), "General")

    def create_scoreboard_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        settings_group = QGroupBox("Post-Game Scoreboard")
        settings_layout = QFormLayout()

        self.post_game_scoreboard_checkbox = QCheckBox("Show Post-Game Scoreboard")
        self.post_game_scoreboard_checkbox.setChecked(self.state.hud_positions.get('show_post_game_scoreboard', True))
        self.post_game_scoreboard_checkbox.stateChanged.connect(self.toggle_post_game_scoreboard)
        settings_layout.addRow(self._with_help(self.post_game_scoreboard_checkbox,
            "Automatically show a scoreboard at the end of each match\n"
            "with stats like units built, money spent, and who won."))

        saved_limit = self.state.hud_positions.get('saved_scoreboard_limit', -1)
        self.saved_scoreboard_limit_spinbox = QSpinBox()
        self.saved_scoreboard_limit_spinbox.setRange(-1, 9999)
        self.saved_scoreboard_limit_spinbox.setSpecialValueText("Unlimited")
        self.saved_scoreboard_limit_spinbox.setValue(saved_limit)
        self.saved_scoreboard_limit_spinbox.valueChanged.connect(self.update_saved_scoreboard_limit)
        settings_layout.addRow("Saved Scoreboards:", self.saved_scoreboard_limit_spinbox)

        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)

        actions_group = QGroupBox("Saved Scoreboards")
        actions_layout = QVBoxLayout()

        open_saved_button = QPushButton("Open Saved Scoreboard")
        open_saved_button.clicked.connect(self.open_saved_scoreboard)
        actions_layout.addWidget(open_saved_button)

        open_recent_button = QPushButton("Open Most Recent Scoreboard")
        open_recent_button.clicked.connect(self.open_most_recent_scoreboard)
        actions_layout.addWidget(open_recent_button)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        layout.addStretch()

        tab.setLayout(layout)
        self.tabs.addTab(self._wrap_in_scroll_area(tab), "Scoreboard")

    def select_game_path(self):
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        game_path = QFileDialog.getExistingDirectory(self, "Select Game Folder")
        if game_path:
            # Validate that this is a valid game folder by checking for spawn.ini
            spawn_ini_path = os.path.join(game_path, 'spawn.ini')
            if os.path.exists(spawn_ini_path):
                self.path_edit.setText(game_path)
                self.state.hud_positions['game_path'] = game_path
                self.state.game_path = game_path
            else:
                # Show error without mentioning spawn.ini
                msg_box = QMessageBox()
                msg_box.setWindowTitle("Invalid Game Path")
                msg_box.setText("Invalid game path selected.")
                msg_box.setInformativeText("Please select a valid game folder.")
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()

    def _set_name_color_button(self):
        self._set_color_button_state(
            self.name_color_button,
            self.state.hud_positions.get('name_color', '#FFFFFF'),
            self.DEFAULT_COLOR_LABELS['name'],
            self.state.hud_positions.get('name_color_mode') == 'custom',
        )

    def choose_name_color(self):
        color = QColorDialog.getColor(self._get_name_picker_initial_color(), self, "Select Name Color")
        if color.isValid():
            self.update_name_color(color.name())

    def reset_name_color(self):
        default_setting = self._get_default_setting('name')
        self.state.hud_positions['name_color_mode'] = default_setting.get('mode', 'default')
        default_color = default_setting.get('color')
        if default_color:
            self.state.hud_positions['name_color'] = default_color
        else:
            self.state.hud_positions.pop('name_color', None)
        self._set_name_color_button()
        self.apply_resource_widget_colors()

    def update_name_color(self, color_value):
        color = QColor(color_value)
        if not color.isValid():
            return
        self.state.hud_positions['name_color_mode'] = 'custom'
        self.state.hud_positions['name_color'] = color.name()
        self._set_name_color_button()
        self.apply_resource_widget_colors()

    def _set_money_color_button(self):
        legacy_mode = str(self._get_default_setting('money').get('legacy_mode', 'Use player color')).strip().lower()
        default_label = "Default (White)" if legacy_mode == 'white' else self.DEFAULT_COLOR_LABELS['money']
        self._set_color_button_state(
            self.money_color_button,
            self.state.hud_positions.get('money_custom_color', '#FFFFFF'),
            default_label,
            self.state.hud_positions.get('money_color_mode') == 'custom',
        )

    def choose_money_color(self):
        color = QColorDialog.getColor(self._get_money_picker_initial_color(), self, "Select Money Color")
        if color.isValid():
            self.update_money_color(color.name())

    def reset_money_color(self):
        default_setting = self._get_default_setting('money')
        self.state.hud_positions['money_color_mode'] = default_setting.get('mode', 'default')
        self.state.hud_positions['money_color'] = default_setting.get('legacy_mode', 'Use player color')
        default_color = default_setting.get('color')
        if default_color:
            self.state.hud_positions['money_custom_color'] = default_color
        else:
            self.state.hud_positions.pop('money_custom_color', None)
        self._set_money_color_button()
        self.apply_resource_widget_colors()

    def update_money_color(self, color_value):
        color = QColor(color_value)
        if not color.isValid():
            return
        self.state.hud_positions['money_color_mode'] = 'custom'
        self.state.hud_positions['money_custom_color'] = color.name()
        self._set_money_color_button()
        self.apply_resource_widget_colors()

    def _set_money_spent_color_button(self):
        self._set_color_button_state(
            self.money_spent_color_button,
            self.state.hud_positions.get('money_spent_color', '#76B5C5'),
            self.DEFAULT_COLOR_LABELS['money_spent'],
            self.state.hud_positions.get('money_spent_color_mode') == 'custom',
        )

    def choose_money_spent_color(self):
        color = QColorDialog.getColor(
            self._get_money_spent_picker_initial_color(),
            self,
            "Select Money Spent Color",
        )
        if color.isValid():
            self.update_money_spent_color(color.name())

    def reset_money_spent_color(self):
        default_setting = self._get_default_setting('money_spent')
        self.state.hud_positions['money_spent_color_mode'] = default_setting.get('mode', 'default')
        default_color = default_setting.get('color')
        if default_color:
            self.state.hud_positions['money_spent_color'] = default_color
        else:
            self.state.hud_positions.pop('money_spent_color', None)
        self._set_money_spent_color_button()
        self.apply_resource_widget_colors()

    def update_money_spent_color(self, color_value):
        color = QColor(color_value)
        if not color.isValid():
            return
        self.state.hud_positions['money_spent_color_mode'] = 'custom'
        self.state.hud_positions['money_spent_color'] = color.name()
        self._set_money_spent_color_button()
        self.apply_resource_widget_colors()

    def _set_power_good_color_button(self):
        self._set_color_button_state(
            self.power_good_color_button,
            self.state.hud_positions.get('power_good_color', '#00FF00'),
            'Default (Green)',
            self.state.hud_positions.get('power_good_color_mode') == 'custom',
        )

    def _set_power_low_color_button(self):
        self._set_color_button_state(
            self.power_low_color_button,
            self.state.hud_positions.get('power_low_color', '#FF0000'),
            'Default (Red)',
            self.state.hud_positions.get('power_low_color_mode') == 'custom',
        )

    def choose_power_good_color(self):
        initial = QColor(self.state.hud_positions.get('power_good_color', '#00FF00'))
        color = QColorDialog.getColor(initial, self, "Select Good Power Color")
        if color.isValid():
            self.state.hud_positions['power_good_color_mode'] = 'custom'
            self.state.hud_positions['power_good_color'] = color.name()
            self._set_power_good_color_button()
            self.apply_resource_widget_colors()

    def reset_power_good_color(self):
        self.state.hud_positions['power_good_color_mode'] = 'default'
        self.state.hud_positions.pop('power_good_color', None)
        self._set_power_good_color_button()
        self.apply_resource_widget_colors()

    def choose_power_low_color(self):
        initial = QColor(self.state.hud_positions.get('power_low_color', '#FF0000'))
        color = QColorDialog.getColor(initial, self, "Select Low Power Color")
        if color.isValid():
            self.state.hud_positions['power_low_color_mode'] = 'custom'
            self.state.hud_positions['power_low_color'] = color.name()
            self._set_power_low_color_button()
            self.apply_resource_widget_colors()

    def reset_power_low_color(self):
        self.state.hud_positions['power_low_color_mode'] = 'default'
        self.state.hud_positions.pop('power_low_color', None)
        self._set_power_low_color_button()
        self.apply_resource_widget_colors()

    def apply_resource_widget_colors(self):
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                if hasattr(combined_window, 'resource_widget'):
                    resource_widget = combined_window.resource_widget
                    resource_widget.update_name_widget_color()
                    resource_widget.update_money_widget_color()
                    resource_widget.update_money_spent_widget_color()
                    resource_widget.update_power_widget_color()
        else:
            for _, resource_window in self.state.hud_windows:
                if resource_window is None:
                    continue
                resource_window.update_name_widget_color()
                resource_window.update_money_widget_color()
                resource_window.update_money_spent_widget_color()
                resource_window.update_power_widget_color()

    def update_layout(self, layout_type):
        self.state.hud_positions['unit_layout'] = layout_type
        logging.info(f"Updated layout to: {layout_type}")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                # Handle Combined HUD mode
                for combined_window, _ in self.state.hud_windows:
                    if hasattr(combined_window, 'update_unit_layout'):
                        combined_window.update_unit_layout(layout_type)
            else:
                # Handle separate HUD mode (existing logic)
                for unit_window, _ in self.state.hud_windows:
                    if unit_window:
                        if isinstance(unit_window, tuple):
                            for uw in unit_window:
                                uw.update_layout(layout_type)
                        else:
                            unit_window.update_layout(layout_type)
        else:
            logging.info("HUD windows do not exist yet, storing the layout for later.")
        self.update_distance_between_numbers()

    def update_unit_window_size(self):
        new_size = self.counter_size_spinbox.value()
        self.state.hud_positions['unit_counter_size'] = new_size
        logging.info(f"Updated unit window size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.unit_widget.update_all_counters_size(new_size)
        else:
            for unit_window, _ in self.state.hud_windows:
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.update_all_counters_size(new_size)
                    else:
                        unit_window.update_all_counters_size(new_size)

    def update_name_widget_size(self):
        new_size = self.name_size_spinbox.value()
        self.state.hud_positions['name_widget_size'] = new_size
        logging.info(f"Updated name widget size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.name_widget.update_data_size(new_size)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.name_widget.update_data_size(new_size)

    def update_name_font(self, family):
        self.state.hud_positions['name_font_family'] = family
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.name_widget.update_font_family(family)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.name_widget.update_font_family(family)

    def update_money_widget_size(self):
        new_size = self.money_size_spinbox.value()
        self.state.hud_positions['money_widget_size'] = new_size
        logging.info(f"Updated money widget size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.money_widget.update_data_size(new_size)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.money_widget.update_data_size(new_size)

    def update_money_font(self, family):
        self.state.hud_positions['money_font_family'] = family
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.money_widget.update_font_family(family)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.money_widget.update_font_family(family)

    def update_money_spent_widget_size(self):
        new_size = self.money_spent_size_spinbox.value()
        self.state.hud_positions['money_spent_widget_size'] = new_size
        logging.info(f"Updated money spent widget size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.money_spent_widget.update_data_size(new_size)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.money_spent_widget.update_data_size(new_size)

    def update_money_spent_font(self, family):
        self.state.hud_positions['money_spent_font_family'] = family
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.money_spent_widget.update_font_family(family)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.money_spent_widget.update_font_family(family)

    def update_power_widget_size(self):
        new_size = self.power_size_spinbox.value()
        self.state.hud_positions['power_widget_size'] = new_size
        logging.info(f"Updated power widget size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.power_widget.update_data_size(new_size)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.power_widget.update_data_size(new_size)

    def update_power_font(self, family):
        self.state.hud_positions['power_font_family'] = family
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.power_widget.update_font_family(family)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.power_widget.update_font_family(family)

    def update_superweapon_widget_size(self):
        new_size = self.superweapon_size_spinbox.value()
        self.state.hud_positions['superweapon_widget_size'] = new_size
        logging.info(f"Updated superweapon widget size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.superweapon_widget.set_size_for_all(new_size)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.superweapon_widget.set_size_for_all(new_size)

    def toggle_name(self, state_val):
        self.toggle_hud_element('show_name', 'name_widget', state_val)

    def toggle_money(self, state_val):
        self.toggle_hud_element('show_money', 'money_widget', state_val)

    def toggle_money_spent(self, state_val):
        self.toggle_hud_element('show_money_spent', 'money_widget_spent', state_val)

    def toggle_power(self, state_val):
        self.toggle_hud_element('show_power', 'power_widget', state_val)

    def toggle_game_time(self, state_val):
        visible = (state_val == 2)
        self.state.hud_positions['show_game_time'] = visible
        logging.info(f"Toggled show_game_time to: {visible}")
        if self.state.hud_positions.get('combined_hud', False):
            item = getattr(self.state, 'game_time_workspace_item', None)
            if item is not None:
                if hasattr(item, 'set_content_visible'):
                    item.set_content_visible(visible)
                elif visible:
                    item.show()
                else:
                    item.hide()
        else:
            window = getattr(self.state, 'game_time_window', None)
            if window is not None:
                if visible:
                    window.show()
                else:
                    window.hide()

    def toggle_map_name(self, state_val):
        visible = (state_val == 2)
        self.state.hud_positions['show_map_name'] = visible
        logging.info(f"Toggled show_map_name to: {visible}")
        if self.state.hud_positions.get('combined_hud', False):
            item = getattr(self.state, 'map_name_workspace_item', None)
            if item is not None:
                if hasattr(item, 'set_content_visible'):
                    item.set_content_visible(visible)
                elif visible:
                    item.show()
                else:
                    item.hide()
        else:
            window = getattr(self.state, 'map_name_window', None)
            if window is not None:
                if visible:
                    window.show()
                else:
                    window.hide()

    def toggle_superweapons(self, state_val):
        enabled = (state_val == 2)
        if hasattr(self, 'show_superweapons_checkbox'):
            self.show_superweapons_checkbox.blockSignals(True)
            self.show_superweapons_checkbox.setChecked(enabled)
            self.show_superweapons_checkbox.blockSignals(False)
        if hasattr(self, 'show_superweapon_panel_checkbox'):
            self.show_superweapon_panel_checkbox.blockSignals(True)
            self.show_superweapon_panel_checkbox.setChecked(enabled)
            self.show_superweapon_panel_checkbox.blockSignals(False)
        self.toggle_hud_element('show_superweapons', 'superweapon_widget', state_val)

    def toggle_superweapon_frames(self, state_val):
        show = (state_val != 0)
        self.state.hud_positions['show_superweapon_frames'] = show
        logging.info(f"Toggled show_superweapon_frames to: {show}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.superweapon_widget.set_show_frames_for_all(show)
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.superweapon_widget.set_show_frames_for_all(show)

    def update_superweapon_layout(self, layout_type):
        self.state.hud_positions['superweapon_layout'] = layout_type
        logging.info(f"Updated superweapon layout to: {layout_type}")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                combined_window.resource_widget.superweapon_widget.set_layout_type(layout_type)
                combined_window.resource_widget.superweapon_widget.update_labels()
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.superweapon_widget.set_layout_type(layout_type)
                resource_window.superweapon_widget.update_labels()

    def update_data_update_frequency(self):
        new_freq = self.update_frequency_spinbox.value()
        self.state.hud_positions['data_update_frequency'] = new_freq
        logging.info(f"Update frequency set to: {new_freq} ms")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                for combined_window, _ in self.state.hud_windows:
                    resource_widget = getattr(combined_window, 'resource_widget', None)
                    if resource_widget is not None:
                        resource_widget.update_numeric_animation_duration(new_freq)
            else:
                for _, resource_window in self.state.hud_windows:
                    if resource_window is not None:
                        resource_window.update_numeric_animation_duration(new_freq)

    def toggle_flag(self, state_val):
        self.toggle_hud_element('show_flag', 'flag_widget', state_val)

    def update_game_time_widget_size(self):
        new_size = self.game_time_size_spinbox.value()
        self.state.hud_positions['game_time_widget_size'] = new_size
        logging.info(f"Updated game time widget size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            widget = getattr(self.state, 'game_time_widget', None)
            if widget is not None:
                widget.update_data_size(new_size)
            item = getattr(self.state, 'game_time_workspace_item', None)
            if item is not None and hasattr(item, '_queue_sync_to_inner'):
                item._queue_sync_to_inner()
        else:
            window = getattr(self.state, 'game_time_window', None)
            if window is not None:
                window.update_widget_size(new_size)

    def _update_game_time_font_family(self, family):
        self.update_game_time_font(QFont(family))

    def update_game_time_font(self, font):
        family = font.family()
        self.state.hud_positions['game_time_font_family'] = family
        logging.info(f"Updated game time font family: {family}")
        if self.state.hud_positions.get('combined_hud', False):
            widget = getattr(self.state, 'game_time_widget', None)
            if widget is not None:
                widget.update_font_family(family)
            item = getattr(self.state, 'game_time_workspace_item', None)
            if item is not None and hasattr(item, '_queue_sync_to_inner'):
                item._queue_sync_to_inner()
        else:
            window = getattr(self.state, 'game_time_window', None)
            if window is not None:
                window.update_font_family(family)

    def _set_game_time_color_button(self):
        custom_mode = self.state.hud_positions.get('game_time_color_mode', 'custom') == 'custom'
        self._set_color_button_state(
            self.game_time_color_button,
            self.state.hud_positions.get('game_time_color', '#FFFFFF'),
            self.DEFAULT_COLOR_LABELS['game_time'],
            custom_mode,
        )

    def choose_game_time_color(self):
        initial = QColor(self.state.hud_positions.get('game_time_color', '#FFFFFF'))
        color = QColorDialog.getColor(initial, self, "Select Game Time Color")
        if not color.isValid():
            return
        self.update_game_time_color(color.name())

    def reset_game_time_color(self):
        default_setting = self._get_default_setting('game_time')
        self.state.hud_positions['game_time_color_mode'] = default_setting.get('mode', 'custom')
        self._set_game_time_color_button()
        self.update_game_time_color(
            default_setting.get('color', '#FFFFFF'),
            custom_mode=default_setting.get('mode', 'custom') == 'custom',
        )

    def update_game_time_color(self, color_value, custom_mode=True):
        color = QColor(color_value)
        if not color.isValid():
            return
        color_name = color.name()
        self.state.hud_positions['game_time_color'] = color_name
        self.state.hud_positions['game_time_color_mode'] = 'custom' if custom_mode else 'default'
        self._set_game_time_color_button()
        logging.info(f"Updated game time color: {color_name}")
        if self.state.hud_positions.get('combined_hud', False):
            widget = getattr(self.state, 'game_time_widget', None)
            if widget is not None:
                widget.update_color(new_text_color=color)
            item = getattr(self.state, 'game_time_workspace_item', None)
            if item is not None and hasattr(item, '_queue_sync_to_inner'):
                item._queue_sync_to_inner()
        else:
            window = getattr(self.state, 'game_time_window', None)
            if window is not None:
                window.update_text_color(color_name)

    def update_map_name_widget_size(self):
        new_size = self.map_name_size_spinbox.value()
        self.state.hud_positions['map_name_widget_size'] = new_size
        logging.info(f"Updated map name widget size: {new_size}")
        if self.state.hud_positions.get('combined_hud', False):
            widget = getattr(self.state, 'map_name_widget', None)
            if widget is not None:
                widget.update_data_size(new_size)
            item = getattr(self.state, 'map_name_workspace_item', None)
            if item is not None and hasattr(item, '_queue_sync_to_inner'):
                item._queue_sync_to_inner()
        else:
            window = getattr(self.state, 'map_name_window', None)
            if window is not None:
                window.update_widget_size(new_size)

    def update_map_name_font(self, family):
        self.state.hud_positions['map_name_font_family'] = family
        if self.state.hud_positions.get('combined_hud', False):
            widget = getattr(self.state, 'map_name_widget', None)
            if widget is not None:
                widget.update_font_family(family)
            item = getattr(self.state, 'map_name_workspace_item', None)
            if item is not None and hasattr(item, '_queue_sync_to_inner'):
                item._queue_sync_to_inner()
        else:
            window = getattr(self.state, 'map_name_window', None)
            if window is not None and hasattr(window, 'update_font_family'):
                window.update_font_family(family)

    def _set_map_name_color_button(self):
        custom_mode = self.state.hud_positions.get('map_name_color_mode', 'custom') == 'custom'
        self._set_color_button_state(
            self.map_name_color_button,
            self.state.hud_positions.get('map_name_color', '#FFFFFF'),
            self.DEFAULT_COLOR_LABELS['map_name'],
            custom_mode,
        )

    def choose_map_name_color(self):
        initial = QColor(self.state.hud_positions.get('map_name_color', '#FFFFFF'))
        color = QColorDialog.getColor(initial, self, "Select Map Name Color")
        if not color.isValid():
            return
        self.update_map_name_color(color.name())

    def reset_map_name_color(self):
        default_setting = self._get_default_setting('map_name')
        self.state.hud_positions['map_name_color_mode'] = default_setting.get('mode', 'custom')
        self._set_map_name_color_button()
        self.update_map_name_color(
            default_setting.get('color', '#FFFFFF'),
            custom_mode=default_setting.get('mode', 'custom') == 'custom',
        )

    def update_map_name_color(self, color_value, custom_mode=True):
        color = QColor(color_value)
        if not color.isValid():
            return
        color_name = color.name()
        self.state.hud_positions['map_name_color'] = color_name
        self.state.hud_positions['map_name_color_mode'] = 'custom' if custom_mode else 'default'
        self._set_map_name_color_button()
        logging.info(f"Updated map name color: {color_name}")
        if self.state.hud_positions.get('combined_hud', False):
            widget = getattr(self.state, 'map_name_widget', None)
            if widget is not None:
                widget.update_color(new_text_color=color)
            item = getattr(self.state, 'map_name_workspace_item', None)
            if item is not None and hasattr(item, '_queue_sync_to_inner'):
                item._queue_sync_to_inner()
        else:
            window = getattr(self.state, 'map_name_window', None)
            if window is not None:
                window.update_text_color(color_name)

    def toggle_post_game_scoreboard(self, state_val):
        enabled = (state_val == 2)
        self.set_post_game_scoreboard_enabled(enabled)

    def update_saved_scoreboard_limit(self):
        value = self.saved_scoreboard_limit_spinbox.value()
        self.state.hud_positions['saved_scoreboard_limit'] = value
        logging.info(f"Updated saved_scoreboard_limit to: {value}")

    def open_saved_scoreboard(self):
        history_dir = getattr(self.state, 'MATCH_HISTORY_DIR', 'match_history')
        os.makedirs(history_dir, exist_ok=True)
        selected_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Saved Scoreboard",
            history_dir,
            "Scoreboard Files (*.json);;All Files (*)"
        )
        if selected_path:
            self.open_scoreboard_from_path(selected_path)

    def open_most_recent_scoreboard(self):
        history_dir = getattr(self.state, 'MATCH_HISTORY_DIR', 'match_history')
        if not os.path.isdir(history_dir):
            self.show_scoreboard_error("No saved scoreboards were found.")
            return

        json_paths = [
            os.path.join(history_dir, entry)
            for entry in os.listdir(history_dir)
            if entry.lower().endswith('.json')
        ]
        if not json_paths:
            self.show_scoreboard_error("No saved scoreboards were found.")
            return

        most_recent_path = max(json_paths, key=os.path.getmtime)
        self.open_scoreboard_from_path(most_recent_path)

    def open_scoreboard_from_path(self, scoreboard_path):
        try:
            payload = load_scoreboard_payload_from_file(scoreboard_path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            logging.exception("Failed to load scoreboard from %s", scoreboard_path)
            self.show_scoreboard_error(f"Could not load scoreboard:\n{error}")
            return

        if getattr(self.state, 'scoreboard_window', None) is not None:
            self.state.scoreboard_window.close()

        self.state.scoreboard_window = PostGameScoreboardWindow(payload, self.state)
        self.state.scoreboard_window.show()
        self.state.scoreboard_window.raise_()
        self.state.scoreboard_window.activateWindow()

    def show_scoreboard_error(self, message):
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Scoreboard")
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()

    def set_post_game_scoreboard_enabled(self, enabled):
        self.state.hud_positions['show_post_game_scoreboard'] = enabled
        logging.info(f"Toggled show_post_game_scoreboard to: {enabled}")

        if hasattr(self, 'post_game_scoreboard_checkbox'):
            self.post_game_scoreboard_checkbox.blockSignals(True)
            self.post_game_scoreboard_checkbox.setChecked(enabled)
            self.post_game_scoreboard_checkbox.blockSignals(False)

        if not enabled and getattr(self.state, 'scoreboard_window', None) is not None:
            self.state.scoreboard_window.close()
            self.state.scoreboard_window = None

    def toggle_hud_element(self, element, widget_name, state_val):
        self.state.hud_positions[element] = (state_val == 2)
        logging.info(f"Toggled {element} state to: {self.state.hud_positions[element]}")
        fixed_positions = {
            'name_widget': 0,
            'flag_widget': 1,
            'money_widget': 2,
            'money_widget_spent': 3,
            'power_widget': 4,
            'superweapon_widget': 5,
            'unit_widget': 6
        }
        fixed_index = fixed_positions.get(widget_name, None)
        if fixed_index is None:
            return
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                if hasattr(combined_window, 'set_element_visibility'):
                    combined_window.set_element_visibility(widget_name, state_val == 2)
        else:
            index_mapping = {
                'name_widget': 0,
                'money_widget': 1,
                'money_widget_spent': 2,
                'power_widget': 3,
                'flag_widget': 4,
                'superweapon_widget': 5
            }
            index = index_mapping.get(widget_name)
            if index is not None:
                for _, resource_window in self.state.hud_windows:
                    window = resource_window.windows[index]
                    if state_val == 2:
                        window.show()
                    else:
                        window.hide()

    def update_combined_widget(self, parent, target_widget, fixed_index, visible):
        """Show or hide a widget in combined HUD mode."""
        if visible:
            target_widget.show()
        else:
            target_widget.hide()

    def open_unit_selection(self):
        from UnitSelectionWindow import UnitSelectionWindow
        if self.unit_selection_window is None or not self.unit_selection_window.isVisible():
            self.unit_selection_window = UnitSelectionWindow(self.state.selected_units_dict, self.state.hud_windows)
            logging.info("Opening Unit Selection window")
            self.unit_selection_window.show()

    def load_selected_units(self):
        json_file = 'unit_selection.json'
        data, changed = load_selected_units_file(json_file)
        if changed:
            save_selected_units_file(data, json_file)
            logging.info("Normalized legacy selected units data in %s", json_file)
        return data

    def create_help_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setFrameShape(QTextEdit.Shape.NoFrame)
        text.setStyleSheet(
            "QTextEdit { background-color: #16213e; color: #c0c0e0; font-size: 13px; border: none; }"
        )
        text.setHtml("""
        <style>
            body  { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #c0c0e0; }
            h2    { color: #e94560; margin-bottom: 4px; margin-top: 20px; }
            h3    { color: #a0c0ff; margin-bottom: 2px; margin-top: 14px; }
            p     { margin: 4px 0 8px 0; line-height: 1.6; }
            ul    { margin: 4px 0 8px 16px; line-height: 1.7; }
            b     { color: #e0e0ff; }
            hr    { border: none; border-top: 1px solid #2d2d4e; margin: 16px 0; }
        </style>

        <h2>Getting Started</h2>
        <p>
            ⚠️ <b>Run this app as Administrator.</b> Without administrator privileges the app
            may fail to read game memory or fail to spawn HUD windows correctly.
            Right-click the executable and choose <b>Run as administrator</b>, or set it
            permanently via Properties → Compatibility → "Run this program as an administrator".
        </p>
        <p>
            Start by setting your <b>Game Path</b> in the General tab — point it to the folder
            where your Red Alert 2 / Yuri's Revenge is installed. The app reads live memory from
            the game process, so the game must be running for the HUD to display data.
        </p>
        <p>
            ⚠️ <b>Run the game in Borderless Window mode.</b> If the game is set to exclusive
            fullscreen, the HUD windows will be hidden behind it and won't appear on top.
            Borderless window mode allows the overlay to sit above the game as intended.
        </p>
        <p>
            The recommended renderer is <b>CnC-DDraw (Stretched)</b>. This renderer supports
            borderless window mode and is the most compatible option for running the overlay
            correctly on top of the game.
        </p>
        <p>
            Once the game is running, HUD windows will appear automatically. Drag them anywhere
            on screen. Your layout is saved when you close this control panel.
        </p>

        <hr/>

        <h2>HUD Modes</h2>
        <h3>Separate Windows (Default)</h3>
        <p>
            Each element (name, money, power, units, factory, superweapons) is its own
            independent draggable window. You can place them anywhere on screen with full flexibility.
        </p>
        <h3>Single Window Mode</h3>
        <p>
            All elements for a player are combined into one window. Easier to manage but less
            flexible in layout. Toggle this in the <b>General</b> tab under HUD Mode.
        </p>

        <h3>Widget Backgrounds</h3>
        <p>
            In the <b>Widgets</b> tab, the non-unit HUD widgets now support an optional solid
            background rectangle behind the content. This is useful when text or numbers are hard
            to read over bright or busy map areas.
        </p>
        <ul>
            <li>You can turn the background on or off per widget.</li>
            <li>You can choose the background color, including transparency.</li>
            <li>You can set a custom width and height for the rectangle.</li>
            <li>These settings are saved and work in both separate-window mode and single-window mode.</li>
        </ul>

        <hr/>

        <h2>How Window Positions Are Saved</h2>
        <p>
            Every HUD window remembers its position on screen. Positions are saved automatically
            when you close the control panel and restored the next time the app starts.
            Positions are saved <b>per player identity</b>, so each player's windows remember
            exactly where you placed them independently of other players.
        </p>

        <h3>Color Mode (Default)</h3>
        <p>
            The app identifies each player by their <b>in-game color</b> (red, blue, green, etc.).
            Each color has its own saved window positions.
        </p>
        <ul>
            <li>Place a player's windows wherever you like during a game.</li>
            <li>Next game, if that same color appears, the windows snap back to exactly where you left them.</li>
            <li>Different colors each have independent positions.</li>
        </ul>

        <h3>Player Number Mode</h3>
        <p>
            If players use <b>random colors</b>, color-based tracking won't work reliably.
            Enable <b>"Use Player Numbers Instead of Colors"</b> (General tab) to identify
            players by their slot number (Player 1–8) regardless of color.
        </p>
        <p>
            You can optionally enter a player's name for each slot. When a name is set, the app
            matches that player to the correct slot even if they join in a different order.
            <b>If no name is set</b>, players are assigned to slots in the order they are detected —
            positions are still saved and restored correctly by slot number.
        </p>

        <hr/>

        <h2>Unit Counter</h2>
        <p>
            Use the <b>Select Units</b> button in the Units tab to choose which units to track
            for each faction. Units are organized by faction and type (Infantry, Tank, Aircraft, etc.).
        </p>
        <ul>
            <li><b>Left-click</b> a unit to select or deselect it.</li>
            <li><b>Right-click</b> a unit to lock its position (it won't move even as other units are added or removed) or to set an exact position number.</li>
            <li>The number badge on a unit image shows its current display position in the counter.</li>
        </ul>
        <p>
            In <b>Separate Counter Mode</b> (Units tab), unit images and unit numbers appear in
            two separate windows so you can position them independently — useful for streamers
            who want numbers in one corner and images in another.
        </p>

        <hr/>

        <h2>Factory &amp; Superweapon Panels</h2>
        <p>
            The factory panel shows what each player is currently building, including a queue
            of upcoming units. The superweapon panel shows each player's available superweapons
            and their countdown timers.
        </p>
        <p>
            Both panels support <b>Vertical</b> and <b>Horizontal</b> layouts and adjustable
            cameo sizes. Frames around each cameo are colored with the player's in-game color.
        </p>

        <hr/>

        <h2>Post-Game Scoreboard</h2>
        <p>
            When a match ends, a scoreboard automatically appears with match stats.
            You can also open saved scoreboards at any time from the <b>Scoreboard</b> tab.
            Set a limit on how many scoreboards are saved to disk, or leave it unlimited.
        </p>

        <hr/>

        <h2>Update Frequency</h2>
        <p>
            The app reads game memory every <b>1000 ms (1 second)</b> by default.
            You can lower this in the General tab for more responsive updates, or raise it
            to reduce CPU usage. Values below 200 ms are not recommended.
        </p>

        <hr/>

        <h2>Tips</h2>
        <ul>
            <li>All settings are saved automatically on close — no save button needed.</li>
            <li>Hover over any <b>?</b> badge next to a setting for a quick explanation.</li>
            <li>The HUD windows are always-on-top and click-through — they won't interfere with gameplay.</li>
            <li>If a window disappears off-screen, delete <b>hud_positions.json</b> to reset all positions.</li>
        </ul>
        """)

        layout.addWidget(text)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Help")

    def create_help_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setFrameShape(QTextEdit.Shape.NoFrame)
        text.setStyleSheet(
            "QTextEdit { background-color: #16213e; color: #c0c0e0; font-size: 13px; border: none; }"
        )
        text.setHtml("""
        <style>
            body  { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; color: #c0c0e0; }
            h2    { color: #e94560; margin-bottom: 4px; margin-top: 20px; }
            h3    { color: #a0c0ff; margin-bottom: 2px; margin-top: 14px; }
            p     { margin: 4px 0 8px 0; line-height: 1.6; }
            ul    { margin: 4px 0 8px 16px; line-height: 1.7; }
            b     { color: #e0e0ff; }
            hr    { border: none; border-top: 1px solid #2d2d4e; margin: 16px 0; }
        </style>

        <h2>Getting Started</h2>
        <p>
            <b>Run this app as Administrator.</b> Without administrator privileges the app
            may fail to read game memory or fail to spawn HUD windows correctly.
            Right-click the executable and choose <b>Run as administrator</b>, or set it
            permanently via Properties -> Compatibility -> "Run this program as an administrator".
        </p>
        <p>
            Start by setting your <b>Game Path</b> in the General tab. Point it to the folder
            where your Red Alert 2 / Yuri's Revenge is installed. The app reads live memory from
            the game process, so the game must be running for the HUD to display data.
        </p>
        <p>
            <b>Run the game in Borderless Window mode.</b> If the game is set to exclusive
            fullscreen, the HUD windows will be hidden behind it and will not appear on top.
            Borderless window mode allows the overlay to sit above the game as intended.
        </p>
        <p>
            The recommended renderer is <b>CnC-DDraw (Stretched)</b>. This renderer supports
            borderless window mode and is the most compatible option for running the overlay
            correctly on top of the game.
        </p>
        <p>
            Once the game is running, HUD windows will appear automatically. Drag them anywhere
            on screen. Your layout is saved when you close this control panel.
        </p>

        <hr/>

        <h2>HUD Modes</h2>
        <h3>Separate Windows (Default)</h3>
        <p>
            Each element (name, money, power, units, factory, superweapons) is its own
            independent draggable window. You can place them anywhere on screen with full flexibility.
        </p>
        <h3>Single Window Mode</h3>
        <p>
            All elements for a player are combined into one window. Easier to manage but less
            flexible in layout. Toggle this in the <b>General</b> tab under HUD Mode.
        </p>

        <h3>Widget Backgrounds</h3>
        <p>
            In the <b>Widgets</b> tab, the non-unit HUD widgets support an optional solid
            background rectangle behind the content. This is useful when text or numbers are hard
            to read over bright or busy map areas.
        </p>
        <ul>
            <li>You can turn the background on or off per widget.</li>
            <li>You can choose the background color, including transparency.</li>
            <li>You can set a custom width and height for the rectangle.</li>
            <li>These settings are saved and work in both separate-window mode and single-window mode.</li>
        </ul>

        <h3>Fonts and Colors</h3>
        <p>
            Most HUD widgets can be styled directly from the control panel. You can choose a font
            family per widget, use custom colors, or fall back to the default/player-color behavior
            where that makes sense.
        </p>

        <hr/>

        <h2>How Window Positions Are Saved</h2>
        <p>
            Every HUD window remembers its position on screen. Positions are saved automatically
            when you close the control panel and restored the next time the app starts.
            Positions are saved <b>per player identity</b>, so each player's windows remember
            exactly where you placed them independently of other players.
        </p>

        <h3>Color Mode (Default)</h3>
        <p>
            The app identifies each player by their <b>in-game color</b> (red, blue, green, etc.).
            Each color has its own saved window positions.
        </p>
        <ul>
            <li>Place a player's windows wherever you like during a game.</li>
            <li>Next game, if that same color appears, the windows snap back to exactly where you left them.</li>
            <li>Different colors each have independent positions.</li>
        </ul>

        <h3>Player Number Mode</h3>
        <p>
            If players use <b>random colors</b>, color-based tracking will not work reliably.
            Enable <b>"Use Player Numbers Instead of Colors"</b> (General tab) to identify
            players by their slot number (Player 1-8) regardless of color.
        </p>
        <p>
            You can optionally enter a player's name for each slot. When a name is set, the app
            matches that player to the correct slot even if they join in a different order.
            <b>If no name is set</b>, players are assigned to slots in the order they are detected -
            positions are still saved and restored correctly by slot number.
        </p>

        <hr/>

        <h2>Widgets</h2>
        <p>
            The <b>Widgets</b> tab controls the main non-unit HUD elements. In addition to player
            name, flag, money, money spent, and power, the app can also show:
        </p>
        <ul>
            <li><b>Game Time</b> as a live match clock with adjustable size, font, color, and background.</li>
            <li><b>Map Name</b> as a separate HUD element with its own size, font, color, and background settings.</li>
        </ul>

        <hr/>

        <h2>Unit Counter</h2>
        <p>
            Use the <b>Select Units</b> button in the Units tab to choose which units to track
            for each faction. Units are organized by faction and type (Infantry, Tank, Aircraft, etc.).
        </p>
        <ul>
            <li><b>Left-click</b> a unit to select or deselect it.</li>
            <li><b>Right-click</b> a unit to lock its position (it will not move even as other units are added or removed) or to set an exact position number.</li>
            <li>The number badge on a unit image shows its current display position in the counter.</li>
        </ul>
        <p>
            In <b>Separate Counter Mode</b> (Units tab), unit images and unit numbers appear in
            two separate windows so you can position them independently - useful for streamers
            who want numbers in one corner and images in another.
        </p>

        <hr/>

        <h2>Factory &amp; Superweapon Panels</h2>
        <p>
            The factory panel shows what each player is currently building, including a queue
            of upcoming units. The superweapon panel shows each player's available superweapons
            and their countdown timers.
        </p>
        <p>
            Both panels support <b>Vertical</b> and <b>Horizontal</b> layouts and adjustable
            cameo sizes. Frames around each cameo are colored with the player's in-game color.
        </p>

        <hr/>

        <h2>Post-Game Scoreboard</h2>
        <p>
            When a match ends, a scoreboard automatically appears with match stats.
            You can also open saved scoreboards at any time from the <b>Scoreboard</b> tab.
            Set a limit on how many scoreboards are saved to disk, or leave it unlimited.
        </p>
        <ul>
            <li><b>Timeline</b> tab: estimated score timeline plus match-event tracking.</li>
            <li><b>Player Breakdown</b> tab: per-player summary cards and unit totals.</li>
            <li><b>Graphs</b> tab: switch between tracked metrics and filter unit-based graphs inline.</li>
            <li>Timeline events can include superweapon usage/build progress, radar tech, battle lab tech, special-unit builds, and MCV loss.</li>
            <li>Timeline filter preferences are remembered between scoreboard sessions.</li>
        </ul>

        <hr/>

        <h2>Update Frequency</h2>
        <p>
            The app reads game memory every <b>1000 ms (1 second)</b> by default.
            You can lower this in the General tab for more responsive updates, or raise it
            to reduce CPU usage. Values below 200 ms are not recommended.
        </p>

        <hr/>

        <h2>Tips</h2>
        <ul>
            <li>All settings are saved automatically on close - no save button needed.</li>
            <li>Hover over any <b>?</b> badge next to a setting for a quick explanation.</li>
            <li>The HUD windows are always-on-top and click-through - they will not interfere with gameplay.</li>
            <li>If a window disappears off-screen, delete <b>hud_positions.json</b> to reset all positions.</li>
        </ul>
        """)

        layout.addWidget(text)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Help")

    def close_all_counter_windows(self):
        """Close all HUD counter windows in both single and multiple window modes."""
        # Close unit and resource windows
        for unit_window, resource_window in self.state.hud_windows:
            if unit_window:
                if isinstance(unit_window, tuple):
                    # Multiple separate windows mode
                    for uw in unit_window:
                        uw.close()
                else:
                    # Single window mode or combined HUD mode
                    unit_window.close()
            if resource_window:
                if hasattr(resource_window, 'windows') and resource_window.windows:
                    # Separate mode with individual resource windows
                    for window in resource_window.windows:
                        window.close()
                else:
                    # Single resource window
                    resource_window.close()
        
        # Close factory windows if they exist
        if hasattr(self.state, 'factory_windows'):
            for factory_win in self.state.factory_windows:
                factory_win.close()
            self.state.factory_windows.clear()

        if hasattr(self.state, 'single_window_workspace') and self.state.single_window_workspace:
            self.state.single_window_workspace.close()
            self.state.single_window_workspace = None

        if getattr(self.state, 'game_time_window', None) is not None:
            self.state.game_time_window.close()
            self.state.game_time_window = None

        if getattr(self.state, 'game_time_workspace_item', None) is not None:
            self.state.game_time_workspace_item.close()
            self.state.game_time_workspace_item = None
            self.state.game_time_widget = None

        if getattr(self.state, 'map_name_window', None) is not None:
            self.state.map_name_window.close()
            self.state.map_name_window = None

        if getattr(self.state, 'map_name_workspace_item', None) is not None:
            self.state.map_name_workspace_item.close()
            self.state.map_name_workspace_item = None
            self.state.map_name_widget = None
        
        # Clear the hud_windows list
        self.state.hud_windows.clear()
        logging.info("All counter windows closed")
    
    def closeEvent(self, event):
        """Handle window close event (X button clicked)."""
        self.state.is_shutting_down = True

        # Close unit selection window if it exists and is visible
        if self.unit_selection_window is not None and self.unit_selection_window.isVisible():
            logging.info("Closing unit selection window")
            self.unit_selection_window.close()

        # Save while the HUD windows still exist so their live screen positions can be read.
        try:
            from hud_manager import save_hud_positions
            save_selected_units(self.state)
            save_hud_positions(self.state)
            logging.info("Settings saved on control panel close")
        except Exception as save_error:
            logging.exception("Error saving settings on close: %s", save_error)

        # Close all HUD counter windows after persistence is complete.
        self.close_all_counter_windows()

        super().closeEvent(event)
    


def save_selected_units(state):
    json_file = 'unit_selection.json'
    state.selected_units_dict = save_selected_units_file(state.selected_units_dict, json_file)
    logging.info("Saved selected units.")
