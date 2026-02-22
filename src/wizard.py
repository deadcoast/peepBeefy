"""
First-run setup wizard for peepBeefy.

This module provides an interactive configuration wizard that guides users
through initial setup, including theme selection, banner mode configuration,
and animation preferences.
"""

import logging
from typing import Optional
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text
from rich import box

from config import AppConfig, BannerConfig
from themes import ThemeRegistry, Theme
from banner import BannerDatabase

logger = logging.getLogger(__name__)


def show_theme_preview(theme_name: str, console: Optional[Console] = None) -> None:
    """Display a visual preview of a theme by name.
    
    This is a standalone function that can be used outside the wizard
    for showing theme previews in the settings menu.
    
    Args:
        theme_name: Name of the theme to preview
        console: Optional Rich Console instance (creates new one if not provided)
    """
    if console is None:
        console = Console()
    
    theme = ThemeRegistry.get_theme(theme_name)
    
    # Create sample content with theme colors
    preview_text = Text()
    preview_text.append(theme.name.replace("_", " "), style=f"bold {theme.palette.primary}")
    preview_text.append("\n\n", style="white")
    
    # Show color samples
    preview_text.append("Primary: ", style="dim white")
    preview_text.append("████ ", style=theme.palette.primary)
    preview_text.append("Highlight: ", style="dim white")
    preview_text.append("████ ", style=theme.palette.highlight)
    preview_text.append("\n")
    
    preview_text.append("Success: ", style="dim white")
    preview_text.append("████ ", style=theme.palette.success)
    preview_text.append("Error: ", style="dim white")
    preview_text.append("████ ", style=theme.palette.error)
    
    # Create panel with theme styling
    panel = Panel(
        preview_text,
        border_style=theme.palette.primary,
        box=box.DOUBLE,
        padding=(0, 1)
    )
    
    console.print(panel)


class SetupWizard:
    """Interactive first-run setup wizard for peepBeefy configuration.
    
    The wizard guides users through:
    1. Theme selection with visual previews
    2. Banner mode configuration (random, fixed, category)
    3. Animation preferences (enabled, intensity)
    
    Attributes:
        console: Rich Console instance for rendering
        _banner_db: BannerDatabase instance for banner previews
    """
    
    def __init__(self, console: Console, banner_db: Optional[BannerDatabase] = None):
        """Initialize the setup wizard.
        
        Args:
            console: Rich Console instance for rendering
            banner_db: Optional BannerDatabase instance for banner previews
        """
        self.console = console
        self._banner_db = banner_db
        
    def run(self) -> AppConfig:
        """Run the complete setup wizard flow.
        
        Returns:
            AppConfig object with user's selected preferences
        """
        logger.info("Starting first-run setup wizard")
        
        try:
            # Display welcome screen
            self._show_welcome()
            
            # Step 1: Theme selection
            theme_variant = self._select_theme()
            
            # Step 2: Banner mode selection
            banner_config = self._select_banner_mode()
            
            # Step 3: Animation preferences
            animation_config = self._select_animation_preferences()
            
            # Merge animation config into banner config
            banner_config.animation_enabled = animation_config["enabled"]
            banner_config.animation_intensity = animation_config["intensity"]
            banner_config.animation_duration = animation_config.get("duration", 3.0)
            banner_config.animation_fps = animation_config.get("fps", 8)
            
            # Build final configuration
            config = AppConfig(
                version=1,
                first_run_complete=True,
                theme_variant=theme_variant,
                banner=banner_config,
                user_preferences={}
            )
            
            # Show completion message
            self._show_completion()
            
            logger.info("Setup wizard completed successfully")
            return config
            
        except KeyboardInterrupt:
            # User skipped wizard - return default config
            logger.info("Setup wizard skipped by user, using defaults")
            self.console.print()
            self.console.print("[yellow]Setup skipped. Using default configuration.[/]")
            self.console.print()
            
            return AppConfig(
                version=1,
                first_run_complete=True,
                theme_variant="CRT_Cyan",
                banner=BannerConfig(),
                user_preferences={}
            )
    
    def _show_welcome(self) -> None:
        """Display welcome screen with setup wizard introduction."""
        welcome_text = Text()
        welcome_text.append("Welcome to ", style="white")
        welcome_text.append("peepBeefy", style="bold cyan")
        welcome_text.append("!\n\n", style="white")
        welcome_text.append(
            "This wizard will help you configure your peepBeefy experience.\n"
            "You can change these settings later in the Settings menu.\n\n"
            "Press Enter to continue or Ctrl+C to skip and use defaults.",
            style="dim white"
        )
        
        panel = Panel(
            welcome_text,
            title="[bold cyan]Setup Wizard[/]",
            border_style="cyan",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
        
        # Wait for user to press Enter
        try:
            input()
        except KeyboardInterrupt:
            logger.info("Setup wizard skipped by user")
            raise
    
    def _show_completion(self) -> None:
        """Display completion message after wizard finishes."""
        completion_text = Text()
        completion_text.append("Setup Complete!", style="bold green")
        completion_text.append("\n\n", style="white")
        completion_text.append(
            "Your preferences have been saved.\n"
            "You can change these settings anytime using the Settings menu.",
            style="white"
        )
        
        panel = Panel(
            completion_text,
            title="[bold green]✓ Configuration Saved[/]",
            border_style="green",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def _select_theme(self) -> str:
        """Theme selection step with visual previews.

        Displays all available themes with sample panels showing their colors.
        Users can select a theme or skip to use the default (CRT_Cyan).

        Returns:
            Selected theme name
        """
        self.console.print()
        self.console.print("[bold cyan]Step 1/3: Theme Selection[/]")
        self.console.print("[dim]Choose your color theme. Each theme changes the colors used throughout peepBeefy.[/]")
        self.console.print()

        # Get all available themes
        theme_names = ThemeRegistry.list_themes()

        # Display preview for each theme
        for i, theme_name in enumerate(theme_names, 1):
            theme = ThemeRegistry.get_theme(theme_name)
            self._show_theme_preview(theme, i)

        self.console.print()

        # Prompt for selection
        choices = [str(i) for i in range(1, len(theme_names) + 1)]
        choice = Prompt.ask(
            "[cyan]Select theme[/]",
            choices=choices,
            default="1",
            show_choices=True
        )

        selected_theme = theme_names[int(choice) - 1]
        logger.info(f"User selected theme: {selected_theme}")

        return selected_theme

    def _show_theme_preview(self, theme: Theme, number: int) -> None:
        """Display a visual preview of a theme.

        Args:
            theme: Theme to preview
            number: Theme number for selection
        """
        # Create sample content with theme colors
        preview_text = Text()
        preview_text.append(f"{number}. ", style="white bold")
        preview_text.append(theme.name.replace("_", " "), style=f"bold {theme.palette.primary}")
        preview_text.append("\n\n", style="white")

        # Show color samples
        preview_text.append("Primary: ", style="dim white")
        preview_text.append("████ ", style=theme.palette.primary)
        preview_text.append("Highlight: ", style="dim white")
        preview_text.append("████ ", style=theme.palette.highlight)
        preview_text.append("\n")

        preview_text.append("Success: ", style="dim white")
        preview_text.append("████ ", style=theme.palette.success)
        preview_text.append("Error: ", style="dim white")
        preview_text.append("████ ", style=theme.palette.error)

        # Create panel with theme styling
        panel = Panel(
            preview_text,
            border_style=theme.palette.primary,
            box=box.DOUBLE,
            padding=(0, 1)
        )

        self.console.print(panel)


    
    def _select_banner_mode(self) -> BannerConfig:
        """Banner mode selection step with mode explanations.
        
        Presents three banner modes:
        - random: Different banner each launch
        - fixed: Same banner every time
        - category: Random from selected categories
        
        Returns:
            BannerConfig with selected mode and preferences
        """
        self.console.print()
        self.console.print("[bold cyan]Step 2/3: Banner Mode Selection[/]")
        self.console.print("[dim]Choose how peepBeefy selects ASCII art banners on startup.[/]")
        self.console.print()
        
        # Display mode options
        self.console.print("[white bold]1.[/] [cyan]Random[/] - Show a different banner each time")
        self.console.print("   [dim]Keeps things fresh with variety from all categories[/]")
        self.console.print()
        
        self.console.print("[white bold]2.[/] [cyan]Fixed[/] - Always show the same banner")
        self.console.print("   [dim]Pick your favorite and stick with it[/]")
        self.console.print()
        
        self.console.print("[white bold]3.[/] [cyan]Category[/] - Random from selected categories")
        self.console.print("   [dim]Filter by style (e.g., only minimal or cursive banners)[/]")
        self.console.print()
        
        # Prompt for mode selection
        mode_choice = Prompt.ask(
            "[cyan]Select banner mode[/]",
            choices=["1", "2", "3"],
            default="1"
        )
        
        # Map choice to mode
        mode_map = {"1": "random", "2": "fixed", "3": "category"}
        selected_mode = mode_map[mode_choice]
        
        # Create banner config based on mode
        banner_config = BannerConfig(mode=selected_mode)
        
        # Handle mode-specific configuration
        if selected_mode == "fixed":
            banner_config = self._select_fixed_banner(banner_config)
        elif selected_mode == "category":
            banner_config = self._select_categories(banner_config)
        
        logger.info(f"User selected banner mode: {selected_mode}")
        return banner_config
    
    def _select_fixed_banner(self, config: BannerConfig) -> BannerConfig:
        """Allow user to select a specific banner for fixed mode.
        
        Args:
            config: BannerConfig to update
            
        Returns:
            Updated BannerConfig with selected banner
        """
        self.console.print()
        self.console.print("[dim]Loading available banners...[/]")
        
        # Load banners if database available
        if self._banner_db is None:
            self.console.print("[yellow]Banner database not available. Using default banner.[/]")
            return config
        
        try:
            banners_by_category = self._banner_db.load_banners()
            
            # Flatten to list of (category, name) tuples
            banner_list = []
            for category, banners in banners_by_category.items():
                for banner in banners:
                    banner_list.append((category, banner.metadata.name))
            
            if not banner_list:
                self.console.print("[yellow]No banners found. Using default.[/]")
                return config
            
            # Display banner options (first 10 for simplicity)
            self.console.print()
            self.console.print("[cyan]Available banners:[/]")
            display_count = min(10, len(banner_list))
            
            for i, (category, name) in enumerate(banner_list[:display_count], 1):
                self.console.print(f"[white bold]{i}.[/] {category}:{name}")
            
            if len(banner_list) > display_count:
                self.console.print(f"[dim]... and {len(banner_list) - display_count} more[/]")
            
            self.console.print()
            
            # Prompt for selection
            choices = [str(i) for i in range(1, display_count + 1)]
            choice = Prompt.ask(
                "[cyan]Select banner[/]",
                choices=choices + ["skip"],
                default="1"
            )
            
            if choice != "skip":
                idx = int(choice) - 1
                category, name = banner_list[idx]
                config.selected_banner = f"{category}:{name}"
                logger.info(f"User selected fixed banner: {config.selected_banner}")
            
        except Exception as e:
            logger.error(f"Error loading banners for selection: {e}")
            self.console.print(f"[yellow]Could not load banners: {e}[/]")
        
        return config
    
    def _select_categories(self, config: BannerConfig) -> BannerConfig:
        """Allow user to select banner categories for category mode.
        
        Args:
            config: BannerConfig to update
            
        Returns:
            Updated BannerConfig with selected categories
        """
        self.console.print()
        self.console.print("[dim]Loading available categories...[/]")
        
        # Load categories if database available
        if self._banner_db is None:
            self.console.print("[yellow]Banner database not available. Using default categories.[/]")
            return config
        
        try:
            categories = self._banner_db.list_categories()
            
            if not categories:
                self.console.print("[yellow]No categories found. Using defaults.[/]")
                return config
            
            # Display category options
            self.console.print()
            self.console.print("[cyan]Available categories:[/]")
            for i, category in enumerate(categories, 1):
                self.console.print(f"[white bold]{i}.[/] {category}")
            
            self.console.print()
            self.console.print("[dim]Enter category numbers separated by commas (e.g., 1,3,4)[/]")
            self.console.print("[dim]Or press Enter to use all categories[/]")
            
            # Prompt for selection
            selection = Prompt.ask(
                "[cyan]Select categories[/]",
                default="all"
            )
            
            if selection.lower() != "all":
                # Parse comma-separated numbers
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(",")]
                    selected_categories = [categories[i] for i in indices if 0 <= i < len(categories)]
                    
                    if selected_categories:
                        config.selected_categories = selected_categories
                        logger.info(f"User selected categories: {selected_categories}")
                    else:
                        self.console.print("[yellow]Invalid selection. Using all categories.[/]")
                except (ValueError, IndexError) as e:
                    self.console.print(f"[yellow]Invalid input: {e}. Using all categories.[/]")
            else:
                config.selected_categories = categories
                logger.info("User selected all categories")
            
        except Exception as e:
            logger.error(f"Error loading categories for selection: {e}")
            self.console.print(f"[yellow]Could not load categories: {e}[/]")
        
        return config
    
    def _select_animation_preferences(self) -> dict:
        """Animation preferences selection step.
        
        Asks user if they want animations enabled and, if so, what intensity level.
        Shows brief animation preview for each intensity option.
        
        Returns:
            Dictionary with animation preferences (enabled, intensity, duration, fps)
        """
        self.console.print()
        self.console.print("[bold cyan]Step 3/3: Animation Preferences[/]")
        self.console.print("[dim]Configure fire animation effects for banners.[/]")
        self.console.print()
        
        # Ask if animations should be enabled
        animation_enabled = Confirm.ask(
            "[cyan]Enable fire animations?[/]",
            default=True
        )
        
        if not animation_enabled:
            logger.info("User disabled animations")
            return {
                "enabled": False,
                "intensity": "normal",
                "duration": 3.0,
                "fps": 8
            }
        
        # Ask for intensity level
        self.console.print()
        self.console.print("[cyan]Animation Intensity:[/]")
        self.console.print()
        
        self.console.print("[white bold]1.[/] [cyan]Subtle[/] - Gentle flickering")
        self.console.print("   [dim]Less visual noise, good for focus[/]")
        self.console.print()
        
        self.console.print("[white bold]2.[/] [cyan]Normal[/] - Balanced animation")
        self.console.print("   [dim]Default setting, nice visual appeal[/]")
        self.console.print()
        
        self.console.print("[white bold]3.[/] [cyan]Intense[/] - Maximum fire effect")
        self.console.print("   [dim]Full DOOM PSX experience[/]")
        self.console.print()
        
        # Prompt for intensity selection
        intensity_choice = Prompt.ask(
            "[cyan]Select intensity[/]",
            choices=["1", "2", "3"],
            default="2"
        )
        
        # Map choice to intensity
        intensity_map = {"1": "subtle", "2": "normal", "3": "intense"}
        selected_intensity = intensity_map[intensity_choice]
        
        logger.info(f"User selected animation intensity: {selected_intensity}")
        
        return {
            "enabled": True,
            "intensity": selected_intensity,
            "duration": 3.0,
            "fps": 8
        }
