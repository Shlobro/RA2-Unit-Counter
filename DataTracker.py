import logging
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QFontDatabase, QColor
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

# Import the new widget classes
from DataWidget import MoneyWidget, PowerWidget, NameWidget, FlagWidget, MoneySpentWidget

faction_to_flag = {
    "British": "RA2_Flag_Britain.png",
    "Confederation": "RA2_Flag_Cuba.png",
    "Germans": "RA2_Flag_Germany.png",
    "Arabs": "RA2_Flag_Iraq.png",
    "French": "RA2_Flag_France.png",
    "Alliance": "RA2_Flag_Korea.png",
    "Africans": "RA2_Flag_Libya.png",
    "Russians": "RA2_Flag_Russia.png",
    "Americans": "RA2_Flag_USA.png",
    "YuriCountry": "RA2_Yuricountry.png"
}

class ResourceWindow(QMainWindow):
    def __init__(self, player, player_count, hud_positions, player_index, combined_mode=False):
        """
        If combined_mode is True, all resource widgets are embedded in a single window.
        Otherwise, separate windows are created for each widget.
        """
        super().__init__()
        self.player = player
        self.hud_positions = hud_positions
        self.combined_mode = combined_mode

        # Load sizes from hud_positions
        name_widget_size = self.hud_positions.get('name_widget_size', 50)
        money_widget_size = self.hud_positions.get('money_widget_size', 50)
        power_widget_size = self.hud_positions.get('power_widget_size', 50)
        flag_widget_size = self.hud_positions.get('flag_widget_size', 50)
        money_spent_widget_size = self.hud_positions.get('money_spent_widget_size', 50)

        # Load fonts
        font_id = QFontDatabase.addApplicationFont("Other/Futured.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)
        if font_family:
            money_font = QFont(font_family[0], 18, QFont.Bold)
        else:
            money_font = QFont("Arial", 18, QFont.Bold)
        power_font = QFont("Impact", 18, QFont.Bold)
        username_font = QFont("Roboto", 16, QFont.Bold)

        # Create the resource widgets
        self.name_widget = NameWidget(
            data=self.player.username.value,
            image_path=None,
            text_color=self.player.color,
            size=name_widget_size,
            font=username_font
        )
        self.flag_widget = FlagWidget(
            image_path="Flags/PNG/" + faction_to_flag[self.player.country_name.value.decode('utf-8')],
            size=flag_widget_size
        )
        money_color_option = self.hud_positions.get('money_color', 'Use player color')
        if money_color_option == 'Use player color':
            money_text_color = self.player.color
        elif money_color_option == 'White':
            money_text_color = Qt.white
        else:
            money_text_color = Qt.white
        self.money_widget = MoneyWidget(
            data=self.player.balance,
            text_color=money_text_color,
            size=money_widget_size,
            font=money_font
        )
        self.power_widget = PowerWidget(
            data=self.player.power,
            image_path='icons/bolt.png',
            image_color=Qt.green,
            text_color=Qt.green,
            size=power_widget_size,
            font=power_font
        )
        self.money_spent_widget = MoneySpentWidget(
            data=self.player.spent_credit,
            text_color=QColor(118, 181, 197),
            size=money_spent_widget_size,
            font=money_font
        )

        if self.combined_mode:
            # Combined mode: Create one composite widget for all resource widgets.

            self.setWindowTitle(f'{self.player.color_name} Combined HUD')

            central_widget = QWidget()
            layout = QVBoxLayout(central_widget)

            if self.hud_positions.get('show_name', True):
                layout.addWidget(self.name_widget)
            if self.hud_positions.get('show_flag', True):
                layout.addWidget(self.flag_widget)
            if self.hud_positions.get('show_money', True):
                layout.addWidget(self.money_widget)
            if self.hud_positions.get('show_money_spent', True):
                layout.addWidget(self.money_spent_widget)
            if self.hud_positions.get('show_power', True):
                layout.addWidget(self.power_widget)

            self.setCentralWidget(central_widget)
        else:
            # Separate mode: Create individual top-level windows for each resource widget.
            self.name_window = self.create_window_with_widget(
                f"Player {player_index} Name", self.name_widget, player_count, 'name', self.player.color_name
            )
            if self.hud_positions.get('show_name', True):
                self.name_window.show()
            else:
                self.name_window.hide()

            self.flag_window = self.create_window_with_widget(
                f"Player {player_index} Flag", self.flag_widget, player_count, 'flag', self.player.color_name
            )
            if self.hud_positions.get('show_flag', True):
                self.flag_window.show()
            else:
                self.flag_window.hide()

            self.money_window = self.create_window_with_widget(
                f"Player {player_index} Money", self.money_widget, player_count, 'money', self.player.color_name
            )
            if self.hud_positions.get('show_money', True):
                self.money_window.show()
            else:
                self.money_window.hide()

            self.power_window = self.create_window_with_widget(
                f"Player {player_index} Power", self.power_widget, player_count, 'power', self.player.color_name
            )
            if self.hud_positions.get('show_power', True):
                self.power_window.show()
            else:
                self.power_window.hide()

            self.money_spent_window = self.create_window_with_widget(
                f"Player {player_index} Money Spent", self.money_spent_widget, player_count, 'money_spent',
                self.player.color_name
            )
            if self.hud_positions.get('show_money_spent', True):
                self.money_spent_window.show()
            else:
                self.money_spent_window.hide()

            self.windows = [
                self.name_window,
                self.money_window,
                self.money_spent_window,
                self.power_window,
                self.flag_window
            ]

    def create_window_with_widget(self, title, widget, player_count, hud_type, player_color):
        """Create a new window for a given widget with a specified title."""
        window = QWidget()
        window.setWindowTitle(title)
        window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        window.setAttribute(Qt.WA_TranslucentBackground)

        # Get the initial position of the HUD using hud_type parameter
        pos = self.get_default_position(player_color, hud_type, player_count, self.hud_positions)
        window.setGeometry(pos['x'], pos['y'], widget.sizeHint().width(), widget.sizeHint().height())

        # Create layout and add widget
        layout = QVBoxLayout()
        layout.addWidget(widget)
        window.setLayout(layout)

        # Implement movable functionality with hud_type in closure:
        offset = None
        def mouse_press_event(event):
            nonlocal offset
            if event.button() == Qt.LeftButton:
                offset = event.pos()
        def mouse_move_event(event):
            nonlocal offset
            if offset is not None:
                x = event.globalX() - offset.x()
                y = event.globalY() - offset.y()
                window.move(x, y)
                self.update_hud_position_for_type(hud_type, x, y)
        window.mousePressEvent = mouse_press_event
        window.mouseMoveEvent = mouse_move_event

        window.show()  # Show the window immediately
        return window

    def update_hud_position_for_type(self, hud_type, x, y):
        if not isinstance(self.player.color_name, str):
            player_color_str = self.player.color_name.name()
        else:
            player_color_str = self.player.color_name

        if player_color_str not in self.hud_positions:
            self.hud_positions[player_color_str] = {}
        self.hud_positions[player_color_str][hud_type] = {"x": x, "y": y}

    def get_default_position(self, player_color, hud_type, player_count, hud_positions):
        if not isinstance(player_color, str):
            player_color_str = player_color.name()
        else:
            player_color_str = player_color

        if player_color_str not in hud_positions:
            hud_positions[player_color_str] = {}
        if hud_type not in hud_positions[player_color_str]:
            default_position = {"x": 100, "y": 100}
            hud_positions[player_color_str][hud_type] = default_position
        else:
            default_position = hud_positions[player_color_str][hud_type]
        default_position['x'] = int(default_position['x'])
        default_position['y'] = int(default_position['y'])
        return default_position

    def update_labels(self):
        """Update the money, money spent, and power values."""
        self.money_widget.update_data(self.player.balance)
        self.money_spent_widget.update_data(self.player.spent_credit)
        self.power_widget.update_data(self.player.power)
        if self.player.power < 0:
            self.power_widget.update_color(new_image_color=Qt.red, new_text_color=Qt.red)
        else:
            self.power_widget.update_color(new_image_color=Qt.green, new_text_color=Qt.green)

    def update_all_data_size(self, new_size):
        """Resize all DataWidgets in this ResourceWindow."""
        self.name_widget.update_data_size(new_size)
        self.money_widget.update_data_size(new_size)
        self.power_widget.update_data_size(new_size)

    def update_money_widget_color(self):
        money_color_option = self.hud_positions.get('money_color', 'Use player color').strip().lower()
        if money_color_option == 'use player color':
            money_text_color = self.player.color
        elif money_color_option == 'white':
            money_text_color = QColor(Qt.white)
        else:
            money_text_color = QColor(Qt.white)
        self.money_widget.update_color(new_text_color=money_text_color)
