from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTabWidget, QFormLayout, QGroupBox,
    QLabel, QSpinBox, QComboBox, QCheckBox, QPushButton, QHBoxLayout, QLineEdit, QFileDialog
)
from PySide6.QtCore import Qt
import json
import logging
import os

from UnitWindow import CombinedHudWindow


class ControlPanel(QMainWindow):
    def __init__(self, state):
        super().__init__()
        self.state = state
        # Load selected units into state.
        self.state.selected_units_dict = self.load_selected_units()

        self.setWindowTitle("HUD Control Panel")
        self.setGeometry(100, 100, 600, 600)  # Wider to accommodate tabs

        # Create a tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Create individual tabs
        self.create_unit_settings_tab()
        self.create_name_flag_money_tab()
        self.create_factory_settings_tab()
        self.create_game_path_data_tab()
        self.create_hud_mode_tab()
        self.create_quit_tab()  # Optionally, you might put the Quit button elsewhere.

        self.unit_selection_window = None

        # Store reference in state so other modules can access control panel settings.
        self.state.control_panel = self

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

    def update_flag_widget_size(self):
        new_size = self.flag_size_spinbox.value()
        self.state.hud_positions['flag_widget_size'] = new_size
        logging.info(f"Updated flag widget size: {new_size}")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                for combined_window, _ in self.state.hud_windows:
                    combined_window.resource_widget.flag_widget.update_data_size(new_size)
            else:
                for _, resource_window in self.state.hud_windows:
                    resource_window.flag_widget.update_data_size(new_size)



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
        flag_size_label = QLabel("Flag Widget Size:")
        flag_size = self.state.hud_positions.get('flag_widget_size', 50)
        self.flag_size_spinbox = QSpinBox()
        self.flag_size_spinbox.setRange(5, 500)
        self.flag_size_spinbox.setValue(flag_size)
        self.flag_size_spinbox.valueChanged.connect(self.update_flag_widget_size)
        flag_layout.addRow(flag_size_label, self.flag_size_spinbox)
        flag_group.setLayout(flag_layout)
        layout.addWidget(flag_group)

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

    def update_flag_widget_size(self):
        new_size = self.flag_size_spinbox.value()
        self.state.hud_positions['flag_widget_size'] = new_size
        logging.info(f"Updated flag widget size: {new_size}")
        if self.state.hud_windows:
            if self.state.hud_positions.get('combined_hud', False):
                for combined_window, _ in self.state.hud_windows:
                    combined_window.resource_widget.flag_widget.update_data_size(new_size)
            else:
                for _, resource_window in self.state.hud_windows:
                    resource_window.flag_widget.update_data_size(new_size)

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

        tab.setLayout(layout)
        self.tabs.addTab(tab, "Name/Flag/Money")


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

    def create_game_path_data_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Game Path Settings
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
        layout.addWidget(path_group)

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
        self.tabs.addTab(tab, "Game Path & Data")

    def create_hud_mode_tab(self):
        tab = QWidget()
        layout = QFormLayout()
        self.combined_hud_checkbox = QCheckBox("Use Combined HUD Mode")
        self.combined_hud_checkbox.setChecked(self.state.hud_positions.get('combined_hud', False))
        self.combined_hud_checkbox.stateChanged.connect(self.toggle_combined_hud)
        layout.addRow(self.combined_hud_checkbox)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "HUD Mode")

    def create_quit_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(self.on_quit)
        layout.addWidget(quit_button)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Quit")

    def select_game_path(self):
        from PySide6.QtWidgets import QFileDialog
        game_path = QFileDialog.getExistingDirectory(self, "Select Game Folder")
        if game_path:
            self.path_edit.setText(game_path)
            self.state.hud_positions['game_path'] = game_path

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

    def toggle_name(self, state_val):
        self.toggle_hud_element('show_name', 'name_widget', state_val)

    def toggle_money(self, state_val):
        self.toggle_hud_element('show_money', 'money_widget', state_val)

    def toggle_money_spent(self, state_val):
        self.toggle_hud_element('show_money_spent', 'money_widget_spent', state_val)

    def toggle_power(self, state_val):
        self.toggle_hud_element('show_power', 'power_widget', state_val)

    def update_data_update_frequency(self):
        new_freq = self.update_frequency_spinbox.value()
        self.state.hud_positions['data_update_frequency'] = new_freq
        logging.info(f"Update frequency set to: {new_freq} ms")

    def toggle_flag(self, state_val):
        self.toggle_hud_element('show_flag', 'flag_widget', state_val)

    def toggle_hud_element(self, element, widget_name, state_val):
        self.state.hud_positions[element] = (state_val == 2)
        logging.info(f"Toggled {element} state to: {self.state.hud_positions[element]}")
        fixed_positions = {
            'name_widget': 0,
            'flag_widget': 1,
            'money_widget': 2,
            'money_widget_spent': 3,
            'power_widget': 4,
            'unit_widget': 5
        }
        fixed_index = fixed_positions.get(widget_name, None)
        if fixed_index is None:
            return
        if self.state.hud_positions.get('combined_hud', False):
            for combined_window, _ in self.state.hud_windows:
                if widget_name == 'unit_widget':
                    parent = combined_window  # CombinedHudWindow's layout.
                    target_widget = combined_window.unit_widget
                else:
                    parent = combined_window.resource_widget.centralWidget()
                    if widget_name == 'name_widget':
                        target_widget = combined_window.resource_widget.name_widget
                    elif widget_name == 'flag_widget':
                        target_widget = combined_window.resource_widget.flag_widget
                    elif widget_name == 'money_widget':
                        target_widget = combined_window.resource_widget.money_widget
                    elif widget_name == 'money_widget_spent':
                        target_widget = combined_window.resource_widget.money_spent_widget
                    elif widget_name == 'power_widget':
                        target_widget = combined_window.resource_widget.power_widget
                    else:
                        continue
                self.update_combined_widget(parent, target_widget, fixed_index, state_val == 2)
        else:
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


    def open_unit_selection(self):
        from UnitSelectionWindow import UnitSelectionWindow
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
        
        # Clear the hud_windows list
        self.state.hud_windows.clear()
        logging.info("All counter windows closed")
    
    def closeEvent(self, event):
        """Handle window close event (X button clicked)."""
        self.close_all_counter_windows()
        super().closeEvent(event)
    
    def on_quit(self):
        self.close_all_counter_windows()
        from app_manager import on_closing
        on_closing(self.state)


def save_selected_units(state):
    json_file = 'unit_selection.json'
    import json
    with open(json_file, 'w') as file:
        json.dump(state.selected_units_dict, file, indent=4)
    logging.info("Saved selected units.")
