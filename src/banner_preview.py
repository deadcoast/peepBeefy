"""Banner preview system for peepBeefy.

This module provides functionality for displaying multiple banners in a grid layout
with pagination, metadata display, and adaptive layout based on terminal size.
"""

import logging
from typing import List, Optional, Tuple
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.style import Style
from rich import box

from banner import Banner, BannerDatabase
from themes import Theme

logger = logging.getLogger(__name__)


class BannerPreview:
    """Renders multiple banners in a grid layout with pagination support.
    
    Displays banners in columns (2-3 based on terminal width) with banner name,
    category, and optional metadata. Supports pagination for large collections.
    
    Attributes:
        _theme: Theme instance for styling
        _console: Rich Console instance for rendering
        _banners_per_page: Number of banners to show per page
    """
    
    def __init__(self, theme: Theme, console: Console):
        """Initialize the BannerPreview.
        
        Args:
            theme: Theme instance for color styling
            console: Rich Console instance for rendering
        """
        self._theme = theme
        self._console = console
        self._banners_per_page = self._calculate_banners_per_page()
    
    def _calculate_banners_per_page(self) -> int:
        """Calculate how many banners to show per page based on terminal size.
        
        Returns:
            Number of banners per page (10-20 based on terminal height)
        """
        term_width, term_height = self._console.size
        
        # Estimate: each banner preview takes ~10 lines (art + metadata + spacing)
        # Reserve 10 lines for header, footer, and navigation
        available_height = term_height - 10
        
        # Calculate banners per page (minimum 10, maximum 20)
        banners_per_page = max(10, min(20, available_height // 10))
        
        logger.debug(f"Terminal height: {term_height}, banners per page: {banners_per_page}")
        return banners_per_page
    
    def _get_column_count(self) -> int:
        """Determine number of columns based on terminal width.
        
        Returns:
            Number of columns (1 for narrow terminals <80, 2-3 for wider)
        """
        term_width, _ = self._console.size
        
        if term_width < 80:
            return 1
        elif term_width < 160:
            return 2
        else:
            return 3
    
    def _scale_banner(self, banner: Banner, max_width: int, max_height: int) -> List[str]:
        """Scale or truncate banner to fit within preview area.
        
        Args:
            banner: Banner to scale
            max_width: Maximum width in characters
            max_height: Maximum height in lines
        
        Returns:
            List of scaled banner lines
        """
        scaled_lines = []
        
        # Truncate height if needed
        lines_to_show = banner.lines[:max_height]
        
        # Truncate width if needed
        for line in lines_to_show:
            if len(line) > max_width:
                # Truncate and add ellipsis
                scaled_lines.append(line[:max_width-3] + "...")
            else:
                scaled_lines.append(line)
        
        # Add ellipsis line if we truncated height
        if len(banner.lines) > max_height:
            scaled_lines.append("...")
        
        return scaled_lines
    
    def _render_banner_preview(
        self,
        banner: Banner,
        max_width: int,
        max_height: int
    ) -> Panel:
        """Render a single banner preview with metadata.
        
        Args:
            banner: Banner to preview
            max_width: Maximum width for banner content
            max_height: Maximum height for banner content
        
        Returns:
            Rich Panel with banner preview and metadata
        """
        # Scale banner to fit preview area
        scaled_lines = self._scale_banner(banner, max_width, max_height)
        
        # Create content with banner art
        content = Text()
        for i, line in enumerate(scaled_lines):
            if i > 0:
                content.append("\n")
            # Apply theme primary color to banner
            content.append(line, style=Style(color=self._theme.palette.primary))
        
        # Add metadata below banner
        content.append("\n\n")
        content.append(f"Category: ", style=Style(color=self._theme.palette.dim))
        content.append(f"{banner.metadata.category}", style=Style(color=self._theme.palette.highlight))
        
        content.append("\n")
        content.append(f"Name: ", style=Style(color=self._theme.palette.dim))
        content.append(f"{banner.metadata.name}", style=Style(color=self._theme.palette.highlight))
        
        # Add description if available
        if banner.metadata.description and banner.metadata.description != banner.metadata.name:
            content.append("\n")
            content.append(f"Description: ", style=Style(color=self._theme.palette.dim))
            content.append(f"{banner.metadata.description}", style=Style(color=self._theme.palette.text))
        
        # Add author if available
        if banner.metadata.author:
            content.append("\n")
            content.append(f"Author: ", style=Style(color=self._theme.palette.dim))
            content.append(f"{banner.metadata.author}", style=Style(color=self._theme.palette.text))
        
        # Add animation compatibility indicator
        if banner.metadata.animation_compatible:
            content.append("\n")
            content.append("🔥 ", style=Style(color=self._theme.palette.warning))
            content.append("Animation compatible", style=Style(color=self._theme.palette.success))
        
        # Create panel with banner title
        title = f"{banner.metadata.category}:{banner.metadata.name}"
        panel = Panel(
            content,
            title=title,
            box=self._theme.get_box_style(),
            border_style=self._theme.get_border_style(),
            padding=(0, 1)
        )
        
        return panel
    
    def display_grid(
        self,
        banners: List[Banner],
        page: int = 1,
        filter_animated: bool = False
    ) -> None:
        """Display banners in a grid layout with pagination.
        
        Args:
            banners: List of banners to display
            page: Page number to display (1-indexed)
            filter_animated: If True, only show animation-compatible banners
        """
        try:
            # Validate inputs
            if not isinstance(banners, list):
                logger.error(f"Invalid banners type: {type(banners)}, expected list")
                self._console.print("[red]Error: Invalid banners data[/red]")
                return
            
            if not isinstance(page, int) or page < 1:
                logger.warning(f"Invalid page number: {page}, using page 1")
                page = 1
            
            if not isinstance(filter_animated, bool):
                logger.warning(f"Invalid filter_animated type: {type(filter_animated)}, using False")
                filter_animated = False
            
            # Filter by animation compatibility if requested
            if filter_animated:
                banners = [b for b in banners if b.metadata.animation_compatible]
                logger.info(f"Filtered to {len(banners)} animation-compatible banners")
            
            # Handle empty banner list
            if not banners:
                self._console.print("[yellow]No banners available to display[/yellow]")
                logger.warning("No banners to display")
                return
            
            # Calculate pagination
            total_banners = len(banners)
            total_pages = max(1, (total_banners + self._banners_per_page - 1) // self._banners_per_page)
            
            # Validate page number against total pages
            if page > total_pages:
                logger.warning(f"Page {page} exceeds total pages {total_pages}, using last page")
                page = total_pages
            
            # Get banners for current page
            start_idx = (page - 1) * self._banners_per_page
            end_idx = min(start_idx + self._banners_per_page, total_banners)
            page_banners = banners[start_idx:end_idx]
            
            # Display header
            self._console.print()
            header = Panel(
                f"[bold]Banner Preview[/bold] - Page {page}/{total_pages} ({total_banners} banners)",
                box=box.ROUNDED,
                border_style=self._theme.palette.primary
            )
            self._console.print(header)
            self._console.print()
            
            # Get column count and calculate preview dimensions
            columns = self._get_column_count()
            term_width, _ = self._console.size
            
            # Calculate max dimensions for each preview
            # Account for panel borders (4 chars) and spacing between columns (2 chars)
            column_width = (term_width - (columns * 4) - ((columns - 1) * 2)) // columns
            max_preview_width = max(20, column_width - 4)  # Reserve space for padding
            max_preview_height = 8  # Limit preview height
            
            logger.debug(f"Grid layout: {columns} columns, preview size: {max_preview_width}x{max_preview_height}")
            
            # Display banners in grid
            if columns == 1:
                # Single column layout
                for banner in page_banners:
                    try:
                        panel = self._render_banner_preview(banner, max_preview_width, max_preview_height)
                        self._console.print(panel)
                        self._console.print()
                    except Exception as e:
                        logger.error(f"Error rendering banner {banner.metadata.category}:{banner.metadata.name}: {e}")
                        # Show error panel instead
                        error_panel = Panel(
                            f"[red]Error rendering banner[/red]\n{banner.metadata.category}:{banner.metadata.name}",
                            border_style="red"
                        )
                        self._console.print(error_panel)
            else:
                # Multi-column layout using Table
                table = Table(
                    show_header=False,
                    show_edge=False,
                    padding=(0, 1),
                    box=None
                )
                
                # Add columns
                for _ in range(columns):
                    table.add_column()
                
                # Add rows
                for i in range(0, len(page_banners), columns):
                    row_banners = page_banners[i:i+columns]
                    row_panels = []
                    
                    for b in row_banners:
                        try:
                            panel = self._render_banner_preview(b, max_preview_width, max_preview_height)
                            row_panels.append(panel)
                        except Exception as e:
                            logger.error(f"Error rendering banner {b.metadata.category}:{b.metadata.name}: {e}")
                            # Add error panel
                            error_panel = Panel(
                                f"[red]Error[/red]\n{b.metadata.category}:{b.metadata.name}",
                                border_style="red"
                            )
                            row_panels.append(error_panel)
                    
                    # Pad row if needed
                    while len(row_panels) < columns:
                        row_panels.append("")
                    
                    table.add_row(*row_panels)
                
                self._console.print(table)
            
            # Display navigation footer
            self._console.print()
            nav_text = Text()
            
            if page > 1:
                nav_text.append("[←] Previous  ", style=Style(color=self._theme.palette.highlight))
            else:
                nav_text.append("[←] Previous  ", style=Style(color=self._theme.palette.dim))
            
            if page < total_pages:
                nav_text.append("[→] Next", style=Style(color=self._theme.palette.highlight))
            else:
                nav_text.append("[→] Next", style=Style(color=self._theme.palette.dim))
            
            nav_text.append(f"  |  Page {page}/{total_pages}", style=Style(color=self._theme.palette.text))
            
            footer = Panel(
                nav_text,
                box=box.ROUNDED,
                border_style=self._theme.palette.primary
            )
            self._console.print(footer)
            self._console.print()
            
        except Exception as e:
            logger.error(f"Fatal error in display_grid: {e}", exc_info=True)
            self._console.print(f"[red]Error displaying banner grid: {e}[/red]")
    
    def preview_animation(
        self,
        banner: Banner,
        duration: float = 2.0,
        fps: int = 8,
        intensity: str = "normal"
    ) -> None:
        """Show a brief animation preview for a banner.
        
        Args:
            banner: Banner to animate
            duration: Animation duration in seconds (default 2.0 for preview)
            fps: Frames per second
            intensity: Animation intensity level
        """
        try:
            # Validate inputs
            if banner is None:
                logger.error("Cannot preview animation: banner is None")
                self._console.print("[red]Error: No banner provided[/red]")
                return
            
            if not isinstance(duration, (int, float)) or duration <= 0 or duration > 10:
                logger.warning(f"Invalid duration {duration}, using default 2.0s")
                duration = 2.0
            
            if not isinstance(fps, int) or fps < 4 or fps > 30:
                logger.warning(f"Invalid FPS {fps}, using default 8")
                fps = 8
            
            valid_intensities = ["subtle", "normal", "intense"]
            if intensity not in valid_intensities:
                logger.warning(f"Invalid intensity '{intensity}', using 'normal'")
                intensity = "normal"
            
            from animation import FireAnimator
            
            self._console.print()
            self._console.print(f"[bold]Previewing animation for {banner.metadata.category}:{banner.metadata.name}[/bold]")
            self._console.print()
            
            animator = FireAnimator(intensity=intensity)
            animator.animate_banner(banner, self._console, duration=duration, fps=fps)
            
            self._console.print()
            logger.info(f"Previewed animation for {banner.metadata.category}:{banner.metadata.name}")
            
        except Exception as e:
            logger.error(f"Failed to preview animation: {e}", exc_info=True)
            self._console.print(f"[red]Failed to preview animation: {e}[/red]")
