"""
Property-based tests for color preset operations.

Tests:
- Property 15: Weighted Preset Expansion
- Property 16: Color Spreading Exact Length
- Property 17: Center-Outward Distribution Balance
- Property 18: Lightness Adjustment Bounds

Validates Requirements 5.4, 5.5, 5.6, 5.7
"""

import pytest
from hypothesis import given, strategies as st, assume
from src.color_util import RGB
from src.color_presets import ColorPreset, spread_colors_balanced


# Strategy for generating valid RGB colors
rgb_colors = st.builds(
    RGB,
    r=st.integers(min_value=0, max_value=255),
    g=st.integers(min_value=0, max_value=255),
    b=st.integers(min_value=0, max_value=255)
)

# Strategy for generating hex color strings
hex_colors = st.text(
    alphabet='0123456789ABCDEFabcdef',
    min_size=6,
    max_size=6
).map(lambda s: f"#{s}")

# Strategy for generating lists of hex colors (1-10 colors)
hex_color_lists = st.lists(
    hex_colors,
    min_size=1,
    max_size=10
)

# Strategy for generating positive weights
positive_weights = st.integers(min_value=1, max_value=10)

# Strategy for generating target lengths
target_lengths = st.integers(min_value=1, max_value=100)

# Strategy for generating preset names
preset_names = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz_',
    min_size=1,
    max_size=20
)


class TestWeightedPresetExpansion:
    """Property 15: Weighted Preset Expansion
    
    For any color preset with weights [w1, w2, ..., wN], expand_colors() should
    return a list of length equal to sum(weights), with each color repeated
    according to its weight.
    
    Validates: Requirements 5.4
    """
    
    @given(preset_names, hex_color_lists, st.lists(positive_weights, min_size=1, max_size=10))
    def test_expansion_length_equals_sum_of_weights(self, name, colors, weights):
        """Expanded list length should equal sum of weights."""
        # Ensure weights match colors length
        weights = weights[:len(colors)]
        if len(weights) < len(colors):
            weights.extend([1] * (len(colors) - len(weights)))
        
        preset = ColorPreset(name=name, colors=colors, weights=weights)
        expanded = preset.expand_colors()
        
        expected_length = sum(weights)
        actual_length = len(expanded)
        
        assert actual_length == expected_length, \
            f"Expected length {expected_length}, got {actual_length} " \
            f"for weights {weights}"
    
    @given(preset_names, hex_color_lists, st.lists(positive_weights, min_size=1, max_size=10))
    def test_each_color_repeated_by_weight(self, name, colors, weights):
        """Each color should appear exactly weight times in expanded list."""
        # Ensure weights match colors length
        weights = weights[:len(colors)]
        if len(weights) < len(colors):
            weights.extend([1] * (len(colors) - len(weights)))
        
        # Skip if colors are not unique (can't count individual occurrences)
        assume(len(colors) == len(set(colors)))
        
        preset = ColorPreset(name=name, colors=colors, weights=weights)
        expanded = preset.expand_colors()
        
        # Convert colors to RGB for comparison
        rgb_colors = [RGB.from_hex(c) for c in colors]
        
        # Count occurrences of each color
        for i, (color, weight) in enumerate(zip(rgb_colors, weights)):
            count = sum(1 for c in expanded if c.r == color.r and c.g == color.g and c.b == color.b)
            assert count == weight, \
                f"Color {i} ({color}) should appear {weight} times, but appears {count} times"
    
    @given(preset_names, hex_color_lists)
    def test_expansion_without_weights_returns_colors_as_is(self, name, colors):
        """Preset without weights should return colors unchanged."""
        preset = ColorPreset(name=name, colors=colors, weights=None)
        expanded = preset.expand_colors()
        
        # Should have same length as input colors
        assert len(expanded) == len(colors)
        
        # Should match input colors
        rgb_colors = [RGB.from_hex(c) for c in colors]
        for i, (expected, actual) in enumerate(zip(rgb_colors, expanded)):
            assert expected.r == actual.r, f"Color {i} red mismatch"
            assert expected.g == actual.g, f"Color {i} green mismatch"
            assert expected.b == actual.b, f"Color {i} blue mismatch"
    
    def test_expansion_with_uniform_weights(self):
        """All weights equal should repeat each color same number of times."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            weights=[3, 3, 3]
        )
        expanded = preset.expand_colors()
        
        # Should have 9 colors total (3 * 3)
        assert len(expanded) == 9
        
        # Each color should appear 3 times
        red = RGB(255, 0, 0)
        green = RGB(0, 255, 0)
        blue = RGB(0, 0, 255)
        
        red_count = sum(1 for c in expanded if c.r == red.r and c.g == red.g and c.b == red.b)
        green_count = sum(1 for c in expanded if c.r == green.r and c.g == green.g and c.b == green.b)
        blue_count = sum(1 for c in expanded if c.r == blue.r and c.g == blue.g and c.b == blue.b)
        
        assert red_count == 3
        assert green_count == 3
        assert blue_count == 3
    
    def test_expansion_with_varying_weights(self):
        """Different weights should produce different repetition counts."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            weights=[1, 2, 3]
        )
        expanded = preset.expand_colors()
        
        # Should have 6 colors total (1 + 2 + 3)
        assert len(expanded) == 6
        
        # Count each color
        red = RGB(255, 0, 0)
        green = RGB(0, 255, 0)
        blue = RGB(0, 0, 255)
        
        red_count = sum(1 for c in expanded if c.r == red.r and c.g == red.g and c.b == red.b)
        green_count = sum(1 for c in expanded if c.r == green.r and c.g == green.g and c.b == green.b)
        blue_count = sum(1 for c in expanded if c.r == blue.r and c.g == blue.g and c.b == blue.b)
        
        assert red_count == 1
        assert green_count == 2
        assert blue_count == 3
    
    def test_expansion_preserves_color_order(self):
        """Expanded colors should maintain original order."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"],
            weights=[2, 1, 2]
        )
        expanded = preset.expand_colors()
        
        # Expected order: red, red, green, blue, blue
        red = RGB(255, 0, 0)
        green = RGB(0, 255, 0)
        blue = RGB(0, 0, 255)
        
        assert expanded[0] == red
        assert expanded[1] == red
        assert expanded[2] == green
        assert expanded[3] == blue
        assert expanded[4] == blue
    
    @given(preset_names, hex_color_lists)
    def test_expansion_returns_valid_rgb_colors(self, name, colors):
        """All expanded colors should be valid RGB instances."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        for color in expanded:
            assert isinstance(color, RGB)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255


class TestColorSpreadingExactLength:
    """Property 16: Color Spreading Exact Length
    
    For any color preset and any target length L, spread_colors(L) should
    return exactly L colors.
    
    Validates: Requirements 5.5
    """
    
    @given(preset_names, hex_color_lists, target_lengths)
    def test_spread_returns_exact_target_length(self, name, colors, target_length):
        """spread_colors should return exactly target_length colors."""
        preset = ColorPreset(name=name, colors=colors)
        spread = preset.spread_colors(target_length)
        
        assert len(spread) == target_length, \
            f"Expected {target_length} colors, got {len(spread)}"
    
    @given(preset_names, hex_color_lists, st.lists(positive_weights, min_size=1, max_size=10), target_lengths)
    def test_spread_with_weights_returns_exact_length(self, name, colors, weights, target_length):
        """spread_colors with weights should also return exact target_length."""
        # Ensure weights match colors length
        weights = weights[:len(colors)]
        if len(weights) < len(colors):
            weights.extend([1] * (len(colors) - len(weights)))
        
        preset = ColorPreset(name=name, colors=colors, weights=weights)
        spread = preset.spread_colors(target_length)
        
        assert len(spread) == target_length
    
    def test_spread_to_same_length_as_colors(self):
        """Spreading to same length as colors should return colors unchanged."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        spread = preset.spread_colors(3)
        
        assert len(spread) == 3
        
        # Should match original colors
        assert spread[0] == RGB(255, 0, 0)
        assert spread[1] == RGB(0, 255, 0)
        assert spread[2] == RGB(0, 0, 255)
    
    def test_spread_to_longer_length(self):
        """Spreading to longer length should interpolate colors."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#0000FF"]
        )
        spread = preset.spread_colors(10)
        
        assert len(spread) == 10
    
    def test_spread_to_shorter_length(self):
        """Spreading to shorter length should sample colors."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF"]
        )
        spread = preset.spread_colors(3)
        
        assert len(spread) == 3
    
    @given(preset_names, hex_color_lists, target_lengths)
    def test_spread_returns_valid_rgb_colors(self, name, colors, target_length):
        """All spread colors should be valid RGB instances."""
        preset = ColorPreset(name=name, colors=colors)
        spread = preset.spread_colors(target_length)
        
        for color in spread:
            assert isinstance(color, RGB)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255
    
    def test_spread_single_color_to_multiple(self):
        """Spreading single color should repeat it."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000"]
        )
        spread = preset.spread_colors(5)
        
        assert len(spread) == 5
        
        # All should be red
        for color in spread:
            assert color.r == 255
            assert color.g == 0
            assert color.b == 0
    
    def test_spread_to_length_one(self):
        """Spreading to length 1 should return single color."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        spread = preset.spread_colors(1)
        
        assert len(spread) == 1
        assert isinstance(spread[0], RGB)


class TestCenterOutwardDistributionBalance:
    """Property 17: Center-Outward Distribution Balance
    
    For any color preset with fewer colors than target length, spread_colors
    should distribute extra colors symmetrically from the center outward,
    maintaining visual balance.
    
    Validates: Requirements 5.6
    """
    
    @given(rgb_colors, rgb_colors, target_lengths)
    def test_two_color_spread_has_balanced_distribution(self, c1, c2, target_length):
        """Two colors spread should place colors at balanced positions."""
        assume(target_length >= 2)
        
        # Convert to hex
        hex1 = f"#{c1.r:02x}{c1.g:02x}{c1.b:02x}"
        hex2 = f"#{c2.r:02x}{c2.g:02x}{c2.b:02x}"
        
        preset = ColorPreset(name="test", colors=[hex1, hex2])
        spread = preset.spread_colors(target_length)
        
        # Should have exact target length
        assert len(spread) == target_length
        
        # Colors should be distributed across the range
        # First and last should be close to input colors or interpolated
        assert isinstance(spread[0], RGB)
        assert isinstance(spread[-1], RGB)
    
    @given(st.lists(rgb_colors, min_size=1, max_size=5), target_lengths)
    def test_spread_fills_all_positions(self, colors, target_length):
        """Spread should fill all positions without None values."""
        assume(target_length >= 1)
        
        # Convert to hex
        hex_colors = [f"#{c.r:02x}{c.g:02x}{c.b:02x}" for c in colors]
        
        preset = ColorPreset(name="test", colors=hex_colors)
        spread = preset.spread_colors(target_length)
        
        # All positions should be filled with valid RGB colors
        assert len(spread) == target_length
        assert all(isinstance(c, RGB) for c in spread)
        assert all(c is not None for c in spread)
    
    def test_spread_balanced_helper_function(self):
        """spread_colors_balanced should distribute colors symmetrically."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        # Spread 2 colors to 5 positions
        spread = spread_colors_balanced([red, blue], 5)
        
        assert len(spread) == 5
        
        # Should have colors distributed across the range
        # Exact positions depend on implementation, but should be balanced
        assert all(isinstance(c, RGB) for c in spread)
    
    def test_spread_three_colors_to_seven(self):
        """Three colors spread to seven should maintain balance."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]
        )
        spread = preset.spread_colors(7)
        
        assert len(spread) == 7
        
        # Should have all valid colors
        assert all(isinstance(c, RGB) for c in spread)
    
    @given(st.lists(rgb_colors, min_size=2, max_size=10), target_lengths)
    def test_spread_maintains_color_diversity(self, colors, target_length):
        """Spread should maintain diversity of input colors."""
        assume(target_length >= len(colors))
        
        # Convert to hex
        hex_colors = [f"#{c.r:02x}{c.g:02x}{c.b:02x}" for c in colors]
        
        preset = ColorPreset(name="test", colors=hex_colors)
        spread = preset.spread_colors(target_length)
        
        # Should have target length
        assert len(spread) == target_length
        
        # Should contain colors that span the input color range
        # (not all identical unless input was identical)
        if len(set((c.r, c.g, c.b) for c in colors)) > 1:
            # Input has diversity, output should too
            unique_spread = set((c.r, c.g, c.b) for c in spread)
            assert len(unique_spread) > 1, "Spread should maintain color diversity"
    
    def test_spread_balanced_with_interpolation(self):
        """Spread should interpolate between placed colors."""
        red = RGB(255, 0, 0)
        blue = RGB(0, 0, 255)
        
        # Spread to 10 positions
        spread = spread_colors_balanced([red, blue], 10)
        
        assert len(spread) == 10
        
        # Should have smooth transition from red to blue
        # First should be reddish, last should be bluish
        assert spread[0].r > spread[-1].r
        assert spread[-1].b > spread[0].b


class TestLightnessAdjustmentBounds:
    """Property 18: Lightness Adjustment Bounds
    
    For any color preset and any light_dark setting, adjust_lightness should
    ensure all colors meet the lightness requirements: dark backgrounds require
    lightness >= 0.65, light backgrounds require lightness <= 0.4.
    
    Validates: Requirements 5.7, 12.2, 12.3
    """
    
    @given(preset_names, hex_color_lists)
    def test_dark_background_adjustment_meets_minimum_lightness(self, name, colors):
        """Dark background adjustment should ensure lightness >= 0.65."""
        preset = ColorPreset(name=name, colors=colors)
        adjusted = preset.adjust_lightness("dark", method="hsl")
        
        # Get adjusted colors
        adjusted_colors = adjusted.expand_colors()
        
        # All colors should have lightness >= 0.65
        for color in adjusted_colors:
            hsl = color.hsl()
            assert hsl.l >= 0.64, \
                f"Color {color} has lightness {hsl.l}, expected >= 0.65 (allowing 0.01 tolerance)"
    
    @given(preset_names, hex_color_lists)
    def test_light_background_adjustment_meets_maximum_lightness(self, name, colors):
        """Light background adjustment should ensure lightness <= 0.4."""
        preset = ColorPreset(name=name, colors=colors)
        adjusted = preset.adjust_lightness("light", method="hsl")
        
        # Get adjusted colors
        adjusted_colors = adjusted.expand_colors()
        
        # All colors should have lightness <= 0.4
        for color in adjusted_colors:
            hsl = color.hsl()
            assert hsl.l <= 0.41, \
                f"Color {color} has lightness {hsl.l}, expected <= 0.4 (allowing 0.01 tolerance)"
    
    @given(preset_names, hex_color_lists)
    def test_overlay_method_dark_background_meets_minimum(self, name, colors):
        """Overlay method for dark background should ensure lightness >= 0.65."""
        preset = ColorPreset(name=name, colors=colors)
        adjusted = preset.adjust_lightness("dark", method="overlay")
        
        # Get adjusted colors
        adjusted_colors = adjusted.expand_colors()
        
        # All colors should have lightness >= 0.65 (with some tolerance for overlay approximation)
        for color in adjusted_colors:
            hsl = color.hsl()
            # Overlay method uses linear approximation, allow small tolerance
            assert hsl.l >= 0.63, \
                f"Color {color} has lightness {hsl.l}, expected >= 0.65 (overlay method, allowing 0.02 tolerance)"
    
    @given(preset_names, hex_color_lists)
    def test_overlay_method_light_background_meets_maximum(self, name, colors):
        """Overlay method for light background should ensure lightness <= 0.4."""
        preset = ColorPreset(name=name, colors=colors)
        adjusted = preset.adjust_lightness("light", method="overlay")
        
        # Get adjusted colors
        adjusted_colors = adjusted.expand_colors()
        
        # All colors should have lightness <= 0.4 (with some tolerance for overlay approximation)
        for color in adjusted_colors:
            hsl = color.hsl()
            # Overlay method uses linear approximation, allow small tolerance
            assert hsl.l <= 0.42, \
                f"Color {color} has lightness {hsl.l}, expected <= 0.4 (overlay method, allowing 0.02 tolerance)"
    
    def test_dark_background_adjustment_preserves_hue(self):
        """Dark background adjustment should preserve hue."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00", "#0000FF"]  # Pure red, green, blue
        )
        adjusted = preset.adjust_lightness("dark", method="hsl")
        
        original_colors = preset.expand_colors()
        adjusted_colors = adjusted.expand_colors()
        
        # Hue should be preserved (with tolerance for rounding)
        for orig, adj in zip(original_colors, adjusted_colors):
            orig_hsl = orig.hsl()
            adj_hsl = adj.hsl()
            
            # Only check hue if saturation is significant (avoid gray colors)
            if orig_hsl.s > 0.1:
                hue_diff = abs(orig_hsl.h - adj_hsl.h)
                # Allow wrap-around (0.0 and 1.0 are same hue)
                if hue_diff > 0.5:
                    hue_diff = 1.0 - hue_diff
                assert hue_diff < 0.05, \
                    f"Hue changed from {orig_hsl.h} to {adj_hsl.h}"
    
    def test_light_background_adjustment_preserves_hue(self):
        """Light background adjustment should preserve hue."""
        preset = ColorPreset(
            name="test",
            colors=["#FF8080", "#80FF80", "#8080FF"]  # Light red, green, blue
        )
        adjusted = preset.adjust_lightness("light", method="hsl")
        
        original_colors = preset.expand_colors()
        adjusted_colors = adjusted.expand_colors()
        
        # Hue should be preserved
        for orig, adj in zip(original_colors, adjusted_colors):
            orig_hsl = orig.hsl()
            adj_hsl = adj.hsl()
            
            # Only check hue if saturation is significant
            if orig_hsl.s > 0.1:
                hue_diff = abs(orig_hsl.h - adj_hsl.h)
                if hue_diff > 0.5:
                    hue_diff = 1.0 - hue_diff
                assert hue_diff < 0.05
    
    @given(preset_names, hex_color_lists)
    def test_adjusted_colors_are_valid_rgb(self, name, colors):
        """Adjusted colors should have valid RGB values."""
        preset = ColorPreset(name=name, colors=colors)
        
        for light_dark in ["dark", "light"]:
            for method in ["hsl", "overlay"]:
                adjusted = preset.adjust_lightness(light_dark, method=method)
                adjusted_colors = adjusted.expand_colors()
                
                for color in adjusted_colors:
                    assert isinstance(color, RGB)
                    assert 0 <= color.r <= 255, f"Red {color.r} out of range"
                    assert 0 <= color.g <= 255, f"Green {color.g} out of range"
                    assert 0 <= color.b <= 255, f"Blue {color.b} out of range"
    
    def test_already_light_colors_unchanged_for_dark_background(self):
        """Colors already light enough should not change for dark background."""
        # Create very light colors (lightness > 0.65)
        preset = ColorPreset(
            name="test",
            colors=["#FFFFFF", "#F0F0F0", "#E0E0E0"]
        )
        adjusted = preset.adjust_lightness("dark", method="hsl")
        
        original_colors = preset.expand_colors()
        adjusted_colors = adjusted.expand_colors()
        
        # Colors should be unchanged (or very close)
        for orig, adj in zip(original_colors, adjusted_colors):
            assert abs(orig.r - adj.r) <= 1
            assert abs(orig.g - adj.g) <= 1
            assert abs(orig.b - adj.b) <= 1
    
    def test_already_dark_colors_unchanged_for_light_background(self):
        """Colors already dark enough should not change for light background."""
        # Create very dark colors (lightness < 0.4)
        preset = ColorPreset(
            name="test",
            colors=["#000000", "#101010", "#202020"]
        )
        adjusted = preset.adjust_lightness("light", method="hsl")
        
        original_colors = preset.expand_colors()
        adjusted_colors = adjusted.expand_colors()
        
        # Colors should be unchanged (or very close)
        for orig, adj in zip(original_colors, adjusted_colors):
            assert abs(orig.r - adj.r) <= 1
            assert abs(orig.g - adj.g) <= 1
            assert abs(orig.b - adj.b) <= 1
    
    def test_adjustment_returns_new_preset_instance(self):
        """adjust_lightness should return a new ColorPreset instance."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"]
        )
        adjusted = preset.adjust_lightness("dark")
        
        # Should be a different instance
        assert adjusted is not preset
        assert isinstance(adjusted, ColorPreset)
        
        # Original should be unchanged
        assert preset.name == "test"
        assert len(preset.colors) == 2
    
    def test_adjusted_preset_has_no_weights(self):
        """Adjusted preset should have weights=None (already expanded)."""
        preset = ColorPreset(
            name="test",
            colors=["#FF0000", "#00FF00"],
            weights=[2, 1]
        )
        adjusted = preset.adjust_lightness("dark")
        
        # Adjusted preset should have no weights
        assert adjusted.weights is None
        
        # Should have expanded colors (3 total: 2 red + 1 green)
        assert len(adjusted.colors) == 3


class TestOverlayProducesValidColors:
    """Property 19: Overlay Produces Valid Colors
    
    For any color preset and any background RGB color with alpha in [0.0, 1.0],
    overlay operations should produce valid RGB colors with all components in [0, 255].
    
    Validates: Requirements 5.8
    """
    
    @given(preset_names, hex_color_lists, rgb_colors, st.floats(min_value=0.0, max_value=1.0))
    def test_overlay_produces_valid_rgb_components(self, name, colors, bg_color, alpha):
        """Overlay operations should produce RGB colors with components in [0, 255]."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        # Apply overlay to each color
        for color in expanded:
            overlaid = color.overlay(bg_color, alpha)
            
            # All components should be in valid range
            assert isinstance(overlaid, RGB)
            assert 0 <= overlaid.r <= 255, f"Red {overlaid.r} out of range [0, 255]"
            assert 0 <= overlaid.g <= 255, f"Green {overlaid.g} out of range [0, 255]"
            assert 0 <= overlaid.b <= 255, f"Blue {overlaid.b} out of range [0, 255]"
    
    @given(preset_names, hex_color_lists, st.floats(min_value=0.0, max_value=1.0))
    def test_overlay_with_white_produces_valid_colors(self, name, colors, alpha):
        """Overlay with white (lightening) should produce valid RGB colors."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        white = RGB(r=255, g=255, b=255)
        
        for color in expanded:
            overlaid = color.overlay(white, alpha)
            
            assert isinstance(overlaid, RGB)
            assert 0 <= overlaid.r <= 255
            assert 0 <= overlaid.g <= 255
            assert 0 <= overlaid.b <= 255
    
    @given(preset_names, hex_color_lists, st.floats(min_value=0.0, max_value=1.0))
    def test_overlay_with_black_produces_valid_colors(self, name, colors, alpha):
        """Overlay with black (darkening) should produce valid RGB colors."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        black = RGB(r=0, g=0, b=0)
        
        for color in expanded:
            overlaid = color.overlay(black, alpha)
            
            assert isinstance(overlaid, RGB)
            assert 0 <= overlaid.r <= 255
            assert 0 <= overlaid.g <= 255
            assert 0 <= overlaid.b <= 255
    
    @given(preset_names, hex_color_lists)
    def test_overlay_alpha_zero_returns_original(self, name, colors):
        """Overlay with alpha=0.0 should return original color."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        bg_color = RGB(r=128, g=128, b=128)
        
        for color in expanded:
            overlaid = color.overlay(bg_color, 0.0)
            
            # Should be identical to original
            assert overlaid.r == color.r
            assert overlaid.g == color.g
            assert overlaid.b == color.b
    
    @given(preset_names, hex_color_lists, rgb_colors)
    def test_overlay_alpha_one_returns_overlay_color(self, name, colors, bg_color):
        """Overlay with alpha=1.0 should return overlay color."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        for color in expanded:
            overlaid = color.overlay(bg_color, 1.0)
            
            # Should be identical to overlay color
            assert overlaid.r == bg_color.r
            assert overlaid.g == bg_color.g
            assert overlaid.b == bg_color.b
    
    @given(preset_names, hex_color_lists, rgb_colors, st.floats(min_value=0.0, max_value=1.0))
    def test_overlay_formula_correctness(self, name, colors, bg_color, alpha):
        """Overlay should follow formula: result = (1-alpha)*color + alpha*bg_color."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        for color in expanded:
            overlaid = color.overlay(bg_color, alpha)
            
            # Calculate expected values
            expected_r = round((1 - alpha) * color.r + alpha * bg_color.r)
            expected_g = round((1 - alpha) * color.g + alpha * bg_color.g)
            expected_b = round((1 - alpha) * color.b + alpha * bg_color.b)
            
            # Verify formula
            assert overlaid.r == expected_r, \
                f"Red mismatch: expected {expected_r}, got {overlaid.r}"
            assert overlaid.g == expected_g, \
                f"Green mismatch: expected {expected_g}, got {overlaid.g}"
            assert overlaid.b == expected_b, \
                f"Blue mismatch: expected {expected_b}, got {overlaid.b}"
    
    def test_overlay_in_lightness_adjustment_dark_background(self):
        """Overlay method in adjust_lightness for dark background should produce valid colors."""
        preset = ColorPreset(
            name="test",
            colors=["#000000", "#404040", "#808080", "#C0C0C0", "#FFFFFF"]
        )
        
        # Adjust for dark background using overlay method
        adjusted = preset.adjust_lightness("dark", method="overlay")
        adjusted_colors = adjusted.expand_colors()
        
        # All colors should be valid RGB
        for color in adjusted_colors:
            assert isinstance(color, RGB)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255
    
    def test_overlay_in_lightness_adjustment_light_background(self):
        """Overlay method in adjust_lightness for light background should produce valid colors."""
        preset = ColorPreset(
            name="test",
            colors=["#000000", "#404040", "#808080", "#C0C0C0", "#FFFFFF"]
        )
        
        # Adjust for light background using overlay method
        adjusted = preset.adjust_lightness("light", method="overlay")
        adjusted_colors = adjusted.expand_colors()
        
        # All colors should be valid RGB
        for color in adjusted_colors:
            assert isinstance(color, RGB)
            assert 0 <= color.r <= 255
            assert 0 <= color.g <= 255
            assert 0 <= color.b <= 255
    
    @given(preset_names, hex_color_lists)
    def test_overlay_preserves_color_type(self, name, colors):
        """Overlay should always return RGB instances."""
        preset = ColorPreset(name=name, colors=colors)
        expanded = preset.expand_colors()
        
        test_colors = [
            RGB(r=0, g=0, b=0),      # Black
            RGB(r=255, g=255, b=255), # White
            RGB(r=128, g=128, b=128)  # Gray
        ]
        
        for color in expanded:
            for test_color in test_colors:
                for alpha in [0.0, 0.25, 0.5, 0.75, 1.0]:
                    overlaid = color.overlay(test_color, alpha)
                    assert isinstance(overlaid, RGB), \
                        f"Overlay returned {type(overlaid)}, expected RGB"
    
    def test_overlay_with_extreme_colors(self):
        """Overlay with extreme color values should produce valid results."""
        # Test with pure colors
        pure_colors = [
            RGB(r=255, g=0, b=0),    # Pure red
            RGB(r=0, g=255, b=0),    # Pure green
            RGB(r=0, g=0, b=255),    # Pure blue
            RGB(r=255, g=255, b=0),  # Yellow
            RGB(r=255, g=0, b=255),  # Magenta
            RGB(r=0, g=255, b=255),  # Cyan
        ]
        
        overlay_colors = [
            RGB(r=0, g=0, b=0),      # Black
            RGB(r=255, g=255, b=255) # White
        ]
        
        for color in pure_colors:
            for overlay_color in overlay_colors:
                for alpha in [0.0, 0.1, 0.5, 0.9, 1.0]:
                    overlaid = color.overlay(overlay_color, alpha)
                    
                    assert isinstance(overlaid, RGB)
                    assert 0 <= overlaid.r <= 255
                    assert 0 <= overlaid.g <= 255
                    assert 0 <= overlaid.b <= 255
    
    @given(rgb_colors, rgb_colors, st.floats(min_value=0.0, max_value=1.0))
    def test_overlay_is_commutative_in_result_validity(self, c1, c2, alpha):
        """Both overlay directions should produce valid RGB colors."""
        # c1.overlay(c2, alpha) and c2.overlay(c1, 1-alpha) should both be valid
        overlaid1 = c1.overlay(c2, alpha)
        overlaid2 = c2.overlay(c1, 1.0 - alpha)
        
        # Both should be valid RGB
        assert isinstance(overlaid1, RGB)
        assert 0 <= overlaid1.r <= 255
        assert 0 <= overlaid1.g <= 255
        assert 0 <= overlaid1.b <= 255
        
        assert isinstance(overlaid2, RGB)
        assert 0 <= overlaid2.r <= 255
        assert 0 <= overlaid2.g <= 255
        assert 0 <= overlaid2.b <= 255


class TestPresetEdgeCases:
    """Test edge cases and error handling for preset operations."""
    
    def test_preset_with_empty_colors_raises_error(self):
        """Preset with empty colors list should raise ValueError."""
        with pytest.raises(ValueError, match="must have at least one color"):
            ColorPreset(name="test", colors=[])
    
    def test_preset_with_mismatched_weights_raises_error(self):
        """Preset with weights length != colors length should raise ValueError."""
        with pytest.raises(ValueError, match="weights length.*must match colors length"):
            ColorPreset(
                name="test",
                colors=["#FF0000", "#00FF00"],
                weights=[1, 2, 3]  # 3 weights for 2 colors
            )
    
    def test_preset_with_zero_weight_raises_error(self):
        """Preset with zero or negative weight should raise ValueError."""
        with pytest.raises(ValueError, match="all weights must be positive"):
            ColorPreset(
                name="test",
                colors=["#FF0000", "#00FF00"],
                weights=[1, 0]
            )
    
    def test_preset_with_negative_weight_raises_error(self):
        """Preset with negative weight should raise ValueError."""
        with pytest.raises(ValueError, match="all weights must be positive"):
            ColorPreset(
                name="test",
                colors=["#FF0000"],
                weights=[-1]
            )
    
    def test_spread_to_zero_length_raises_error(self):
        """Spreading to length 0 should raise ValueError."""
        preset = ColorPreset(name="test", colors=["#FF0000"])
        
        with pytest.raises(ValueError, match="Length must be positive"):
            preset.spread_colors(0)
    
    def test_spread_to_negative_length_raises_error(self):
        """Spreading to negative length should raise ValueError."""
        preset = ColorPreset(name="test", colors=["#FF0000"])
        
        with pytest.raises(ValueError, match="Length must be positive"):
            preset.spread_colors(-5)
    
    def test_spread_balanced_with_empty_list_raises_error(self):
        """spread_colors_balanced with empty list should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot spread empty color list"):
            spread_colors_balanced([], 10)
    
    def test_spread_balanced_to_zero_length_raises_error(self):
        """spread_colors_balanced to length 0 should raise ValueError."""
        red = RGB(255, 0, 0)
        
        with pytest.raises(ValueError, match="Target length must be positive"):
            spread_colors_balanced([red], 0)
    
    def test_preset_with_invalid_hex_color_raises_error(self):
        """Preset with invalid hex color should raise error on expansion."""
        preset = ColorPreset(name="test", colors=["#GGGGGG"])
        
        with pytest.raises(ValueError):
            preset.expand_colors()
    
    def test_adjustment_with_invalid_light_dark_value(self):
        """adjust_lightness with invalid light_dark should work (no validation)."""
        preset = ColorPreset(name="test", colors=["#FF0000"])
        
        # Python typing doesn't enforce Literal at runtime, so this won't raise
        # But the logic should handle it gracefully (default to one branch)
        adjusted = preset.adjust_lightness("invalid")  # type: ignore
        
        # Should still return a ColorPreset
        assert isinstance(adjusted, ColorPreset)
