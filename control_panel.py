import json
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QFormLayout, QGroupBox,
    QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton, QHBoxLayout, QLineEdit, QFileDialog, QMessageBox,
    QColorDialog, QFontComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
import logging
import os

from UnitWindow import CombinedHudWindow
from hud_position_utils import normalize_position
from scoreboard_window import PostGameScoreboardWindow, load_scoreboard_payload_from_file
from selected_units_utils import load_selected_units_file, save_selected_units_file


class ControlPanel(QMainWindow):
    def __init__(self, state):
        super().__init__()
        self.state = state
        # Load selected units into state.
        self.state.selected_units_dict = self.load_selected_units()

        self.setWindowTitle("HUD Control Panel")
        self.setGeometry(100, 100, 600, 600)  # Wider to accommodate tabs
        self.restore_saved_position()

        # Create a tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create individual tabs
        self.create_unit_settings_tab()
        self.create_name_flag_money_tab()
        self.create_factory_settings_tab()
        self.create_superweapon_settings_tab()
        self.create_scoreboard_settings_tab()
        self.create_general_settings_tab()

        self.unit_selection_window = None

        # Store reference in state so other modules can access control panel settings.
        self.state.control_panel = self

    def restore_saved_position(self):
        saved_position = self.state.hud_positions.get('control_panel_position')
        if not saved_position:
            return

        normalized_position = normalize_position(saved_position)
        self.move(normalized_position['x'], normalized_position['y'])

    def create_unit_settings_tab(self):
        tab = QWidget()
        layout = QFormLayout()

        unit_size_label = QLabel("Unit Window Size:")
        counter_size = self.state.hud_positions.get('unit_counter_size', 75)
        self.counter_size_spinbox = QSpinBox()
        self.counter_size_spinbox.setRange(5, 250)
        self.counter_size_spinbox.setValue(counter_size)
        self.counter_size_spinbox.valueChanged.connect(self.update_unit_window_size)
        layout.addRow(unit_size_label, self.counter_size_spinbox)

        image_size_label = QLabel("Image Size:")
        image_size = self.state.hud_positions.get('image_size', 75)
        self.image_size_spinbox = QSpinBox()
        self.image_size_spinbox.setRange(5, 250)
        self.image_size_spinbox.setValue(image_size)
        self.image_size_spinbox.valueChanged.connect(self.update_image_size)
        layout.addRow(image_size_label, self.image_size_spinbox)

        number_size_label = QLabel("Number Size:")
        number_size = self.state.hud_positions.get('number_size', 75)
        self.number_size_spinbox = QSpinBox()
        self.number_size_spinbox.setRange(5, 250)
        self.number_size_spinbox.setValue(number_size)
        self.number_size_spinbox.valueChanged.connect(self.update_number_size)
        layout.addRow(number_size_label, self.number_size_spinbox)

        distance_label = QLabel("Distance Between Numbers:")
        distance = self.state.hud_positions.get('distance_between_numbers', 0)
        self.distance_spinbox = QSpinBox()
        self.distance_spinbox.setRange(0, 150)
        self.distance_spinbox.setValue(distance)
        self.distance_spinbox.valueChanged.connect(self.update_distance_between_numbers)
        layout.addRow(distance_label, self.distance_spinbox)

        distance_images_label = QLabel("Distance Between Images:")
        distance_images = self.state.hud_positions.get('distance_between_images', 0)
        self.distance_images_spinbox = QSpinBox()
        self.distance_images_spinbox.setRange(0, 150)
        self.distance_images_spinbox.setValue(distance_images)
        self.distance_images_spinbox.valueChanged.connect(self.update_distance_between_images)
        layout.addRow(distance_images_label, self.distance_images_spinbox)

        self.unit_frame_checkbox = QCheckBox("Show Unit Frames")
        self.unit_frame_checkbox.setChecked(self.state.hud_positions.get('show_unit_frames', True))
        self.unit_frame_checkbox.stateChanged.connect(self.toggle_unit_frames)
        layout.addRow(self.unit_frame_checkbox)

        self.separate_units_checkbox = QCheckBox("Separate Unit Counters")
        self.separate_units_checkbox.setChecked(self.state.hud_positions.get('separate_unit_counters', False))
        self.separate_units_checkbox.stateChanged.connect(self.toggle_separate_unit_counters)
        layout.addRow(self.separate_units_checkbox)

        layout_label = QLabel("Select Unit Layout:")
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Vertical", "Horizontal"])
        layout_type = self.state.hud_positions.get('unit_layout', 'Vertical')
        self.layout_combo.setCurrentText(layout_type)
        self.layout_combo.currentTextChanged.connect(self.update_layout)
        layout.addRow(layout_label, self.layout_combo)

        selection_button = QPushButton("Select Units")
        selection_button.clicked.connect(self.open_unit_selection)
        layout.addRow(selection_button)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Unit Settings")

        # Set initial control states based on the separate_unit_counters setting.
        if self.state.hud_positions.get('separate_unit_counters', False):
            self.image_size_spinbox.setEnabled(True)
            self.number_size_spinbox.setEnabled(True)
            self.distance_spinbox.setEnabled(True)
            self.distance_images_spinbox.setEnabled(True)
            self.counter_size_spinbox.setEnabled(False)
        else:
            self.image_size_spinbox.setEnabled(False)
            self.number_size_spinbox.setEnabled(False)
            self.distance_spinbox.setEnabled(False)
            self.distance_images_spinbox.setEnabled(True)  # Always enabled for spacing between images
            self.counter_size_spinbox.setEnabled(True)

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



    def toggle_separate_unit_counters(self, state_val):

        separate = (state_val != 0)
        self.state.hud_positions['separate_unit_counters'] = separate
        logging.info(f"Toggled separate_unit_counters to: {separate}")

        if separate:
            self.counter_size_spinbox.setEnabled(False)
            self.image_size_spinbox.setEnabled(True)
            self.number_size_spinbox.setEnabled(True)
            self.distance_spinbox.setEnabled(True)
            self.distance_images_spinbox.setEnabled(True)
        else:
            self.counter_size_spinbox.setEnabled(True)
            self.image_size_spinbox.setEnabled(False)
            self.number_size_spinbox.setEnabled(False)
            self.distance_spinbox.setEnabled(False)
            self.distance_images_spinbox.setEnabled(True)  # Always enabled for spacing between images

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
        name_group = QGroupBox("Name Widget Settings")
        name_layout = QFormLayout()
        self.name_checkbox = QCheckBox("Show Name")
        self.name_checkbox.setChecked(self.state.hud_positions.get('show_name', True))
        self.name_checkbox.stateChanged.connect(self.toggle_name)
        name_layout.addRow(self.name_checkbox)
        name_size_label = QLabel("Name Widget Size:")
        name_size = self.state.hud_positions.get('name_widget_size', 50)
        self.name_size_spinbox = QSpinBox()
        self.name_size_spinbox.setRange(5, 500)
        self.name_size_spinbox.setValue(name_size)
        self.name_size_spinbox.valueChanged.connect(self.update_name_widget_size)
        name_layout.addRow(name_size_label, self.name_size_spinbox)
        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        # Flag Settings
        flag_group = QGroupBox("Flag Widget Settings")
        flag_layout = QFormLayout()
        self.flag_checkbox = QCheckBox("Show Flag")
        self.flag_checkbox.setChecked(self.state.hud_positions.get('show_flag', True))
        self.flag_checkbox.stateChanged.connect(self.toggle_flag)
        flag_layout.addRow(self.flag_checkbox)
        self.save_flags_as_images_checkbox = QCheckBox("Save Flags As Images")
        self.save_flags_as_images_checkbox.setChecked(self.state.hud_positions.get('save_flags_as_images', False))
        self.save_flags_as_images_checkbox.stateChanged.connect(self.toggle_save_flags_as_images)
        flag_layout.addRow(self.save_flags_as_images_checkbox)
        flag_size_label = QLabel("Flag Widget Size:")
        flag_size = self.state.hud_positions.get('flag_widget_size', 50)
        self.flag_size_spinbox = QSpinBox()
        self.flag_size_spinbox.setRange(5, 500)
        self.flag_size_spinbox.setValue(flag_size)
        self.flag_size_spinbox.valueChanged.connect(self.update_flag_widget_size)
        flag_layout.addRow(flag_size_label, self.flag_size_spinbox)
        flag_group.setLayout(flag_layout)
        layout.addWidget(flag_group)

        # Money Settings
        money_group = QGroupBox("Money Widget Settings")
        money_layout = QFormLayout()
        self.money_checkbox = QCheckBox("Show Money")
        self.money_checkbox.setChecked(self.state.hud_positions.get('show_money', True))
        self.money_checkbox.stateChanged.connect(self.toggle_money)
        money_layout.addRow(self.money_checkbox)
        money_size_label = QLabel("Money Widget Size:")
        money_size = self.state.hud_positions.get('money_widget_size', 50)
        self.money_size_spinbox = QSpinBox()
        self.money_size_spinbox.setRange(5, 500)
        self.money_size_spinbox.setValue(money_size)
        self.money_size_spinbox.valueChanged.connect(self.update_money_widget_size)
        money_layout.addRow(money_size_label, self.money_size_spinbox)
        money_group.setLayout(money_layout)
        layout.addWidget(money_group)

        # Money Spent Settings
        money_spent_group = QGroupBox("Money Spent Widget Settings")
        money_spent_layout = QFormLayout()
        self.money_spent_checkbox = QCheckBox("Show Money Spent")
        self.money_spent_checkbox.setChecked(self.state.hud_positions.get('show_money_spent', True))
        self.money_spent_checkbox.stateChanged.connect(self.toggle_money_spent)
        money_spent_layout.addRow(self.money_spent_checkbox)
        money_spent_size_label = QLabel("Money Spent Widget Size:")
        money_spent_size = self.state.hud_positions.get('money_spent_widget_size', 50)
        self.money_spent_size_spinbox = QSpinBox()
        self.money_spent_size_spinbox.setRange(5, 500)
        self.money_spent_size_spinbox.setValue(money_spent_size)
        self.money_spent_size_spinbox.valueChanged.connect(self.update_money_spent_widget_size)
        money_spent_layout.addRow(money_spent_size_label, self.money_spent_size_spinbox)
        money_spent_group.setLayout(money_spent_layout)
        layout.addWidget(money_spent_group)

        # Power Settings
        power_group = QGroupBox("Power Widget Settings")
        power_layout = QFormLayout()
        self.power_checkbox = QCheckBox("Show Power")
        self.power_checkbox.setChecked(self.state.hud_positions.get('show_power', True))
        self.power_checkbox.stateChanged.connect(self.toggle_power)
        power_layout.addRow(self.power_checkbox)
        power_size_label = QLabel("Power Widget Size:")
        power_size = self.state.hud_positions.get('power_widget_size', 50)
        self.power_size_spinbox = QSpinBox()
        self.power_size_spinbox.setRange(5, 500)
        self.power_size_spinbox.setValue(power_size)
        self.power_size_spinbox.valueChanged.connect(self.update_power_widget_size)
        power_layout.addRow(power_size_label, self.power_size_spinbox)
        power_group.setLayout(power_layout)
        layout.addWidget(power_group)

        game_time_group = QGroupBox("Game Time Widget Settings")
        game_time_layout = QFormLayout()
        self.game_time_checkbox = QCheckBox("Show Game Time")
        self.game_time_checkbox.setChecked(self.state.hud_positions.get('show_game_time', True))
        self.game_time_checkbox.stateChanged.connect(self.toggle_game_time)
        game_time_layout.addRow(self.game_time_checkbox)

        game_time_size_label = QLabel("Game Time Widget Size:")
        game_time_size = self.state.hud_positions.get('game_time_widget_size', 50)
        self.game_time_size_spinbox = QSpinBox()
        self.game_time_size_spinbox.setRange(5, 500)
        self.game_time_size_spinbox.setValue(game_time_size)
        self.game_time_size_spinbox.valueChanged.connect(self.update_game_time_widget_size)
        game_time_layout.addRow(game_time_size_label, self.game_time_size_spinbox)

        game_time_font_label = QLabel("Game Time Font:")
        self.game_time_font_combo = QFontComboBox()
        saved_game_time_font = self.state.hud_positions.get('game_time_font_family', 'Arial')
        self.game_time_font_combo.setCurrentFont(QFont(saved_game_time_font))
        self.game_time_font_combo.currentFontChanged.connect(self.update_game_time_font)
        game_time_layout.addRow(game_time_font_label, self.game_time_font_combo)

        self.game_time_color_button = QPushButton()
        self.game_time_color_button.clicked.connect(self.choose_game_time_color)
        self._set_game_time_color_button(self.state.hud_positions.get('game_time_color', '#FFFFFF'))
        game_time_layout.addRow("Game Time Color:", self.game_time_color_button)

        game_time_group.setLayout(game_time_layout)
        layout.addWidget(game_time_group)

        map_name_group = QGroupBox("Map Name Widget Settings")
        map_name_layout = QFormLayout()
        self.map_name_checkbox = QCheckBox("Show Map Name")
        self.map_name_checkbox.setChecked(self.state.hud_positions.get('show_map_name', True))
        self.map_name_checkbox.stateChanged.connect(self.toggle_map_name)
        map_name_layout.addRow(self.map_name_checkbox)

        map_name_size_label = QLabel("Map Name Widget Size:")
        map_name_size = self.state.hud_positions.get('map_name_widget_size', 50)
        self.map_name_size_spinbox = QSpinBox()
        self.map_name_size_spinbox.setRange(5, 500)
        self.map_name_size_spinbox.setValue(map_name_size)
        self.map_name_size_spinbox.valueChanged.connect(self.update_map_name_widget_size)
        map_name_layout.addRow(map_name_size_label, self.map_name_size_spinbox)

        self.map_name_color_button = QPushButton()
        self.map_name_color_button.clicked.connect(self.choose_map_name_color)
        self._set_map_name_color_button(self.state.hud_positions.get('map_name_color', '#FFFFFF'))
        map_name_layout.addRow(QLabel("Map Name Color:"), self.map_name_color_button)

        map_name_group.setLayout(map_name_layout)
        layout.addWidget(map_name_group)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Name/Flag/Money")

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
        layout.addRow(self.show_factory_queue_checkbox)


        self.show_factory_checkbox = QCheckBox("Show Factory Window")
        show_factory_window = self.state.hud_positions.get("show_factory_window", True)
        self.show_factory_checkbox.setChecked(show_factory_window)
        self.show_factory_checkbox.stateChanged.connect(self.toggle_factory_window)
        layout.addRow(self.show_factory_checkbox)


        factory_size_label = QLabel("Factory Widget Size:")
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
        layout.addRow(factory_frame_label, self.factory_frame_checkbox)


        factory_layout_label = QLabel("Select Factory Layout:")
        self.factory_layout_combo = QComboBox()
        self.factory_layout_combo.addItems(["Vertical", "Horizontal"])
        factory_layout_type = self.state.hud_positions.get('factory_layout', 'Horizontal')
        self.factory_layout_combo.setCurrentText(factory_layout_type)
        self.factory_layout_combo.currentTextChanged.connect(self.update_factory_layout)
        layout.addRow(factory_layout_label, self.factory_layout_combo)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Factory Settings")

    def create_superweapon_settings_tab(self):
        tab = QWidget()
        layout = QFormLayout()

        self.show_superweapon_panel_checkbox = QCheckBox("Show Superweapon Window")
        show_superweapons = self.state.hud_positions.get("show_superweapons", True)
        self.show_superweapon_panel_checkbox.setChecked(show_superweapons)
        self.show_superweapon_panel_checkbox.stateChanged.connect(self.toggle_superweapons)
        layout.addRow(self.show_superweapon_panel_checkbox)

        superweapon_size_label = QLabel("Superweapon Widget Size:")
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
        layout.addRow(superweapon_frame_label, self.superweapon_frame_checkbox)

        superweapon_layout_label = QLabel("Select Superweapon Layout:")
        self.superweapon_layout_combo = QComboBox()
        self.superweapon_layout_combo.addItems(["Vertical", "Horizontal"])
        superweapon_layout_type = self.state.hud_positions.get('superweapon_layout', 'Horizontal')
        self.superweapon_layout_combo.setCurrentText(superweapon_layout_type)
        self.superweapon_layout_combo.currentTextChanged.connect(self.update_superweapon_layout)
        layout.addRow(superweapon_layout_label, self.superweapon_layout_combo)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Superweapon Settings")

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

        # Game Path Settings
        path_group = QGroupBox("Game Path Settings")
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

        # HUD Mode Settings
        hud_mode_group = QGroupBox("HUD Mode Settings")
        hud_mode_layout = QFormLayout()
        self.combined_hud_checkbox = QCheckBox("Use Single Window HUD Mode")
        self.combined_hud_checkbox.setChecked(self.state.hud_positions.get('combined_hud', False))
        self.combined_hud_checkbox.stateChanged.connect(self.toggle_combined_hud)
        hud_mode_layout.addRow(self.combined_hud_checkbox)
        self.use_player_numbers_checkbox = QCheckBox("Use Player Numbers Instead of Colors")
        self.use_player_numbers_checkbox.setChecked(self.state.hud_positions.get('use_player_numbers', False))
        self.use_player_numbers_checkbox.stateChanged.connect(self.toggle_player_number_mode)
        hud_mode_layout.addRow(self.use_player_numbers_checkbox)
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
        update_frequency_label = QLabel("Update Frequency (ms, 1000 ms = 1 second):")
        default_freq = self.state.hud_positions.get('data_update_frequency', 1000)
        self.update_frequency_spinbox = QSpinBox()
        self.update_frequency_spinbox.setRange(100, 10000)
        self.update_frequency_spinbox.setValue(default_freq)
        self.update_frequency_spinbox.valueChanged.connect(self.update_data_update_frequency)
        data_update_layout.addRow(update_frequency_label, self.update_frequency_spinbox)
        data_update_group.setLayout(data_update_layout)
        layout.addWidget(data_update_group)

        tab.setLayout(layout)
        self.tabs.addTab(tab, "General Settings")

    def create_scoreboard_settings_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        settings_group = QGroupBox("Post-Game Scoreboard")
        settings_layout = QFormLayout()

        self.post_game_scoreboard_checkbox = QCheckBox("Show Post-Game Scoreboard")
        self.post_game_scoreboard_checkbox.setChecked(self.state.hud_positions.get('show_post_game_scoreboard', True))
        self.post_game_scoreboard_checkbox.stateChanged.connect(self.toggle_post_game_scoreboard)
        settings_layout.addRow(self.post_game_scoreboard_checkbox)

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
        self.tabs.addTab(tab, "Scoreboard")

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

    def update_money_color(self, color):
        color = color.strip()
        self.state.hud_positions['money_color'] = color
        logging.info(f"HUD money color updated to: '{color}'")
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                if hasattr(combined_window, 'resource_widget'):
                    combined_window.resource_widget.update_money_widget_color()
        else:
            for _, resource_window in self.state.hud_windows:
                resource_window.update_money_widget_color()

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
                if visible:
                    item.show()
                    if getattr(item, 'inner_widget', None) is not None:
                        item.inner_widget.show()
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
                if visible:
                    item.show()
                    if getattr(item, 'inner_widget', None) is not None:
                        item.inner_widget.show()
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

    def _set_game_time_color_button(self, color_value):
        color = QColor(color_value)
        if not color.isValid():
            color = QColor('#FFFFFF')
        self.game_time_color_button.setProperty('selected_color', color.name())
        self.game_time_color_button.setText(color.name())
        self.game_time_color_button.setStyleSheet(
            f"background-color: {color.name()}; color: {'#000000' if color.lightness() > 128 else '#FFFFFF'};"
        )

    def choose_game_time_color(self):
        initial = QColor(self.state.hud_positions.get('game_time_color', '#FFFFFF'))
        color = QColorDialog.getColor(initial, self, "Select Game Time Color")
        if not color.isValid():
            return
        self.update_game_time_color(color.name())

    def update_game_time_color(self, color_value):
        color = QColor(color_value)
        if not color.isValid():
            return
        color_name = color.name()
        self.state.hud_positions['game_time_color'] = color_name
        self._set_game_time_color_button(color_name)
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

    def _set_map_name_color_button(self, color_value):
        color = QColor(color_value)
        if not color.isValid():
            color = QColor('#FFFFFF')
        self.map_name_color_button.setProperty('selected_color', color.name())
        self.map_name_color_button.setText(color.name())
        self.map_name_color_button.setStyleSheet(
            f"background-color: {color.name()}; color: {'#000000' if color.lightness() > 128 else '#FFFFFF'};"
        )

    def choose_map_name_color(self):
        initial = QColor(self.state.hud_positions.get('map_name_color', '#FFFFFF'))
        color = QColorDialog.getColor(initial, self, "Select Map Name Color")
        if not color.isValid():
            return
        self.update_map_name_color(color.name())

    def update_map_name_color(self, color_value):
        color = QColor(color_value)
        if not color.isValid():
            return
        color_name = color.name()
        self.state.hud_positions['map_name_color'] = color_name
        self._set_map_name_color_button(color_name)
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

    def toggle_save_flags_as_images(self, state_val):
        enabled = (state_val == 2)
        self.state.hud_positions['save_flags_as_images'] = enabled
        logging.info(f"Toggled save_flags_as_images to: {enabled}")

        from hud_manager import create_hud_windows
        create_hud_windows(self.state)

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

        self.state.scoreboard_window = PostGameScoreboardWindow(payload)
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
