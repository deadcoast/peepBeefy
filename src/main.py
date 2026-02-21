
"""
peepBeefy (v0.0.3 prototype)

Gamer-focused process "peeper" that surfaces what's actually clogging your system.
- Interactive, beginner-friendly (default mode)
- Rich tables with color-coded metrics
- Service mapping (helps explain "hidden" background stuff)
- Snapshot + diff (catch what started itself)

No process termination in this version (by design).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import psutil
import typer
from rich import box
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import install as rich_traceback_install

# Import banner system modules
from banner import BannerDatabase, BannerRenderer
from config import ConfigManager
from themes import ThemeRegistry
from logging_config import setup_logging

# --- Rich / Typer setup -------------------------------------------------------

rich_traceback_install(show_locals=False, suppress=[typer, psutil])

PEEP_THEME = Theme({
    "peep.accent": "#555555",                # Structural borders (dark grey)
    "peep.accent.lite": "#777777",           # Title bar decorations (lighter grey)
    "peep.brand": "bold #777777",            # Generic label branding
    "peep.brand.peep": "#CCCCCC",            # "peep" in peepBeefy
    "peep.brand.b": "bold #AB1E00",          # "B" in peepBeefy (warm ember)
    "peep.brand.eefy": "#8B1A00",            # "eefy" in peepBeefy (deep ember)
    "peep.error": "bold red",
    "peep.success": "green",
    "peep.muted": "dim",
    "peep.heading": "bold",
    "peep.metric.hot": "bold red",
    "peep.metric.warn": "yellow",
    "peep.metric.ok": "green",
    "peep.diff.added": "green",
    "peep.diff.removed": "red",
    "peep.tag": "cyan",
    "peep.service": "magenta",
    "peep.kind.windows": "dim",
    "peep.kind.service": "magenta",
    "peep.kind.app": "cyan",
})

console = Console(highlight=False, theme=PEEP_THEME)
app = typer.Typer(
    add_completion=False,
    help="peepBeefy — find and display heavy running processes (gamer-friendly).",
)

peep_app = typer.Typer(add_completion=False, help="User-friendly 'peep' commands.")
dev_app = typer.Typer(add_completion=False, help="Developer-spec commands (advanced).")
baseline_app = typer.Typer(add_completion=False, help="Baseline snapshot + diff.")
config_app = typer.Typer(add_completion=False, help="Configuration management commands.")
banner_app = typer.Typer(add_completion=False, help="Banner management commands.")
theme_app = typer.Typer(add_completion=False, help="Theme management commands.")
app.add_typer(peep_app, name="peep")
app.add_typer(dev_app, name="dev")
app.add_typer(baseline_app, name="baseline")
app.add_typer(config_app, name="config")
app.add_typer(banner_app, name="banner")
app.add_typer(theme_app, name="theme")

dev_top_app = typer.Typer(add_completion=False, help="Developer-spec 'top' commands with explicit flags.")
dev_app.add_typer(dev_top_app, name="top")



# --- Branding ----------------------------------------------------------------

BANNER = r"""
                                            
                      (          (          
         (   (      ( )\   (   ( )\ ) (     
 `  )   ))\ ))\`  ) )((_) ))\ ))(()/( )\ )  
 /(/(  /((_)((_)(/(((_)_ /((_)((_)(_)|()/(  
((_)_\(_))(_))((_)_\| _ |_))(_))(_) _|)(_)) 
| '_ \) -_) -_) '_ \) _ Y -_) -_)|  _| || | 
| .__/\___\___| .__/|___|___\___||_|  \_, | 
|_|           |_|                     |__/  
"""

APP_NAME = "peepBeefy"
VERSION = "0.0.3"

# Rich markup for the branded name — used in titles, prompts, panel headers.
BRANDED_NAME = "[peep.brand.peep]peep[/][peep.brand.b]B[/][peep.brand.eefy]eefy[/]"


# --- Data model ---------------------------------------------------------------

@dataclass
class ServiceInfo:
    name: str
    display_name: str = ""
    start_type: str = ""  # auto / manual / disabled (best-effort)
    status: str = ""      # running / stopped (best-effort)


@dataclass
class ProcRow:
    pid: int
    name: str
    exe: str
    username: str
    cpu_pct: float
    rss_bytes: int
    read_bps: float
    write_bps: float
    beef_score: float
    kind: str                 # Windows / Service / App
    tags: List[str]
    services: List[ServiceInfo]
    cmdline: str


# --- Classification rules -----------------------------------------------------

# Tag definitions — label + description (no emoji; cp1252-safe).
TAG_DEFS: Dict[str, Tuple[str, str]] = {
    "OVERLAY": ("", "Overlay / hook"),
    "RGB": ("", "RGB / vendor control"),
    "VR": ("", "VR runtime"),
    "VPN": ("", "VPN"),
    "UPDATER": ("", "Updater"),
    "LAUNCHER": ("", "Launcher"),
    "BROWSER": ("", "Browser"),
    "MONITOR": ("", "Monitoring"),
    "AUDIO": ("", "Audio stack"),
    "CAPTURE": ("", "Capture / streaming"),
}

# Real, non-placeholder patterns (best-effort).
# We match against: process name, exe path, cmdline (lowercased).
TAG_RULES: List[Tuple[str, List[str]]] = [
    # Overlays / hooks / OSD
    ("OVERLAY", [
        r"\brtss(\.exe)?\b",
        r"rivatuner",
        r"gamebarpresencewriter",
        r"xboxgamebar",
        r"\bgameoverlayui\.exe\b",         # Steam overlay helper
        r"nvsphelper",                     # NVIDIA Share helper (older)
        r"nvidia share",
        r"shadowplay",
        r"obs64\.exe|obs\.exe",
        r"discord\.exe.*--type=renderer",  # discord overlay path often uses renderer procs
    ]),
    # Capture / streaming (separate from overlay)
    ("CAPTURE", [
        r"\bobs64\.exe\b|\bobs\.exe\b",
        r"\bstreamlabs\b",
        r"\bxsplit\b",
        r"\bnvidia broadcast\b",
    ]),
    # MSI / ASUS / Corsair / etc RGB + vendor suites
    ("RGB", [
        r"msi\.center|msi center|msi_centralserver|msi\.centralserver|mystic",
        r"mystic_light|mysticlight|ledkeeper|lightkeeper",
        r"dragon center",
        r"icue|corsair\.service",
        r"razer|synapse|chroma",
        r"armoury|aura",
        r"signalrgb",
    ]),
    # VR runtime
    ("VR", [
        r"\bovrserver_x64\.exe\b|\bovrserver\.exe\b",
        r"\bovrserviceLauncher\.exe\b",
        r"oculus|meta quest|quest remote desktop",
        r"steamvr",
        r"virtualdesktop",
    ]),
    # VPN
    ("VPN", [
        r"nordvpn",
        r"expressvpn",
        r"surfshark",
        r"protonvpn",
        r"openvpn",
        r"wireguard",
    ]),
    # Updaters
    ("UPDATER", [
        r"updater",
        r"update\.exe",
        r"googleupdate",
        r"adobe.*(update|updater)",
        r"epicwebhelper.*update",
        r"steam.*(update|service)",
    ]),
    # Launchers
    ("LAUNCHER", [
        r"epicgameslauncher",
        r"battle\.net|blizzard",
        r"riotclient",
        r"steam\.exe",
        r"gog galaxy",
        r"ubisoftconnect|uplay",
    ]),
    # Browsers
    ("BROWSER", [
        r"\bchrome\.exe\b|\bmsedge\.exe\b|\bfirefox\.exe\b",
    ]),
    # Monitoring / telemetry tools
    ("MONITOR", [
        r"presentmon",
        r"capframex",
        r"hwinfo",
        r"core temp",
        r"aida64",
        r"msiafterburner",
    ]),
    # Audio stack / enhancement
    ("AUDIO", [
        r"nahimic",
        r"sonic studio",
        r"steelseries sonar",
        r"voicemeeter",
    ]),
]


# --- Utility functions --------------------------------------------------------

def _now_ts() -> float:
    return time.time()


def _windows_dir() -> str:
    return os.environ.get("WINDIR", r"C:\Windows")


def is_windows_process(exe_path: str) -> bool:
    if not exe_path:
        return False
    w = _windows_dir().lower().rstrip("\\/")
    p = exe_path.lower()
    return p.startswith(w + "\\") or p.startswith(w + "/")


def short_path(path: str, max_len: int = 54) -> str:
    if not path:
        return ""
    if len(path) <= max_len:
        return path
    # keep drive + tail
    drive = ""
    if re.match(r"^[a-zA-Z]:\\", path):
        drive = path[:3]
        rest = path[3:]
    else:
        rest = path
    tail_len = max_len - len(drive) - 5
    return f"{drive}…\\{rest[-tail_len:]}"


def bytes_to_human(n: float) -> str:
    # bytes
    if n < 1024:
        return f"{n:.0f} B"
    units = ["KB", "MB", "GB", "TB"]
    v = n
    for u in units:
        v /= 1024.0
        if v < 1024.0:
            return f"{v:.1f} {u}"
    return f"{v:.1f} PB"


def rate_to_human(bps: float) -> str:
    return f"{bytes_to_human(bps)}/s"


def color_metric(value: float, thresholds: Tuple[float, float], fmt: str = "{:.1f}") -> Text:
    """
    thresholds: (warn, hot)
    """
    warn, hot = thresholds
    if value >= hot:
        style = "peep.metric.hot"
    elif value >= warn:
        style = "peep.metric.warn"
    else:
        style = "peep.metric.ok"
    return Text(fmt.format(value), style=style)


def color_bytes(value_bytes: float, thresholds_mb_s: Tuple[float, float]) -> Text:
    mb_s = value_bytes / (1024 ** 2)
    warn, hot = thresholds_mb_s
    if mb_s >= hot:
        style = "peep.metric.hot"
    elif mb_s >= warn:
        style = "peep.metric.warn"
    else:
        style = "peep.metric.ok"
    return Text(rate_to_human(value_bytes), style=style)


def safe_str(x: Any) -> str:
    try:
        return str(x)
    except Exception:
        return ""


def _error(msg: str) -> None:
    console.print(Panel(Text(msg, style="peep.error"), border_style="red", box=box.ROUNDED))


def _success(msg: str) -> None:
    console.print(Panel(Text(msg, style="peep.success"), border_style="green", box=box.ROUNDED))


def _sampled(
    seconds: float = 1.0,
    include_windows: bool = False,
    include_services: bool = True,
) -> List[ProcRow]:
    with console.status("[peep.accent]Sampling processes\u2026[/peep.accent]", spinner="dots"):
        return collect_samples(seconds=seconds, include_windows=include_windows, include_services=include_services)


def match_tags(name: str, exe: str, cmdline: str) -> List[str]:
    hay = f"{name} {exe} {cmdline}".lower()
    tags: List[str] = []
    for tag, patterns in TAG_RULES:
        for pat in patterns:
            try:
                if re.search(pat, hay, re.IGNORECASE):
                    tags.append(tag)
                    break
            except re.error:
                # should never happen, but don't kill the app
                continue
    # Deduplicate preserving order
    seen = set()
    out: List[str] = []
    for t in tags:
        if t not in seen:
            out.append(t)
            seen.add(t)
    return out


def get_services_by_pid() -> Dict[int, List[ServiceInfo]]:
    """
    Map PID -> list of ServiceInfo (best-effort).
    Requires Windows. If not available or access denied, returns empty mapping.
    """
    mapping: Dict[int, List[ServiceInfo]] = {}
    if os.name != "nt":
        return mapping
    try:
        for s in psutil.win_service_iter():
            try:
                d = s.as_dict()
                pid = d.get("pid") or 0
                if not pid:
                    continue
                si = ServiceInfo(
                    name=safe_str(d.get("name", "")),
                    display_name=safe_str(d.get("display_name", "")),
                    start_type=safe_str(d.get("start_type", "")),
                    status=safe_str(d.get("status", "")),
                )
                mapping.setdefault(int(pid), []).append(si)
            except Exception:
                continue
    except Exception:
        return {}
    return mapping


def compute_beef_score(cpu_pct: float, rss_bytes: int, read_bps: float, write_bps: float) -> float:
    """
    Beef score: higher = more likely to cause "why is my PC chugging?"
    Tuned for gamers: disk spikes and CPU spikes matter more than RAM alone.

    - CPU: dominant
    - IO: very dominant (stutter risk)
    - RAM: moderate
    """
    mem_mb = rss_bytes / (1024 ** 2)
    io_mb_s = (read_bps + write_bps) / (1024 ** 2)
    return cpu_pct * 2.0 + io_mb_s * 8.0 + mem_mb / 250.0


def proc_kind(exe: str, username: str, pid: int, svc_map: Dict[int, List[ServiceInfo]]) -> str:
    if is_windows_process(exe):
        return "Windows"
    # Service-backed if mapped OR running under a service account.
    u = (username or "").lower()
    if pid in svc_map:
        return "Service"
    if any(x in u for x in ["nt authority\\system", "local service", "network service"]):
        return "Service"
    return "App"


def try_get(proc: psutil.Process, attr: str, default: Any = "") -> Any:
    try:
        return getattr(proc, attr)()
    except Exception:
        return default


# --- Sampling engine ----------------------------------------------------------

def collect_samples(
    seconds: float = 1.0,
    include_windows: bool = False,
    include_services: bool = True,
) -> List[ProcRow]:
    """
    Snapshot processes and sample CPU + IO deltas over `seconds`.
    """
    svc_map = get_services_by_pid() if include_services else {}
    start_io: Dict[int, Tuple[int, int]] = {}
    procs: Dict[int, Dict[str, Any]] = {}

    # Prime CPU percent readings
    for p in psutil.process_iter(attrs=["pid", "name"]):
        pid = p.info.get("pid", 0) or 0
        if not pid:
            continue
        try:
            p.cpu_percent(None)
            io0 = None
            try:
                io0 = p.io_counters()
            except Exception:
                io0 = None
            if io0:
                start_io[pid] = (int(getattr(io0, "read_bytes", 0)), int(getattr(io0, "write_bytes", 0)))
            procs[pid] = {"p": p}
        except Exception:
            continue

    time.sleep(max(0.2, float(seconds)))

    rows: List[ProcRow] = []
    for pid, meta in procs.items():
        try:
            p = psutil.Process(pid)
            name = safe_str(p.name())
            exe = safe_str(try_get(p, "exe", ""))
            if not include_windows and is_windows_process(exe):
                continue
            username = safe_str(try_get(p, "username", ""))
            cmdline_list = try_get(p, "cmdline", [])
            cmdline = " ".join(cmdline_list) if isinstance(cmdline_list, list) else safe_str(cmdline_list)

            cpu = float(p.cpu_percent(None))
            rss = int(try_get(p, "memory_info", None).rss) if try_get(p, "memory_info", None) else 0

            io1 = None
            try:
                io1 = p.io_counters()
            except Exception:
                io1 = None
            r_bps = 0.0
            w_bps = 0.0
            if io1 and pid in start_io:
                r0, w0 = start_io.get(pid, (0, 0))
                r1 = int(getattr(io1, "read_bytes", 0))
                w1 = int(getattr(io1, "write_bytes", 0))
                dt = max(0.2, float(seconds))
                r_bps = max(0.0, (r1 - r0) / dt)
                w_bps = max(0.0, (w1 - w0) / dt)

            tags = match_tags(name, exe, cmdline)
            beef = compute_beef_score(cpu, rss, r_bps, w_bps)
            kind = proc_kind(exe, username, pid, svc_map)
            services = svc_map.get(pid, [])

            rows.append(
                ProcRow(
                    pid=pid,
                    name=name,
                    exe=exe,
                    username=username,
                    cpu_pct=cpu,
                    rss_bytes=rss,
                    read_bps=r_bps,
                    write_bps=w_bps,
                    beef_score=beef,
                    kind=kind,
                    tags=tags,
                    services=services,
                    cmdline=cmdline,
                )
            )
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            continue
        except psutil.AccessDenied:
            # still include minimal data
            try:
                p = psutil.Process(pid)
                name = safe_str(p.name())
            except Exception:
                name = f"PID {pid}"
            rows.append(
                ProcRow(
                    pid=pid,
                    name=name,
                    exe="",
                    username="",
                    cpu_pct=0.0,
                    rss_bytes=0,
                    read_bps=0.0,
                    write_bps=0.0,
                    beef_score=0.0,
                    kind="Unknown",
                    tags=[],
                    services=[],
                    cmdline="",
                )
            )
        except Exception:
            continue
    return rows


# --- Rendering ----------------------------------------------------------------

def tag_badge(tags: List[str]) -> Text:
    if not tags:
        return Text("")
    parts: List[Text] = []
    for t in tags[:3]:
        icon, _desc = TAG_DEFS.get(t, ("", t))
        parts.append(Text(f"{icon}{t}", style="peep.tag"))
    out = Text(" ")
    for i, part in enumerate(parts):
        if i:
            out.append(" ")
        out.append(part)
    return out


def service_badge(services: List[ServiceInfo]) -> Text:
    if not services:
        return Text("")
    # show up to 2 display names
    names = []
    for s in services[:2]:
        dn = s.display_name or s.name
        if dn:
            names.append(dn)
    if len(services) > 2:
        names.append(f"+{len(services) - 2}")
    txt = ", ".join(names)
    return Text(txt, style="peep.service")


def kind_badge(kind: str) -> Text:
    if kind == "Windows":
        return Text("Windows", style="peep.kind.windows")
    if kind == "Service":
        return Text("Service", style="peep.kind.service")
    if kind == "App":
        return Text("App", style="peep.kind.app")
    return Text(kind, style="peep.metric.warn")


def _score_style(score: float) -> str:
    if score >= 60:
        return "peep.metric.hot"
    if score >= 25:
        return "peep.metric.warn"
    if score >= 5:
        return "peep.accent"
    return "peep.muted"


def _metric_text(label: str, value: str, style: str) -> Text:
    """Render a metric with dim label and colored value — the core visual separation."""
    t = Text()
    t.append(label, style="peep.muted")
    t.append(value, style=style)
    return t


def _build_offender(r: ProcRow, max_beef: float) -> Text:
    """Build a two-line entry for a top offender process."""
    BAR_WIDTH = 20
    fill = min(BAR_WIDTH, int((r.beef_score / max(max_beef, 1.0)) * BAR_WIDTH))
    empty = BAR_WIDTH - fill
    style = _score_style(r.beef_score)

    entry = Text()
    # Line 1: bar + score + name + tag
    entry.append("  ")
    entry.append("\u2588" * fill, style=style)
    entry.append("\u2591" * empty, style="peep.muted")
    entry.append(f"  {r.beef_score:>5.0f}", style=style)
    entry.append("    ")
    entry.append(r.name, style="bold")
    entry.append(f" ({r.pid})", style="peep.muted")
    if r.tags:
        entry.append(f"   {', '.join(r.tags[:2])}", style="peep.tag")
    elif r.services:
        svc = r.services[0].display_name or r.services[0].name
        entry.append(f"   {svc}", style="peep.service")

    # Line 2: metrics with label/value separation
    indent = " " * (BAR_WIDTH + 10)
    entry.append(f"\n{indent}")

    cpu_s = "peep.metric.hot" if r.cpu_pct >= 15 else "peep.metric.warn" if r.cpu_pct >= 5 else "peep.metric.ok"
    entry.append_text(_metric_text("CPU ", f"{r.cpu_pct:.1f}", cpu_s))
    entry.append("  |  ", style="peep.muted")

    ram_mb = r.rss_bytes / (1024 ** 2)
    ram_s = "peep.metric.hot" if ram_mb >= 2000 else "peep.metric.warn" if ram_mb >= 800 else "peep.metric.ok"
    entry.append_text(_metric_text("RAM ", f"{ram_mb:.0f}M", ram_s))
    entry.append("  |  ", style="peep.muted")

    total_io = r.read_bps + r.write_bps
    io_mb = total_io / (1024 ** 2)
    io_s = "peep.metric.hot" if io_mb >= 20 else "peep.metric.warn" if io_mb >= 2 else "peep.metric.ok"
    entry.append_text(_metric_text("IO ", rate_to_human(total_io), io_s))

    return entry


def _build_compact(r: ProcRow) -> Text:
    """Build a single dim line for an 'also running' process."""
    line = Text("  ")
    line.append(r.name, style="dim bold")
    line.append(f" ({r.pid})", style="peep.muted")
    ram_mb = r.rss_bytes / (1024 ** 2)
    line.append(f"   {ram_mb:.0f}M", style="peep.muted")
    if r.tags:
        line.append(f"   {', '.join(r.tags[:1])}", style="dim")
    elif r.kind == "Service":
        line.append("   Service", style="dim")
    return line


def build_table(rows: List[ProcRow], title: str, limit: int = 25) -> Table:
    """Compact table for watch mode (Live refresh)."""
    display_rows = rows[:limit]
    max_beef = max((r.beef_score for r in display_rows), default=1.0) if display_rows else 1.0

    table = Table(
        title=title,
        title_style="peep.heading",
        box=box.SIMPLE_HEAVY,
        show_lines=False,
        header_style="peep.heading",
        padding=(0, 1),
    )
    table.add_column("BEEF", justify="left", no_wrap=True, min_width=14)
    table.add_column("CPU%", justify="right", no_wrap=True, width=5)
    table.add_column("RAM", justify="right", no_wrap=True, width=7)
    table.add_column("IO", justify="right", no_wrap=True, width=10)
    table.add_column("Process", justify="left", no_wrap=True, max_width=30)
    table.add_column("Info", justify="left", no_wrap=True)

    for r in display_rows:
        BAR_W = 8
        fill = min(BAR_W, int((r.beef_score / max(max_beef, 1.0)) * BAR_W))
        empty = BAR_W - fill
        style = _score_style(r.beef_score)
        bar = Text()
        bar.append("\u2588" * fill, style=style)
        bar.append("\u2591" * empty, style="peep.muted")
        bar.append(f" {r.beef_score:.0f}", style=style)

        cpu_txt = color_metric(r.cpu_pct, thresholds=(5.0, 15.0), fmt="{:.1f}")
        ram_mb = r.rss_bytes / (1024 ** 2)
        ram_s = "peep.metric.ok"
        if ram_mb >= 2000:
            ram_s = "peep.metric.hot"
        elif ram_mb >= 800:
            ram_s = "peep.metric.warn"
        ram_txt = Text(f"{ram_mb:.0f}M", style=ram_s)
        total_io = r.read_bps + r.write_bps
        io_txt = color_bytes(total_io, thresholds_mb_s=(2.0, 20.0))
        proc_txt = Text()
        proc_txt.append(r.name, style="bold")
        proc_txt.append(f" ({r.pid})", style="peep.muted")
        info_parts: List[str] = []
        if r.tags:
            info_parts.append(", ".join(r.tags[:2]))
        if r.services:
            svc = r.services[0].display_name or r.services[0].name
            info_parts.append(svc)
        info_txt = Text(" | ".join(info_parts), style="peep.tag") if info_parts else Text(short_path(r.exe, max_len=30), style="peep.muted")
        table.add_row(bar, cpu_txt, ram_txt, io_txt, proc_txt, info_txt)
    return table


def render_rows(
    rows: List[ProcRow],
    sort_key: str = "beef",
    limit: int = 25,
    fat_only: bool = False,
    title: str = "",
) -> None:
    if fat_only:
        rows = [r for r in rows if (r.cpu_pct >= 3.0 or (r.read_bps + r.write_bps) >= 2 * (1024 ** 2) or (r.rss_bytes / (1024 ** 2)) >= 600)]
    if sort_key == "cpu":
        rows.sort(key=lambda r: r.cpu_pct, reverse=True)
    elif sort_key == "io":
        rows.sort(key=lambda r: (r.read_bps + r.write_bps), reverse=True)
    elif sort_key == "mem":
        rows.sort(key=lambda r: r.rss_bytes, reverse=True)
    else:
        rows.sort(key=lambda r: r.beef_score, reverse=True)

    display = rows[:limit]
    if not display:
        _error("No processes matched the filter.")
        return

    ttl = title or f"{APP_NAME} -- Top {sort_key.upper()} (sampled)"
    max_beef = max((r.beef_score for r in display), default=1.0)
    hot_count = sum(1 for r in display if r.beef_score >= 25)

    # --- Header: double-line box ---
    header = Text()
    header.append(f"  {ttl}\n", style="peep.heading")
    header.append(f"  {len(display)} processes", style="peep.muted")
    if hot_count:
        header.append("  |  ", style="peep.muted")
        header.append(f"{hot_count} heavy", style="peep.metric.warn")
    console.print()
    console.print(Panel(header, box=box.DOUBLE, border_style="peep.accent"))

    # --- Split: top offenders (featured) vs also-running (compact) ---
    TOP_N = min(5, len(display))
    top = display[:TOP_N]
    rest = display[TOP_N:]

    # --- Top Offenders panel ---
    parts: List[Text] = []
    for r in top:
        parts.append(_build_offender(r, max_beef))
    body = Text("\n\n").join(parts)
    console.print(Panel(
        body,
        title="[peep.heading]Top Offenders[/peep.heading]",
        box=box.ROUNDED,
        border_style="peep.accent",
        padding=(1, 1),
    ))

    # --- Also Running panel (compact, dim) ---
    if rest:
        compact_lines = [_build_compact(r) for r in rest]
        compact_body = Text("\n").join(compact_lines)
        console.print(Panel(
            compact_body,
            title="[peep.muted]Also Running[/peep.muted]",
            box=box.ROUNDED,
            border_style="dim",
            padding=(0, 1),
        ))

    console.print(Text("  view-only mode  |  Service = can run with no taskbar icon", style="peep.muted"))
    console.print()


# --- Baseline snapshot/diff ---------------------------------------------------

def snapshot_to_file(path: Path, include_windows: bool = False) -> Dict[str, Any]:
    rows = _sampled(seconds=0.6, include_windows=include_windows, include_services=True)
    data = {
        "_meta": {"app": APP_NAME, "version": VERSION, "created_at": _now_ts()},
        "processes": [
            {
                "pid": r.pid,
                "name": r.name,
                "exe": r.exe,
                "username": r.username,
                "kind": r.kind,
            }
            for r in rows
        ],
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def diff_from_file(path: Path, include_windows: bool = False) -> Dict[str, Any]:
    before = json.loads(path.read_text(encoding="utf-8"))
    before_set = set()
    for p in before.get("processes", []):
        before_set.add((p.get("name", ""), p.get("exe", "")))

    now_rows = _sampled(seconds=0.6, include_windows=include_windows, include_services=True)
    now_set = set((r.name, r.exe) for r in now_rows)

    new = sorted(list(now_set - before_set))
    gone = sorted(list(before_set - now_set))

    return {
        "new": [{"name": n, "exe": e} for (n, e) in new],
        "gone": [{"name": n, "exe": e} for (n, e) in gone],
        "_meta": {"baseline": str(path), "checked_at": _now_ts()},
    }


def _render_diff(d: Dict[str, Any], baseline_path: Path, new_limit: int = 50, gone_limit: int = 25) -> None:
    new = d["new"]
    gone = d["gone"]
    console.print(Rule(f"Diff vs {baseline_path.name}", style="peep.accent"))
    if new:
        t = Table(box=box.SIMPLE, show_header=True, header_style="peep.heading")
        t.add_column("", width=2)
        t.add_column("Process", style="peep.heading")
        t.add_column("Path", style="peep.muted")
        for item in new[:new_limit]:
            t.add_row(Text("+", style="peep.diff.added"), Text(item["name"], style="peep.heading"), short_path(item["exe"]))
        console.print(t)
    else:
        console.print(Panel("No new processes since baseline.", style="peep.success", box=box.ROUNDED))
    if gone:
        t = Table(box=box.SIMPLE, show_header=True, header_style="peep.heading")
        t.add_column("", width=2)
        t.add_column("Process", style="peep.heading")
        t.add_column("Path", style="peep.muted")
        for item in gone[:gone_limit]:
            t.add_row(Text("-", style="peep.diff.removed"), Text(item["name"], style="peep.heading"), short_path(item["exe"]))
        console.print(t)


# --- Interactive CLI (CLI03) --------------------------------------------------

MENU_ITEMS: List[Tuple[str, str, str]] = [
    ("[>]", "beefy peep all", "Quick Scan (recommended): CPU + Disk + RAM combined score"),
    ("[>]", "beefy peep cpu", "CPU Hog Finder: who’s stealing CPU time"),
    ("[>]", "beefy peep io", "Disk Hog Finder (stutter risk): reads/writes per second"),
    ("[>]", "beefy peep mem", "RAM Hog Finder: high memory background apps"),
    ("[>]", "beefy peep clutter", "Gamer Clutter: RGB / overlays / VR / VPN / updaters"),
    ("[>]", "beefy peep watch", "Live Watch: refresh a scoreboard every second"),
    ("[>]", "beefy baseline save", "Save a baseline snapshot (for later diff)"),
    ("[>]", "beefy baseline diff", "Compare against a baseline snapshot"),
    ("[⚙]", "settings", "Configure banner, theme, and animation preferences"),
    ("[?]", "help", "Show help"),
    ("", "quit", "Exit"),
]



def print_header() -> None:
    """Display the peepBeefy banner using the banner system.
    
    Checks for first run and launches setup wizard if needed.
    Loads configuration, initializes the banner database, selects a banner
    based on user preferences, and renders it with the configured theme.
    Supports both static and animated rendering based on configuration.
    Falls back gracefully to the hardcoded BANNER if anything fails.
    """
    console.clear()
    
    # Try to load banner system with graceful fallback
    try:
        # Check for first run and launch wizard if needed
        config_manager = ConfigManager()
        
        if config_manager.is_first_run():
            # Import wizard module
            from wizard import SetupWizard
            
            # Launch setup wizard
            assets_dir = Path(__file__).parent.parent / ".assets"
            wizard = SetupWizard(console, assets_dir)
            config = wizard.run()
            
            # Save configuration
            config_manager.save(config)
            
            # Mark first run as complete
            config_manager.mark_first_run_complete()
        else:
            # Load existing configuration
            config = config_manager.load()
        
        # Get theme
        theme = ThemeRegistry.get_theme(config.theme_variant)
        
        # Initialize banner database with assets directory
        assets_dir = Path(__file__).parent.parent / ".assets"
        banner_db = BannerDatabase(assets_dir)
        
        # Initialize banner renderer
        renderer = BannerRenderer(theme)
        
        # Select banner with terminal size adaptation
        banner = renderer.select_banner_with_adaptation(banner_db, console, config)
        
        # Check if animation is enabled in configuration
        if config.banner.animation_enabled:
            # Log animation status at INFO level
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Animation enabled: duration={config.banner.animation_duration}s, "
                       f"fps={config.banner.animation_fps}, intensity={config.banner.animation_intensity}")
            
            # Render animated banner
            renderer.render_animated(
                banner,
                console,
                duration=config.banner.animation_duration,
                fps=config.banner.animation_fps,
                intensity=config.banner.animation_intensity
            )
        else:
            # Log animation status at INFO level
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Animation disabled, rendering static banner")
            
            # Render static banner
            panel = renderer.render_static(banner, console)
            
            # Add title and subtitle
            title = Text.from_markup(f"{BRANDED_NAME}  [peep.muted]v{VERSION}[/]")
            subtitle = Text("Find and display the heavy background stuff (gamer-friendly).", style="peep.muted")
            
            # Create a new panel with the banner content but with title and subtitle
            final_panel = Panel(
                panel.renderable,
                title=title,
                subtitle=subtitle,
                box=box.HEAVY,
                border_style="peep.accent",
            )
            
            console.print(final_panel)
        
    except Exception as e:
        # Fallback to original hardcoded banner if anything fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to load banner system: {e}", exc_info=True)
        
        # Use original hardcoded banner as fallback
        title = Text.from_markup(f"{BRANDED_NAME}  [peep.muted]v{VERSION}[/]")
        subtitle = Text("Find and display the heavy background stuff (gamer-friendly).", style="peep.muted")
        panel = Panel(
            Align.left(Text(BANNER, style="peep.accent.lite")),
            title=title,
            subtitle=subtitle,
            box=box.HEAVY,
            border_style="peep.accent",
        )
        console.print(panel)


def show_settings_menu() -> None:
    """Display and handle the settings menu for configuration.
    
    Provides options to configure:
    - Banner mode and selection
    - Theme variant
    - Animation settings
    - Reconfigure (re-run setup wizard)
    """
    from src.config import ConfigManager, AppConfig, BannerConfig
    from src.themes import ThemeRegistry
    from src.banner import BannerDatabase
    from pathlib import Path
    
    config_manager = ConfigManager()
    config = config_manager.load()
    
    while True:
        # Display current configuration
        current_config_text = Text()
        current_config_text.append("Current Configuration:\n\n", style="bold white")
        current_config_text.append(f"  Theme: ", style="white")
        current_config_text.append(f"{config.theme_variant}\n", style="peep.accent")
        current_config_text.append(f"  Banner Mode: ", style="white")
        current_config_text.append(f"{config.banner.mode}\n", style="peep.accent")
        
        if config.banner.mode == "fixed" and config.banner.selected_banner:
            current_config_text.append(f"  Selected Banner: ", style="white")
            current_config_text.append(f"{config.banner.selected_banner}\n", style="peep.accent")
        elif config.banner.mode == "category":
            current_config_text.append(f"  Categories: ", style="white")
            current_config_text.append(f"{', '.join(config.banner.selected_categories)}\n", style="peep.accent")
        
        current_config_text.append(f"  Animation: ", style="white")
        anim_status = "Enabled" if config.banner.animation_enabled else "Disabled"
        current_config_text.append(f"{anim_status}\n", style="peep.accent")
        
        if config.banner.animation_enabled:
            current_config_text.append(f"  Animation Intensity: ", style="white")
            current_config_text.append(f"{config.banner.animation_intensity}\n", style="peep.accent")
            current_config_text.append(f"  Animation Duration: ", style="white")
            current_config_text.append(f"{config.banner.animation_duration}s\n", style="peep.accent")
            current_config_text.append(f"  Animation FPS: ", style="white")
            current_config_text.append(f"{config.banner.animation_fps}\n", style="peep.accent")
        
        # Settings menu options
        settings_table = Table(box=None, show_header=False, padding=(0, 1))
        settings_table.add_column("", width=3, style="peep.accent", no_wrap=True)
        settings_table.add_column("Option", style="peep.heading", no_wrap=True, min_width=22)
        settings_table.add_column("Description")
        
        settings_table.add_row("[1]", "Change Banner Mode", "Switch between random, fixed, or category mode")
        settings_table.add_row("[2]", "Change Theme", "Select a different color theme")
        settings_table.add_row("[3]", "Toggle Animation", "Enable or disable banner animation")
        settings_table.add_row("[4]", "Animation Settings", "Configure animation intensity, duration, and FPS")
        settings_table.add_row("[5]", "Reconfigure", "Re-run the setup wizard")
        settings_table.add_row("[B]", "Back", "Return to main menu")
        
        console.print(Panel(
            current_config_text,
            title="[peep.accent.lite]Settings[/]",
            box=box.ROUNDED,
            border_style="peep.accent",
            padding=(1, 2),
        ))
        
        console.print(Panel(
            settings_table,
            title="[peep.accent.lite]──[/] Options [peep.accent.lite]──[/]",
            box=box.ROUNDED,
            border_style="peep.accent",
            padding=(1, 2),
        ))
        
        choice = Prompt.ask("Select option", default="B").strip().lower()
        
        if choice in ("b", "back", ""):
            return
        
        if choice == "1":
            # Change banner mode
            console.print("\n[bold white]Banner Modes:[/]")
            console.print("  [peep.accent]random[/] - Show a different banner each time")
            console.print("  [peep.accent]fixed[/] - Always show the same banner")
            console.print("  [peep.accent]category[/] - Random from selected categories\n")
            
            mode = Prompt.ask(
                "Select mode",
                choices=["random", "fixed", "category"],
                default=config.banner.mode
            )
            config.banner.mode = mode
            
            if mode == "fixed":
                # Show available banners for selection
                assets_dir = Path(__file__).parent.parent / ".assets"
                banner_db = BannerDatabase(assets_dir)
                categories = banner_db.list_categories()
                
                console.print("\n[bold white]Available Categories:[/]")
                for i, cat in enumerate(categories, 1):
                    console.print(f"  [{i}] {cat}")
                
                cat_choice = Prompt.ask("Select category number", default="1")
                try:
                    cat_idx = int(cat_choice) - 1
                    if 0 <= cat_idx < len(categories):
                        selected_cat = categories[cat_idx]
                        # Get banners in this category
                        banners = banner_db._cache.get(selected_cat, [])
                        if banners:
                            console.print(f"\n[bold white]Banners in {selected_cat}:[/]")
                            for i, banner in enumerate(banners, 1):
                                console.print(f"  [{i}] {banner.metadata.name} - {banner.metadata.description}")
                            
                            banner_choice = Prompt.ask("Select banner number", default="1")
                            try:
                                banner_idx = int(banner_choice) - 1
                                if 0 <= banner_idx < len(banners):
                                    selected_banner = banners[banner_idx]
                                    config.banner.selected_banner = f"{selected_cat}:{selected_banner.metadata.name}"
                                    _success(f"Selected banner: {config.banner.selected_banner}")
                            except (ValueError, IndexError):
                                _error("Invalid banner selection")
                except (ValueError, IndexError):
                    _error("Invalid category selection")
            
            elif mode == "category":
                # Allow category filtering
                assets_dir = Path(__file__).parent.parent / ".assets"
                banner_db = BannerDatabase(assets_dir)
                categories = banner_db.list_categories()
                
                console.print("\n[bold white]Available Categories:[/]")
                for i, cat in enumerate(categories, 1):
                    console.print(f"  [{i}] {cat}")
                
                console.print("\n[peep.muted]Enter category numbers separated by commas (e.g., 1,2,3)[/]")
                cat_input = Prompt.ask("Select categories", default="1")
                
                try:
                    selected_indices = [int(x.strip()) - 1 for x in cat_input.split(",")]
                    selected_cats = [categories[i] for i in selected_indices if 0 <= i < len(categories)]
                    if selected_cats:
                        config.banner.selected_categories = selected_cats
                        _success(f"Selected categories: {', '.join(selected_cats)}")
                    else:
                        _error("No valid categories selected")
                except (ValueError, IndexError):
                    _error("Invalid category selection")
            
            config_manager.save(config)
            _success("Banner mode updated")
            continue
        
        elif choice == "2":
            # Change theme
            from src.wizard import show_theme_preview
            
            themes = ThemeRegistry.list_themes()
            console.print("\n[bold white]Available Themes:[/]")
            
            for i, theme_name in enumerate(themes, 1):
                console.print(f"\n[{i}] {theme_name}")
                show_theme_preview(theme_name)
            
            theme_choice = Prompt.ask(
                "Select theme number",
                choices=[str(i) for i in range(1, len(themes) + 1)],
                default="1"
            )
            
            try:
                theme_idx = int(theme_choice) - 1
                if 0 <= theme_idx < len(themes):
                    config.theme_variant = themes[theme_idx]
                    config_manager.save(config)
                    _success(f"Theme changed to: {config.theme_variant}")
                    console.print("[peep.muted]Theme will apply on next banner display[/]")
            except (ValueError, IndexError):
                _error("Invalid theme selection")
            continue
        
        elif choice == "3":
            # Toggle animation
            config.banner.animation_enabled = not config.banner.animation_enabled
            config_manager.save(config)
            status = "enabled" if config.banner.animation_enabled else "disabled"
            _success(f"Animation {status}")
            continue
        
        elif choice == "4":
            # Animation settings
            if not config.banner.animation_enabled:
                console.print("[peep.warning]Animation is currently disabled. Enable it first.[/]")
                continue
            
            console.print("\n[bold white]Animation Settings:[/]")
            
            # Intensity
            console.print("\n[peep.accent]Intensity Levels:[/]")
            console.print("  [1] subtle - Reduced flicker (50% of normal)")
            console.print("  [2] normal - Standard animation")
            console.print("  [3] intense - Increased flicker (150% of normal)")
            
            intensity_map = {"1": "subtle", "2": "normal", "3": "intense"}
            current_intensity = {"subtle": "1", "normal": "2", "intense": "3"}.get(config.banner.animation_intensity, "2")
            
            intensity_choice = Prompt.ask(
                "Select intensity",
                choices=["1", "2", "3"],
                default=current_intensity
            )
            config.banner.animation_intensity = intensity_map[intensity_choice]
            
            # Duration
            duration_str = Prompt.ask(
                "Animation duration (seconds, 0.5-10.0)",
                default=str(config.banner.animation_duration)
            )
            try:
                duration = float(duration_str)
                if 0.5 <= duration <= 10.0:
                    config.banner.animation_duration = duration
                else:
                    _error("Duration must be between 0.5 and 10.0 seconds")
            except ValueError:
                _error("Invalid duration value")
            
            # FPS
            fps_str = Prompt.ask(
                "Animation FPS (4-30)",
                default=str(config.banner.animation_fps)
            )
            try:
                fps = int(fps_str)
                if 4 <= fps <= 30:
                    config.banner.animation_fps = fps
                else:
                    _error("FPS must be between 4 and 30")
            except ValueError:
                _error("Invalid FPS value")
            
            config_manager.save(config)
            _success("Animation settings updated")
            continue
        
        elif choice == "5":
            # Reconfigure - re-run setup wizard
            from src.wizard import run_setup_wizard
            
            console.print("\n[bold white]Re-running Setup Wizard[/]")
            console.print("[peep.muted]Your current settings will be used as defaults[/]")
            
            if Confirm.ask("Continue?", default=True):
                new_config = run_setup_wizard(current_config=config)
                config_manager.save(new_config)
                config = new_config
                _success("Configuration updated")
            continue
        
        else:
            _error("Invalid option. Please select 1-5 or B.")


def print_menu() -> None:
    t = Table(box=None, show_header=False, padding=(0, 1))
    t.add_column("", width=3, style="peep.accent", no_wrap=True)
    t.add_column("Key", width=3, style="peep.brand", no_wrap=True)
    t.add_column("Command", style="peep.heading", no_wrap=True, min_width=22)
    t.add_column("Description")
    
    # Keyboard shortcuts for each menu item
    shortcuts = ["1", "2", "3", "4", "5", "6", "7", "8", "s", "h", "q"]
    
    for idx, (icon, cmd, desc) in enumerate(MENU_ITEMS):
        shortcut = shortcuts[idx] if idx < len(shortcuts) else ""
        t.add_row(icon, f"[{shortcut}]" if shortcut else "", cmd, desc)
    
    console.print(Panel(
        t,
        title=f"[peep.accent.lite]──[/] {BRANDED_NAME} [peep.accent.lite]Commands ──[/]",
        subtitle="[peep.muted]Type a command, number, or letter shortcut[/peep.muted]",
        box=box.ROUNDED,
        border_style="peep.accent",
        padding=(1, 2),
    ))


def interactive_loop() -> None:
    print_header()
    console.print(
        Panel(
            Text(
                "New user mode: you don’t need flags.\n"
                "Just type a short command like: beefy peep all\n\n"
                "Tip: Run Windows Terminal as Administrator for more details.",
                style="white",
            ),
            title="Welcome",
            title_align="left",
            box=box.SQUARE,
        )
    )

    # Defaults geared for rookies
    seconds = 1.0
    limit = 25
    include_windows = False
    include_services = True
    fat_only = True

    while True:
        print_menu()
        cmd = Prompt.ask(BRANDED_NAME, default="beefy peep all").strip().lower()
        
        # Handle keyboard shortcuts (Requirements 5.2, 5.3)
        shortcut_map = {
            "1": "peep all",
            "2": "peep cpu",
            "3": "peep io",
            "4": "peep mem",
            "5": "peep clutter",
            "6": "peep watch",
            "7": "baseline save",
            "8": "baseline diff",
            "s": "settings",
            "h": "help",
            "?": "help",
        }
        
        # Map shortcut to full command
        if cmd in shortcut_map:
            cmd = shortcut_map[cmd]
        
        # Allow users to type the same command they would type in the shell (teaches CLI-only usage).
        for prefix in ("beefy ", "peepbeefy "):
            if cmd.startswith(prefix):
                cmd = cmd[len(prefix):].lstrip()
                break


        if cmd in ("q", "quit", "exit"):
            console.print(Text("Later \U0001f44b", style="peep.heading"))
            return

        if cmd in ("help", "?"):
            console.print(
                Panel(
                    Text(
                        "Commands you can type:\n"
                        "- peep all | cpu | io | mem | clutter | watch\n"
                        "- baseline save <file>\n"
                        "- baseline diff <file>\n\n"
                        "This version does NOT end processes.\n"
                        "It helps you *see* what is hogging CPU/RAM/Disk and which ones are Services.",
                        style="white",
                    ),
                    title="Help",
                    title_align="left",
                    box=box.SQUARE,
                )
            )
            continue

        # Settings (comprehensive settings menu)
        if cmd in ("settings", "config"):
            show_settings_menu()
            continue

        # Parse baseline commands
        if cmd.startswith("baseline "):
            parts = cmd.split()
            if len(parts) >= 2 and parts[1] == "save":
                file = Prompt.ask("Baseline file name", default="baseline.json")
                path = Path(file).expanduser().resolve()
                snapshot_to_file(path, include_windows=include_windows)
                _success(f"Saved baseline to: {path}")
                continue
            if len(parts) >= 2 and parts[1] == "diff":
                file = Prompt.ask("Baseline file name", default="baseline.json")
                path = Path(file).expanduser().resolve()
                if not path.exists():
                    _error(f"Baseline not found: {path}")
                    continue
                d = diff_from_file(path, include_windows=include_windows)
                _render_diff(d, path, new_limit=30, gone_limit=15)
                continue

        # peep commands
        if cmd.startswith("peep"):
            parts = cmd.split()
            mode = parts[1] if len(parts) >= 2 else "all"

            if mode == "watch":
                watch_seconds = float(Prompt.ask("Sample seconds per refresh", default=str(seconds)))
                refresh = float(Prompt.ask("Refresh interval (seconds)", default="1.0"))
                loops = int(Prompt.ask("How many refreshes? (Ctrl+C to exit early)", default="60"))
                sort_key = "beef"
                with Live(console=console, refresh_per_second=4) as live:
                    try:
                        for i in range(loops):
                            rows = collect_samples(seconds=watch_seconds, include_windows=include_windows, include_services=include_services)
                            # fat mode inside watch is very helpful
                            if fat_only:
                                rows = [r for r in rows if (r.cpu_pct >= 3.0 or (r.read_bps + r.write_bps) >= 2 * (1024 ** 2) or (r.rss_bytes / (1024 ** 2)) >= 600)]
                            rows.sort(key=lambda r: r.beef_score, reverse=True)
                            table = build_table(rows, title=f"{APP_NAME} Watch — Top BEEF (refresh {i+1}/{loops})", limit=limit)
                            live.update(table)
                            time.sleep(max(0.2, refresh))
                    except KeyboardInterrupt:
                        pass
                continue

            # Normal peep modes
            rows = _sampled(seconds=seconds, include_windows=include_windows, include_services=include_services)

            if mode == "cpu":
                render_rows(rows, sort_key="cpu", limit=limit, fat_only=fat_only, title=f"{APP_NAME} — CPU Hog Finder")
            elif mode == "io":
                render_rows(rows, sort_key="io", limit=limit, fat_only=fat_only, title=f"{APP_NAME} — Disk Hog Finder")
            elif mode == "mem":
                render_rows(rows, sort_key="mem", limit=limit, fat_only=fat_only, title=f"{APP_NAME} — RAM Hog Finder")
            elif mode == "clutter":
                clutter = [r for r in rows if r.tags]
                # Sort by beef so the "cloggy" clutter floats
                clutter.sort(key=lambda r: r.beef_score, reverse=True)
                render_rows(clutter, sort_key="beef", limit=limit, fat_only=False, title=f"{APP_NAME} — Gamer Clutter (tagged)")
            else:
                render_rows(rows, sort_key="beef", limit=limit, fat_only=fat_only, title=f"{APP_NAME} — Quick Scan (BEEF Score)")
            continue

        # Unknown input
        # Improved error messages with suggestions (Requirements 5.6, 5.7)
        _error(f"Unknown command: '{cmd}'")
        
        # Suggest similar commands using simple string matching
        all_commands = [
            "peep all", "peep cpu", "peep io", "peep mem", "peep clutter", "peep watch",
            "baseline save", "baseline diff", "settings", "help", "quit"
        ]
        
        # Find commands that start with the same letter or contain the input
        suggestions = []
        for command in all_commands:
            if cmd and (command.startswith(cmd[0]) or cmd in command):
                suggestions.append(command)
        
        if suggestions:
            console.print(f"\n[peep.muted]Did you mean:[/peep.muted]")
            for suggestion in suggestions[:3]:  # Show top 3 suggestions
                console.print(f"  [peep.highlight]beefy {suggestion}[/peep.highlight]")
        
        console.print(f"\n[peep.muted]Type 'help' to see all commands, or use shortcuts like '1' for quick scan.[/peep.muted]")


# --- CLI02 / CLI01 commands ---------------------------------------------------

@peep_app.command("all")
def peep_all(
    fat: bool = typer.Option(True, "--fat/--no-fat", help="Show only the 'fat' processes (recommended)."),
    seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Sampling window in seconds."),
    limit: int = typer.Option(25, "--limit", min=5, max=200, help="Rows to show."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map PIDs to Windows services."),
):
    """Quick Scan (combined BEEF score)."""
    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)
    render_rows(rows, sort_key="beef", limit=limit, fat_only=fat, title=f"{APP_NAME} — Quick Scan (BEEF Score)")


@peep_app.command("cpu")
def peep_cpu(
    fat: bool = typer.Option(True, "--fat/--no-fat", help="Show only the 'fat' processes (recommended)."),
    seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Sampling window in seconds."),
    limit: int = typer.Option(25, "--limit", min=5, max=200, help="Rows to show."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map PIDs to Windows services."),
):
    """CPU Hog Finder."""
    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)
    render_rows(rows, sort_key="cpu", limit=limit, fat_only=fat, title=f"{APP_NAME} — CPU Hog Finder")


@peep_app.command("io")
def peep_io(
    fat: bool = typer.Option(True, "--fat/--no-fat", help="Show only the 'fat' processes (recommended)."),
    seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Sampling window in seconds."),
    limit: int = typer.Option(25, "--limit", min=5, max=200, help="Rows to show."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map PIDs to Windows services."),
):
    """Disk Hog Finder (stutter risk)."""
    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)
    render_rows(rows, sort_key="io", limit=limit, fat_only=fat, title=f"{APP_NAME} — Disk Hog Finder")


@peep_app.command("mem")
def peep_mem(
    fat: bool = typer.Option(True, "--fat/--no-fat", help="Show only the 'fat' processes (recommended)."),
    seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Sampling window in seconds."),
    limit: int = typer.Option(25, "--limit", min=5, max=200, help="Rows to show."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map PIDs to Windows services."),
):
    """RAM Hog Finder."""
    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)
    render_rows(rows, sort_key="mem", limit=limit, fat_only=fat, title=f"{APP_NAME} — RAM Hog Finder")


@peep_app.command("clutter")
def peep_clutter(
    seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Sampling window in seconds."),
    limit: int = typer.Option(30, "--limit", min=5, max=200, help="Rows to show."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map PIDs to Windows services."),
):
    """Show tagged gamer clutter: RGB / overlays / VR / VPN / etc."""
    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)
    rows = [r for r in rows if r.tags]
    rows.sort(key=lambda r: r.beef_score, reverse=True)
    render_rows(rows, sort_key="beef", limit=limit, fat_only=False, title=f"{APP_NAME} — Gamer Clutter (tagged)")


@peep_app.command("watch")
def peep_watch(
    seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Sampling window in seconds."),
    refresh: float = typer.Option(1.0, "--refresh", min=0.2, help="Refresh interval seconds."),
    loops: int = typer.Option(60, "--loops", min=1, max=3600, help="Number of refreshes."),
    fat: bool = typer.Option(True, "--fat/--no-fat", help="Fat-only mode (recommended)."),
    limit: int = typer.Option(25, "--limit", min=5, max=200, help="Rows to show."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map PIDs to Windows services."),
):
    """Live watch view (updates table)."""
    include_windows = deep
    include_services = services
    with Live(console=console, refresh_per_second=4) as live:
        try:
            for i in range(loops):
                rows = collect_samples(seconds=seconds, include_windows=include_windows, include_services=include_services)
                if fat:
                    rows = [r for r in rows if (r.cpu_pct >= 3.0 or (r.read_bps + r.write_bps) >= 2 * (1024 ** 2) or (r.rss_bytes / (1024 ** 2)) >= 600)]
                rows.sort(key=lambda r: r.beef_score, reverse=True)
                table = build_table(rows, title=f"{APP_NAME} Watch — Top BEEF (refresh {i+1}/{loops})", limit=limit)
                live.update(table)
                time.sleep(max(0.2, refresh))
        except KeyboardInterrupt:
            pass


@baseline_app.command("save")
def baseline_save(
    file: Path = typer.Argument(Path("baseline.json"), help="Where to save the baseline snapshot."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
):
    """Save a baseline snapshot."""
    path = file.expanduser().resolve()
    snapshot_to_file(path, include_windows=deep)
    _success(f"Saved baseline to: {path}")


@baseline_app.command("diff")
def baseline_diff(
    file: Path = typer.Argument(Path("baseline.json"), help="Baseline snapshot file."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows system processes."),
    json_out: bool = typer.Option(False, "--json", help="Output diff as JSON."),
):
    """Diff current process set against a baseline snapshot."""
    path = file.expanduser().resolve()
    if not path.exists():
        _error(f"Baseline not found: {path}")
        raise typer.Exit(code=2)
    d = diff_from_file(path, include_windows=deep)
    if json_out:
        console.print_json(json.dumps(d))
        return
    _render_diff(d, path)


# --- Config commands ----------------------------------------------------------

@config_app.command("show")
def config_show():
    """Display current configuration."""
    config_manager = ConfigManager()
    config = config_manager.load()
    
    # Create a formatted table for configuration display
    table = Table(box=box.ROUNDED, show_header=True, border_style="peep.accent")
    table.add_column("Setting", style="peep.heading", no_wrap=True)
    table.add_column("Value", style="peep.brand")
    
    # General settings
    table.add_row("First Run Complete", str(config.first_run_complete))
    table.add_row("Theme Variant", config.theme_variant)
    
    # Banner settings
    table.add_row("", "")  # Separator
    table.add_row("[bold]Banner Settings[/bold]", "")
    table.add_row("  Mode", config.banner.mode)
    table.add_row("  Selected Banner", config.banner.selected_banner or "(none)")
    table.add_row("  Selected Categories", ", ".join(config.banner.selected_categories))
    table.add_row("  Animation Enabled", str(config.banner.animation_enabled))
    table.add_row("  Animation Duration", f"{config.banner.animation_duration}s")
    table.add_row("  Animation FPS", str(config.banner.animation_fps))
    table.add_row("  Animation Intensity", config.banner.animation_intensity)
    
    console.print()
    console.print(Panel(
        table,
        title=f"{BRANDED_NAME} Configuration",
        box=box.DOUBLE,
        border_style="peep.accent",
        padding=(1, 2)
    ))
    console.print()
    console.print(f"[peep.muted]Config file: {config_manager.CONFIG_FILE}[/peep.muted]")
    console.print()


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Configuration key to set (e.g., 'theme', 'banner.mode')"),
    value: str = typer.Argument(..., help="Value to set"),
):
    """Set a configuration value."""
    config_manager = ConfigManager()
    config = config_manager.load()
    
    # Parse the key path (support nested keys like "banner.mode")
    key_parts = key.split(".")
    
    try:
        if key == "theme" or key == "theme_variant":
            # Validate theme
            from themes import ThemeRegistry
            available_themes = ThemeRegistry.list_themes()
            if value not in available_themes:
                _error(f"Invalid theme '{value}'. Available themes: {', '.join(available_themes)}")
                raise typer.Exit(code=1)
            config.theme_variant = value
            _success(f"Theme set to: {value}")
            
        elif key == "banner.mode":
            if value not in ["random", "fixed", "category"]:
                _error(f"Invalid banner mode '{value}'. Must be: random, fixed, or category")
                raise typer.Exit(code=1)
            config.banner.mode = value
            _success(f"Banner mode set to: {value}")
            
        elif key == "banner.selected_banner":
            # Validate format CATEGORY:NAME
            if ":" not in value:
                _error(f"Invalid banner format '{value}'. Must be CATEGORY:NAME")
                raise typer.Exit(code=1)
            config.banner.selected_banner = value
            _success(f"Selected banner set to: {value}")
            
        elif key == "banner.animation_enabled":
            bool_value = value.lower() in ("true", "yes", "1", "on")
            config.banner.animation_enabled = bool_value
            _success(f"Animation enabled set to: {bool_value}")
            
        elif key == "banner.animation_duration":
            try:
                duration = float(value)
                if not (0.5 <= duration <= 10.0):
                    _error("Animation duration must be between 0.5 and 10.0 seconds")
                    raise typer.Exit(code=1)
                config.banner.animation_duration = duration
                _success(f"Animation duration set to: {duration}s")
            except ValueError:
                _error(f"Invalid duration value '{value}'. Must be a number.")
                raise typer.Exit(code=1)
                
        elif key == "banner.animation_fps":
            try:
                fps = int(value)
                if not (4 <= fps <= 30):
                    _error("Animation FPS must be between 4 and 30")
                    raise typer.Exit(code=1)
                config.banner.animation_fps = fps
                _success(f"Animation FPS set to: {fps}")
            except ValueError:
                _error(f"Invalid FPS value '{value}'. Must be an integer.")
                raise typer.Exit(code=1)
                
        elif key == "banner.animation_intensity":
            if value not in ["subtle", "normal", "intense"]:
                _error(f"Invalid intensity '{value}'. Must be: subtle, normal, or intense")
                raise typer.Exit(code=1)
            config.banner.animation_intensity = value
            _success(f"Animation intensity set to: {value}")
            
        else:
            _error(f"Unknown configuration key: {key}")
            console.print("\n[peep.muted]Available keys:[/peep.muted]")
            console.print("  theme, banner.mode, banner.selected_banner,")
            console.print("  banner.animation_enabled, banner.animation_duration,")
            console.print("  banner.animation_fps, banner.animation_intensity")
            raise typer.Exit(code=1)
        
        # Save the updated configuration
        config_manager.save(config)
        
    except typer.Exit:
        raise
    except Exception as e:
        _error(f"Failed to set configuration: {e}")
        raise typer.Exit(code=1)


@config_app.command("reset")
def config_reset(
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Reset configuration to defaults."""
    if not confirm:
        confirmed = Confirm.ask(
            f"[peep.warning]Reset all configuration to defaults?[/peep.warning]",
            default=False
        )
        if not confirmed:
            console.print("[peep.muted]Reset cancelled.[/peep.muted]")
            return
    
    config_manager = ConfigManager()
    
    # Delete the config file
    if config_manager.CONFIG_FILE.exists():
        try:
            config_manager.CONFIG_FILE.unlink()
            _success("Configuration reset to defaults")
        except Exception as e:
            _error(f"Failed to reset configuration: {e}")
            raise typer.Exit(code=1)
    else:
        console.print("[peep.muted]Configuration already at defaults (no config file found).[/peep.muted]")


# --- Banner commands ----------------------------------------------------------

@banner_app.command("preview")
def banner_preview(
    category: Optional[str] = typer.Option(None, "--category", "-c", help="Filter by category (e.g., ALT, 1ST_BEEFS)"),
    page: int = typer.Option(1, "--page", "-p", help="Page number to display"),
    animated: bool = typer.Option(False, "--animated", "-a", help="Show only animation-compatible banners"),
):
    """Show banner preview grid with pagination."""
    from banner_preview import BannerPreview
    
    # Load configuration and theme
    config_manager = ConfigManager()
    config = config_manager.load()
    theme = ThemeRegistry.get_theme(config.theme_variant)
    
    # Load banners
    assets_dir = Path(__file__).parent.parent / ".assets"
    banner_db = BannerDatabase(assets_dir)
    banner_dict = banner_db.load_banners()
    
    # Filter by category if specified
    if category:
        if category not in banner_dict:
            _error(f"Category '{category}' not found")
            console.print(f"\n[peep.muted]Available categories: {', '.join(banner_db.list_categories())}[/peep.muted]")
            raise typer.Exit(code=1)
        banners = banner_dict[category]
    else:
        # Get all banners from all categories
        banners = []
        for cat_banners in banner_dict.values():
            banners.extend(cat_banners)
    
    # Create preview renderer and display
    preview = BannerPreview(theme, console)
    preview.display_grid(banners, page=page, filter_animated=animated)


# --- Theme commands -----------------------------------------------------------

@theme_app.command("set")
def theme_set(
    theme_name: str = typer.Argument(..., help="Theme name (e.g., CRT_Cyan, Amber_Terminal)"),
    preview: bool = typer.Option(True, "--preview/--no-preview", help="Show theme preview before applying"),
):
    """Change the color theme."""
    # Validate theme name
    available_themes = ThemeRegistry.list_themes()
    if theme_name not in available_themes:
        _error(f"Theme '{theme_name}' not found")
        console.print(f"\n[peep.muted]Available themes: {', '.join(available_themes)}[/peep.muted]")
        raise typer.Exit(code=1)
    
    # Get the theme
    theme = ThemeRegistry.get_theme(theme_name)
    
    # Show preview if requested
    if preview:
        console.print()
        console.print(f"[bold]Theme Preview: {theme_name}[/bold]")
        console.print()
        
        # Create a sample panel with the theme
        sample_content = Text()
        sample_content.append("Primary Color\n", style=Style(color=theme.palette.primary))
        sample_content.append("Highlight Color\n", style=Style(color=theme.palette.highlight, bold=True))
        sample_content.append("Success Color\n", style=Style(color=theme.palette.success))
        sample_content.append("Error Color\n", style=Style(color=theme.palette.error))
        sample_content.append("Warning Color\n", style=Style(color=theme.palette.warning))
        sample_content.append("Dim Color\n", style=Style(color=theme.palette.dim))
        sample_content.append("Text Color", style=Style(color=theme.palette.text))
        
        sample_panel = Panel(
            sample_content,
            title=f"Theme: {theme_name}",
            box=theme.get_box_style(),
            border_style=theme.get_border_style(),
            padding=(1, 2)
        )
        console.print(sample_panel)
        console.print()
        
        # Ask for confirmation
        confirmed = Confirm.ask(f"Apply theme '{theme_name}'?", default=True)
        if not confirmed:
            console.print("[peep.muted]Theme change cancelled.[/peep.muted]")
            return
    
    # Apply the theme
    config_manager = ConfigManager()
    config = config_manager.load()
    config.theme_variant = theme_name
    config_manager.save(config)
    
    _success(f"Theme set to: {theme_name}")


@theme_app.command("list")
def theme_list():
    """List all available themes."""
    available_themes = ThemeRegistry.list_themes()
    
    # Load current theme
    config_manager = ConfigManager()
    config = config_manager.load()
    current_theme = config.theme_variant
    
    console.print()
    console.print("[bold]Available Themes:[/bold]")
    console.print()
    
    for theme_name in available_themes:
        theme = ThemeRegistry.get_theme(theme_name)
        
        # Mark current theme
        marker = "→ " if theme_name == current_theme else "  "
        
        # Create a small color sample
        sample = Text()
        sample.append("█", style=Style(color=theme.palette.primary))
        sample.append("█", style=Style(color=theme.palette.highlight))
        sample.append("█", style=Style(color=theme.palette.success))
        sample.append("█", style=Style(color=theme.palette.warning))
        sample.append("█", style=Style(color=theme.palette.error))
        
        console.print(f"{marker}{theme_name:20} ", end="")
        console.print(sample)
    
    console.print()


@dev_app.command("dump")
def dev_dump(
    seconds: float = typer.Option(1.0, "--seconds", min=0.2, help="Sampling window seconds."),
    deep: bool = typer.Option(False, "--deep", help="Include Windows processes."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map services."),
    json_out: bool = typer.Option(True, "--json/--no-json", help="Output JSON."),
):
    """
    Developer dump: full JSON payload of sampled processes.
    This exists for power users / debugging / building the future 'trim' feature safely.
    """
    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)
    payload = {
        "_meta": {"app": APP_NAME, "version": VERSION, "sample_seconds": seconds, "created_at": _now_ts()},
        "rows": [asdict(r) for r in rows],
    }
    if json_out:
        console.print_json(json.dumps(payload))
    else:
        console.print(payload)



@dev_app.command("info")
def dev_info(
    query: str = typer.Argument(..., help="PID (number) or process name (substring)."),
    seconds: float = typer.Option(0.6, "--seconds", min=0.2, help="Sampling window seconds."),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="Include Windows processes (dev view default = yes)."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map services."),
):
    """
    Developer info: explain a process (path, cmdline, services, live CPU/RAM/IO sample).
    """
    q = query.strip()
    pid: Optional[int] = None
    if q.isdigit():
        pid = int(q)

    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)
    matches: List[ProcRow] = []
    if pid is not None:
        matches = [r for r in rows if r.pid == pid]
    else:
        needle = q.lower()
        matches = [r for r in rows if needle in r.name.lower()]

    if not matches:
        _error(f"No matches for: {query}")
        raise typer.Exit(code=1)

    for r in matches[:10]:
        # Build two-column detail table
        detail = Table(box=None, show_header=False, padding=(0, 1))
        detail.add_column("Field", style="peep.heading", width=10, no_wrap=True)
        detail.add_column("Value")

        detail.add_row("Process", Text(f"{r.name}  (PID {r.pid})", style="peep.heading"))
        detail.add_row("Type", kind_badge(r.kind))
        detail.add_row("User", Text(r.username, style="peep.muted"))
        detail.add_row("Path", Text(r.exe, style="peep.muted"))
        if r.cmdline:
            detail.add_row("Cmd", Text(r.cmdline, style="peep.muted"))
        if r.tags:
            tag_txt = ", ".join([f"{TAG_DEFS.get(t, ('', t))[0]}{t}" for t in r.tags])
            detail.add_row("Tags", Text(tag_txt, style="peep.tag"))
        if r.services:
            svc_lines = []
            for s in r.services[:10]:
                dn = s.display_name or s.name
                extra = []
                if s.start_type:
                    extra.append(s.start_type)
                if s.status:
                    extra.append(s.status)
                suffix = f" ({', '.join(extra)})" if extra else ""
                svc_lines.append(f"- {dn}{suffix}")
            detail.add_row("Services", Text("\n".join(svc_lines), style="peep.service"))

        # Metrics
        cpu = color_metric(r.cpu_pct, thresholds=(5.0, 15.0), fmt="{:.1f}")
        ram_mb = r.rss_bytes / (1024 ** 2)
        ram = Text(f"{ram_mb:.0f} MB", style=("peep.metric.hot" if ram_mb >= 2000 else "peep.metric.warn" if ram_mb >= 800 else "peep.metric.ok"))
        read = color_bytes(r.read_bps, thresholds_mb_s=(2.0, 20.0))
        write = color_bytes(r.write_bps, thresholds_mb_s=(2.0, 20.0))
        beef = Text(f"{r.beef_score:.1f}", style=("peep.metric.hot" if r.beef_score >= 60 else "peep.metric.warn" if r.beef_score >= 25 else "peep.metric.ok"))
        metrics = Text.assemble(
            ("BEEF ", "bold"), beef, ("   CPU ", "bold"), cpu,
            ("   RAM ", "bold"), ram, ("   Read ", "bold"), read, ("   Write ", "bold"), write
        )

        console.print(Rule("Process Info", style="peep.accent"))
        console.print(Panel(detail, subtitle=metrics, box=box.SQUARE, border_style="peep.accent"))


def _dev_top(
    metric: str,
    seconds: float,
    limit: int,
    deep: bool,
    services: bool,
    fat: bool,
    json_out: bool,
):
    rows = _sampled(seconds=seconds, include_windows=deep, include_services=services)

    if fat:
        rows = [r for r in rows if (r.cpu_pct >= 3.0 or (r.read_bps + r.write_bps) >= 2 * (1024 ** 2) or (r.rss_bytes / (1024 ** 2)) >= 600)]

    if metric == "cpu":
        rows.sort(key=lambda r: r.cpu_pct, reverse=True)
    elif metric == "io":
        rows.sort(key=lambda r: (r.read_bps + r.write_bps), reverse=True)
    elif metric == "mem":
        rows.sort(key=lambda r: r.rss_bytes, reverse=True)
    else:
        rows.sort(key=lambda r: r.beef_score, reverse=True)

    if json_out:
        payload = {
            "_meta": {"app": APP_NAME, "version": VERSION, "metric": metric, "seconds": seconds, "created_at": _now_ts()},
            "rows": [asdict(r) for r in rows[:limit]],
        }
        console.print_json(json.dumps(payload))
        return

    render_rows(rows, sort_key=("beef" if metric == "beef" else metric), limit=limit, fat_only=False, title=f"{APP_NAME} — DEV TOP {metric.upper()}")


@dev_top_app.command("beef")
def dev_top_beef(
    seconds: float = typer.Option(1.0, "--seconds", min=0.2),
    limit: int = typer.Option(25, "--limit", min=5, max=500),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="Include Windows processes (dev default = yes)."),
    services: bool = typer.Option(True, "--services/--no-services"),
    fat: bool = typer.Option(False, "--fat", help="Filter to obvious hogs only."),
    json_out: bool = typer.Option(False, "--json", help="Output JSON."),
):
    _dev_top("beef", seconds, limit, deep, services, fat, json_out)


@dev_top_app.command("cpu")
def dev_top_cpu(
    seconds: float = typer.Option(1.0, "--seconds", min=0.2),
    limit: int = typer.Option(25, "--limit", min=5, max=500),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="Include Windows processes (dev default = yes)."),
    services: bool = typer.Option(True, "--services/--no-services"),
    fat: bool = typer.Option(False, "--fat", help="Filter to obvious hogs only."),
    json_out: bool = typer.Option(False, "--json", help="Output JSON."),
):
    _dev_top("cpu", seconds, limit, deep, services, fat, json_out)


@dev_top_app.command("io")
def dev_top_io(
    seconds: float = typer.Option(1.0, "--seconds", min=0.2),
    limit: int = typer.Option(25, "--limit", min=5, max=500),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="Include Windows processes (dev default = yes)."),
    services: bool = typer.Option(True, "--services/--no-services"),
    fat: bool = typer.Option(False, "--fat", help="Filter to obvious hogs only."),
    json_out: bool = typer.Option(False, "--json", help="Output JSON."),
):
    _dev_top("io", seconds, limit, deep, services, fat, json_out)


@dev_top_app.command("mem")
def dev_top_mem(
    seconds: float = typer.Option(1.0, "--seconds", min=0.2),
    limit: int = typer.Option(25, "--limit", min=5, max=500),
    deep: bool = typer.Option(True, "--deep/--no-deep", help="Include Windows processes (dev default = yes)."),
    services: bool = typer.Option(True, "--services/--no-services"),
    fat: bool = typer.Option(False, "--fat", help="Filter to obvious hogs only."),
    json_out: bool = typer.Option(False, "--json", help="Output JSON."),
):
    _dev_top("mem", seconds, limit, deep, services, fat, json_out)



@app.callback(invoke_without_command=True)
def _default(ctx: typer.Context, debug: bool = typer.Option(False, "--debug", help="Enable debug logging")):
    """
    Default behavior: start the interactive CLI if no subcommand is provided.
    """
    # Initialize logging
    setup_logging(debug=debug)
    
    if ctx.invoked_subcommand is None:
        interactive_loop()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
