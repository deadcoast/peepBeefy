# Design Document: hyfetch Integration Analysis

## Overview

This design document specifies the architecture and implementation approach for enhancing peepBeefy by integrating sophisticated color handling, terminal detection, and rendering patterns from hyfetch. The design maintains peepBeefy's retro CRT aesthetic and existing 3-layer architecture while adding modern color capabilities, terminal adaptation, and performance optimizations.

### Design Goals

1. **Modular Integration**: Create self-contained modules that integrate cleanly with existing peepBeefy systems
2. **Backward Compatibility**: Maintain existing configuration schema and theme system while extending capabilities
3. **Performance**: Achieve <200ms startup time through caching and lazy loading
4. **Graceful Degradation**: Support terminals with varying color capabilities (RGB → 8-bit → ANSI)
5. **Retro Aesthetic Preservation**: Enhance capabilities without compromising peepBeefy's CRT terminal feel

### Integration Strategy

The integration follows a phased approach:
- **Phase 1**: Core color utilities and terminal detection (Requirements 1-3)
- **Phase 2**: Gradient and preset systems (Requirements 4-5)
- **Phase 3**: Configuration and data models (Requirements 6-7)
- **Phase 4**: ASCII rendering and color alignment (Requirements 8-9)
- **Phase 5**: Advanced features (Requirements 10-13)
- **Phase 6**: Testing and documentation (Requirements 14-15)

## Architecture

### Module Organization

New modules will be added to `src/` following peepBeefy's flat structure:

```
src/
├── color_util.py          # RGB/HSL conversion, lightness adjustment, ANSI generation
├── color_scale.py         # Gradient generation and color interpolation
├── terminal_detect.py     # Terminal capability detection (Unix/Windows)
├── color_presets.py       # Preset management and color spreading
├── ascii_renderer.py      # Color alignment and ASCII art coloring
├── serializer.py          # Enhanced JSON serialization for dataclasses
└── (existing modules)
```

### Dependency Graph

```
┌─────────────────┐
│  color_util.py  │ ← Core color operations (RGB/HSL/ANSI)
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    │         │              │             │
┌───▼────┐ ┌─▼──────────┐ ┌─▼────────┐ ┌──▼──────────┐
│ themes │ │color_scale │ │terminal_ │ │color_presets│
│  .py   │ │    .py     │ │detect.py │ │    .py      │
└───┬────┘ └─────┬──────┘ └────┬─────┘ └──────┬──────┘
    │            │              │              │
    └────────────┴──────┬───────┴──────────────┘
                        │
                  ┌─────▼──────────┐
                  │ascii_renderer  │
                  │     .py        │
                  └────────────────┘
```

### Integration Points with Existing Systems

1. **themes.py**: Extended with color mode detection and palette adaptation
2. **config.py**: Enhanced with new configuration fields for color modes and presets
3. **banner.py**: Integrated with ascii_renderer for color alignment
4. **animation.py**: Uses color_util for RGB/8-bit fallback in fire palette

## Components and Interfaces

### Component 1: Color Utility System (color_util.py)

**Purpose**: Provide comprehensive color manipulation and ANSI code generation

**Key Classes**:

```python
@dataclass
class RGB:
    r: int  # 0-255
    g: int  # 0-255
    b: int  # 0-255
    
    @classmethod
    def from_hex(cls, hex: str) -> RGB
    
    def to_ansi_rgb(self, foreground: bool = True) -> str
    def to_ansi_8bit(self, foreground: bool = True) -> str
    def to_ansi(self, mode: AnsiMode, foreground: bool = True) -> str
    
    def hsl(self) -> HSL
    def set_light(self, light: float, at_least: bool = None, at_most: bool = None) -> RGB
    def lighten(self, multiplier: float) -> RGB
    def overlay(self, color: RGB, alpha: float) -> RGB
    def is_light(self) -> bool

@dataclass
class HSL:
    h: float  # 0.0-1.0 (hue)
    s: float  # 0.0-1.0 (saturation)
    l: float  # 0.0-1.0 (lightness)
    
    def rgb(self) -> RGB
```

**Key Functions**:

```python
def redistribute_rgb(r: int, g: int, b: int) -> tuple[int, int, int]
    """Redistribute RGB components when values exceed 255 after transformation"""

def color(msg: str) -> str
    """Parse Minecraft-style color codes (&0-&f, &l, &r, &gf(#RGB))"""

def printc(msg: str) -> None
    """Print with Minecraft-style color codes"""
```

**Design Decisions**:
- Use dataclasses for immutability and type safety
- Support both RGB and 8-bit ANSI modes for terminal compatibility
- Implement HSL conversion using Python's colorsys module
- Provide Minecraft-style color codes for easy text formatting

### Component 2: Color Scale System (color_scale.py)

**Purpose**: Generate smooth color gradients for ASCII art and themes

**Key Classes**:

```python
class Scale:
    colors: list[RGB]
    rgb: list[RGB]  # Pre-computed gradient array
    
    def __init__(self, scale: list[str], resolution: int = 300)
    def __call__(self, ratio: float) -> RGB
        """Get color at ratio (0.0-1.0) in gradient"""
```

**Key Functions**:

```python
def create_gradient(colors: list[RGB], resolution: int) -> list[RGB]
    """Create gradient array using linear interpolation"""

def create_gradient_hex(colors: list[str], resolution: int = 300) -> list[RGB]
    """Create gradient from hex color strings"""

def get_raw(gradient: list[RGB], ratio: float) -> RGB
    """Get color at specific ratio in pre-computed gradient"""
```

**Design Decisions**:
- Pre-compute gradients for O(1) lookup performance
- Use linear interpolation for smooth transitions
- Default resolution of 300 steps balances quality and memory
- Support initialization from hex strings for convenience

### Component 3: Terminal Detection System (terminal_detect.py)

**Purpose**: Detect terminal color capabilities and background color

**Key Functions**:

```python
def detect_ansi_mode() -> AnsiMode | None
    """Detect terminal color mode (rgb/8bit/ansi)"""

def unix_detect_ansi_mode() -> AnsiMode | None
    """Unix-specific detection using TERM/COLORTERM env vars"""

def windows_detect_ansi_mode() -> AnsiMode | None
    """Windows-specific detection using ConEmuANSI and build version"""

def get_background_color() -> RGB | None
    """Detect terminal background color using OSC 11 sequence"""

def unix_read_osc(seq: int) -> str
    """Read OSC response from terminal (Unix only)"""
```

**Type Definitions**:

```python
AnsiMode = Literal["rgb", "8bit", "ansi", "default"]
```

**Design Decisions**:
- Platform-specific detection for Unix/Windows
- Check COLORTERM for truecolor/24bit indicators
- Check TERM for 256color/color/ansi indicators
- Use OSC 11 for background color detection (Unix only)
- Graceful fallback when detection fails (return None)
- Timeout handling for SSH sessions (500ms vs 50ms local)

### Component 4: Color Preset System (color_presets.py)

**Purpose**: Manage pre-defined color schemes and apply them to text

**Key Classes**:

```python
@dataclass
class ColorPreset:
    name: str
    colors: list[str]  # Hex color strings
    weights: list[int] | None = None  # Optional repetition factors
    
    def expand_colors(self) -> list[RGB]
        """Expand colors according to weights"""
    
    def spread_colors(self, length: int) -> list[RGB]
        """Distribute colors across specified length"""
    
    def adjust_lightness(self, light_dark: LightDark, method: str = "hsl") -> ColorPreset
        """Adjust colors for light/dark backgrounds"""
```

**Key Functions**:

```python
def load_presets(preset_file: Path) -> dict[str, ColorPreset]
    """Load color presets from JSON configuration"""

def spread_colors_balanced(colors: list[RGB], target_length: int) -> list[RGB]
    """Distribute colors with center-outward balancing"""
```

**Design Decisions**:
- Support simple presets (array of colors) and weighted presets
- Spread colors from center outward for balanced appearance
- Support lightness adjustment for background adaptation
- Load presets from JSON for easy customization

### Component 5: ASCII Renderer System (ascii_renderer.py)

**Purpose**: Apply colors to ASCII art with flexible alignment modes

**Key Classes**:

```python
@dataclass
class ColorAlignment:
    mode: Literal["horizontal", "vertical", "custom"]
    custom_colors: dict[str, str] | None = None  # For custom mode
    
    @classmethod
    def from_dict(cls, d: dict) -> ColorAlignment

class ASCIIColorizer:
    def __init__(self, preset: ColorPreset, alignment: ColorAlignment, ansi_mode: AnsiMode)
    
    def colorize(self, lines: list[str]) -> list[str]
        """Apply colors to ASCII art lines"""
    
    def colorize_horizontal(self, lines: list[str]) -> list[str]
        """One color per line"""
    
    def colorize_vertical(self, lines: list[str]) -> list[str]
        """Gradient across character positions"""
    
    def colorize_custom(self, lines: list[str]) -> list[str]
        """Custom per-ASCII-color-index mapping"""
    
    def strip_neofetch_codes(self, line: str) -> str
        """Remove existing neofetch color codes"""
```

**Design Decisions**:
- Support three alignment modes: horizontal, vertical, custom
- Strip existing color codes before applying new colors
- Preserve ASCII art structure and whitespace
- Use preset system for color source

### Component 6: Enhanced Serialization (serializer.py)

**Purpose**: Robust JSON serialization for dataclass-based configuration

**Key Functions**:

```python
def json_stringify(obj: Any, indent: int = 2) -> str
    """Convert dataclass to pretty-printed JSON"""

def to_dict(obj: Any) -> dict | list | Any
    """Convert dataclass to dictionary recursively"""

def from_dict(cls: type, d: dict) -> Any
    """Reconstruct dataclass from dictionary"""
```

**Design Decisions**:
- Handle nested dataclass structures recursively
- Convert enums to string representations
- Support custom serialization for complex types (Path, ColorAlignment)
- Validate required fields during deserialization


## Data Models

### Configuration Schema Extensions

**Extended AppConfig** (config.py):

```python
@dataclass
class BannerConfig:
    # Existing fields
    mode: str = "random"
    selected_banner: Optional[str] = None
    selected_categories: List[str] = field(default_factory=lambda: ["1ST_BEEFS"])
    animation_enabled: bool = True
    animation_duration: float = 3.0
    animation_fps: int = 8
    animation_intensity: str = "normal"
    
    # New fields for hyfetch integration
    color_preset: Optional[str] = None  # Preset name from color_presets.json
    color_alignment: str = "horizontal"  # "horizontal", "vertical", "custom"
    custom_color_map: Optional[Dict[str, str]] = None  # For custom alignment

@dataclass
class DisplayConfig:
    """New configuration section for display settings"""
    color_mode: AnsiMode = "default"  # "default", "rgb", "8bit", "ansi"
    auto_detect_background: bool = True
    force_light_dark: Optional[LightDark] = None  # Override detection
    lightness_adjustment: float = 0.65  # For dark backgrounds
    use_gradients: bool = False  # Enable gradient effects

@dataclass
class AppConfig:
    version: int = 1
    first_run_complete: bool = False
    theme_variant: str = "CRT_Cyan"
    banner: BannerConfig = field(default_factory=BannerConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)  # New section
    user_preferences: Dict[str, Any] = field(default_factory=dict)
```

**Migration Strategy**:
- Version 1 → Version 2: Add display section with defaults
- Existing configs load without display section (use defaults)
- Save operation includes new fields

### Theme System Extensions

**Extended ColorPalette** (themes.py):

```python
@dataclass
class ColorPalette:
    # Existing fields
    primary: str
    highlight: str
    success: str
    error: str
    warning: str
    dim: str
    text: str
    
    # New methods
    def to_rgb_palette(self) -> dict[str, RGB]:
        """Convert hex colors to RGB objects"""
    
    def adjust_for_background(self, bg_color: RGB) -> ColorPalette:
        """Adjust palette based on background lightness"""
```

**Extended Theme** (themes.py):

```python
class Theme:
    def __init__(self, name: str, palette: ColorPalette):
        self.name = name
        self.palette = palette
        self._rgb_palette: Optional[dict[str, RGB]] = None
    
    # New methods
    def get_color_mode(self) -> AnsiMode:
        """Get appropriate color mode for terminal"""
    
    def adapt_to_terminal(self, bg_color: Optional[RGB] = None) -> Theme:
        """Create terminal-adapted theme variant"""
```

### Banner Metadata Extensions

**Extended BannerMetadata** (banner.py):

```python
@dataclass
class BannerMetadata:
    category: str
    name: str
    author: Optional[str] = None
    description: Optional[str] = None
    dimensions: Tuple[int, int] = (0, 0)
    animation_compatible: bool = True
    
    # New fields for color alignment
    flame_lines: Optional[List[int]] = None  # Explicit flame zone
    recommended_preset: Optional[str] = None  # Suggested color preset
    color_zones: Optional[Dict[str, List[int]]] = None  # Named color zones
```

### Cache Data Models

**Cache Structure**:

```python
@dataclass
class CacheEntry:
    timestamp: float
    data: Any

@dataclass
class BannerCache:
    banners: Dict[str, List[Banner]]
    last_modified: float

@dataclass
class TerminalCache:
    ansi_mode: AnsiMode
    background_color: Optional[RGB]
    supports_rgb: bool
    supports_256: bool
    detected_at: float
    ttl: float = 3600.0  # 1 hour TTL
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

After analyzing all acceptance criteria, I identified the following consolidations to eliminate redundancy:

**Consolidations**:
- Properties 1.1 and 1.2 (RGB↔HSL conversion) → Combined into single round-trip property
- Properties 2.3 and 2.4 (8-bit grayscale vs color cube) → Combined into single 8-bit conversion property
- Properties 6.1 and 6.6 (serialization/deserialization) → Combined into single round-trip property
- Properties 8.4 and 8.5 (horizontal/vertical spreading) → Covered by general spreading property
- Terminal detection examples (3.1-3.8, 10.1-10.7) → Grouped into unit tests, not properties

**Eliminated as non-testable**:
- Implementation details (4.7, 13.7)
- Architectural requirements (7.1-7.4, 11.5-11.6)
- Integration test descriptions (14.1-14.4, 14.6)
- Documentation requirements (15.1-15.7)

**Result**: 45 unique testable properties from 107 acceptance criteria

### Property 1: RGB-HSL Round-Trip Preservation

*For any* valid RGB color, converting to HSL and back to RGB should produce a color equivalent to the original (within rounding tolerance of ±1 per component).

**Validates: Requirements 1.1, 1.2**

### Property 2: Lightness Adjustment Preserves Hue and Saturation

*For any* RGB color and any lightness value in [0.0, 1.0], setting the lightness should preserve the original hue and saturation values (within tolerance of ±0.01).

**Validates: Requirements 1.3, 12.7**

### Property 3: RGB Redistribution Maintains Proportions

*For any* RGB color and any multiplier that causes component overflow (>255), the redistribute_rgb function should ensure all components are ≤255 while maintaining the proportional relationships between R, G, and B components.

**Validates: Requirements 1.4**

### Property 4: Color Overlay Produces Valid RGB

*For any* two RGB colors and any alpha value in [0.0, 1.0], the overlay operation should produce a valid RGB color where each component is in [0, 255] and equals the weighted average: (1-alpha)*c1 + alpha*c2.

**Validates: Requirements 1.5**

### Property 5: Lightness Classification Threshold

*For any* RGB color, is_light() should return True if and only if the HSL lightness value is greater than 0.5.

**Validates: Requirements 1.7**

### Property 6: RGB ANSI Format Correctness

*For any* RGB color, to_ansi_rgb(foreground=True) should produce a string matching the format `\033[38;2;R;G;Bm` with the exact R, G, B values, and to_ansi_rgb(foreground=False) should use prefix `\033[48;2;R;G;Bm`.

**Validates: Requirements 2.1, 2.6**

### Property 7: 8-bit ANSI Code Range Validity

*For any* RGB color, to_ansi_8bit() should produce a code in the valid range: grayscale colors (low saturation) should map to codes 232-255, and saturated colors should map to codes 16-231.

**Validates: Requirements 2.2, 2.3, 2.4**

### Property 8: Color Cube Formula Correctness

*For any* saturated RGB color converted to 8-bit, the color code should equal `16 + 36*r + 6*g + b` where r, g, b are the RGB components scaled to [0, 5].

**Validates: Requirements 2.5**

### Property 9: Unified ANSI Interface Consistency

*For any* RGB color and any valid AnsiMode ("rgb", "8bit", "ansi"), to_ansi(mode) should produce output equivalent to calling the mode-specific method (to_ansi_rgb, to_ansi_8bit, or to_ansi_16).

**Validates: Requirements 2.7**

### Property 10: Terminal Detection Graceful Failure

*For any* environment where terminal capabilities cannot be determined, detect_ansi_mode() should return None rather than raising an exception.

**Validates: Requirements 3.6**

### Property 11: Gradient Length Matches Resolution

*For any* list of N RGB colors and any resolution R, create_gradient should produce a gradient array of length (N-1) * R.

**Validates: Requirements 4.2**

### Property 12: Linear Interpolation Correctness

*For any* two RGB colors c1 and c2 and any ratio r in [0.0, 1.0], the interpolated color should have each component equal to `c2 * r + c1 * (1 - r)` (rounded to nearest integer).

**Validates: Requirements 4.3**

### Property 13: Gradient Ratio Lookup Bounds

*For any* gradient and any ratio in [0.0, 1.0], the lookup should return a valid RGB color from the gradient array, with ratio 0.0 returning the first color and ratio 1.0 returning the last color.

**Validates: Requirements 4.4, 4.5**

### Property 14: Gradient Hex Initialization

*For any* list of valid hex color strings, create_gradient_hex should successfully create a gradient without errors.

**Validates: Requirements 4.6**

### Property 15: Weighted Preset Expansion

*For any* color preset with weights [w1, w2, ..., wN], expand_colors() should return a list of length equal to sum(weights), with each color repeated according to its weight.

**Validates: Requirements 5.4**

### Property 16: Color Spreading Exact Length

*For any* color preset and any target length L, spread_colors(L) should return exactly L colors.

**Validates: Requirements 5.5**

### Property 17: Center-Outward Distribution Balance

*For any* color preset with fewer colors than target length, spread_colors should distribute extra colors symmetrically from the center outward, maintaining visual balance.

**Validates: Requirements 5.6**

### Property 18: Lightness Adjustment Bounds

*For any* color preset and any light_dark setting, adjust_lightness should ensure all colors meet the lightness requirements: dark backgrounds require lightness ≥ 0.65, light backgrounds require lightness ≤ 0.4.

**Validates: Requirements 5.7, 12.2, 12.3**

### Property 19: Overlay Produces Valid Colors

*For any* color preset and any background RGB color with alpha in [0.0, 1.0], overlay operations should produce valid RGB colors with all components in [0, 255].

**Validates: Requirements 5.8**

### Property 20: Dataclass Serialization Round-Trip

*For any* dataclass instance, converting to dictionary with to_dict() and reconstructing with from_dict() should produce an equivalent object with all field values preserved.

**Validates: Requirements 6.1, 6.2, 6.6**

### Property 21: Enum Serialization to String

*For any* dataclass containing enum fields, to_dict() should convert enum values to their string representations (enum.value or enum.name).

**Validates: Requirements 6.3**

### Property 22: JSON Output Validity

*For any* dataclass instance, json_stringify() should produce valid JSON that can be parsed back into a dictionary.

**Validates: Requirements 6.5**

### Property 23: Required Field Validation

*For any* dictionary missing required fields for a dataclass, from_dict() should raise a TypeError or ValueError indicating the missing field.

**Validates: Requirements 6.7**

### Property 24: Configuration Type Validation

*For any* configuration data with invalid types (e.g., string where int expected), the Config_Manager load operation should either coerce to valid types or raise an appropriate error.

**Validates: Requirements 7.7**

### Property 25: Horizontal Alignment One Color Per Line

*For any* ASCII art with N lines and any color list, horizontal alignment should apply exactly one color per line, cycling through colors if fewer than N colors are provided.

**Validates: Requirements 8.1, 8.4**

### Property 26: Vertical Alignment Gradient Across Width

*For any* ASCII art with width W and any color list, vertical alignment should spread colors across W character positions, creating a horizontal gradient effect.

**Validates: Requirements 8.2, 8.5**

### Property 27: Custom Alignment Mapping

*For any* ASCII art with color codes and any custom color mapping, custom alignment should replace each color code with the mapped color.

**Validates: Requirements 8.3**

### Property 28: Neofetch Code Removal

*For any* ASCII art line containing neofetch color codes (e.g., `\033[...m`), strip_neofetch_codes() should remove all such codes while preserving the text content.

**Validates: Requirements 8.6**

### Property 29: ASCII Structure Preservation

*For any* ASCII art, colorization should not change the text content or whitespace structure—only ANSI color codes should be added.

**Validates: Requirements 8.7**

### Property 30: Minecraft Color Code Replacement

*For any* string containing Minecraft color codes (&0-&f, &l, &o, &n, &r, &-, &~, &*), the color() function should replace all codes with their corresponding ANSI escape sequences.

**Validates: Requirements 9.1, 9.2, 9.3**

### Property 31: RGB Color Code Parsing

*For any* string containing RGB color codes in formats &gf(#RRGGBB), &gb(#RRGGBB), or &gf(R,G,B), the color() function should parse and convert them to ANSI RGB escape codes.

**Validates: Requirements 9.4, 9.5, 9.6**

### Property 32: Automatic Reset Code Appending

*For any* string, printc() should ensure the output ends with the ANSI reset code `\033[0m`.

**Validates: Requirements 9.7**

### Property 33: OSC Response Parsing

*For any* valid OSC 11 response in format `rgb:RRRR/GGGG/BBBB`, the parser should extract RGB values correctly, converting 16-bit values to 8-bit (0-255) range.

**Validates: Requirements 10.4**

### Property 34: Distro Name Case Insensitivity

*For any* distro name string, the Banner_Database should match it case-insensitively (e.g., "Ubuntu", "ubuntu", "UBUNTU" should all match).

**Validates: Requirements 11.2**

### Property 35: Distro Partial Matching

*For any* partial distro name that is a substring of a known distro, the Banner_Database should attempt to find a match using partial word matching.

**Validates: Requirements 11.4**

### Property 36: Distro Fallback Banner

*For any* unrecognized or invalid distro name, the Banner_Database should return a fallback banner rather than raising an exception.

**Validates: Requirements 11.7**

### Property 37: Background Lightness Classification

*For any* RGB background color, the Theme_System should classify it as "light" if HSL lightness > 0.5, otherwise "dark".

**Validates: Requirements 12.1**

### Property 38: Overlay Lightness Adjustment Validity

*For any* color and any overlay-based lightness adjustment, the result should be a valid RGB color with all components in [0, 255].

**Validates: Requirements 12.4**

### Property 39: Cache Reuse on Repeated Access

*For any* cached data (distro detection, font logos), the second access should return the cached result without re-executing the expensive operation.

**Validates: Requirements 13.2, 13.3**

### Property 40: Cache Freshness Validation

*For any* cached data, if the source file modification time is newer than the cache timestamp, the cache should be invalidated and regenerated.

**Validates: Requirements 13.4, 13.5**

### Property 41: Cache Failure Graceful Handling

*For any* cache directory creation or write failure, the system should continue operating without crashing, falling back to non-cached operation.

**Validates: Requirements 13.6**

### Property 42: Backward Compatible Config Loading

*For any* configuration file from an older schema version, the Config_Manager should load it successfully, applying migrations and using defaults for new fields.

**Validates: Requirements 14.5**

### Property 43: Graceful Terminal Degradation

*For any* terminal with limited color capabilities (e.g., no RGB support), all color features should degrade gracefully to the best available mode (RGB → 8-bit → ANSI) without errors.

**Validates: Requirements 14.7**

### Property 44: Hex Color Format Support

*For any* valid hex color string in either 6-character (#RRGGBB) or 3-character (#RGB) format, RGB.from_hex() should parse it correctly.

**Validates: Requirements 1.6**

### Property 45: Gradient Smoothness

*For any* gradient created from a list of colors, consecutive colors in the gradient array should have small component differences (|ΔR|, |ΔG|, |ΔB| ≤ resolution-dependent threshold), ensuring smooth transitions.

**Validates: Requirements 4.1**


## Error Handling

### Error Categories and Strategies

#### 1. Color Conversion Errors

**Scenarios**:
- Invalid hex color format
- RGB values out of range
- HSL values out of range

**Strategy**:
```python
def from_hex(cls, hex: str) -> RGB:
    try:
        hex = hex.lstrip("#")
        if len(hex) not in (3, 6):
            raise ValueError(f"Invalid hex length: {len(hex)}")
        # ... conversion logic
    except (ValueError, IndexError) as e:
        logger.error(f"Failed to parse hex color '{hex}': {e}")
        raise ValueError(f"Invalid hex color format: {hex}") from e
```

**Recovery**: Raise descriptive ValueError with original hex string for debugging

#### 2. Terminal Detection Failures

**Scenarios**:
- Terminal not a TTY
- OSC query timeout
- Unsupported terminal emulator
- Permission errors accessing terminal

**Strategy**:
```python
def detect_ansi_mode() -> AnsiMode | None:
    try:
        # Platform-specific detection
        return unix_detect_ansi_mode()
    except Exception as e:
        logger.warning(f"Terminal detection failed: {e}")
        return None  # Graceful fallback
```

**Recovery**: Return None and use default mode ("8bit" as safe fallback)

#### 3. File I/O Errors

**Scenarios**:
- Preset file not found
- Cache directory creation failure
- Corrupted cache file
- Permission errors

**Strategy**:
```python
def load_presets(preset_file: Path) -> dict[str, ColorPreset]:
    try:
        with open(preset_file, 'r') as f:
            data = json.load(f)
        return parse_presets(data)
    except FileNotFoundError:
        logger.warning(f"Preset file not found: {preset_file}, using defaults")
        return get_default_presets()
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted preset file: {e}")
        return get_default_presets()
    except Exception as e:
        logger.error(f"Unexpected error loading presets: {e}")
        return get_default_presets()
```

**Recovery**: Use built-in default presets, continue operation

#### 4. Configuration Errors

**Scenarios**:
- Invalid configuration schema
- Type mismatches
- Missing required fields
- Corrupted JSON

**Strategy**:
```python
def load(self) -> AppConfig:
    try:
        data = json.load(config_file)
        return AppConfig.from_dict(data)
    except json.JSONDecodeError as e:
        logger.error(f"Corrupted config: {e}")
        self._backup_corrupted()
        return AppConfig()  # Use defaults
    except (TypeError, ValueError) as e:
        logger.error(f"Invalid config schema: {e}")
        self._backup_corrupted()
        return AppConfig()
```

**Recovery**: Backup corrupted file, use default configuration

#### 5. Gradient Generation Errors

**Scenarios**:
- Empty color list
- Single color (no gradient possible)
- Invalid resolution

**Strategy**:
```python
def create_gradient(colors: list[RGB], resolution: int) -> list[RGB]:
    if not colors:
        raise ValueError("Cannot create gradient from empty color list")
    if len(colors) == 1:
        # Single color "gradient" - just repeat the color
        return [colors[0]] * resolution
    if resolution < 1:
        raise ValueError(f"Resolution must be >= 1, got {resolution}")
    # ... gradient creation
```

**Recovery**: Raise descriptive errors for invalid inputs, handle edge cases gracefully

#### 6. ASCII Rendering Errors

**Scenarios**:
- Empty ASCII art
- Mismatched color list length
- Invalid alignment mode

**Strategy**:
```python
def colorize(self, lines: list[str]) -> list[str]:
    if not lines:
        logger.warning("Empty ASCII art provided")
        return []
    
    if not self.preset.colors:
        logger.warning("No colors in preset, returning uncolored ASCII")
        return lines
    
    try:
        if self.alignment.mode == "horizontal":
            return self.colorize_horizontal(lines)
        elif self.alignment.mode == "vertical":
            return self.colorize_vertical(lines)
        elif self.alignment.mode == "custom":
            return self.colorize_custom(lines)
        else:
            logger.error(f"Invalid alignment mode: {self.alignment.mode}")
            return lines  # Return uncolored
    except Exception as e:
        logger.error(f"Colorization failed: {e}", exc_info=True)
        return lines  # Fallback to uncolored
```

**Recovery**: Return uncolored ASCII art, log error for debugging

### Error Logging Strategy

All modules use Python's logging module with appropriate levels:

- **DEBUG**: Detailed diagnostic information (color conversions, cache hits)
- **INFO**: Normal operation milestones (preset loaded, terminal detected)
- **WARNING**: Recoverable issues (cache miss, fallback used)
- **ERROR**: Serious issues that don't stop execution (file I/O failure)
- **CRITICAL**: Fatal errors that prevent operation (should be rare)

### User-Facing Error Messages

Error messages should be:
1. **Descriptive**: Explain what went wrong
2. **Actionable**: Suggest how to fix it
3. **Non-technical**: Avoid implementation details in user messages

Example:
```python
# Bad
raise ValueError("RGB.from_hex: invalid length")

# Good
raise ValueError(
    f"Invalid color format '{hex}'. "
    f"Expected #RRGGBB (6 chars) or #RGB (3 chars), got {len(hex)} chars."
)
```

## Testing Strategy

### Dual Testing Approach

The testing strategy uses both unit tests and property-based tests to achieve comprehensive coverage:

**Unit Tests**: Verify specific examples, edge cases, and error conditions
**Property Tests**: Verify universal properties across all inputs

Together, these approaches provide complementary coverage—unit tests catch concrete bugs, property tests verify general correctness.

### Property-Based Testing Framework

**Library**: `hypothesis` for Python
**Configuration**: Minimum 100 iterations per property test

**Example Property Test**:

```python
from hypothesis import given, strategies as st
import pytest

@given(
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)
def test_rgb_hsl_roundtrip(r, g, b):
    """
    Feature: hyfetch-integration-analysis, Property 1: RGB-HSL Round-Trip Preservation
    
    For any valid RGB color, converting to HSL and back to RGB should produce
    a color equivalent to the original (within rounding tolerance of ±1 per component).
    """
    original = RGB(r, g, b)
    hsl = original.hsl()
    recovered = hsl.rgb()
    
    # Allow ±1 tolerance for rounding errors
    assert abs(recovered.r - original.r) <= 1
    assert abs(recovered.g - original.g) <= 1
    assert abs(recovered.b - original.b) <= 1
```

### Unit Test Organization

Unit tests are organized by module:

```
tests/
├── unit/
│   ├── test_color_util.py          # RGB/HSL conversion, ANSI generation
│   ├── test_color_scale.py         # Gradient generation
│   ├── test_terminal_detect.py     # Terminal capability detection
│   ├── test_color_presets.py       # Preset loading and spreading
│   ├── test_ascii_renderer.py      # Color alignment
│   └── test_serializer.py          # JSON serialization
├── property/
│   ├── test_color_properties.py    # Properties 1-9, 30-32, 44
│   ├── test_gradient_properties.py # Properties 11-14, 45
│   ├── test_preset_properties.py   # Properties 15-19
│   ├── test_serialization_properties.py  # Properties 20-23
│   ├── test_config_properties.py   # Properties 24, 42
│   ├── test_renderer_properties.py # Properties 25-29
│   ├── test_terminal_properties.py # Properties 10, 33-38, 43
│   └── test_cache_properties.py    # Properties 39-41
└── integration/
    ├── test_theme_integration.py   # Theme + terminal detection
    ├── test_animation_integration.py  # Animation + color system
    ├── test_banner_integration.py  # Banner + ASCII renderer
    └── test_config_integration.py  # Config + all systems
```

### Test Coverage Goals

- **Line Coverage**: ≥90% for all new modules
- **Branch Coverage**: ≥85% for conditional logic
- **Property Coverage**: 100% of identified properties tested

### Integration Testing

Integration tests verify that hyfetch-inspired features work with existing peepBeefy systems:

**Test 1: Color System + Animation Engine**
```python
def test_fire_animation_with_rgb_fallback():
    """Verify FireAnimator uses RGB or 8-bit based on terminal capability"""
    # Mock terminal with no RGB support
    with mock.patch('themes.TerminalCapabilities.supports_rgb', return_value=False):
        animator = FireAnimator(intensity="normal")
        assert animator._use_rgb == False
        assert animator._palette == FirePalette.STYLES_8BIT
```

**Test 2: Terminal Detection + Theme System**
```python
def test_theme_adapts_to_terminal():
    """Verify themes adapt colors based on terminal background"""
    bg_color = RGB(30, 30, 30)  # Dark background
    theme = ThemeRegistry.get_theme("CRT_Cyan")
    adapted = theme.adapt_to_terminal(bg_color)
    
    # Verify all text colors have sufficient lightness
    for color_name, color_hex in adapted.palette.__dict__.items():
        if color_name in ('text', 'highlight', 'primary'):
            rgb = RGB.from_hex(color_hex)
            assert rgb.hsl().l >= 0.65
```

**Test 3: ASCII Renderer + Banner System**
```python
def test_ascii_renderer_preserves_banner_structure():
    """Verify colorization doesn't alter ASCII art structure"""
    banner = banner_db.get_banner(category="1ST_BEEFS", name="CLASSIC")
    original_lines = banner.lines.copy()
    
    renderer = ASCIIColorizer(
        preset=ColorPreset("test", ["#FF0000", "#00FF00"]),
        alignment=ColorAlignment("horizontal"),
        ansi_mode="rgb"
    )
    
    colored_lines = renderer.colorize(banner.lines)
    
    # Strip ANSI codes and verify text is unchanged
    for original, colored in zip(original_lines, colored_lines):
        stripped = strip_ansi_codes(colored)
        assert stripped == original
```

### Performance Testing

Performance tests ensure the <200ms startup target is maintained:

```python
def test_startup_performance():
    """Verify application startup completes within 200ms"""
    import time
    
    start = time.monotonic()
    
    # Simulate startup sequence
    config = ConfigManager().load()
    theme = ThemeRegistry.get_theme(config.theme_variant)
    banner_db = BannerDatabase(assets_dir)
    banner = banner_db.get_banner()  # Should use cache
    
    elapsed = time.monotonic() - start
    
    assert elapsed < 0.2, f"Startup took {elapsed:.3f}s, exceeds 200ms target"
```

### Mocking Strategy

For terminal-dependent features, use mocking to simulate different environments:

```python
@pytest.fixture
def mock_rgb_terminal():
    """Mock terminal with RGB support"""
    with mock.patch.dict(os.environ, {
        'COLORTERM': 'truecolor',
        'TERM': 'xterm-256color'
    }):
        yield

@pytest.fixture
def mock_ansi_terminal():
    """Mock terminal with only ANSI support"""
    with mock.patch.dict(os.environ, {
        'TERM': 'linux'
    }):
        yield
```

### Test Execution

**Run all tests**:
```bash
pytest tests/ -v
```

**Run only property tests**:
```bash
pytest tests/property/ -v
```

**Run with coverage**:
```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

**Run performance tests**:
```bash
pytest tests/performance/ -v --benchmark-only
```

### Continuous Integration

All tests should run on:
- Python 3.9, 3.10, 3.11, 3.12
- Ubuntu, macOS, Windows
- With and without optional dependencies

### Test Data

Test data is organized in `tests/fixtures/`:
```
tests/fixtures/
├── presets/
│   ├── valid_preset.json
│   ├── weighted_preset.json
│   └── invalid_preset.json
├── configs/
│   ├── v1_config.json
│   ├── v2_config.json
│   └── corrupted_config.json
└── ascii/
    ├── simple_banner.txt
    ├── complex_banner.txt
    └── colored_banner.txt
```

## Implementation Notes

### Phase 1: Core Color Utilities (Week 1)

**Modules**: color_util.py, terminal_detect.py

**Tasks**:
1. Implement RGB and HSL dataclasses with conversion methods
2. Implement ANSI code generation (RGB, 8-bit, 16-color)
3. Implement terminal capability detection (Unix/Windows)
4. Implement Minecraft-style color code parser
5. Write unit tests and property tests for color operations
6. Integration test with existing themes.py

**Deliverables**:
- color_util.py with full RGB/HSL/ANSI support
- terminal_detect.py with platform-specific detection
- Test suite with ≥90% coverage
- Documentation for color utility API

### Phase 2: Gradient and Preset Systems (Week 2)

**Modules**: color_scale.py, color_presets.py

**Tasks**:
1. Implement gradient generation with linear interpolation
2. Implement Scale class for gradient lookup
3. Implement ColorPreset dataclass and loading
4. Implement color spreading algorithms
5. Implement lightness adjustment for presets
6. Write property tests for gradient smoothness
7. Create default preset collection

**Deliverables**:
- color_scale.py with gradient generation
- color_presets.py with preset management
- Default presets JSON file
- Test suite with property tests
- Documentation for gradient and preset APIs

### Phase 3: Configuration and Serialization (Week 3)

**Modules**: serializer.py, updates to config.py

**Tasks**:
1. Implement generic dataclass serialization
2. Implement custom serializers for Path, ColorAlignment
3. Extend AppConfig with DisplayConfig section
4. Implement v1→v2 migration
5. Write serialization round-trip tests
6. Test backward compatibility with old configs

**Deliverables**:
- serializer.py with dataclass serialization
- Updated config.py with new fields
- Migration function for v1→v2
- Test suite with backward compatibility tests
- Migration guide documentation

### Phase 4: ASCII Rendering (Week 4)

**Modules**: ascii_renderer.py, updates to banner.py

**Tasks**:
1. Implement ColorAlignment dataclass
2. Implement ASCIIColorizer class
3. Implement horizontal/vertical/custom alignment modes
4. Implement neofetch code stripping
5. Extend BannerMetadata with color zone fields
6. Write property tests for structure preservation
7. Integration test with banner system

**Deliverables**:
- ascii_renderer.py with all alignment modes
- Updated banner.py with color zone support
- Test suite with structure preservation tests
- Documentation for ASCII rendering API

### Phase 5: Advanced Features (Week 5)

**Modules**: Updates to themes.py, config.py

**Tasks**:
1. Implement OSC background color detection
2. Implement theme adaptation based on background
3. Implement caching system for banners and terminal detection
4. Implement cache freshness validation
5. Write cache property tests
6. Performance testing for startup time

**Deliverables**:
- OSC detection in terminal_detect.py
- Theme adaptation in themes.py
- Caching system in config.py and banner.py
- Performance test suite
- Optimization documentation

### Phase 6: Testing and Documentation (Week 6)

**Tasks**:
1. Complete all property-based tests
2. Achieve ≥90% code coverage
3. Write integration tests for all systems
4. Write comprehensive API documentation
5. Write migration guide for existing code
6. Write troubleshooting guide
7. Performance profiling and optimization

**Deliverables**:
- Complete test suite (unit + property + integration)
- API documentation for all new modules
- Migration guide for developers
- Troubleshooting guide for users
- Performance analysis report

### Performance Considerations

**Startup Time Budget** (200ms total):
- Config loading: 20ms
- Terminal detection: 30ms (with timeout)
- Banner cache loading: 50ms
- Theme initialization: 10ms
- Preset loading: 20ms
- Remaining: 70ms for application logic

**Optimization Strategies**:
1. **Lazy Loading**: Load presets only when needed
2. **Caching**: Cache terminal detection, banner database
3. **Pre-computation**: Pre-compute gradients at initialization
4. **Pickle Cache**: Use pickle for fast banner cache loading
5. **Avoid OSC**: Skip OSC detection by default (opt-in)

**Memory Considerations**:
- Gradient arrays: ~300 RGB objects per gradient (~7KB)
- Banner cache: ~100 banners × 1KB = ~100KB
- Preset cache: ~20 presets × 500B = ~10KB
- Total additional memory: ~120KB (acceptable)

### Backward Compatibility

**Configuration**:
- Old configs (v1) load with defaults for new fields
- Migration is automatic and transparent
- Old config files are never modified (atomic save)

**Themes**:
- Existing themes work without modification
- New color mode detection is opt-in
- Fallback to existing behavior if detection fails

**Banners**:
- Existing banner database format unchanged
- New metadata fields are optional
- Old banners render correctly without color zones

**Animation**:
- FireAnimator maintains existing API
- RGB/8-bit fallback is automatic
- No changes required to existing animation code

### Security Considerations

**File I/O**:
- Validate all file paths to prevent directory traversal
- Use safe JSON parsing (no eval or exec)
- Handle corrupted files gracefully

**Terminal I/O**:
- Timeout OSC queries to prevent hangs
- Restore terminal mode even on exceptions
- Validate OSC responses before parsing

**User Input**:
- Validate hex color formats
- Sanitize preset names (no path separators)
- Limit gradient resolution to prevent memory exhaustion

## Diagrams

### Color System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Color System                          │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐      │
│  │   RGB    │◄────►│   HSL    │      │  ANSI    │      │
│  │ (r,g,b)  │      │ (h,s,l)  │      │  Codes   │      │
│  └────┬─────┘      └────┬─────┘      └────▲─────┘      │
│       │                 │                  │             │
│       │  ┌──────────────┴──────────────┐   │             │
│       └─►│  Color Operations           │───┘             │
│          │  - lighten()                │                 │
│          │  - set_light()              │                 │
│          │  - overlay()                │                 │
│          │  - is_light()               │                 │
│          └─────────────────────────────┘                 │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

### Terminal Detection Flow

```
┌─────────────────────────────────────────────────────────┐
│              Terminal Detection Flow                     │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Detect OS     │
                  └───────┬───────┘
                          │
            ┌─────────────┴─────────────┐
            │                           │
            ▼                           ▼
    ┌───────────────┐          ┌───────────────┐
    │ Unix Detection│          │Win Detection  │
    └───────┬───────┘          └───────┬───────┘
            │                           │
            │ Check COLORTERM           │ Check ConEmuANSI
            │ Check TERM                │ Check Win Build
            │                           │
            └─────────────┬─────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Return Mode   │
                  │ rgb/8bit/ansi │
                  └───────────────┘
```

### Gradient Generation Process

```
Input: [Color1, Color2, Color3], Resolution=100

┌─────────┐     ┌─────────┐     ┌─────────┐
│ Color1  │────►│ Color2  │────►│ Color3  │
└─────────┘     └─────────┘     └─────────┘
     │               │               │
     │  100 steps    │  100 steps    │
     ▼               ▼               ▼
┌─────────────────────────────────────────┐
│  Gradient Array (200 colors total)      │
│  [C1, C1', C1'', ..., C2, ..., C3]      │
└─────────────────────────────────────────┘
                    │
                    │ Lookup by ratio
                    ▼
            ┌───────────────┐
            │ gradient[i]   │
            │ where i =     │
            │ ratio * len   │
            └───────────────┘
```

### ASCII Rendering Pipeline

```
┌─────────────────────────────────────────────────────────┐
│              ASCII Rendering Pipeline                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Load Banner   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Strip Existing│
                  │ Color Codes   │
                  └───────┬───────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Select Mode   │
                  └───────┬───────┘
                          │
            ┌─────────────┼─────────────┐
            │             │             │
            ▼             ▼             ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐
    │Horizontal│  │ Vertical │  │  Custom  │
    │ (1/line) │  │(gradient)│  │ (mapped) │
    └─────┬────┘  └─────┬────┘  └─────┬────┘
          │             │             │
          └─────────────┼─────────────┘
                        │
                        ▼
                ┌───────────────┐
                │ Apply Colors  │
                │ + ANSI Codes  │
                └───────┬───────┘
                        │
                        ▼
                ┌───────────────┐
                │ Colored ASCII │
                └───────────────┘
```

## Conclusion

This design document specifies a comprehensive integration of hyfetch's color handling, terminal detection, and rendering capabilities into peepBeefy. The modular architecture ensures clean integration with existing systems while maintaining backward compatibility and the retro CRT aesthetic.

Key design principles:
- **Modularity**: Self-contained modules with clear interfaces
- **Graceful Degradation**: Support for varying terminal capabilities
- **Performance**: Caching and lazy loading for <200ms startup
- **Testability**: Property-based testing for correctness guarantees
- **Maintainability**: Clear error handling and comprehensive documentation

The phased implementation approach allows for incremental development and testing, with each phase building on the previous one. The comprehensive test strategy ensures correctness through both unit tests and property-based tests, providing confidence in the implementation.
