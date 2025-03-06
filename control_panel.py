# control_panel.py
import json
import logging
import os

from PySide6.QtWidgets import (
    QWidget, QPushButton, QCheckBox, QVBoxLayout,
    QMainWindow, QLabel, QSpinBox, QComboBox, QFileDialog, QLineEdit,
    QHBoxLayout, QMessageBox, QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt

from UnitSelectionWindow import UnitSelectionWindow

class ControlPanel(QMainWindow):
    def __init__(self, state):
        super().__init__()
        self.state = state
        # Load selected units into state.
        self.state.selected_units_dict = self.load_selected_units()

        self.setWindowTitle("HUD Control Panel")
        self.setGeometry(100, 100, 400, 600)
        main_layout = QVBoxLayout()

        # Unit Window Settings Group
        unit_group = QGroupBox("Unit Window Settings")
        unit_layout = QFormLayout()

        unit_size_label = QLabel("Unit Window Size:")
        counter_size = self.state.hud_positions.get('unit_counter_size', 75)
        self.counter_size_spinbox = QSpinBox()
        self.counter_size_spinbox.setRange(5, 250)
        self.counter_size_spinbox.setValue(counter_size)
        self.counter_size_spinbox.valueChanged.connect(self.update_unit_window_size)
        unit_layout.addRow(unit_size_label, self.counter_size_spinbox)

        image_size_label = QLabel("Image Size:")
        image_size = self.state.hud_positions.get('image_size', 75)
        self.image_size_spinbox = QSpinBox()
        self.image_size_spinbox.setRange(5, 250)
        self.image_size_spinbox.setValue(image_size)
        self.image_size_spinbox.valueChanged.connect(self.update_image_size)
        unit_layout.addRow(image_size_label, self.image_size_spinbox)

        number_size_label = QLabel("Number Size:")
        number_size = self.state.hud_positions.get('number_size', 75)
        self.number_size_spinbox = QSpinBox()
        self.number_size_spinbox.setRange(5, 250)
        self.number_size_spinbox.setValue(number_size)
        self.number_size_spinbox.valueChanged.connect(self.update_number_size)
        unit_layout.addRow(number_size_label, self.number_size_spinbox)

        distance_label = QLabel("Distance Between Numbers:")
        distance = self.state.hud_positions.get('distance_between_numbers', 0)
        self.distance_spinbox = QSpinBox()
        self.distance_spinbox.setRange(0, 150)
        self.distance_spinbox.setValue(distance)
        self.distance_spinbox.valueChanged.connect(self.update_distance_between_numbers)
        unit_layout.addRow(distance_label, self.distance_spinbox)

        self.unit_frame_checkbox = QCheckBox("Show Unit Frames")
        self.unit_frame_checkbox.setChecked(self.state.hud_positions.get('show_unit_frames', True))
        self.unit_frame_checkbox.stateChanged.connect(self.toggle_unit_frames)
        unit_layout.addRow(self.unit_frame_checkbox)

        self.separate_units_checkbox = QCheckBox("Separate Unit Counters")
        self.separate_units_checkbox.setChecked(self.state.hud_positions.get('separate_unit_counters', False))
        self.separate_units_checkbox.stateChanged.connect(self.toggle_separate_unit_counters)
        unit_layout.addRow(self.separate_units_checkbox)

        layout_label = QLabel("Select Unit Layout:")
        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Vertical", "Horizontal"])
        layout_type = self.state.hud_positions.get('unit_layout', 'Vertical')
        self.layout_combo.setCurrentText(layout_type)
        self.layout_combo.currentTextChanged.connect(self.update_layout)
        unit_layout.addRow(layout_label, self.layout_combo)

        selection_button = QPushButton("Select Units")
        selection_button.clicked.connect(self.open_unit_selection)
        unit_layout.addRow(selection_button)

        unit_group.setLayout(unit_layout)
        main_layout.addWidget(unit_group)

        # Name Widget Settings Group
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
        main_layout.addWidget(name_group)

        # Flag Widget Settings Group
        flag_group = QGroupBox("Flag Widget Settings")
        flag_layout = QFormLayout()

        self.flag_checkbox = QCheckBox("Show Flag")
        self.flag_checkbox.setChecked(self.state.hud_positions.get('show_flag', True))
        self.flag_checkbox.stateChanged.connect(self.toggle_flag)
        flag_layout.addRow(self.flag_checkbox)

        flag_size_label = QLabel("Flag Widget Size:")
        flag_size = self.state.hud_positions.get('flag_widget_size', 50)
        self.flag_size_spinbox = QSpinBox()
        self.flag_size_spinbox.setRange(5, 500)
        self.flag_size_spinbox.setValue(flag_size)
        self.flag_size_spinbox.valueChanged.connect(self.update_flag_widget_size)
        flag_layout.addRow(flag_size_label, self.flag_size_spinbox)

        flag_group.setLayout(flag_layout)
        main_layout.addWidget(flag_group)

        # Money Widget Settings Group
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

        money_color_label = QLabel("Money Text Color:")
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Use player color", "White"])
        money_color = self.state.hud_positions.get('money_color', 'Use player color')
        self.color_combo.setCurrentText(money_color)
        self.color_combo.currentTextChanged.connect(self.update_money_color)
        money_layout.addRow(money_color_label, self.color_combo)

        money_group.setLayout(money_layout)
        main_layout.addWidget(money_group)

        # Power Widget Settings Group
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
        main_layout.addWidget(power_group)

        # Game Path Settings Group
        path_group = QGroupBox("Game Path Settings")
        path_layout = QHBoxLayout()

        self.path_edit = QLineEdit()
        game_path_val = self.state.hud_positions.get('game_path', '')
        self.path_edit.setText(game_path_val)
        self.path_edit.setPlaceholderText("Enter or select the game path")
        path_layout.addWidget(self.path_edit)

        self.path_button = QPushButton("Browse")
        self.path_button.clicked.connect(self.select_game_path)
        path_layout.addWidget(self.path_button)

        path_group.setLayout(path_layout)
        main_layout.addWidget(path_group)

        # Data Update Settings Group
        data_update_group = QGroupBox("Data Update Settings")
        data_update_layout = QFormLayout()

        # Label makes it clear that 1000 ms equals one second
        update_frequency_label = QLabel("Update Frequency (ms, 1000 ms = 1 second):")
        # Use the value from hud_positions or default to 1000
        default_freq = self.state.hud_positions.get('data_update_frequency', 1000)
        self.update_frequency_spinbox = QSpinBox()
        self.update_frequency_spinbox.setRange(100, 10000)  # Adjust range as needed
        self.update_frequency_spinbox.setValue(default_freq)
        self.update_frequency_spinbox.valueChanged.connect(self.update_data_update_frequency)
        data_update_layout.addRow(update_frequency_label, self.update_frequency_spinbox)

        data_update_group.setLayout(data_update_layout)
        main_layout.addWidget(data_update_group)

        # Quit Button
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.on_quit)
        main_layout.addWidget(quit_button)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.unit_selection_window = None

        # Store reference in state (so other modules can access control panel settings if needed)
        self.state.control_panel = self

        # Set initial control states based on the separate_unit_counters setting.
        if self.state.hud_positions.get('separate_unit_counters', False):
            self.image_size_spinbox.setEnabled(True)
            self.number_size_spinbox.setEnabled(True)
            self.distance_spinbox.setEnabled(True)
            self.counter_size_spinbox.setEnabled(False)
            self.update_distance_between_numbers()
        else:
            self.image_size_spinbox.setEnabled(False)
            self.number_size_spinbox.setEnabled(False)
            self.distance_spinbox.setEnabled(False)
            self.counter_size_spinbox.setEnabled(True)

    def on_quit(self):
        from app_manager import on_closing
        on_closing(self.state)

    def toggle_unit_frames(self, state_val):
        self.state.hud_positions['show_unit_frames'] = (state_val != 0)
        logging.info(f"Toggled show_unit_frames to: {self.state.hud_positions['show_unit_frames']}")
        if self.state.hud_windows:
            for unit_window, _ in self.state.hud_windows:
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.update_show_unit_frames(self.state.hud_positions['show_unit_frames'])
                    else:
                        unit_window.update_show_unit_frames(self.state.hud_positions['show_unit_frames'])

    def toggle_separate_unit_counters(self, state_val):
        self.state.hud_positions['separate_unit_counters'] = (state_val != 0)
        logging.info(f"Toggled separate_unit_counters to: {self.state.hud_positions['separate_unit_counters']}")
        if self.state.hud_positions['separate_unit_counters']:
            self.image_size_spinbox.setEnabled(True)
            self.number_size_spinbox.setEnabled(True)
            self.distance_spinbox.setEnabled(True)
            self.counter_size_spinbox.setEnabled(False)
        else:
            self.image_size_spinbox.setEnabled(False)
            self.number_size_spinbox.setEnabled(False)
            self.distance_spinbox.setEnabled(False)
            self.counter_size_spinbox.setEnabled(True)
        if len(self.state.hud_windows) > 0:
            for unit_window, _ in self.state.hud_windows:
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.close()
                    else:
                        unit_window.close()
            self.state.hud_windows = [(None, resource_window) for unit_window, resource_window in self.state.hud_windows]
            from hud_manager import create_unit_windows_in_current_mode
            create_unit_windows_in_current_mode(self.state)
            for unit_window, _ in self.state.hud_windows:
                if unit_window:
                    if isinstance(unit_window, tuple):
                        for uw in unit_window:
                            uw.show()
                    else:
                        unit_window.show()

    def update_image_size(self):
        new_size = self.image_size_spinbox.value()
        self.state.hud_positions['image_size'] = new_size
        logging.info(f"Updated image size in hud_positions: {new_size}")
        if self.state.hud_windows:
            for unit_window, _ in self.state.hud_windows:
                if unit_window and isinstance(unit_window, tuple):
                    unit_window_images, _ = unit_window
                    unit_window_images.update_all_counters_size(new_size)

    def update_number_size(self):
        new_size = self.number_size_spinbox.value()
        self.state.hud_positions['number_size'] = new_size
        logging.info(f"Updated number size in hud_positions: {new_size}")
        if self.state.hud_windows:
            for unit_window, _ in self.state.hud_windows:
                if unit_window and isinstance(unit_window, tuple):
                    _, unit_window_numbers = unit_window
                    unit_window_numbers.update_all_counters_size(new_size)

    def update_distance_between_numbers(self):
        new_distance = self.distance_spinbox.value()
        self.state.hud_positions['distance_between_numbers'] = new_distance
        logging.info(f"Updated distance between numbers in hud_positions: {new_distance}")
        if self.state.hud_windows:
            for unit_window, _ in self.state.hud_windows:
                if unit_window and isinstance(unit_window, tuple):
                    _, unit_window_numbers = unit_window
                    unit_window_numbers.update_spacing(new_distance)

    def update_flag_widget_size(self):
        new_size = self.flag_size_spinbox.value()
        self.state.hud_positions['flag_widget_size'] = new_size
        logging.info(f"Updated flag widget size in hud_positions: {new_size}")
        if self.state.hud_windows:
            for _, resource_window in self.state.hud_windows:
                resource_window.flag_widget.update_data_size(new_size)

    def toggle_flag(self, state_val):
        self.toggle_hud_element('show_flag', 'flag_widget', state_val)

    def toggle_hud_element(self, element, widget_name, state_val):
        self.state.hud_positions[element] = (state_val == 2)
        logging.info(f"Toggled {element} state to: {self.state.hud_positions[element]}")
        index_mapping = {
            'name_widget': 0,
            'money_widget': 1,
            'power_widget': 2,
            'flag_widget': 3
        }
        index = index_mapping.get(widget_name)
        if index is not None:
            for _, resource_window in self.state.hud_windows:
                window = resource_window.windows[index]
                if state_val == 2:
                    window.show()
                else:
                    window.hide()

    def select_game_path(self):
        game_path = QFileDialog.getExistingDirectory(self, "Select Game Folder")
        if game_path:
            self.path_edit.setText(game_path)
            self.state.hud_positions['game_path'] = game_path

    def update_money_color(self, color):
        color = color.strip()
        self.state.hud_positions['money_color'] = color
        logging.info(f"HUD money color updated to: '{color}'")
        if self.state.hud_windows:
            for _, resource_window in self.state.hud_windows:
                logging.debug(f"Updating money widget color for player {resource_window.player.username.value}")
                resource_window.update_money_widget_color()

    def update_layout(self, layout_type):
        self.state.hud_positions['unit_layout'] = layout_type
        logging.info(f"Updated layout to: {layout_type}")
        if self.state.hud_windows:
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
        logging.info(f"Updated unit window size in hud_positions: {new_size}")
        if self.state.hud_windows:
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
        logging.info(f"Updated name widget size in hud_positions: {new_size}")
        if self.state.hud_windows:
            for _, resource_window in self.state.hud_windows:
                resource_window.name_widget.update_data_size(new_size)

    def update_money_widget_size(self):
        new_size = self.money_size_spinbox.value()
        self.state.hud_positions['money_widget_size'] = new_size
        logging.info(f"Updated money widget size in hud_positions: {new_size}")
        if self.state.hud_windows:
            for _, resource_window in self.state.hud_windows:
                resource_window.money_widget.update_data_size(new_size)

    def update_power_widget_size(self):
        new_size = self.power_size_spinbox.value()
        self.state.hud_positions['power_widget_size'] = new_size
        logging.info(f"Updated power widget size in hud_positions: {new_size}")
        if self.state.hud_windows:
            for _, resource_window in self.state.hud_windows:
                resource_window.power_widget.update_data_size(new_size)

    def open_unit_selection(self):
        if self.unit_selection_window is None or not self.unit_selection_window.isVisible():
            self.unit_selection_window = UnitSelectionWindow(self.state.selected_units_dict, self.state.hud_windows)
            logging.info("Opening Unit Selection window")
            self.unit_selection_window.show()

    def load_selected_units(self):
        json_file = 'unit_selection.json'
        if os.path.exists(json_file):
            with open(json_file, 'r') as file:
                data = json.load(file)
                if 'selected_units' not in data:
                    data['selected_units'] = {}
                return data
        return {'selected_units': {}}

    def toggle_name(self, state_val):
        self.toggle_hud_element('show_name', 'name_widget', state_val)

    def toggle_money(self, state_val):
        self.toggle_hud_element('show_money', 'money_widget', state_val)

    def toggle_power(self, state_val):
        self.toggle_hud_element('show_power', 'power_widget', state_val)

    def update_data_update_frequency(self):
        new_freq = self.update_frequency_spinbox.value()
        self.state.hud_positions['data_update_frequency'] = new_freq
        logging.info(f"Update frequency set to: {new_freq} ms")


def save_selected_units(state):
    json_file = 'unit_selection.json'
    with open(json_file, 'w') as file:
        json.dump(state.selected_units_dict, file, indent=4)
    logging.info("Saved selected units.")
