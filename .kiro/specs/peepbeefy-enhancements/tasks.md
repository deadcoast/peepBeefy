# Implementation Plan: peepBeefy Enhancements

## Overview

This implementation plan converts the peepBeefy enhancements design into actionable coding tasks. The implementation follows a 4-phase approach: Core Infrastructure, Animation System, Interactive Configuration, and Polish & Optimization. Each task builds incrementally on previous work, with checkpoints to validate progress.

The implementation will use **Python** with the Rich library for terminal rendering, following peepBeefy's existing architecture.

## Tasks

- [x] 1. Phase 1: Core Infrastructure - Banner System Foundation
  - [x] 1.1 Create banner.py module with data models
    - Implement `BannerMetadata` dataclass with category, name, author, description, dimensions, and animation_compatible fields
    - Implement `Banner` dataclass with metadata and lines, including width and height properties
    - Add type hints and docstrings for all classes
    - _Requirements: 1.1, 1.3, 4.1, 9.1_
  
  - [x] 1.2 Write property test for Banner data model
    - **Property 3: Banner Parsing Preserves Content**
    - **Validates: Requirements 1.5, 4.2, 4.5**
  
  - [x] 1.3 Implement BannerDatabase class with ASCII parser
    - Create `BannerDatabase` class with `__init__` accepting assets_dir Path
    - Implement state machine parser for ASCII database format (INITIAL → DELIMITER → DEFINITIONS → HEADER → CONTENT states)
    - Parse category:name headers and extract banner content lines
    - Handle "---" delimiters and DEFINITIONS section
    - Preserve whitespace and special characters in ASCII art
    - Return Dict[str, List[Banner]] mapping categories to banner lists
    - _Requirements: 1.1, 1.3, 4.1, 4.2, 4.5_
  
  - [x] 1.4 Write property tests for BannerDatabase parser
    - **Property 2: Banner Category Grouping**
    - **Property 38: Parsing Error Continuation**
    - **Validates: Requirements 1.3, 4.3**
  
  - [x] 1.5 Implement banner selection methods in BannerDatabase
    - Implement `get_banner()` method with optional category and name parameters
    - Implement `get_random_banner()` with optional category filtering
    - Implement `list_categories()` to return available categories
    - Add hardcoded fallback banner for error recovery
    - _Requirements: 1.2, 1.4, 10.1, 10.2_
  
  - [x] 1.6 Write property test for random banner selection
    - **Property 1: Banner Random Selection Distribution**
    - **Validates: Requirements 1.2, 1.4**

  - [x] 1.7 Add banner metadata parsing support
    - Parse metadata comments (lines starting with "# key: value") after banner headers
    - Extract author, description, animation_compatible, flame_lines fields
    - Use banner name as default description if metadata missing
    - Handle unknown metadata keys gracefully (forward compatibility)
    - _Requirements: 9.1, 9.2, 9.5_
  
  - [x] 1.8 Write property tests for banner metadata
    - **Property 19: Banner Metadata Parsing**
    - **Property 20: Banner Metadata Default Fallback**
    - **Validates: Requirements 9.1, 9.2, 9.5**

- [x] 2. Phase 1: Core Infrastructure - Configuration System
  - [x] 2.1 Create config.py module with configuration data models
    - Implement `BannerConfig` dataclass with mode, selected_banner, selected_categories, animation settings
    - Implement `AppConfig` dataclass with version, first_run_complete, theme_variant, banner, user_preferences
    - Add default values matching design specification
    - _Requirements: 2.1, 2.2, 2.3, 6.7_
  
  - [x] 2.2 Implement ConfigManager class with JSON persistence
    - Create `ConfigManager` class with CONFIG_DIR and CONFIG_FILE class variables
    - Implement `load()` method to read JSON config from disk
    - Implement `save()` method with atomic write (temp file + rename)
    - Create config directory if it doesn't exist
    - Handle FileNotFoundError by returning default AppConfig
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 2.3 Write property tests for configuration persistence
    - **Property 5: Configuration Round-Trip Preservation**
    - **Property 6: Configuration Directory Creation**
    - **Property 7: Configuration JSON Validity**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 3.6, 6.2, 6.3, 6.7, 7.5, 11.1**
  
  - [x] 2.4 Add configuration validation and error handling
    - Implement schema validation in `load()` method
    - Validate animation_duration range (0.5-10.0)
    - Validate animation_fps range (4-30)
    - Validate theme_variant against available themes
    - Handle JSONDecodeError for corrupted config files
    - Backup corrupted config files before creating fresh config
    - _Requirements: 6.4, 6.5, 10.6, 10.7_
  
  - [x] 2.5 Write property tests for configuration validation
    - **Property 8: Configuration Schema Validation**
    - **Property 26: Corrupted Config Recovery**
    - **Validates: Requirements 6.4, 10.6, 10.7**

  - [x] 2.6 Implement configuration migration system
    - Implement `migrate()` method with version chain support
    - Add `is_first_run()` method to detect missing config
    - Create migration function template for future schema changes
    - Log migration operations at INFO level
    - _Requirements: 6.6, 12.1, 14.3_
  
  - [x] 2.7 Write property test for configuration migration
    - **Property 9: Configuration Version Migration**
    - **Validates: Requirements 6.6**

- [x] 3. Phase 1: Core Infrastructure - Theme System
  - [x] 3.1 Create themes.py module with theme data models
    - Implement `ColorPalette` dataclass with primary, highlight, success, error, warning, dim, text colors
    - Implement `Theme` class with name, palette, and styling methods
    - Implement `get_box_style()` returning box.DOUBLE
    - Implement `get_border_style()` returning palette.primary
    - Implement `style_command()` and `style_description()` methods
    - _Requirements: 7.1, 7.2, 7.3, 7.4_
  
  - [x] 3.2 Implement ThemeRegistry with predefined themes
    - Create `ThemeRegistry` class with THEMES class variable
    - Define CRT_Cyan theme (default) with cyan/white palette
    - Define Amber_Terminal theme with amber/orange palette
    - Define Green_Phosphor theme with green palette
    - Define Synthwave theme with magenta/pink palette
    - Implement `get_theme()` class method with fallback to CRT_Cyan
    - Implement `list_themes()` class method
    - _Requirements: 7.2, 7.6, 7.7_
  
  - [x] 3.3 Write property tests for theme system
    - **Property 10: Theme Box Style Consistency**
    - **Property 11: Theme Color Consistency**
    - **Validates: Requirements 7.3, 7.4**
  
  - [x] 3.4 Implement terminal capability detection
    - Create `TerminalCapabilities` class with static methods
    - Implement `supports_rgb()` checking COLORTERM environment variable
    - Implement `supports_256_color()` checking terminal type
    - Implement `get_dimensions()` returning terminal width and height
    - Implement `get_fallback_palette()` for ANSI color fallbacks
    - _Requirements: 15.1, 15.2, 15.3_
  
  - [x] 3.5 Write property test for terminal color fallback
    - **Property 35: Terminal Color Capability Fallback**
    - **Validates: Requirements 15.2**

- [x] 4. Phase 1: Core Infrastructure - Banner Renderer
  - [x] 4.1 Implement BannerRenderer class for static rendering
    - Create `BannerRenderer` class with theme parameter
    - Implement `render_static()` method returning Rich Panel
    - Apply theme colors to banner text
    - Use DOUBLE box borders from theme
    - Handle empty banners gracefully
    - _Requirements: 1.6, 7.3, 7.4_
  
  - [x] 4.2 Add terminal size validation to BannerRenderer
    - Implement `validate_terminal_size()` method
    - Check banner width and height against console dimensions
    - Return boolean indicating if banner fits
    - _Requirements: 10.4_
  
  - [x] 4.3 Write property test for banner dimension validation
    - **Property 24: Banner Dimension Validation**
    - **Validates: Requirements 10.4**
  
  - [x] 4.4 Implement banner selection with size adaptation
    - Implement `get_fallback_banner()` method returning hardcoded default
    - Create banner selection algorithm with terminal size filtering
    - Implement fallback chain: selected → category → random → fallback
    - Log banner selection decisions at INFO level
    - _Requirements: 10.1, 10.2, 10.5, 14.1_
  
  - [x] 4.5 Write property tests for error recovery
    - **Property 22: Banner Load Error Recovery**
    - **Property 25: Oversized Banner Adaptation**
    - **Validates: Requirements 10.2, 10.5**

- [x] 5. Phase 1: Core Infrastructure - Integration
  - [x] 5.1 Integrate banner system into main.py startup
    - Import banner, config, and themes modules
    - Load configuration at startup
    - Initialize BannerDatabase with assets directory
    - Select banner based on configuration
    - Render banner before showing interactive menu
    - Handle all errors gracefully with fallbacks
    - _Requirements: 1.1, 1.2, 2.7, 7.7_
  
  - [x] 5.2 Write unit tests for main.py integration
    - Test banner displays on startup
    - Test configuration loads correctly
    - Test fallback works when files missing
    - _Requirements: 1.1, 10.1_

- [ ] 6. Checkpoint - Phase 1 Complete
  - Ensure all Phase 1 tests pass, verify banner displays on startup with random selection, confirm configuration persists between runs. Ask the user if questions arise.

- [ ] 7. Phase 2: Animation System - Fire Animation Engine
  - [ ] 7.1 Create animation.py module with FirePalette
    - Implement `FirePalette` class with 12-step DOOM PSX color palette
    - Define COLORS tuple with hex color codes (ember → flame → tips)
    - Create STYLES tuple with Rich Style objects for each color
    - _Requirements: 3.1, 3.3_
  
  - [ ] 7.2 Extract and generalize fire animation from install.py
    - Create `FireAnimator` class with intensity parameter
    - Implement `animate_banner()` method accepting banner, console, duration, fps
    - Build animation frames with per-character coloring
    - Use Rich Live context for smooth animation display
    - Implement frame timing with configurable FPS
    - _Requirements: 3.1, 3.2, 3.3_
  
  - [ ] 7.3 Implement flame zone detection heuristic
    - Implement `_detect_zones()` method returning flame_lines and text_lines
    - Use 60/40 split heuristic (top 60% flame, bottom 40% text)
    - Support metadata override via flame_lines field
    - _Requirements: 3.4, 3.5_
  
  - [ ] 7.4 Write property test for flame zone detection
    - **Property 15: Fire Animation Dimension Adaptation**
    - **Property 16: Flame Zone Coloring Separation**
    - **Validates: Requirements 3.4, 3.5**
  
  - [ ] 7.5 Implement flame coloring algorithm
    - Implement `_apply_flame_coloring()` method for flame zone lines
    - Calculate base palette index based on line position (hotter at top)
    - Apply flicker effect with random palette offsets
    - Adjust flicker probability based on line position
    - Preserve spacing characters without coloring
    - _Requirements: 3.3, 3.5_
  
  - [ ] 7.6 Implement text coloring algorithm with ember cracks
    - Implement `_apply_text_coloring()` method for text zone lines
    - Use white → gray → dim gradient based on line position
    - Apply ember crack effect with random hot color spots
    - Adjust crack probability based on line position
    - _Requirements: 3.3, 3.5_
  
  - [ ] 7.7 Add animation intensity customization
    - Implement intensity multiplier for flicker and crack probabilities
    - Support "subtle" (0.5x), "normal" (1.0x), "intense" (1.5x) modes
    - Apply intensity to both flame and text coloring
    - _Requirements: 11.2, 11.3, 11.4, 11.5_
  
  - [ ] 7.8 Write property tests for animation behavior
    - **Property 17: Animation Duration Respect**
    - **Property 18: Animation Intensity Differentiation**
    - **Validates: Requirements 11.2, 11.3, 11.4, 11.5**

- [ ] 8. Phase 2: Animation System - Integration
  - [ ] 8.1 Add animated rendering to BannerRenderer
    - Implement `render_animated()` method in BannerRenderer
    - Lazy-load FireAnimator only when animation enabled
    - Pass configuration parameters (duration, fps, intensity) to animator
    - Handle animation errors with fallback to static rendering
    - _Requirements: 3.1, 3.6, 3.7, 8.6_
  
  - [ ] 8.2 Write property test for animation lazy loading
    - **Property 14: Animation Lazy Loading**
    - **Validates: Requirements 8.6**
  
  - [ ] 8.3 Update main.py to support animated banners
    - Check animation_enabled in configuration
    - Call render_animated() when enabled, render_static() when disabled
    - Log animation status at INFO level
    - _Requirements: 3.6, 3.7_
  
  - [ ] 8.4 Write unit tests for animation integration
    - Test animation displays when enabled
    - Test static banner displays when disabled
    - Test fallback to static on animation error
    - _Requirements: 3.6, 3.7_

- [ ] 9. Phase 2: Animation System - Performance Optimization
  - [ ] 9.1 Implement banner caching in BannerDatabase
    - Add `_cache` and `_cache_file` instance variables
    - Implement `_is_cache_valid()` checking source file modification times
    - Implement `_load_from_cache()` and `_save_to_cache()` using pickle
    - Update `load_banners()` to use cache when valid
    - Support `force_reload` parameter to bypass cache
    - _Requirements: 8.1, 8.5_
  
  - [ ] 9.2 Write property test for cache invalidation
    - **Property 12: Banner Cache Invalidation**
    - **Validates: Requirements 8.5**
  
  - [ ] 9.3 Optimize animation frame pre-computation
    - Pre-compute all animation frames before starting Live context
    - Store frames in list for smooth playback
    - Cycle through pre-computed frames during animation
    - _Requirements: 8.3_
  
  - [ ] 9.4 Write performance test for banner display
    - **Property 13: Banner Display Performance**
    - **Validates: Requirements 8.3**

- [ ] 10. Checkpoint - Phase 2 Complete
  - Ensure all Phase 2 tests pass, verify fire animation works on banners, confirm performance meets <200ms target with caching. Ask the user if questions arise.

- [ ] 11. Phase 3: Interactive Configuration - First-Run Wizard
  - [ ] 11.1 Implement first-run detection in ConfigManager
    - Update `is_first_run()` to check for missing config file
    - Add `mark_first_run_complete()` method to set flag
    - _Requirements: 12.1_
  
  - [ ] 11.2 Create setup wizard module (wizard.py)
    - Create `SetupWizard` class with console parameter
    - Implement welcome screen with Panel display
    - Implement step-by-step configuration flow
    - Return completed AppConfig object
    - _Requirements: 12.2, 12.3, 12.6_
  
  - [ ] 11.3 Implement theme selection in wizard
    - Display all available themes with visual previews
    - Show sample panel for each theme with colors
    - Use Rich Prompt for user selection
    - Default to CRT_Cyan if user skips
    - _Requirements: 7.6, 12.3_
  
  - [ ] 11.4 Implement banner mode selection in wizard
    - Present options: random, fixed, category
    - Explain each mode with descriptions
    - Show banner preview for fixed mode selection
    - Allow category filtering for category mode
    - _Requirements: 2.2, 2.3, 2.4, 12.3_
  
  - [ ] 11.5 Implement animation preferences in wizard
    - Ask if user wants animations enabled
    - If enabled, ask for intensity level (subtle, normal, intense)
    - Show brief animation preview for each intensity
    - _Requirements: 3.6, 11.6, 12.3_
  
  - [ ] 11.6 Add progress indicator to wizard
    - Display step numbers (Step 1/3, Step 2/3, etc.)
    - Show progress bar or step indicator
    - Allow skipping to use defaults
    - _Requirements: 12.5_
  
  - [ ] 11.7 Integrate wizard into main.py startup
    - Check `is_first_run()` before normal startup
    - Launch wizard if first run detected
    - Save configuration after wizard completes
    - Mark first run as complete
    - _Requirements: 12.1, 12.2, 12.6_
  
  - [ ] 11.8 Write integration test for first-run wizard
    - Test wizard launches on first run
    - Test configuration is saved after wizard
    - Test wizard can be skipped
    - _Requirements: 12.1, 12.2, 12.6_

- [ ] 12. Phase 3: Interactive Configuration - Settings Menu
  - [ ] 12.1 Add Settings menu option to CLI03
    - Add "Settings" menu item to interactive menu
    - Implement settings submenu with configuration options
    - Display current configuration values
    - _Requirements: 5.1_
  
  - [ ] 12.2 Implement banner configuration in settings menu
    - Add "Change Banner Mode" option
    - Add "Select Fixed Banner" option (when mode is fixed)
    - Add "Filter Categories" option (when mode is category)
    - Show current banner mode and selection
    - _Requirements: 2.2, 2.3, 2.4_
  
  - [ ] 12.3 Implement theme configuration in settings menu
    - Add "Change Theme" option
    - Display theme previews before selection
    - Apply theme immediately after selection
    - Save theme preference to config
    - _Requirements: 7.5, 7.6_
  
  - [ ] 12.4 Implement animation configuration in settings menu
    - Add "Toggle Animation" option
    - Add "Animation Intensity" option
    - Add "Animation Duration" option
    - Add "Animation FPS" option
    - Validate input ranges and show helpful errors
    - _Requirements: 3.6, 11.1, 11.2, 11.6_
  
  - [ ] 12.5 Add "Reconfigure" option to settings menu
    - Add option to re-run setup wizard
    - Preserve current config as defaults in wizard
    - _Requirements: 12.7_
  
  - [ ] 12.6 Write unit tests for settings menu
    - Test menu displays current configuration
    - Test configuration changes are saved
    - Test input validation works correctly
    - _Requirements: 5.1, 2.1_

- [ ] 13. Phase 3: Interactive Configuration - Banner Preview System
  - [ ] 13.1 Implement banner preview grid renderer
    - Create `BannerPreview` class with grid layout
    - Display multiple banners in columns (2-3 columns based on terminal width)
    - Show banner name and category for each preview
    - Scale banners to fit preview area if needed
    - _Requirements: 2.6, 13.1, 13.2_
  
  - [ ] 13.2 Write property tests for banner preview
    - **Property 27: Banner Preview Scaling**
    - **Property 37: Banner Preview Display**
    - **Validates: Requirements 2.6, 13.2**

  - [ ] 13.3 Add pagination support to preview grid
    - Implement page navigation (next/previous)
    - Display page indicator (Page 1/5)
    - Show 10-20 banners per page based on terminal size
    - _Requirements: 13.4_
  
  - [ ] 13.4 Write property test for preview pagination
    - **Property 28: Banner Preview Pagination**
    - **Validates: Requirements 13.4**
  
  - [ ] 13.5 Add metadata display to banner previews
    - Show banner description below ASCII art
    - Show author if available
    - Show animation compatibility indicator
    - _Requirements: 9.3, 13.5_
  
  - [ ] 13.6 Write property test for preview metadata
    - **Property 29: Preview Metadata Display**
    - **Validates: Requirements 9.3, 13.5**
  
  - [ ] 13.7 Implement adaptive preview layout
    - Detect terminal width and adjust columns
    - Use single column for narrow terminals (<80 cols)
    - Use 2-3 columns for wider terminals
    - _Requirements: 13.6_
  
  - [ ] 13.8 Write property test for adaptive layout
    - **Property 30: Adaptive Preview Layout**
    - **Validates: Requirements 13.6**
  
  - [ ] 13.9 Add animated banner preview support
    - Show brief animation sample (1-2 seconds) for animated banners
    - Add "Preview Animation" option in banner selection
    - Filter by animation_compatible when animation enabled
    - _Requirements: 9.4, 13.3_
  
  - [ ] 13.10 Write property test for animation compatibility filtering
    - **Property 21: Animation Compatibility Filtering**
    - **Validates: Requirements 9.4**

- [ ] 14. Phase 3: Interactive Configuration - CLI02 Commands
  - [ ] 14.1 Add "beefy config" command
    - Implement command to display current configuration
    - Show all config values in formatted output
    - Add subcommands: show, set, reset
    - _Requirements: 5.1_
  
  - [ ] 14.2 Add "beefy banner preview" command
    - Implement command to show banner preview grid
    - Support filtering by category: `beefy banner preview --category ALT`
    - Support pagination: `beefy banner preview --page 2`
    - _Requirements: 2.6_

  - [ ] 14.3 Add "beefy theme set" command
    - Implement command to change theme: `beefy theme set Amber_Terminal`
    - Show theme preview before applying
    - Validate theme name against available themes
    - _Requirements: 7.5_
  
  - [ ] 14.4 Add keyboard shortcuts to interactive menu
    - Display shortcuts alongside menu items (e.g., "1. Peep All [P]")
    - Support number input and letter shortcuts
    - Update menu rendering to show shortcuts
    - _Requirements: 5.2, 5.3_
  
  - [ ] 14.5 Implement command history navigation
    - Add up/down arrow support for command history
    - Store recent commands in memory
    - Implement "recent commands" quick-access list
    - _Requirements: 5.4, 5.5_
  
  - [ ] 14.6 Write property test for command history
    - **Property 40: Recent Commands Tracking**
    - **Validates: Requirements 5.5**
  
  - [ ] 14.7 Improve error messages in interactive CLI
    - Add helpful suggestions for invalid inputs
    - Show "Did you mean...?" for typos
    - Maintain command-teaching approach (show full syntax)
    - _Requirements: 5.6, 5.7_
  
  - [ ] 14.8 Write property test for menu input mapping
    - **Property 39: Menu Input Mapping**
    - **Validates: Requirements 5.3**

- [ ] 15. Checkpoint - Phase 3 Complete
  - Ensure all Phase 3 tests pass, verify first-run wizard works correctly, confirm settings menu allows reconfiguration, test banner preview grid displays properly. Ask the user if questions arise.

- [ ] 16. Phase 4: Polish and Optimization - Logging System
  - [ ] 16.1 Implement logging configuration
    - Set up Python logging with file handler
    - Create .logs directory if it doesn't exist
    - Configure log format with timestamp, level, module, message
    - Set default log level to INFO
    - _Requirements: 14.5_
  
  - [ ] 16.2 Add logging to banner system
    - Log banner selection decisions at INFO level
    - Log parsing errors at ERROR level with file and line info
    - Log cache operations at DEBUG level
    - _Requirements: 14.1, 14.2_

  - [ ] 16.3 Write property tests for logging
    - **Property 23: Banner Error Logging**
    - **Property 31: Banner Selection Logging**
    - **Validates: Requirements 10.3, 14.1, 14.2**
  
  - [ ] 16.4 Add logging to configuration system
    - Log configuration changes at INFO level
    - Log migration operations at INFO level
    - Log validation errors at WARNING level
    - _Requirements: 14.3_
  
  - [ ] 16.5 Write property test for configuration logging
    - **Property 32: Configuration Change Logging**
    - **Validates: Requirements 14.3**
  
  - [ ] 16.6 Implement debug mode with verbose logging
    - Add --debug flag to CLI
    - Set log level to DEBUG when flag present
    - Log detailed parsing and rendering information
    - _Requirements: 14.4_
  
  - [ ] 16.7 Write property test for debug mode
    - **Property 33: Debug Mode Verbosity**
    - **Validates: Requirements 14.4**
  
  - [ ] 16.8 Implement log file rotation
    - Check log file size at startup
    - Rotate if size exceeds 10MB
    - Keep last 3 rotated files
    - Delete oldest rotated file when limit reached
    - _Requirements: 14.6_
  
  - [ ] 16.9 Write property test for log rotation
    - **Property 34: Log File Rotation**
    - **Validates: Requirements 14.6**

- [ ] 17. Phase 4: Polish and Optimization - Terminal Compatibility
  - [ ] 17.1 Implement RGB color detection
    - Check COLORTERM environment variable for "truecolor" or "24bit"
    - Check TERM environment variable for RGB support indicators
    - Return boolean indicating RGB support
    - _Requirements: 15.1_
  
  - [ ] 17.2 Implement ANSI color fallback palette
    - Create mapping from RGB hex codes to closest ANSI colors
    - Update Theme.get_fallback_palette() to return ANSI colors
    - Apply fallback palette when RGB not supported
    - _Requirements: 15.2_
  
  - [ ] 17.3 Add color degradation to fire animation
    - Detect terminal color support before animation
    - Use 8-bit color palette when RGB not available
    - Map fire palette to closest 8-bit colors
    - _Requirements: 15.5_

  - [ ] 17.4 Write property test for animation color degradation
    - **Property 36: Animation Color Degradation**
    - **Validates: Requirements 15.5**
  
  - [ ] 17.5 Implement terminal size detection
    - Use Rich Console.size to get dimensions
    - Handle terminals that don't report size
    - Default to 80x24 if size unavailable
    - _Requirements: 15.3_
  
  - [ ] 17.6 Add minimal banner for small terminals
    - Detect terminals smaller than 40x10
    - Display text-only header instead of ASCII art
    - Show "peepBeefy" in styled text
    - _Requirements: 15.4_
  
  - [ ] 17.7 Write unit tests for terminal compatibility
    - Test RGB detection works correctly
    - Test ANSI fallback is applied
    - Test minimal banner displays on small terminals
    - _Requirements: 15.1, 15.2, 15.4_

- [ ] 18. Phase 4: Polish and Optimization - Final Integration
  - [ ] 18.1 Add comprehensive error handling to all modules
    - Wrap all file operations in try-except blocks
    - Log all errors with context information
    - Ensure graceful fallbacks for all failure modes
    - _Requirements: 10.1, 10.2, 10.3, 10.6, 10.7_
  
  - [ ] 18.2 Optimize startup performance
    - Profile startup time with cProfile
    - Identify bottlenecks in banner loading and parsing
    - Apply optimizations to meet <200ms target
    - _Requirements: 8.2, 8.3_
  
  - [ ] 18.3 Add input validation to all user-facing functions
    - Validate menu selections with helpful errors
    - Validate configuration values with range checks
    - Validate file paths before operations
    - _Requirements: 5.6, 6.4_
  
  - [ ] 18.4 Update documentation and docstrings
    - Add module-level docstrings to all new modules
    - Add function/method docstrings with parameter descriptions
    - Update README with new features
    - Add usage examples for new commands
    - _Requirements: All_
  
  - [ ] 18.5 Run all property tests and verify coverage
    - Execute all 40 property tests
    - Verify minimum 100 iterations per test
    - Confirm all properties pass
    - _Requirements: All_
  
  - [ ] 18.6 Run all unit tests and verify coverage
    - Execute complete unit test suite
    - Verify >80% code coverage
    - Fix any failing tests
    - _Requirements: All_

- [ ] 19. Final Checkpoint - Phase 4 Complete
  - Ensure all tests pass (property and unit), verify startup performance <200ms, confirm cross-terminal compatibility, validate all error handling works correctly. Ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties across all inputs
- Unit tests validate specific examples, edge cases, and integration points
- Checkpoints ensure incremental validation at major milestones
- Implementation uses Python with Rich library for terminal rendering
- All code should include type hints and comprehensive docstrings
- Follow peepBeefy's existing 3-layer architecture (CLI01/CLI02/CLI03)
- Maintain the CRT Retro Terminal aesthetic with DOUBLE box borders
