import logging
import os
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QFontDatabase, QColor
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout

# Import the new widget classes
from DataWidget import MoneyWidget, PowerWidget, NameWidget, FlagWidget, MoneySpentWidget
from hud_position_utils import get_player_position, set_player_position
from player_identity import (
    build_player_hud_tooltip,
    get_combined_hud_title,
    get_player_bucket_key,
    get_player_display_label,
    get_player_flag_export_stem,
    get_player_flag_legacy_stems,
    get_player_legacy_bucket_keys,
)
from superweapon_panel import SuperweaponTimerPanel

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
    DEFAULT_MONEY_SPENT_COLOR = QColor(118, 181, 197)

    def __init__(self, player, player_count, hud_positions, player_index, combined_mode=False):
        """
        If combined_mode is True, all resource widgets are embedded in a single window.
        Otherwise, separate windows are created for each widget.
        """
        super().__init__()
        self.player = player
        self.hud_positions = hud_positions
        self.combined_mode = combined_mode
        self._last_exported_flag_key = None
        self.player_bucket_key = get_player_bucket_key(self.player, self.hud_positions)
        self.legacy_player_bucket_keys = get_player_legacy_bucket_keys(self.player, self.hud_positions)
        self.player_display_label = get_player_display_label(self.player, self.hud_positions)

        # Load sizes from hud_positions
        name_widget_size = self.hud_positions.get('name_widget_size', 50)
        money_widget_size = self.hud_positions.get('money_widget_size', 50)
        power_widget_size = self.hud_positions.get('power_widget_size', 50)
        flag_widget_size = self.hud_positions.get('flag_widget_size', 50)
        money_spent_widget_size = self.hud_positions.get('money_spent_widget_size', 50)
        superweapon_widget_size = self.hud_positions.get('superweapon_widget_size', 100)

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
            text_color=self.get_name_widget_color(),
            size=name_widget_size,
            font=username_font
        )
        self.flag_widget = FlagWidget(
            image_path=self.get_flag_image_path(),
            size=flag_widget_size
        )
        self.export_flag_image_if_needed()
        self.money_widget = MoneyWidget(
            data=self.player.balance,
            text_color=self.get_money_widget_color(),
            size=money_widget_size,
            font=money_font
        )
        power_image_color, power_text_color = self.get_power_widget_colors()
        self.power_widget = PowerWidget(
            data=self.player.power,
            image_path='icons/bolt.png',
            image_color=power_image_color,
            text_color=power_text_color,
            size=power_widget_size,
            font=power_font
        )
        self.money_spent_widget = MoneySpentWidget(
            data=self.player.spent_credit,
            text_color=self.get_money_spent_widget_color(),
            size=money_spent_widget_size,
            font=money_font
        )
        self.superweapon_widget = SuperweaponTimerPanel(
            player=self.player,
            hud_positions=self.hud_positions
        )
        self.superweapon_widget.update_size(superweapon_widget_size)
        self._apply_widget_tooltips()

        if self.combined_mode:
            # Combined mode: Create one composite widget for all resource widgets.

            self.setWindowTitle(get_combined_hud_title(self.player, self.hud_positions))

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
            if self.hud_positions.get('show_superweapons', True):
                layout.addWidget(self.superweapon_widget)

            self.setCentralWidget(central_widget)
        else:
            # Separate mode: Create individual top-level windows for each resource widget.
            self.name_window = self.create_window_with_widget(
                f"{self.player_display_label} Name", self.name_widget, player_count, 'name'
            )
            if self.hud_positions.get('show_name', True):
                self.name_window.show()
            else:
                self.name_window.hide()

            self.flag_window = self.create_window_with_widget(
                f"{self.player_display_label} Flag", self.flag_widget, player_count, 'flag'
            )
            if self.hud_positions.get('show_flag', True):
                self.flag_window.show()
            else:
                self.flag_window.hide()

            self.money_window = self.create_window_with_widget(
                f"{self.player_display_label} Money", self.money_widget, player_count, 'money'
            )
            if self.hud_positions.get('show_money', True):
                self.money_window.show()
            else:
                self.money_window.hide()

            self.power_window = self.create_window_with_widget(
                f"{self.player_display_label} Power", self.power_widget, player_count, 'power'
            )
            if self.hud_positions.get('show_power', True):
                self.power_window.show()
            else:
                self.power_window.hide()

            self.money_spent_window = self.create_window_with_widget(
                f"{self.player_display_label} Money Spent", self.money_spent_widget, player_count, 'money_spent'
            )
            if self.hud_positions.get('show_money_spent', True):
                self.money_spent_window.show()
            else:
                self.money_spent_window.hide()

            self.superweapon_window = self.create_window_with_widget(
                f"{self.player_display_label} Superweapons",
                self.superweapon_widget,
                player_count,
                'superweapons'
            )
            if self.hud_positions.get('show_superweapons', True):
                self.superweapon_window.show()
            else:
                self.superweapon_window.hide()

            self.windows = [
                self.name_window,
                self.money_window,
                self.money_spent_window,
                self.power_window,
                self.flag_window,
                self.superweapon_window,
            ]

    def _apply_widget_tooltips(self):
        self._set_tooltip_recursive(self.name_widget, build_player_hud_tooltip(self.player, self.hud_positions, "name"))
        self._set_tooltip_recursive(self.flag_widget, build_player_hud_tooltip(self.player, self.hud_positions, "flag"))
        self._set_tooltip_recursive(self.money_widget, build_player_hud_tooltip(self.player, self.hud_positions, "money"))
        self._set_tooltip_recursive(self.money_spent_widget, build_player_hud_tooltip(self.player, self.hud_positions, "money spent"))
        self._set_tooltip_recursive(self.power_widget, build_player_hud_tooltip(self.player, self.hud_positions, "power"))
        self._set_tooltip_recursive(self.superweapon_widget, build_player_hud_tooltip(self.player, self.hud_positions, "superweapon counter"))

    def _set_tooltip_recursive(self, widget, tooltip_text):
        widget.setToolTip(tooltip_text)
        for child in widget.findChildren(QWidget):
            child.setToolTip(tooltip_text)

    def create_window_with_widget(self, title, widget, player_count, hud_type):
        """Create a new window for a given widget with a specified title."""
        window = QWidget()
        window.setWindowTitle(title)
        if widget.toolTip():
            window.setToolTip(widget.toolTip())
        window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        window.setAttribute(Qt.WA_TranslucentBackground)

        # Get the initial position of the HUD using hud_type parameter
        pos = self.get_default_position(hud_type, player_count, self.hud_positions)
        window.setGeometry(0, 0, widget.sizeHint().width(), widget.sizeHint().height())

        # Create layout and add widget
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(widget)
        window.setLayout(layout)
        widget._container_window = window

        # Implement movable functionality with hud_type in closure:
        offset = None
        def mouse_press_event(event):
            nonlocal offset
            if event.button() == Qt.LeftButton:
                offset = event.pos()
                if hasattr(widget, '_dragging_container'):
                    widget._dragging_container = True
        def mouse_move_event(event):
            nonlocal offset
            if offset is not None:
                x = event.globalX() - offset.x()
                y = event.globalY() - offset.y()
                window.move(x, y)
                if hasattr(widget, 'top_left_to_anchor') and hasattr(widget, 'save_anchor_position'):
                    widget.save_anchor_position(widget.top_left_to_anchor(x, y, window.size()))
                else:
                    self.update_hud_position_for_type(hud_type, x, y)
        def mouse_release_event(event):
            nonlocal offset
            if event.button() == Qt.LeftButton:
                offset = None
                if hasattr(widget, 'top_left_to_anchor') and hasattr(widget, 'save_anchor_position'):
                    widget.save_anchor_position(widget.top_left_to_anchor(window.x(), window.y(), window.size()))
                else:
                    self.update_hud_position_for_type(hud_type, window.x(), window.y())
                if hasattr(widget, '_dragging_container'):
                    QTimer.singleShot(0, lambda: setattr(widget, '_dragging_container', False))
        window.mousePressEvent = mouse_press_event
        window.mouseMoveEvent = mouse_move_event
        window.mouseReleaseEvent = mouse_release_event

        def resize_event(event):
            QWidget.resizeEvent(window, event)
            if not hasattr(widget, 'anchor_to_top_left'):
                return
            if getattr(widget, '_applying_container_geometry', False):
                return
            if getattr(widget, '_dragging_container', False):
                return

            anchor = None
            if hasattr(widget, 'get_saved_anchor_position'):
                anchor = widget.get_saved_anchor_position()
            if not anchor:
                return

            pos = widget.anchor_to_top_left(anchor, window.size())
            new_x = pos['x']
            new_y = pos['y']
            if new_x != window.x() or new_y != window.y():
                window.move(new_x, new_y)
                if hasattr(widget, 'save_anchor_position'):
                    widget.save_anchor_position(anchor)
                else:
                    self.update_hud_position_for_type(hud_type, new_x, new_y)

        window.resizeEvent = resize_event

        window.show()  # Show the window immediately
        window.adjustSize()
        if hasattr(widget, 'anchor_to_top_left') and hasattr(widget, 'get_saved_anchor_position'):
            anchor = widget.get_saved_anchor_position() or pos
            widget.save_anchor_position(anchor)
            pos = widget.anchor_to_top_left(anchor, window.size())
        window.move(pos['x'], pos['y'])
        if hasattr(widget, '_schedule_anchor_refresh'):
            widget._schedule_anchor_refresh()
        return window

    def update_hud_position_for_type(self, hud_type, x, y):
        set_player_position(self.hud_positions, self.player_bucket_key, hud_type, x, y)

    def get_default_position(self, hud_type, player_count, hud_positions):

        legacy_keys = []
        if hud_type == 'superweapons':
            legacy_keys = ['superweapon']

        return get_player_position(
            hud_positions,
            self.player_bucket_key,
            hud_type,
            legacy_root_keys=legacy_keys,
            legacy_bucket_keys=self.legacy_player_bucket_keys,
        )

    def update_labels(self):
        """Update the money, money spent, and power values."""
        self.refresh_flag_widget()
        self.update_name_widget_color()
        self.update_money_widget_color()
        self.update_money_spent_widget_color()
        self.update_power_widget_color()
        self.money_widget.update_data(self.player.balance)
        self.money_spent_widget.update_data(self.player.spent_credit)
        self.power_widget.update_data(self.player.power)
        self.superweapon_widget.update_labels()

    def update_all_data_size(self, new_size):
        """Resize all DataWidgets in this ResourceWindow."""
        self.name_widget.update_data_size(new_size)
        self.money_widget.update_data_size(new_size)
        self.power_widget.update_data_size(new_size)

    def export_flag_image_if_needed(self):
        try:
            folder_name = "player flags"
            os.makedirs(folder_name, exist_ok=True)
            flag_export_stem = get_player_flag_export_stem(self.player, self.hud_positions)
            flag_image_path = self.get_flag_image_path()
            export_key = (flag_export_stem, flag_image_path, self.flag_widget.size)
            if self._last_exported_flag_key == export_key:
                return
            filename = os.path.join(folder_name, f"{flag_export_stem}_flag.png")
            pixmap = QPixmap(flag_image_path).scaled(
                self.flag_widget.size,
                self.flag_widget.size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            if pixmap.isNull():
                logging.warning("Skipping flag export for %s because the pixmap is null.", self.player.username.value)
                return
            if not pixmap.save(filename, "PNG"):
                logging.warning("Failed to save flag image for %s to %s", self.player.username.value, filename)
                return
            for legacy_stem in get_player_flag_legacy_stems(self.player, self.hud_positions):
                legacy_filename = os.path.join(folder_name, f"{legacy_stem}_flag.png")
                if os.path.exists(legacy_filename):
                    os.remove(legacy_filename)
            self._last_exported_flag_key = export_key
            logging.debug("Saved flag image for %s to %s", self.player.username.value, filename)
        except Exception as e:
            logging.exception("Failed to export flag image for %s: %s", self.player.username.value, e)

    def get_flag_image_path(self):
        try:
            country_name = self.player.country_name.value.decode('utf-8').strip('\x00')
        except Exception:
            country_name = ''
        flag_filename = faction_to_flag.get(country_name, "RA2_Yuricountry.png")
        return os.path.join("Flags", "PNG", flag_filename)

    def refresh_flag_widget(self):
        new_image_path = self.get_flag_image_path()
        if self.flag_widget.image_path != new_image_path:
            self.flag_widget.image_path = new_image_path
            self.flag_widget.load_and_set_image()
            self.flag_widget.adjust_size()
            self._last_exported_flag_key = None
        self.export_flag_image_if_needed()

    def update_money_widget_color(self):
        self.money_widget.update_color(new_text_color=self.get_money_widget_color())

    def update_name_widget_color(self):
        self.name_widget.update_color(new_text_color=self.get_name_widget_color())

    def update_money_spent_widget_color(self):
        self.money_spent_widget.update_color(new_text_color=self.get_money_spent_widget_color())
        self.money_spent_widget.load_and_set_image()
        self.money_spent_widget.adjust_size()

    def update_power_widget_color(self):
        image_color, text_color = self.get_power_widget_colors()
        self.power_widget.update_color(new_image_color=image_color, new_text_color=text_color)

    def get_name_widget_color(self):
        return self._resolve_custom_or_default_color(
            mode_key='name_color_mode',
            color_key='name_color',
            default_color=self.player.color,
        )

    def get_money_widget_color(self):
        mode = str(self.hud_positions.get('money_color_mode', '')).strip().lower()
        custom_color = self._get_custom_color('money_custom_color')
        if mode == 'custom' and custom_color is not None:
            return custom_color

        money_color_option = str(self.hud_positions.get('money_color', 'Use player color')).strip().lower()
        if money_color_option == 'white':
            return QColor(Qt.white)
        return QColor(self.player.color)

    def get_money_spent_widget_color(self):
        return self._resolve_custom_or_default_color(
            mode_key='money_spent_color_mode',
            color_key='money_spent_color',
            default_color=self.DEFAULT_MONEY_SPENT_COLOR,
        )

    def get_power_widget_colors(self):
        is_low = self.player.power < 0
        if is_low:
            mode = str(self.hud_positions.get('power_low_color_mode', '')).strip().lower()
            custom = self._get_custom_color('power_low_color') if mode == 'custom' else None
            color = custom if custom is not None else QColor(Qt.red)
        else:
            mode = str(self.hud_positions.get('power_good_color_mode', '')).strip().lower()
            custom = self._get_custom_color('power_good_color') if mode == 'custom' else None
            color = custom if custom is not None else QColor(Qt.green)
        return color, color

    def _get_custom_color(self, key):
        color_value = self.hud_positions.get(key)
        color = QColor(color_value) if color_value else QColor()
        if color.isValid():
            return color
        return None

    def _resolve_custom_or_default_color(self, mode_key, color_key, default_color):
        mode = str(self.hud_positions.get(mode_key, '')).strip().lower()
        custom_color = self._get_custom_color(color_key)
        if mode == 'custom' and custom_color is not None:
            return custom_color
        return QColor(default_color)
