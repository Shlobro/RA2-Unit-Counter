# Combined HUD Mode Documentation

## Overview

Combined HUD Mode is a display option in RA2-Viewer that consolidates all player information into a single movable window per player. Instead of having separate windows for each data type (money, power, name, etc.), everything is unified into one cohesive interface.

## Architecture

### Window Structure
- **Top Section**: Resource information widgets
  - Player name with faction-colored text
  - Country flag image
  - Money display with customizable colors
  - Power display with dynamic green/red indication
  - Money spent tracking (optional)

- **Bottom Section**: Unit counter displays with two modes:
  - **Single Combined Mode**: Unit images and numbers together in one widget
  - **Separated Counters Mode**: Side-by-side layout with images-only and numbers-only widgets

### Implementation Details
- **Main Class**: `CombinedHudWindow` in `UnitWindow.py:253-390`
- **Resource Integration**: Uses `ResourceWindow` with `combined_mode=True`
- **Layout System**: Vertical `QVBoxLayout` with embedded widgets
- **Window Properties**: Frameless, always-on-top, translucent background

## Complete Settings & Adjustments

### Core HUD Mode Settings

#### Combined HUD Toggle
- **Setting**: `'combined_hud'` in hud_positions.json
- **Control**: Checkbox in control panel "Use Combined HUD Mode"
- **Default**: `false`
- **Function**: Switches between Combined HUD (single window per player) and Separate HUD (multiple windows per player) modes

#### Separate Unit Counters
- **Setting**: `'separate_unit_counters'` in hud_positions.json  
- **Control**: Checkbox in control panel
- **Default**: `false`
- **Function**: Within Combined HUD, splits the unit counter section into two side-by-side widgets (images-only + numbers-only)

### Resource Widget Visibility Controls

#### Show/Hide Toggles
- **Show Name**: `'show_name'` (default: `true`)
- **Show Money**: `'show_money'` (default: `true`) 
- **Show Power**: `'show_power'` (default: `true`)
- **Show Flag**: `'show_flag'` (default: `true`)
- **Show Money Spent**: `'show_money_spent'` (default: `false`)

Each toggle individually controls whether that widget appears in the Combined HUD.

### Size Customization Settings

#### Individual Widget Sizes
- **Name Widget Size**: `'name_widget_size'` (default: 50)
- **Money Widget Size**: `'money_widget_size'` (default: 50)  
- **Power Widget Size**: `'power_widget_size'` (default: 50)
- **Flag Widget Size**: `'flag_widget_size'` (default: 50)
- **Money Spent Widget Size**: `'money_spent_widget_size'` (default: 50)

#### Unit Counter Sizing
- **Unit Counter Size**: `'unit_counter_size'` (default: 75)
  - Used when separate_unit_counters is `false`
  - Controls overall size of the combined unit display

- **Image Size**: `'image_size'` (default: 75)
  - Used when separate_unit_counters is `true`
  - Controls size of unit images in the images-only widget

- **Number Size**: `'number_size'` (default: 75)
  - Used when separate_unit_counters is `true`
  - Controls size of unit numbers in the numbers-only widget

- **Distance Between Numbers**: `'distance_between_numbers'` (default: 0)
  - Spacing between number elements when using separated counters

### Visual Appearance Settings

#### Money Display Color
- **Setting**: `'money_color'` 
- **Options**: "Use player color" (default) or "White"
- **Function**: Determines text color for money display widget

#### Unit Display Options
- **Unit Layout**: `'unit_layout'` (default: "Vertical")
  - Options: "Vertical" or "Horizontal"
  - Controls arrangement of unit counters within their container

- **Show Unit Frames**: `'show_unit_frames'` (default: `true`)
  - Toggles frames/borders around unit counter displays

### Positioning System

#### Automatic Position Storage
- **Storage Location**: Per-player color sections in hud_positions.json
- **Key Format**: `[player_color]['combined']` with `{"x": int, "y": int}`
- **Examples**:
  ```json
  "green": {
    "combined": {"x": 273, "y": 173}
  },
  "blue": {
    "combined": {"x": 774, "y": 250}
  }
  ```

#### Movement Interaction
- **Method**: Click and drag anywhere on the Combined HUD window
- **Real-time Updates**: Position immediately saved during drag operations
- **Per-Player Storage**: Each player color maintains independent positioning

### Font Configuration

#### Built-in Font System
- **Money Display**: Futured.ttf (custom font) at 18pt Bold, fallback to Arial
- **Power Display**: Impact at 18pt Bold  
- **Name Display**: Roboto at 16pt Bold
- **Font Scaling**: All fonts scale with their respective widget size settings

## Usage Instructions

### Enabling Combined HUD Mode
1. Open the control panel
2. Check "Use Combined HUD Mode" 
3. Combined HUD windows will replace separate windows for each player

### Customizing Layout
1. **To enable separated unit counters**: Check the separate unit counters option in control panel
2. **To resize widgets**: Use the size spinboxes in control panel for each widget type
3. **To reposition**: Click and drag any Combined HUD window to desired location

### Configuration Persistence
- All settings automatically save to `hud_positions.json`
- Positions and preferences persist between application sessions
- No manual configuration file editing required

## Technical Implementation

### Key Classes
- **CombinedHudWindow**: Main container class (`UnitWindow.py:253-390`)
- **ResourceWindow**: Resource widgets container with `combined_mode=True`
- **UnitWindowWithImages**: Single combined unit display widget
- **UnitWindowImagesOnly/NumbersOnly**: Separated unit counter widgets

### Update System
- **Real-time Data**: `update_labels()` method refreshes all embedded widgets
- **Dynamic Sizing**: `update_unit_counters_size()` handles runtime size changes
- **Layout Updates**: `update_unit_section()` rebuilds unit counter layout when toggling separation mode

### State Management
- **Configuration Storage**: `hud_positions` dictionary in app state
- **Position Tracking**: `update_hud_position()` method saves coordinates during movement
- **Widget Lifecycle**: Proper cleanup and recreation when switching modes

## Advanced Features

### Dynamic Unit Counter Switching
- Switch between single combined and separated unit counters without recreating the entire Combined HUD
- Smooth transition preserves window position and other settings
- Independent size controls become active/inactive based on separation mode

### Multi-Player Support  
- Each player gets their own Combined HUD window
- Independent positioning and sizing per player color
- Simultaneous display of up to 8 players with individual customization

### Performance Optimizations
- Efficient widget reuse when switching unit counter modes
- Minimal memory footprint through proper widget lifecycle management
- Real-time updates without full window recreation