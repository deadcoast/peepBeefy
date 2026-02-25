# Requirements Document: peepBeefy Enhancements

## Introduction

This document specifies requirements for comprehensive enhancements to peepBeefy, a gamer-focused CLI process monitoring tool. The enhancements focus on visual improvements, quality-of-life features, and integration patterns inspired by hyfetch's architecture. The goal is to elevate peepBeefy's retro aesthetic delivery while maintaining its core mission: making system visibility accessible to gamers who may be opening a terminal for the first time.

## Glossary

- **Banner_System**: The ASCII art display system that shows the peepBeefy logo with optional animations
- **Random_Banner_Mode**: A feature that loads different ASCII art banners randomly on startup
- **ASCII_Database**: Collection of pre-designed ASCII art logos stored in .assets directory
- **Fire_Animation**: The DOOM PSX-inspired animated fire effect currently used in install.py
- **Config_System**: User configuration storage and retrieval mechanism
- **Interactive_CLI**: The CLI03 layer - menu-driven interface for beginners
- **Retro_Theme**: The CRT terminal aesthetic with cyan/amber color palette and DOUBLE box borders
- **hyfetch_Pattern**: Integration and configuration patterns learned from the hyfetch reference implementation

## Requirements

### Requirement 1: Random Banner Mode System

**User Story:** As a peepBeefy user, I want to see different ASCII art banners when I launch the application, so that the experience feels fresh and visually engaging.

#### Acceptance Criteria

1. THE Banner_System SHALL load ASCII art from the ASCII_Database on application startup
2. WHEN the application starts, THE Banner_System SHALL randomly select one banner from available options
3. THE Banner_System SHALL support multiple banner categories (1ST_BEEFS, ALT, CURSIVE, FAROUT, LIB, MIN)
4. WHERE Random_Banner_Mode is enabled, THE Banner_System SHALL display a different banner each launch
5. THE Banner_System SHALL parse the ASCII_Database format with category headers and banner definitions
6. WHEN a banner is selected, THE Banner_System SHALL apply the Retro_Theme color styling
7. THE Banner_System SHALL maintain the current BANNER as a fallback if Random_Banner_Mode is disabled

### Requirement 2: Banner Configuration System

**User Story:** As a peepBeefy user, I want to configure which banners appear, so that I can customize my experience.

#### Acceptance Criteria

1. THE Config_System SHALL store user banner preferences persistently
2. THE Config_System SHALL support banner mode options: random, fixed, or specific-category
3. WHEN a user selects "fixed" mode, THE Config_System SHALL remember their chosen banner
4. WHEN a user selects "random" mode, THE Config_System SHALL allow category filtering
5. THE Interactive_CLI SHALL provide a banner selection menu during configuration
6. THE Interactive_CLI SHALL display preview samples of available banners
7. WHERE a user has no saved preference, THE Banner_System SHALL default to the current BANNER

### Requirement 3: Fire Animation Integration

**User Story:** As a peepBeefy user, I want optional animated banners, so that the application feels more dynamic and engaging.

#### Acceptance Criteria

1. THE Banner_System SHALL support both static and animated banner modes
2. WHEN Fire_Animation is enabled, THE Banner_System SHALL apply the DOOM PSX fire effect to selected banners
3. THE Fire_Animation SHALL use the existing 12-step palette and 9-frame sway cycle
4. THE Fire_Animation SHALL adapt to different ASCII art dimensions automatically
5. WHERE a banner has designated "flame zones", THE Fire_Animation SHALL apply per-line coloring
6. THE Config_System SHALL allow users to enable or disable animations
7. IF animation is disabled, THEN THE Banner_System SHALL display static colored banners

### Requirement 4: ASCII Database Parser

**User Story:** As a developer, I want a robust ASCII art parser, so that adding new banners is straightforward.

#### Acceptance Criteria

1. THE ASCII_Database SHALL use the existing format with "---" delimiters and category:name headers
2. THE Banner_System SHALL parse multi-line ASCII art blocks correctly
3. WHEN parsing fails, THE Banner_System SHALL log an error and continue with available banners
4. THE Banner_System SHALL validate ASCII art dimensions before display
5. THE Banner_System SHALL support UTF-8 encoded ASCII art files
6. FOR ALL valid ASCII art entries, parsing then formatting then parsing SHALL produce equivalent output (round-trip property)

### Requirement 5: Enhanced Interactive Menu System

**User Story:** As a peepBeefy user, I want improved menu navigation, so that I can access features more efficiently.

#### Acceptance Criteria

1. THE Interactive_CLI SHALL add a "Settings" menu option for configuration access
2. THE Interactive_CLI SHALL display keyboard shortcuts alongside menu items
3. WHEN a user types a number, THE Interactive_CLI SHALL execute the corresponding menu item
4. THE Interactive_CLI SHALL support command history navigation (up/down arrows)
5. THE Interactive_CLI SHALL provide a "recent commands" quick-access list
6. WHERE a command fails, THE Interactive_CLI SHALL display helpful error messages with suggested fixes
7. THE Interactive_CLI SHALL maintain the current command-teaching approach (showing "beefy peep all" syntax)

### Requirement 6: Configuration File System

**User Story:** As a peepBeefy user, I want my preferences saved automatically, so that I don't have to reconfigure every launch.

#### Acceptance Criteria

1. THE Config_System SHALL store configuration in a JSON file at a standard location
2. THE Config_System SHALL create the config directory if it does not exist
3. WHEN configuration is saved, THE Config_System SHALL write valid JSON with proper encoding
4. WHEN configuration is loaded, THE Config_System SHALL validate the schema
5. IF configuration is invalid or missing, THEN THE Config_System SHALL use sensible defaults
6. THE Config_System SHALL support configuration migration for version updates
7. THE Config_System SHALL store: banner_mode, selected_banner, animation_enabled, theme_variant, and user_preferences

### Requirement 7: Theme Variant System

**User Story:** As a peepBeefy user, I want alternative color themes, so that I can match my terminal aesthetic.

#### Acceptance Criteria

1. THE Retro_Theme SHALL support multiple color palette variants
2. THE Retro_Theme SHALL include at least: CRT_Cyan (default), Amber_Terminal, Green_Phosphor, and Synthwave
3. WHEN a theme is selected, THE Retro_Theme SHALL apply consistent colors across all UI elements
4. THE Retro_Theme SHALL maintain the DOUBLE box border style across all themes
5. THE Config_System SHALL persist the selected theme variant
6. THE Interactive_CLI SHALL provide a theme preview and selection menu
7. WHERE no theme is configured, THE Retro_Theme SHALL default to CRT_Cyan

### Requirement 8: Startup Performance Optimization

**User Story:** As a peepBeefy user, I want fast application startup, so that I can quickly check system status.

#### Acceptance Criteria

1. THE Banner_System SHALL cache parsed ASCII art after first load
2. THE Banner_System SHALL load ASCII_Database asynchronously if possible
3. WHEN the application starts, THE Banner_System SHALL display a banner within 200ms
4. THE Config_System SHALL load configuration without blocking the main thread
5. WHERE caching is used, THE Banner_System SHALL invalidate cache when ASCII files change
6. THE Banner_System SHALL lazy-load animation frames only when animation is enabled

### Requirement 9: Banner Metadata System

**User Story:** As a developer, I want banner metadata support, so that banners can have descriptions and attribution.

#### Acceptance Criteria

1. THE ASCII_Database SHALL support optional metadata comments above banner definitions
2. THE Banner_System SHALL parse metadata including: author, description, dimensions, and animation_compatible
3. WHEN displaying banner selection, THE Interactive_CLI SHALL show banner descriptions
4. THE Banner_System SHALL filter banners by animation compatibility when Fire_Animation is enabled
5. WHERE metadata is missing, THE Banner_System SHALL use the banner name as description

### Requirement 10: Error Recovery and Fallbacks

**User Story:** As a peepBeefy user, I want the application to work even if banner files are corrupted, so that I can always access core functionality.

#### Acceptance Criteria

1. IF ASCII_Database files are missing, THEN THE Banner_System SHALL use the hardcoded default BANNER
2. IF a selected banner fails to load, THEN THE Banner_System SHALL fall back to a working banner
3. WHEN errors occur, THE Banner_System SHALL log detailed error information for debugging
4. THE Banner_System SHALL validate banner dimensions against terminal size
5. IF a banner is too large for the terminal, THEN THE Banner_System SHALL either scale or select an alternative
6. THE Config_System SHALL not crash if configuration file is corrupted
7. WHERE configuration is unreadable, THE Config_System SHALL backup the corrupted file and create fresh config

### Requirement 11: Banner Animation Customization

**User Story:** As a peepBeefy user, I want to customize animation behavior, so that I can balance visual appeal with performance.

#### Acceptance Criteria

1. THE Config_System SHALL store animation preferences: duration, fps, and intensity
2. WHEN Fire_Animation runs, THE Banner_System SHALL respect configured duration and fps
3. THE Fire_Animation SHALL support intensity levels: subtle, normal, and intense
4. WHERE intensity is "subtle", THE Fire_Animation SHALL reduce flicker probability by 50%
5. WHERE intensity is "intense", THE Fire_Animation SHALL increase flicker probability by 50%
6. THE Interactive_CLI SHALL provide animation customization in the settings menu

### Requirement 12: hyfetch-Inspired Configuration Flow

**User Story:** As a peepBeefy user, I want an interactive first-run configuration experience, so that I can set up my preferences easily.

#### Acceptance Criteria

1. WHEN peepBeefy runs for the first time, THE Config_System SHALL detect missing configuration
2. WHEN configuration is missing, THE Interactive_CLI SHALL launch a guided setup wizard
3. THE Interactive_CLI SHALL present configuration options with visual previews
4. THE Interactive_CLI SHALL allow users to skip configuration and use defaults
5. THE Interactive_CLI SHALL display a progress indicator showing configuration steps
6. WHEN configuration is complete, THE Config_System SHALL save preferences automatically
7. THE Interactive_CLI SHALL offer a "reconfigure" command to re-run the setup wizard

### Requirement 13: Banner Preview System

**User Story:** As a peepBeefy user, I want to preview banners before selecting them, so that I can make informed choices.

#### Acceptance Criteria

1. THE Interactive_CLI SHALL display banner previews in a grid layout
2. THE Banner_System SHALL render preview banners at reduced size if needed
3. WHEN previewing animated banners, THE Banner_System SHALL show a brief animation sample
4. THE Interactive_CLI SHALL support pagination for large banner collections
5. THE Interactive_CLI SHALL display banner metadata alongside previews
6. WHERE terminal size is limited, THE Interactive_CLI SHALL adjust preview layout automatically

### Requirement 14: Logging and Diagnostics

**User Story:** As a developer, I want comprehensive logging, so that I can diagnose issues with banner loading and configuration.

#### Acceptance Criteria

1. THE Banner_System SHALL log banner selection decisions at INFO level
2. THE Banner_System SHALL log parsing errors at ERROR level with file and line information
3. THE Config_System SHALL log configuration changes at INFO level
4. WHEN debug mode is enabled, THE Banner_System SHALL log detailed parsing and rendering information
5. THE Banner_System SHALL write logs to a standard location (.logs directory)
6. THE Banner_System SHALL rotate log files to prevent excessive disk usage

### Requirement 15: Terminal Compatibility

**User Story:** As a peepBeefy user, I want the application to work across different terminals, so that I have a consistent experience.

#### Acceptance Criteria

1. THE Banner_System SHALL detect terminal color support (8-bit vs RGB)
2. WHEN terminal supports only 8-bit color, THE Retro_Theme SHALL use ANSI fallback colors
3. THE Banner_System SHALL detect terminal dimensions before rendering
4. IF terminal is too small, THEN THE Banner_System SHALL display a minimal banner or text-only header
5. THE Fire_Animation SHALL gracefully degrade on terminals without RGB support
6. THE Banner_System SHALL handle Windows Terminal, PowerShell, Git Bash, and WSL correctly

