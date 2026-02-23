# Implementation Plan: hyfetch Integration Analysis

## Overview

This implementation plan breaks down the integration of hyfetch-inspired color handling, terminal detection, and rendering capabilities into peepBeefy. The approach follows a 6-phase structure that builds incrementally, starting with core utilities and progressing to advanced features. Each phase includes implementation tasks with property-based tests to verify correctness.

The implementation maintains peepBeefy's retro CRT aesthetic while adding modern color capabilities, terminal adaptation, and performance optimizations. Target startup time is <200ms with all enhancements.

## Tasks

### Phase 1: Core Color Utilities and Terminal Detection

- [x] 1. Create color utility module with RGB/HSL support
  - [x] 1.1 Implement RGB and HSL dataclasses in `src/color_util.py`
    - Create RGB dataclass with r, g, b fields (0-255 range)
    - Create HSL dataclass with h, s, l fields (0.0-1.0 range)
    - Implement RGB.from_hex() supporting both #RRGGBB and #RGB formats
    - Implement RGB.hsl() conversion using colorsys
    - Implement HSL.rgb() conversion using colorsys
    - _Requirements: 1.1, 1.2, 1.6_
  
  - [x] 1.2 Write property test for RGB-HSL round-trip conversion
    - **Property 1: RGB-HSL Round-Trip Preservation**
    - **Property 44: Hex Color Format Support**
    - **Validates: Requirements 1.1, 1.2, 1.6**
  
  - [x] 1.3 Implement lightness adjustment methods
    - Implement RGB.set_light() with at_least/at_most parameters
    - Implement RGB.lighten() with multiplier parameter
    - Implement RGB.is_light() using HSL lightness threshold of 0.5
    - Implement redistribute_rgb() for component overflow handling
    - _Requirements: 1.3, 1.4, 1.7_
  
  - [-] 1.4 Write property tests for lightness operations
    - **Property 2: Lightness Adjustment Preserves Hue and Saturation**
    - **Property 3: RGB Redistribution Maintains Proportions**
    - **Property 5: Lightness Classification Threshold**
    - **Validates: Requirements 1.3, 1.4, 1.7**
  
  - [x] 1.5 Implement color overlay and blending
    - Implement RGB.overlay() with alpha blending
    - _Requirements: 1.5_
  
  - [ ] 1.6 Write property test for color overlay
    - **Property 4: Color Overlay Produces Valid RGB**
    - **Validates: Requirements 1.5**

- [x] 2. Implement ANSI color code generation
  - [x] 2.1 Add ANSI RGB mode support to RGB class
    - Implement RGB.to_ansi_rgb() for 24-bit color codes
    - Support both foreground (38;2) and background (48;2) modes
    - _Requirements: 2.1, 2.6_
  
  - [ ]* 2.2 Write property test for RGB ANSI format
    - **Property 6: RGB ANSI Format Correctness**
    - **Validates: Requirements 2.1, 2.6**
  
  - [x] 2.3 Add ANSI 8-bit mode support to RGB class
    - Implement RGB.to_ansi_8bit() with grayscale detection
    - Implement color cube algorithm for saturated colors (16 + 36*r + 6*g + b)
    - Implement grayscale mapping for low-saturation colors (232-255)
    - _Requirements: 2.2, 2.3, 2.4, 2.5_
  
  - [ ]* 2.4 Write property tests for 8-bit ANSI conversion
    - **Property 7: 8-bit ANSI Code Range Validity**
    - **Property 8: Color Cube Formula Correctness**
    - **Validates: Requirements 2.2, 2.3, 2.4, 2.5**
  
  - [x] 2.5 Implement unified ANSI interface
    - Define AnsiMode type as Literal["rgb", "8bit", "ansi", "default"]
    - Implement RGB.to_ansi() accepting mode parameter
    - _Requirements: 2.7_
  
  - [ ]* 2.6 Write property test for unified ANSI interface
    - **Property 9: Unified ANSI Interface Consistency**
    - **Validates: Requirements 2.7**

- [x] 3. Create terminal capability detection module
  - [x] 3.1 Implement Unix terminal detection in `src/terminal_detect.py`
    - Create unix_detect_ansi_mode() function
    - Check COLORTERM for "truecolor" or "24bit" indicators
    - Check TERM for "256color", "color", "ansi" indicators
    - Handle special cases: "xterm-kitty" → rgb, "linux" → ansi
    - _Requirements: 3.1, 3.2, 3.7, 3.8_
  
  - [x] 3.2 Implement Windows terminal detection
    - Create windows_detect_ansi_mode() function
    - Check ConEmuANSI environment variable
    - Check Windows build version (< 10586 → ansi, >= 14931 → rgb)
    - _Requirements: 3.3, 3.4, 3.5_
  
  - [x] 3.3 Implement platform-agnostic detection wrapper
    - Create detect_ansi_mode() function with platform detection
    - Return None on detection failure (graceful fallback)
    - _Requirements: 3.6_
  
  - [ ]* 3.4 Write property test for graceful failure
    - **Property 10: Terminal Detection Graceful Failure**
    - **Validates: Requirements 3.6**
  
  - [ ]* 3.5 Write unit tests for terminal detection examples
    - Test COLORTERM="truecolor" → rgb
    - Test TERM="xterm-256color" → 8bit
    - Test TERM="linux" → ansi
    - Test ConEmuANSI="ON" → rgb
    - Test Windows build versions
    - _Requirements: 3.1-3.8_

- [x] 4. Implement Minecraft-style color code system
  - [x] 4.1 Implement color code parser in `src/color_util.py`
    - Implement color() function parsing &0-&f codes
    - Support formatting codes: &l (bold), &o (italic), &n (underline), &r (reset)
    - Support extended codes: &- (newline), &~ (reset fg), &* (reset bg)
    - Support RGB codes: &gf(#RRGGBB), &gb(#RRGGBB), &gf(R,G,B)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  
  - [x] 4.2 Implement printc() function
    - Create printc() wrapper that calls color() and prints
    - Automatically append ANSI reset code at end
    - _Requirements: 9.7_
  
  - [ ]* 4.3 Write property tests for color code parsing
    - **Property 30: Minecraft Color Code Replacement**
    - **Property 31: RGB Color Code Parsing**
    - **Property 32: Automatic Reset Code Appending**
    - **Validates: Requirements 9.1-9.7**

- [x] 5. Checkpoint - Phase 1 complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 2: Gradient and Preset Systems

- [x] 6. Create gradient generation system
  - [x] 6.1 Implement gradient interpolation in `src/color_scale.py`
    - Create create_gradient() function with linear interpolation
    - Accept list of RGB colors and resolution parameter
    - Generate (N-1) * resolution interpolated colors
    - _Requirements: 4.1, 4.2, 4.3_
  
  - [ ]* 6.2 Write property tests for gradient generation
    - **Property 11: Gradient Length Matches Resolution**
    - **Property 12: Linear Interpolation Correctness**
    - **Property 45: Gradient Smoothness**
    - **Validates: Requirements 4.1, 4.2, 4.3**
  
  - [x] 6.3 Implement Scale class for gradient lookup
    - Create Scale class with colors list and pre-computed rgb array
    - Implement __init__() accepting hex color strings and resolution
    - Implement __call__() for ratio-based lookup (0.0-1.0)
    - Implement get_raw() helper for array indexing
    - _Requirements: 4.4, 4.5_
  
  - [ ]* 6.4 Write property tests for gradient lookup
    - **Property 13: Gradient Ratio Lookup Bounds**
    - **Validates: Requirements 4.4, 4.5**
  
  - [x] 6.5 Implement hex color initialization
    - Create create_gradient_hex() function
    - _Requirements: 4.6_
  
  - [ ]* 6.6 Write property test for hex initialization
    - **Property 14: Gradient Hex Initialization**
    - **Validates: Requirements 4.6**

- [x] 7. Create color preset management system
  - [x] 7.1 Implement ColorPreset dataclass in `src/color_presets.py`
    - Create ColorPreset with name, colors, and optional weights fields
    - Implement expand_colors() for weight-based repetition
    - Implement spread_colors() with center-outward distribution
    - Implement adjust_lightness() for background adaptation
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [ ]* 7.2 Write property tests for preset operations
    - **Property 15: Weighted Preset Expansion**
    - **Property 16: Color Spreading Exact Length**
    - **Property 17: Center-Outward Distribution Balance**
    - **Property 18: Lightness Adjustment Bounds**
    - **Validates: Requirements 5.4, 5.5, 5.6, 5.7**
  
  - [x] 7.3 Implement preset loading and management
    - Create load_presets() function reading from JSON
    - Create spread_colors_balanced() helper function
    - Implement overlay-based lightness adjustment
    - _Requirements: 5.1, 5.8_
  
  - [ ]* 7.4 Write property test for overlay operations
    - **Property 19: Overlay Produces Valid Colors**
    - **Validates: Requirements 5.8**
  
  - [x] 7.5 Create default preset collection
    - Create JSON file with default color presets
    - Include presets for common themes (rainbow, fire, ocean, etc.)
    - _Requirements: 5.1_

- [x] 8. Checkpoint - Phase 2 complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 3: Configuration and Data Models

- [x] 9. Implement enhanced JSON serialization
  - [x] 9.1 Create serializer module in `src/serializer.py`
    - Implement to_dict() for dataclass to dictionary conversion
    - Handle nested dataclasses recursively
    - Convert enums to string representations
    - Support custom serialization for Path and ColorAlignment types
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [x] 9.2 Implement deserialization
    - Implement from_dict() for dictionary to dataclass reconstruction
    - Validate required fields and raise appropriate errors
    - _Requirements: 6.6, 6.7_
  
  - [x] 9.3 Implement JSON string generation
    - Implement json_stringify() with pretty-printing
    - _Requirements: 6.5_
  
  - [ ]* 9.4 Write property tests for serialization
    - **Property 20: Dataclass Serialization Round-Trip**
    - **Property 21: Enum Serialization to String**
    - **Property 22: JSON Output Validity**
    - **Property 23: Required Field Validation**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.5, 6.6, 6.7**

- [x] 10. Extend configuration schema
  - [x] 10.1 Add new configuration fields to `src/config.py`
    - Extend BannerConfig with color_preset, color_alignment, custom_color_map
    - Create DisplayConfig dataclass with color_mode, auto_detect_background, force_light_dark, lightness_adjustment, use_gradients
    - Add display field to AppConfig
    - Define LightDark type as Literal["light", "dark"]
    - Define ColorAlignMode type as Literal["horizontal", "vertical", "custom"]
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_
  
  - [x] 10.2 Implement configuration migration
    - Create migrate_v1_to_v2() function
    - Add version field handling
    - Provide defaults for new fields when loading old configs
    - _Requirements: 7.6_
  
  - [ ]* 10.3 Write property tests for configuration
    - **Property 24: Configuration Type Validation**
    - **Property 42: Backward Compatible Config Loading**
    - **Validates: Requirements 7.7, 14.5**
  
  - [ ]* 10.4 Write unit tests for migration
    - Test v1 config loads with defaults
    - Test v2 config loads correctly
    - Test corrupted config handling
    - _Requirements: 7.6, 14.5_

- [x] 11. Checkpoint - Phase 3 complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 4: ASCII Rendering and Color Alignment

- [x] 12. Create ASCII color alignment system
  - [x] 12.1 Implement ColorAlignment dataclass in `src/ascii_renderer.py`
    - Create ColorAlignment with mode and optional custom_colors fields
    - Implement from_dict() class method
    - _Requirements: 8.3_
  
  - [x] 12.2 Implement ASCIIColorizer class
    - Create ASCIIColorizer with preset, alignment, and ansi_mode fields
    - Implement colorize() dispatcher method
    - Implement strip_neofetch_codes() helper
    - _Requirements: 8.6, 8.7_
  
  - [ ]* 12.3 Write property test for structure preservation
    - **Property 29: ASCII Structure Preservation**
    - **Validates: Requirements 8.7**
  
  - [ ]* 12.4 Write property test for neofetch code removal
    - **Property 28: Neofetch Code Removal**
    - **Validates: Requirements 8.6**
  
  - [x] 12.3 Implement horizontal alignment mode
    - Create colorize_horizontal() applying one color per line
    - Cycle through colors if fewer colors than lines
    - _Requirements: 8.1, 8.4_
  
  - [ ]* 12.4 Write property test for horizontal alignment
    - **Property 25: Horizontal Alignment One Color Per Line**
    - **Validates: Requirements 8.1, 8.4**
  
  - [x] 12.5 Implement vertical alignment mode
    - Create colorize_vertical() spreading colors across width
    - Create horizontal gradient effect
    - _Requirements: 8.2, 8.5_
  
  - [ ]* 12.6 Write property test for vertical alignment
    - **Property 26: Vertical Alignment Gradient Across Width**
    - **Validates: Requirements 8.2, 8.5**
  
  - [x] 12.7 Implement custom alignment mode
    - Create colorize_custom() using custom color mapping
    - Map ASCII color codes to preset colors
    - _Requirements: 8.3_
  
  - [ ]* 12.8 Write property test for custom alignment
    - **Property 27: Custom Alignment Mapping**
    - **Validates: Requirements 8.3**

- [x] 13. Extend banner system with color metadata
  - [x] 13.1 Update BannerMetadata in `src/banner.py`
    - Add flame_lines field for explicit flame zone
    - Add recommended_preset field for suggested colors
    - Add color_zones field for named color regions
    - _Requirements: 11.5_
  
  - [ ]* 13.2 Write integration test for banner colorization
    - Test ASCIIColorizer preserves banner structure
    - Test all three alignment modes with real banners
    - _Requirements: 8.1, 8.2, 8.3, 14.6_

- [x] 14. Checkpoint - Phase 4 complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 5: Advanced Features

- [x] 15. Implement background color detection
  - [x] 15.1 Add OSC query support to `src/terminal_detect.py`
    - Implement unix_read_osc() for reading OSC responses
    - Implement get_background_color() sending OSC 11 query
    - Set terminal to raw mode before query
    - Implement timeout handling (50ms local, 500ms SSH)
    - Restore terminal mode after query
    - Skip detection for screen/tmux terminals
    - _Requirements: 10.1, 10.2, 10.3, 10.5, 10.6, 10.7_
  
  - [x] 15.2 Implement OSC response parsing
    - Parse RGB values from "rgb:RRRR/GGGG/BBBB" format
    - Convert 16-bit values to 8-bit range
    - _Requirements: 10.4_
  
  - [x] 15.3 Write property test for OSC parsing
    - **Property 33: OSC Response Parsing**
    - **Validates: Requirements 10.4**
  
  - [ ]* 15.4 Write unit tests for OSC detection
    - Test timeout handling
    - Test screen/tmux skip logic
    - Test terminal mode restoration
    - _Requirements: 10.1-10.7_

- [x] 16. Implement distro-specific ASCII art detection
  - [x] 16.1 Extend Banner_Database in `src/banner.py`
    - Implement case-insensitive distro name matching
    - Implement distro name alias support
    - Implement partial word matching fallback
    - Implement fallback banner for unrecognized distros
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.7_
  
  - [ ]* 16.2 Write property tests for distro matching
    - **Property 34: Distro Name Case Insensitivity**
    - **Property 35: Distro Partial Matching**
    - **Property 36: Distro Fallback Banner**
    - **Validates: Requirements 11.2, 11.4, 11.7**
  
  - [ ]* 16.3 Write unit tests for distro detection
    - Test case variations (Ubuntu, ubuntu, UBUNTU)
    - Test alias mapping (coreos → container_linux)
    - Test partial matching
    - Test fallback behavior
    - _Requirements: 11.1-11.7_

- [x] 17. Implement theme adaptation system
  - [x] 17.1 Extend Theme class in `src/themes.py`
    - Add get_color_mode() method using terminal detection
    - Add adapt_to_terminal() method with background color parameter
    - Implement background lightness classification
    - _Requirements: 12.1_
  
  - [ ]* 17.2 Write property test for background classification
    - **Property 37: Background Lightness Classification**
    - **Validates: Requirements 12.1**
  
  - [x] 17.3 Implement theme color adjustment
    - Ensure dark background text has lightness >= 0.65
    - Ensure light background text has lightness <= 0.4
    - Support both HSL and overlay adjustment methods
    - Preserve hue and saturation during adjustment
    - _Requirements: 12.2, 12.3, 12.4, 12.6, 12.7_
  
  - [ ]* 17.4 Write property test for overlay adjustment
    - **Property 38: Overlay Lightness Adjustment Validity**
    - **Validates: Requirements 12.4**
  
  - [x] 17.5 Extend ColorPalette with RGB conversion
    - Add to_rgb_palette() method
    - Add adjust_for_background() method
    - _Requirements: 12.5_

- [x] 18. Implement caching system
  - [x] 18.1 Create cache infrastructure in `src/config.py`
    - Create cache directory at ~/.cache/hyfetch or $XDG_CACHE_HOME/hyfetch
    - Handle cache directory creation failures gracefully
    - _Requirements: 13.1, 13.6_
  
  - [x] 18.2 Implement cache data models
    - Create CacheEntry dataclass with timestamp and data
    - Create BannerCache dataclass
    - Create TerminalCache dataclass with TTL
    - _Requirements: 13.2, 13.3_
  
  - [x] 18.3 Implement cache operations
    - Implement cache write with pickle serialization
    - Implement cache read with freshness validation
    - Validate cache using file modification timestamps
    - Invalidate stale cache automatically
    - _Requirements: 13.4, 13.5_
  
  - [ ]* 18.4 Write property tests for caching
    - **Property 39: Cache Reuse on Repeated Access**
    - **Property 40: Cache Freshness Validation**
    - **Property 41: Cache Failure Graceful Handling**
    - **Validates: Requirements 13.2, 13.3, 13.4, 13.5, 13.6**
  
  - [ ]* 18.5 Write unit tests for cache operations
    - Test cache hit/miss scenarios
    - Test stale cache invalidation
    - Test cache directory creation failure
    - _Requirements: 13.1-13.7_

- [x] 19. Checkpoint - Phase 5 complete
  - Ensure all tests pass, ask the user if questions arise.

### Phase 6: Integration Testing and Performance

- [x] 20. Write integration tests
  - [ ]* 20.1 Test color system with animation engine
    - Verify FireAnimator uses RGB or 8-bit based on terminal capability
    - Test fire palette fallback behavior
    - _Requirements: 14.1_
  
  - [ ]* 20.2 Test terminal detection with theme system
    - Verify themes adapt colors based on terminal background
    - Test lightness adjustment for dark/light backgrounds
    - _Requirements: 14.2_
  
  - [ ]* 20.3 Test gradient engine smoothness
    - Verify smooth color transitions in generated gradients
    - Test gradient lookup at various ratios
    - _Requirements: 14.3_
  
  - [ ]* 20.4 Test preset system loading and application
    - Verify presets load from JSON correctly
    - Test color spreading across different lengths
    - _Requirements: 14.4_
  
  - [ ]* 20.5 Test ASCII renderer with banner system
    - Verify colorization preserves banner structure
    - Test all alignment modes with real banners
    - _Requirements: 14.6_
  
  - [ ]* 20.6 Test graceful degradation
    - Verify all features work on limited terminals
    - Test RGB → 8-bit → ANSI fallback chain
    - _Requirements: 14.7_

- [x] 21. Performance testing and optimization
  - [ ]* 21.1 Write startup performance test
    - Measure total startup time with all enhancements
    - Verify <200ms target is met
    - Profile individual component load times
    - _Requirements: 13.7_
  
  - [x] 21.2 Optimize startup performance if needed
    - Implement lazy loading for presets
    - Optimize cache loading
    - Pre-compute gradients efficiently
    - _Requirements: 13.7_
  
  - [ ]* 21.3 Write memory usage tests
    - Measure memory footprint of gradients
    - Measure banner cache size
    - Verify total additional memory is acceptable
    - _Requirements: 13.7_

- [x] 22. Final checkpoint - All tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at phase boundaries
- Property tests validate universal correctness properties from the design
- Unit tests validate specific examples and edge cases
- Integration tests verify compatibility with existing peepBeefy systems
- Performance tests ensure <200ms startup time target is maintained
- All new modules follow Python dataclass patterns for type safety
- Error handling follows graceful degradation principles
- Caching system improves performance without compromising functionality
