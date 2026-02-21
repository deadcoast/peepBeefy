# v0.0.4: README.md

## Summary

Goal:
  Show gamers what's actually running and what is hogging CPU / RAM / Disk,
  including "invisible" service-backed processes that don't show in the taskbar.

Quick start (Windows 11):

- Install uv if you don't already have it:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Start the interactive CLI (zero typing):
> [Double-click RUN_peepBeefy.bat](.logs/legacy/specs/v0.0.3/install.bat)

Or from the terminal (run inside the root folder):

```powershell
beefy                # interactive mode
beefy peep all       # direct CLI
```

> uv handles Python and all dependencies automatically — no manual pip installs needed.

---

## Usage

### Core Commands

```ps1
beefy peep all         # Quick Scan (recommended)
beefy peep io          # Disk hogs (stutter risk)
beefy peep cpu         # CPU hogs
beefy peep clutter     # Tagged gamer background stacks (RGB/VR/VPN/Overlays)
beefy baseline save    # save a baseline snapshot
beefy baseline diff    # see what started itself.
```

### Configuration Commands

```ps1
beefy config show      # Display current configuration
beefy config set       # Modify configuration settings
beefy config reset     # Reset to default configuration
```

### Banner Commands

```ps1
beefy banner preview              # Preview available banners in a grid
beefy banner preview --category ALT  # Preview banners from specific category
beefy banner preview --page 2     # Navigate to page 2 of banner previews
```

### Theme Commands

```ps1
beefy theme set CRT_Cyan          # Set theme to CRT Cyan (default)
beefy theme set Amber_Terminal    # Set theme to Amber Terminal
beefy theme set Green_Phosphor    # Set theme to Green Phosphor
beefy theme set Synthwave         # Set theme to Synthwave
```

> [!NOTE]
> This version does NOT yet integrate the `trim fat` command option with the `--kill` flag to end processes.

---

## Features

### Random Banner System
- **Multiple ASCII Art Banners**: Choose from various ASCII art logos stored in the `.assets` directory
- **Random Selection**: Different banner displays on each launch (configurable)
- **Banner Modes**:
  - `random`: Show a different banner each time
  - `fixed`: Always show the same banner
  - `category`: Random selection from specific categories
- **Categories**: 1ST_BEEFS, ALT, CURSIVE, FAROUT, LIB, MIN

### Fire Animation
- **DOOM PSX-Inspired Effects**: Optional animated banners with fire effects
- **Configurable Intensity**: Choose from subtle, normal, or intense animation
- **Customizable Duration**: Set animation duration (0.5-10.0 seconds)
- **Adjustable FPS**: Configure frames per second (4-30 FPS)
- **Terminal Compatibility**: Automatically degrades to 8-bit colors on limited terminals

### Theme System
- **Multiple Color Themes**:
  - **CRT_Cyan** (default): Classic cyan terminal aesthetic
  - **Amber_Terminal**: Warm amber/orange palette
  - **Green_Phosphor**: Classic green phosphor monitor
  - **Synthwave**: Magenta/pink retro aesthetic
- **Consistent Styling**: DOUBLE box borders maintained across all themes
- **Terminal Detection**: Automatic RGB/ANSI color fallback

### Configuration System
- **Persistent Settings**: Configuration saved to `~/.peepbeefy/config.json`
- **First-Run Wizard**: Interactive setup on first launch
- **Settings Menu**: Easy reconfiguration through interactive menu
- **Schema Validation**: Automatic validation and migration of config files
- **Graceful Fallbacks**: Corrupted configs are backed up and replaced with defaults

### Banner Preview
- **Grid Layout**: View multiple banners at once
- **Pagination**: Navigate through large banner collections
- **Metadata Display**: See banner name, category, author, and description
- **Animation Preview**: Test animation effects before selecting
- **Adaptive Layout**: Automatically adjusts columns based on terminal width

### Performance
- **Fast Startup**: <200ms banner display with caching
- **Banner Caching**: Parsed banners cached for instant loading
- **Lazy Loading**: Animation engine loaded only when needed
- **Optimized Rendering**: Pre-computed animation frames for smooth playback

---

## Configuration

### Configuration File Location
- **Windows**: `%USERPROFILE%\.peepbeefy\config.json`
- **Linux/Mac**: `~/.peepbeefy/config.json`

### Configuration Options

```json
{
  "version": 1,
  "first_run_complete": true,
  "theme_variant": "CRT_Cyan",
  "banner": {
    "mode": "random",
    "selected_banner": null,
    "selected_categories": ["1ST_BEEFS"],
    "animation_enabled": true,
    "animation_duration": 3.0,
    "animation_fps": 8,
    "animation_intensity": "normal"
  }
}
```

### First-Run Setup
On first launch, peepBeefy will guide you through an interactive setup wizard:
1. **Theme Selection**: Choose your preferred color theme with visual previews
2. **Banner Mode**: Select how banners are displayed (random, fixed, or category)
3. **Animation Preferences**: Enable/disable animations and set intensity

You can re-run the setup wizard anytime from the Settings menu.

---

## Develeoper Notes

### Version Control System

> ATTN: agents

```toml
[agents]
version_authority: false

[human]
version_authority: true
```

> [!NOTE]
> EXCEPTION: Up to and including v0.0.4, the source code WAS part of the documentation, as it was still contained. From v0.0.5 specifications the source code will be versioned separately, and github will be the primary version control system for the SOURCE CODE.

1. A legacy-spec-directory is created in the [specs-archive](.logs/legacy/specs) with its working version as the directory title.
2. The new version will now take effect in the continued development of the ongoing project files.

---

peepBeefy: `FATBOI_PROCESSES_DESTROYER_5000`

---
