"""Demonstration of ASCII renderer capabilities.

This script shows the three alignment modes in action:
- Horizontal: One color per line
- Vertical: Gradient across character positions
- Custom: Custom color mapping
"""

from src.ascii_renderer import ColorAlignment, ASCIIColorizer
from src.color_presets import ColorPreset


def demo_horizontal():
    """Demonstrate horizontal alignment mode."""
    print("\n" + "="*60)
    print("HORIZONTAL ALIGNMENT (one color per line)")
    print("="*60 + "\n")
    
    preset = ColorPreset(
        name="rainbow",
        colors=["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"]
    )
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
    
    ascii_art = [
        "╔═══════════════════════════╗",
        "║                           ║",
        "║      PEEPBEEFY ASCII      ║",
        "║      RENDERER DEMO        ║",
        "║                           ║",
        "║   Horizontal Alignment    ║",
        "║   One Color Per Line      ║",
        "║                           ║",
        "╚═══════════════════════════╝"
    ]
    
    result = colorizer.colorize(ascii_art)
    for line in result:
        print(line)


def demo_vertical():
    """Demonstrate vertical alignment mode."""
    print("\n" + "="*60)
    print("VERTICAL ALIGNMENT (gradient across width)")
    print("="*60 + "\n")
    
    preset = ColorPreset(
        name="fire",
        colors=["#FF0000", "#FF7F00", "#FFFF00", "#FFFFFF"]
    )
    alignment = ColorAlignment(mode="vertical")
    colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
    
    ascii_art = [
        "        *        ",
        "       ***       ",
        "      *****      ",
        "     *******     ",
        "    *********    ",
        "   ***********   ",
        "  *************  ",
        " *************** "
    ]
    
    result = colorizer.colorize(ascii_art)
    for line in result:
        print(line)


def demo_custom():
    """Demonstrate custom alignment mode."""
    print("\n" + "="*60)
    print("CUSTOM ALIGNMENT (custom color mapping)")
    print("="*60 + "\n")
    
    preset = ColorPreset(
        name="ocean",
        colors=["#001F3F", "#0074D9", "#7FDBFF", "#39CCCC"]
    )
    custom_colors = {"0": "0", "1": "1", "2": "2", "3": "3"}
    alignment = ColorAlignment(mode="custom", custom_colors=custom_colors)
    colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
    
    ascii_art = [
        "  ~~~~  ~~~~  ~~~~  ",
        " ~~~~~~ ~~~~~~ ~~~~ ",
        "~~~~~~~~~~~~~~~~~~~~ ",
        " ~~~~ ~~~~~~ ~~~~~~ ",
        "  ~~~~  ~~~~  ~~~~  "
    ]
    
    result = colorizer.colorize(ascii_art)
    for line in result:
        print(line)


def demo_comparison():
    """Show all three modes side by side."""
    print("\n" + "="*60)
    print("COMPARISON: Same ASCII art, different alignment modes")
    print("="*60 + "\n")
    
    preset = ColorPreset(
        name="cyber",
        colors=["#00FF00", "#00FFFF", "#FF00FF", "#FFFF00"]
    )
    
    ascii_art = [
        "  ╔═══╗  ",
        "  ║ █ ║  ",
        "  ╚═══╝  "
    ]
    
    # Horizontal
    print("Horizontal:")
    alignment = ColorAlignment(mode="horizontal")
    colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
    result = colorizer.colorize(ascii_art)
    for line in result:
        print(line)
    
    print()
    
    # Vertical
    print("Vertical:")
    alignment = ColorAlignment(mode="vertical")
    colorizer = ASCIIColorizer(preset, alignment, ansi_mode="rgb")
    result = colorizer.colorize(ascii_art)
    for line in result:
        print(line)


if __name__ == "__main__":
    print("\n" + "█"*60)
    print("█" + " "*58 + "█")
    print("█" + "  ASCII RENDERER DEMONSTRATION".center(58) + "█")
    print("█" + " "*58 + "█")
    print("█"*60)
    
    demo_horizontal()
    demo_vertical()
    demo_custom()
    demo_comparison()
    
    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60 + "\n")
