"""Setup wizard for first-run configuration.

This module provides an interactive setup wizard that guides users through
configuring peepBeefy on their first run, including theme selection, banner
mode selection, and animation preferences.
"""

from pathlib import Path
from typing import Optional
import logging
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich.style import Style
from rich import box

from config import AppConfig, BannerConfig
from themes import ThemeRegistry, Theme
from banner import BannerDatabase, BannerRenderer

logger = logging.getLogger(__name__)


def show_theme_preview(theme_name: str, console: Optional[Console] = None) -> None:
    """Display a preview of a theme's colors.
    
    Args:
        theme_name: Name of the theme to preview
        console: Optional Console instance (creates new one if not provided)
    """
    if console is None:
        console = Console()
    
    theme = ThemeRegistry.get_theme(theme_name)
    
    # Create sample panel with theme colors
    sample_text = Text()
    sample_text.append("Primary ", style=Style(color=theme.palette.primary))
    sample_text.append("• ")
    sample_text.append("Highlight ", style=Style(color=theme.palette.highlight, bold=True))
    sample_text.append("• ")
    sample_text.append("Success ", style=Style(color=theme.palette.success))
    sample_text.append("• ")
    sample_text.append("Warning", style=Style(color=theme.palette.warning))
    
    panel = Panel(
        sample_text,
        title=f"[bold]{theme_name}[/bold]",
        box=theme.get_box_style(),
        border_style=theme.get_border_style(),
        padding=(0, 1)
    )
    
    console.print(panel)


def run_setup_wizard(current_config: Optional[AppConfig] = None, console: Optional[Console] = None) -> AppConfig:
    """Run the setup wizard and return the configured AppConfig.
    
    Args:
        current_config: Optional existing config to use as defaults
        console: Optional Console instance (creates new one if not provided)
        
    Returns:
        Configured AppConfig instance
    """
    if console is None:
        console = Console()
    
    wizard = SetupWizard(console)
    return wizard.run(current_config=current_config)


class SetupWizard:
    """Interactive setup wizard for first-run configuration.
    
    Guides users through a step-by-step configuration process with visual
    previews and helpful descriptions. Follows the hyfetch-inspired pattern
    for interactive configuration.
    
    Attributes:
        console: Rich Console instance for rendering
        _assets_dir: Path to the assets directory for banner previews
    """
    
    def __init__(self, console: Console, assets_dir: Optional[Path] = None):
        """Initialize the setup wizard.
        
        Args:
            console: Rich Console instance for rendering
            assets_dir: Optional path to assets directory, defaults to .assets
        """
        self.console = console
        self._assets_dir = assets_dir or (Path(__file__).parent.parent / ".assets")
    
    def run(self, current_config: Optional[AppConfig] = None) -> AppConfig:
        """Run the complete setup wizard flow.
        
        Displays welcome screen and guides user through configuration steps:
        1. Theme selection
        2. Banner mode selection
        3. Animation preferences
        
        Users can skip the wizard to use default settings.
        
        Args:
            current_config: Optional existing config to use as defaults
        
        Returns:
            Completed AppConfig object with user selections
        """
        # Display welcome screen
        skip = self._show_welcome()
        
        # If user wants to skip, return default config
        if skip:
            logger.info("User skipped setup wizard, using defaults")
            return AppConfig(
                version=1,
                first_run_complete=True,
                theme_variant="CRT_Cyan",
                banner=BannerConfig(
                    mode="random",
                    selected_banner=None,
                    selected_categories=["1ST_BEEFS"],
                    animation_enabled=True,
                    animation_duration=3.0,
                    animation_fps=8,
                    animation_intensity="normal"
                )
            )
        
        # Step 1: Theme selection
        theme_variant = self._select_theme()
        
        # Step 2: Banner mode selection
        banner_mode, selected_banner, selected_categories = self._select_banner_mode()
        
        # Step 3: Animation preferences
        animation_enabled, animation_intensity = self._select_animation_preferences()
        
        # Build configuration
        config = AppConfig(
            version=1,
            first_run_complete=True,
            theme_variant=theme_variant,
            banner=BannerConfig(
                mode=banner_mode,
                selected_banner=selected_banner,
                selected_categories=selected_categories,
                animation_enabled=animation_enabled,
                animation_duration=3.0,
                animation_fps=8,
                animation_intensity=animation_intensity
            )
        )
        
        # Show completion message
        self._show_completion()
        
        return config
    
    def _show_welcome(self) -> bool:
        """Display welcome screen with Panel and skip option.
        
        Returns:
            True if user wants to skip wizard, False otherwise
        """
        self.console.clear()
        
        welcome_text = Text()
        welcome_text.append("Welcome to ", style="bold")
        welcome_text.append("peepBeefy", style="bold cyan")
        welcome_text.append(" Setup!\n\n", style="bold")
        welcome_text.append(
            "This wizard will help you configure your peepBeefy experience.\n"
            "You can change these settings later from the Settings menu.\n\n",
            style="dim"
        )
        welcome_text.append(
            "Press Enter to continue, or type 'skip' to use default settings...",
            style="dim"
        )
        
        panel = Panel(
            welcome_text,
            title="[bold cyan]First-Run Setup[/bold cyan]",
            box=box.DOUBLE,
            border_style="cyan",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        
        # Allow user to skip
        response = self.console.input().strip().lower()
        return response == "skip"
    
    def _show_completion(self) -> None:
        """Display completion message."""
        completion_text = Text()
        completion_text.append("Setup Complete!\n\n", style="bold green")
        completion_text.append(
            "Your preferences have been saved. Enjoy peepBeefy!\n\n"
            "You can reconfigure anytime from the Settings menu.",
            style="dim"
        )
        
        panel = Panel(
            completion_text,
            title="[bold green]✓ All Done[/bold green]",
            box=box.DOUBLE,
            border_style="green",
            padding=(1, 2)
        )
        
        self.console.print(panel)
    
    def _select_theme(self) -> str:
        """Theme selection step with visual previews.
        
        Displays all available themes with sample panels showing their colors.
        Uses Rich Prompt for user selection with CRT_Cyan as default.
        
        Returns:
            Selected theme name
        """
        self.console.clear()
        
        # Show step indicator
        self.console.print(
            Panel(
                "[bold]Step 1/3: Theme Selection[/bold]",
                box=box.ROUNDED,
                border_style="cyan"
            )
        )
        self.console.print()
        
        # Get all available themes
        theme_names = ThemeRegistry.list_themes()
        
        # Display preview for each theme
        for theme_name in theme_names:
            theme = ThemeRegistry.get_theme(theme_name)
            
            # Create sample panel with theme colors
            sample_text = Text()
            sample_text.append("Primary ", style=Style(color=theme.palette.primary))
            sample_text.append("• ")
            sample_text.append("Highlight ", style=Style(color=theme.palette.highlight, bold=True))
            sample_text.append("• ")
            sample_text.append("Success ", style=Style(color=theme.palette.success))
            sample_text.append("• ")
            sample_text.append("Warning", style=Style(color=theme.palette.warning))
            
            panel = Panel(
                sample_text,
                title=f"[bold]{theme_name}[/bold]",
                box=theme.get_box_style(),
                border_style=theme.get_border_style(),
                padding=(0, 1)
            )
            
            self.console.print(panel)
        
        self.console.print()
        
        # Prompt for selection
        selected = Prompt.ask(
            "[cyan]Select theme[/cyan]",
            choices=theme_names,
            default="CRT_Cyan"
        )
        
        logger.info(f"User selected theme: {selected}")
        return selected
    
    def _select_banner_mode(self) -> tuple[str, Optional[str], list[str]]:
        """Banner mode selection step with descriptions and previews.
        
        Presents options: random, fixed, category with explanations.
        Shows banner preview for fixed mode selection.
        Allows category filtering for category mode.
        
        Returns:
            Tuple of (mode, selected_banner, selected_categories)
        """
        self.console.clear()
        
        # Show step indicator
        self.console.print(
            Panel(
                "[bold]Step 2/3: Banner Mode Selection[/bold]",
                box=box.ROUNDED,
                border_style="cyan"
            )
        )
        self.console.print()
        
        # Display mode options with descriptions
        mode_descriptions = {
            "random": "Show a different banner each time you launch peepBeefy",
            "fixed": "Always show the same banner (you'll choose which one)",
            "category": "Show random banners from specific categories"
        }
        
        for mode, description in mode_descriptions.items():
            self.console.print(f"[bold cyan]{mode}[/bold cyan]: {description}")
        
        self.console.print()
        
        # Prompt for mode selection
        mode = Prompt.ask(
            "[cyan]Select banner mode[/cyan]",
            choices=["random", "fixed", "category"],
            default="random"
        )
        
        selected_banner = None
        selected_categories = ["1ST_BEEFS"]  # Default category
        
        # Handle fixed mode - show banner preview and selection
        if mode == "fixed":
            selected_banner = self._select_fixed_banner()
        
        # Handle category mode - allow category filtering
        elif mode == "category":
            selected_categories = self._select_categories()
        
        logger.info(f"User selected banner mode: {mode}, banner: {selected_banner}, categories: {selected_categories}")
        return (mode, selected_banner, selected_categories)
    
    def _select_fixed_banner(self) -> str:
        """Show banner preview and allow user to select a fixed banner.
        
        Returns:
            Selected banner ID in format "CATEGORY:NAME"
        """
        self.console.print()
        self.console.print("[dim]Loading banners for preview...[/dim]")
        
        # Load banner database
        banner_db = BannerDatabase(self._assets_dir)
        banners_dict = banner_db.load_banners()
        
        if not banners_dict:
            self.console.print("[yellow]No banners available, using default[/yellow]")
            return "1ST_BEEFS:BIGBEEF"
        
        # Get first banner from first category as default
        first_category = list(banners_dict.keys())[0]
        first_banner = banners_dict[first_category][0]
        default_id = f"{first_banner.metadata.category}:{first_banner.metadata.name}"
        
        # Show a few banner options (limit to 3 for brevity)
        self.console.print()
        self.console.print("[bold]Available banners (showing first 3):[/bold]")
        
        count = 0
        for category, banners in banners_dict.items():
            for banner in banners:
                if count >= 3:
                    break
                
                banner_id = f"{banner.metadata.category}:{banner.metadata.name}"
                self.console.print(f"  [cyan]{banner_id}[/cyan] - {banner.metadata.description}")
                count += 1
            
            if count >= 3:
                break
        
        self.console.print()
        self.console.print(f"[dim]Tip: You can enter any banner ID in format CATEGORY:NAME[/dim]")
        self.console.print()
        
        # Prompt for banner selection
        banner_id = Prompt.ask(
            "[cyan]Enter banner ID[/cyan]",
            default=default_id
        )
        
        return banner_id
    
    def _select_categories(self) -> list[str]:
        """Allow user to select which categories to include.
        
        Returns:
            List of selected category names
        """
        self.console.print()
        
        # Load banner database to get available categories
        banner_db = BannerDatabase(self._assets_dir)
        categories = banner_db.list_categories()
        
        if not categories:
            self.console.print("[yellow]No categories available, using default[/yellow]")
            return ["1ST_BEEFS"]
        
        # Show available categories
        self.console.print("[bold]Available categories:[/bold]")
        for cat in categories:
            self.console.print(f"  [cyan]{cat}[/cyan]")
        
        self.console.print()
        self.console.print("[dim]Enter categories separated by commas (e.g., 1ST_BEEFS,ALT)[/dim]")
        self.console.print()
        
        # Prompt for category selection
        default_cat = categories[0] if categories else "1ST_BEEFS"
        categories_input = Prompt.ask(
            "[cyan]Select categories[/cyan]",
            default=default_cat
        )
        
        # Parse comma-separated categories
        selected = [cat.strip() for cat in categories_input.split(",")]
        
        # Validate that selected categories exist
        valid_selected = [cat for cat in selected if cat in categories]
        
        if not valid_selected:
            self.console.print(f"[yellow]Invalid categories, using default: {default_cat}[/yellow]")
            return [default_cat]
        
        return valid_selected
    
    def _select_animation_preferences(self) -> tuple[bool, str]:
        """Animation preferences step with intensity selection.
        
        Asks if user wants animations enabled.
        If enabled, asks for intensity level (subtle, normal, intense).
        Shows brief description for each intensity level.
        
        Returns:
            Tuple of (animation_enabled, animation_intensity)
        """
        self.console.clear()
        
        # Show step indicator
        self.console.print(
            Panel(
                "[bold]Step 3/3: Animation Preferences[/bold]",
                box=box.ROUNDED,
                border_style="cyan"
            )
        )
        self.console.print()
        
        # Ask if user wants animations
        self.console.print("[bold]Banner Animation[/bold]")
        self.console.print("peepBeefy can display banners with a DOOM PSX-inspired fire animation effect.")
        self.console.print()
        
        animation_enabled = Confirm.ask(
            "[cyan]Enable banner animations?[/cyan]",
            default=True
        )
        
        animation_intensity = "normal"  # Default
        
        # If animations enabled, ask for intensity level
        if animation_enabled:
            self.console.print()
            self.console.print("[bold]Animation Intensity[/bold]")
            
            # Display intensity options with descriptions
            intensity_descriptions = {
                "subtle": "Gentle flickering, minimal distraction",
                "normal": "Balanced animation, recommended for most users",
                "intense": "Maximum flicker and fire effects"
            }
            
            for intensity, description in intensity_descriptions.items():
                self.console.print(f"[bold cyan]{intensity}[/bold cyan]: {description}")
            
            self.console.print()
            
            # Prompt for intensity selection
            animation_intensity = Prompt.ask(
                "[cyan]Select animation intensity[/cyan]",
                choices=["subtle", "normal", "intense"],
                default="normal"
            )
        
        logger.info(f"User selected animation: enabled={animation_enabled}, intensity={animation_intensity}")
        return (animation_enabled, animation_intensity)
