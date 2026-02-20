#!/usr/bin/env python3
"""
peepBeefy — Installation Script (Rich Edition)

First-time setup for the peepBeefy CLI application.
Designed for Windows Terminal / PowerShell.

Run via:   install.bat          (recommended — handles uv bootstrap)
    or:    uv run --with rich install.py

═══════════════════════════════════════════════════════════════════════
 DESIGN SYSTEM:  "CRT Retro Terminal"

 TARGET AUDIENCE:  PC Gamers
 AESTHETIC:        Purposeful retro — not nostalgic noise.
                   Clean structure, tight color discipline,
                   rhythmic pacing. Every visual choice earned.

 PALETTE:
   Cyan  #00d7d7   — structural (borders, dividers, identity)
   Lite  #5fffff   — highlights, active elements, commands
   Green #00ff87   — success states
   Red   #ff005f   — error states
   Amber #ffd700   — dev/advanced, warnings
   Dim   #6c6c6c   — secondary text, descriptions

 TYPOGRAPHY HIERARCHY:
   1. ASCII banner       bold cyan-lite
   2. Panel titles       bold cyan-lite
   3. Step labels        bold white
   4. Status markers     [ok] [!!] [>>] [..] — colored brackets
   5. Commands           bold cyan-lite (user) / amber (dev)
   6. Descriptions       dim gray

 BOX STYLE:  DOUBLE (══) for primary panels — evokes CRT-era borders
 SPACING:    Rhythmic. 0.2s between steps. Deliberate, not decorative.
═══════════════════════════════════════════════════════════════════════
"""

import random
import subprocess
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.style import Style
from rich.rule import Rule
from rich import box


# ═══════════════════════════════════════════════════════════════
#  DESIGN TOKENS
#  No color literals outside this block. Ever.
# ═══════════════════════════════════════════════════════════════

C      = "#00d7d7"       # cyan — primary / structural
CL     = "#5fffff"       # cyan lite — highlights
G      = "#00ff87"       # green — pass
R      = "#ff005f"       # red — fail
A      = "#ffd700"       # amber — dev / warning
D      = "#6c6c6c"       # dim — secondary

PW     = 72              # panel width — fits 80-col terminals with margin
PACE   = 0.20            # inter-step rhythm (seconds)

console = Console()
SCRIPT_DIR = Path(__file__).parent.resolve()


# ─── Status Markers ───────────────────────────────────────────
#
#  [ok]  green   — step passed
#  [!!]  red     — step failed
#  [>>]  cyan    — step starting
#  [..]  dim     — informational note
#
#  These are the HUD of the installer. Consistent, scannable,
#  instantly readable. Gamers process these in milliseconds.
# ──────────────────────────────────────────────────────────────

def s_ok(m):
    console.print(f"   [bold {G}]\\[ok][/]  {m}")

def s_fail(m):
    console.print(f"   [bold {R}]\\[!!][/]  {m}")

def s_step(m):
    console.print(f"   [bold {C}]\\[>>][/]  [bold]{m}[/]")

def s_info(m):
    console.print(f"   [{D}]\\[..][/]  [{D}]{m}[/]")

def gap():
    console.print()


# ─── Step Runner ──────────────────────────────────────────────
#
#  Every installation step follows the same visual contract:
#    1.  [>>]  label appears
#    2.  spinner animates while work happens
#    3.  [ok] or [!!] replaces spinner
#    4.  brief pause (PACE) before next step
#
#  The spinner is "dots" — minimal, geometric, retro-friendly.
#  Not "aesthetic" or "bouncingBall". Those are decorative.
#  "dots" is structural. It says "working" without distraction.
# ──────────────────────────────────────────────────────────────

def run_step(label: str, action, note: str = None) -> bool:
    """
    Execute an installation step with visual feedback.

    Parameters
    ----------
    label : str
        What we're doing ("Checking for uv package manager")
    action : callable
        Returns (success: bool, message: str)
    note : str, optional
        Secondary info line shown before execution

    Returns
    -------
    bool
        Whether the step succeeded.
    """
    s_step(label)
    if note:
        s_info(note)

    with console.status(
        f"   [{D}]     ...[/]",
        spinner="dots",
        spinner_style=C,
    ):
        success, msg = action()

    (s_ok if success else s_fail)(msg)
    time.sleep(PACE)
    return success


# ═══════════════════════════════════════════════════════════════
#  BANNER
#
#  The ASCII art is hand-crafted. Not pyfiglet. Not generated.
#  pyfiglet would be a downgrade — its fonts don't match this
#  specific letterform. PURPOSEFUL decision: keep the original.
#
#  Rendered inside a DOUBLE-border panel with tight padding.
#  The double border (══) is THE retro CRT signifier.
#  It says "this is a terminal application that knows what it is."
# ═══════════════════════════════════════════════════════════════

BANNER_ART = r"""
                                                    
                          (             (           
          (    (        ( )\    (    (  )\ )  (     
 `  )    ))\  ))\ `  )  )((_)  ))\  ))\(()/(  )\ )  
 /(/(   /((_)/((_)/(/( ((_)_  /((_)/((_)/(_))(()/(  
((_)_\ (_)) (_)) ((_)_\ | _ )(_)) (_)) (_) _| )(_)) 
| '_ \)/ -_)/ -_)| '_ \)| _ \/ -_)/ -_) |  _|| || | 
| .__/ \___|\___|| .__/ |___/\___|\___| |_|   \_, | 
|_|              |_|                          |__/ 
"""


def show_banner():
    """Render the peepBeefy banner and installer preamble."""
    console.clear()
    gap()

    # ── Main banner panel ──
    art = Text(BANNER_ART, style=f"bold {CL}")
    banner = Panel(
        Align.center(art),
        title=f"[bold {CL}]═══ peepBeefy ═══[/]",
        subtitle=f"[{D}]v0.0.4[/]",
        border_style=C,
        box=box.DOUBLE,
        padding=(0, 2),
        width=PW,
    )
    console.print(Align.center(banner))
    gap()

    # ── Tagline ──
    console.print(Align.center(Text.assemble(
        ("Find and display heavy running processes  ", Style(color=D)),
        ("gamer-friendly", Style(color=C, bold=True)),
    )))
    gap()

    # ── Divider ──
    console.print(Align.center(Rule(style=C, characters="─")))
    gap()

    # ── Installer identity ──
    console.print(Align.center(Text.assemble(
        ("INSTALLER", Style(color=CL, bold=True)),
        ("  ", Style()),
        ("First-time setup", Style(color=D)),
    )))
    gap()
    console.print(Align.center(
        Text("This script prepares your system to run peepBeefy.", style=D)
    ))
    console.print(Align.center(
        Text("After setup, you will never need to run this file again.", style=D)
    ))
    gap()
    console.print(Align.center(Rule(style=C, characters="─")))
    gap()


# ═══════════════════════════════════════════════════════════════
#  INSTALLATION ACTIONS
#
#  Each returns (success: bool, message: str).
#  No visual logic here — that's the runner's job.
#  Separation of concerns: actions do work, runner does display.
# ═══════════════════════════════════════════════════════════════

def check_uv() -> tuple[bool, str]:
    """Step 1: Verify uv package manager is installed."""
    try:
        r = subprocess.run(
            ["uv", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            ver = r.stdout.strip()
            return True, f"Found [{G}]{ver}[/]"
        return False, "uv returned an error"
    except FileNotFoundError:
        return False, f"[bold {R}]uv not found[/]"
    except subprocess.TimeoutExpired:
        return False, "uv timed out"
    except Exception as e:
        return False, str(e)


def check_python() -> tuple[bool, str]:
    """Step 2: Ensure Python 3.11+ is available via uv."""
    try:
        r = subprocess.run(
            ["uv", "python", "find", "3.11"],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode == 0:
            return True, "Python 3.11 available"

        # Not found locally — install through uv
        s_info("Python 3.11 not found locally — installing via uv...")
        inst = subprocess.run(
            ["uv", "python", "install", "3.11"],
            capture_output=True, text=True, timeout=120,
        )
        if inst.returncode == 0:
            return True, f"Python 3.11 [{G}]installed[/]"
        return False, f"[bold {R}]Failed to install Python 3.11[/]"
    except subprocess.TimeoutExpired:
        return False, "Python check timed out"
    except Exception as e:
        return False, str(e)


def sync_deps() -> tuple[bool, str]:
    """Step 3: Sync project dependencies via uv."""
    try:
        r = subprocess.run(
            ["uv", "sync", "--quiet"],
            capture_output=True, text=True,
            cwd=str(SCRIPT_DIR),
            timeout=120,
        )
        if r.returncode == 0:
            return True, "All dependencies installed"
        stderr = r.stderr.strip()
        short = stderr[:80] if stderr else "Unknown error"
        return False, f"[bold {R}]Dependency sync failed[/] [{D}]({short})[/]"
    except subprocess.TimeoutExpired:
        return False, "Dependency sync timed out"
    except Exception as e:
        return False, str(e)


def verify_app() -> tuple[bool, str]:
    """Step 4: Smoke-test the application."""
    try:
        r = subprocess.run(
            ["uv", "run", str(SCRIPT_DIR / "src" / "main.py"), "--help"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
        if r.returncode == 0:
            return True, f"peepBeefy is [{G}]ready[/]"
        return False, f"[bold {R}]Application failed to start[/]"
    except subprocess.TimeoutExpired:
        return False, "Verification timed out"
    except Exception as e:
        return False, str(e)


def setup_path() -> tuple[bool, str]:
    """Step 5: Add project directory to user PATH so 'beefy' works globally."""
    import os

    project_dir = str(SCRIPT_DIR)

    # Check if already on PATH (case-insensitive on Windows)
    current_path = os.environ.get("PATH", "")
    path_dirs = [p.strip().rstrip("\\").lower() for p in current_path.split(";") if p.strip()]
    if project_dir.rstrip("\\").lower() in path_dirs:
        return True, f"[{G}]beefy[/] already on PATH"

    # Read the current USER path (not system) from registry via PowerShell
    try:
        r = subprocess.run(
            [
                "powershell", "-noprofile", "-command",
                '[Environment]::GetEnvironmentVariable("Path", "User")',
            ],
            capture_output=True, text=True, timeout=10,
        )
        user_path = r.stdout.strip() if r.returncode == 0 else ""

        # Check if already in user PATH specifically
        user_dirs = [p.strip().rstrip("\\").lower() for p in user_path.split(";") if p.strip()]
        if project_dir.rstrip("\\").lower() in user_dirs:
            return True, f"[{G}]beefy[/] already on PATH"

        # Append project directory to user PATH
        sep = ";" if user_path and not user_path.endswith(";") else ""
        new_path = f"{user_path}{sep}{project_dir}"

        r = subprocess.run(
            [
                "powershell", "-noprofile", "-command",
                f'[Environment]::SetEnvironmentVariable("Path", "{new_path}", "User")',
            ],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0:
            return True, f"[{G}]beefy[/] added to PATH"
        return False, f"[bold {R}]Failed to update PATH[/]"
    except subprocess.TimeoutExpired:
        return False, "PATH update timed out"
    except Exception as e:
        return False, str(e)


# ═══════════════════════════════════════════════════════════════
#  UV-MISSING GUIDE
#
#  This only shows if uv isn't installed. It's the ONE failure
#  state we design a full panel for, because it's the most
#  likely first-run blocker and has a clear fix.
# ═══════════════════════════════════════════════════════════════

def show_uv_guide():
    """Display installation instructions for uv."""
    gap()
    body = Text.assemble(
        ("uv is required to manage Python and dependencies.\n\n", Style(color=D)),
        ("Install uv:\n", Style(bold=True)),
        ('  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"',
         Style(color=A, bold=True)),
        ("\n\n", Style()),
        ("Then ", Style(color=D)),
        ("close and reopen your terminal", Style(bold=True)),
        (" and run this again.", Style(color=D)),
    )
    panel = Panel(
        body,
        title=f"[bold {R}]uv Required[/]",
        border_style=R,
        box=box.DOUBLE,
        padding=(1, 3),
        width=PW,
    )
    console.print(Align.center(panel))
    gap()


# ═══════════════════════════════════════════════════════════════
#  SUCCESS SCREEN
#
#  This is the payoff. The gamer just "completed installation."
#  Make it feel like a mission-complete screen:
#    ✓  SETUP COMPLETE   (big, green, unmistakable)
#    then a clean command reference panel
#
#  Commands are split into two tiers:
#    USER  (cyan-lite)  — what 95% of people need
#    DEV   (amber)      — power-user / developer tools
#
#  The color split communicates hierarchy WITHOUT headers.
#  Gamers parse this instantly: bright = main, gold = advanced.
# ═══════════════════════════════════════════════════════════════

def show_success(needs_restart: bool = False):
    """Render the post-install success screen with usage reference."""
    gap()
    console.print(Align.center(Rule(style=C, characters="─")))
    gap()

    # ── Victory line ──
    console.print(Align.center(Text("SETUP COMPLETE", style=f"bold {G}")))
    gap()

    if needs_restart:
        console.print(Align.center(Text.assemble(
            ("Close and reopen your terminal", Style(bold=True)),
            (" for the ", Style(color=D)),
            ("beefy", Style(color=CL, bold=True)),
            (" command to become available.", Style(color=D)),
        )))
        gap()

    # ── Command reference ──
    lines = Text()
    lines.append("How to use peepBeefy:\n\n", style=Style(bold=True))

    user_cmds = [
        ("beefy",             "Interactive mode (recommended)"),
        ("beefy peep all",    "Quick scan from the command line"),
        ("beefy peep cpu",    "Find CPU hogs"),
        ("beefy peep watch",  "Live scoreboard"),
    ]
    for cmd, desc in user_cmds:
        lines.append(f"  {cmd:<22}", style=Style(color=CL, bold=True))
        lines.append(f"{desc}\n", style=Style(color=D))

    lines.append("\n", style=Style())
    lines.append("Developer spec:\n\n", style=Style(color=D))

    dev_cmds = [
        ("beefy dev dump",     "Full JSON process dump"),
        ("beefy dev info PID", "Deep process inspection"),
        ("beefy dev top beef", "Developer top-N view"),
    ]
    for cmd, desc in dev_cmds:
        lines.append(f"  {cmd:<22}", style=Style(color=A))
        lines.append(f"{desc}\n", style=Style(color=D))

    panel = Panel(
        lines,
        border_style=C,
        box=box.DOUBLE,
        padding=(1, 3),
        width=PW,
    )
    console.print(Align.center(panel))
    gap()

    console.print(Align.center(
        Text("You can close this window. peepBeefy is installed.", style=D)
    ))
    gap()


# ═══════════════════════════════════════════════════════════════
#  MAIN
#
#  Four steps. Linear. No branching. No menus.
#  If any step fails, we stop, explain, and exit.
#  Gamers respect software that fails fast and explains why.
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    show_banner()

    # ── Step 1: uv ──
    if not run_step("Checking for uv package manager", check_uv):
        show_uv_guide()
        input("   Press Enter to exit...")
        return 1

    # ── Step 2: Python ──
    gap()
    if not run_step("Checking Python 3.11+", check_python):
        input("\n   Press Enter to exit...")
        return 1

    # ── Step 3: Dependencies ──
    gap()
    if not run_step("Installing dependencies", sync_deps, note="psutil, rich, typer"):
        s_info("Try running:  uv sync  (from the project directory)")
        input("\n   Press Enter to exit...")
        return 1

    # ── Step 4: Verify ──
    gap()
    if not run_step("Verifying peepBeefy", verify_app):
        input("\n   Press Enter to exit...")
        return 1

    # ── Step 5: PATH ──
    gap()
    path_ok = run_step("Adding beefy to PATH", setup_path)
    needs_restart = path_ok  # PATH was modified, terminal restart needed

    # ── Done ──
    show_success(needs_restart=needs_restart)
    input("   Press Enter to exit...")
    return 0


if __name__ == "__main__":
    sys.exit(main())
