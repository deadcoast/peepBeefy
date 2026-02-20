#!/usr/bin/env python3
"""gameprep.py

GamePrep: a gamer-focused process inspector for Windows 11.

Goal
- Show you *what is actually running* (including service-backed processes that don't show in the taskbar).
- Surface what is *clogging resources* (CPU, RAM, disk I/O) so you can decide what to close before/during play.

Design notes
- Uses Typer + Rich for a fast, readable CLI.
- No placeholders: real sampling logic for CPU% and disk read/write B/s.
- Safe by default: does NOT terminate anything.
- Includes an opinionated but conservative "scan" that tags common vendor utilities / overlays.

Install (Windows)
  py -m pip install psutil rich typer

Examples
  # Top CPU users (sample over 1s), hide Windows core binaries, show service mapping
  python gameprep.py top cpu --seconds 1.0 --limit 25 --non-windows --services

  # Top disk I/O users (often causes stutter)
  python gameprep.py top io --seconds 1.0 --limit 25 --non-windows --services

  # Broad scan: tag common gaming clutter (RGB suites, overlays, VR, VPN, etc.)
  python gameprep.py scan --seconds 0.8 --services

  # Inspect a suspicious process by PID or name
  python gameprep.py info 1234
  python gameprep.py info OVRServer_x64.exe

  # Catch "what started itself": snapshot + diff
  python gameprep.py snapshot baseline.json
  python gameprep.py diff baseline.json

Limitations
- Some fields may require admin rights (handled gracefully).
- Windows service mapping works on Windows only; on other OSes it will show empty.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import psutil
import typer
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich import box

app = typer.Typer(add_completion=False, no_args_is_help=True)
top_app = typer.Typer(add_completion=False, no_args_is_help=True)
app.add_typer(top_app, name="top", help="Show top resource consumers (CPU / RAM / disk I/O).")

console = Console()

# ---------------------------
# Helpers
# ---------------------------

WINDOWS_ROOT = (os.environ.get("WINDIR") or "C:\\Windows").rstrip("\\/")

SERVICE_ACCOUNTS = {
    "nt authority\\system",
    "nt authority\\local service",
    "nt authority\\network service",
}

CRITICAL_NAMES = {
    # Keep conservative. We *display* them if asked, but avoid tagging them in scan.
    "system",
    "system idle process",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "smss.exe",
    "svchost.exe",
    "dwm.exe",
    "explorer.exe",
    "audiodg.exe",
    "conhost.exe",
    "fontdrvhost.exe",
    "wudfhost.exe",
    "registry",
}


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def is_windows_binary(exe: str) -> bool:
    """True if exe lives under C:\Windows (roughly "core OS")."""
    exe_l = _norm(exe)
    win_l = _norm(WINDOWS_ROOT)
    return bool(exe_l) and exe_l.startswith(win_l)


def fmt_bytes(n: Optional[float]) -> str:
    if n is None:
        return ""
    try:
        n_f = float(n)
    except Exception:
        return ""
    if n_f < 0:
        n_f = 0
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while n_f >= 1024 and i < len(units) - 1:
        n_f /= 1024.0
        i += 1
    if i == 0:
        return f"{int(n_f)} {units[i]}"
    return f"{n_f:.1f} {units[i]}"


def fmt_rate(bps: Optional[float]) -> str:
    if bps is None:
        return ""
    return f"{fmt_bytes(bps)}/s"


def short_path(p: str, max_len: int = 48) -> str:
    p = p or ""
    if len(p) <= max_len:
        return p
    # keep start + end
    keep = max_len - 3
    head = keep // 2
    tail = keep - head
    return p[:head] + "..." + p[-tail:]


# ---------------------------
# Process model
# ---------------------------

@dataclass
class ProcRow:
    pid: int
    ppid: int
    name: str
    exe: str
    cmdline: Tuple[str, ...]
    username: str

    cpu_percent: Optional[float] = None
    rss_bytes: Optional[int] = None
    read_bps: Optional[float] = None
    write_bps: Optional[float] = None

    services: Tuple[str, ...] = ()
    tags: Tuple[str, ...] = ()

    @property
    def is_serviceish(self) -> bool:
        u = _norm(self.username)
        return u in SERVICE_ACCOUNTS or bool(self.services)

    @property
    def is_windows(self) -> bool:
        return is_windows_binary(self.exe)

    @property
    def key(self) -> str:
        # stable-ish identity for snapshot diff
        exe = _norm(self.exe)
        name = _norm(self.name)
        return exe if exe else name


# ---------------------------
# Windows service mapping (PID -> [service names])
# ---------------------------


def get_service_map() -> Dict[int, List[str]]:
    """Map PID -> list of service display names (Windows only)."""
    m: Dict[int, List[str]] = {}

    # psutil.win_service_iter exists only on Windows builds of psutil
    win_iter = getattr(psutil, "win_service_iter", None)
    if win_iter is None:
        return m

    try:
        for svc in win_iter():
            try:
                d = svc.as_dict()  # type: ignore[attr-defined]
                pid = d.get("pid")
                if not pid or pid == 0:
                    continue
                name = d.get("name") or ""
                disp = d.get("display_name") or name
                label = f"{disp} ({name})" if disp and name and disp != name else (disp or name)
                m.setdefault(int(pid), []).append(label)
            except Exception:
                continue
    except Exception:
        return m

    # stable output
    for pid in list(m.keys()):
        m[pid] = sorted(set(m[pid]))
    return m


# ---------------------------
# Tagging rules (gamer-focused, conservative)
# ---------------------------

@dataclass(frozen=True)
class TagRule:
    tag: str
    severity: str  # "close", "caution", "info"
    reason: str
    pattern: re.Pattern


def build_tag_rules() -> List[TagRule]:
    """Patterns are matched against name + exe + cmdline (lowercased)."""
    def rx(p: str) -> re.Pattern:
        return re.compile(p, re.IGNORECASE)

    return [
        # RGB / vendor suites
        TagRule("msi", "caution", "MSI Center / MSI services (polling/RGB/utilities).", rx(r"\b(msi\.?|msi_).*(center|centralserver|companion|lan|oled|case|service)\b|\bmsi center\b")),
        TagRule("mystic_light", "caution", "Mystic Light / LEDKeeper style RGB services.", rx(r"mystic\s*light|ledkeeper|lightkeeper|mysticlight")),
        TagRule("icue", "caution", "Corsair iCUE background components.", rx(r"\bicue\b|corsair.*(service|agent)")),
        TagRule("armoury_crate", "caution", "ASUS Armoury Crate / Aura components.", rx(r"armoury\s*crate|aura.*(service|sync)|asus.*(service|framework)")),
        TagRule("razer", "caution", "Razer Synapse / Chroma components.", rx(r"razer|synapse|chroma")),

        # Overlays / hooks
        TagRule("rtss", "caution", "RTSS overlay / frame limiter.", rx(r"\brtss\b|rivatuner")),
        TagRule("steam_overlay", "caution", "Steam overlay helper.", rx(r"gameoverlayui\.exe")),
        TagRule("xbox_game_bar", "caution", "Xbox Game Bar overlay components.", rx(r"gamebarpresencewriter|xbox.*game\s*bar")),
        TagRule("discord", "info", "Discord (may include overlay depending on settings).", rx(r"\bdiscord\b")),
        TagRule("nvidia_overlay", "caution", "NVIDIA overlay/recording helpers (ShadowPlay/Share).", rx(r"shadowplay|nvsphelper|nvidia\s*share|nvidia\s*app")),
        TagRule("amd_overlay", "caution", "AMD Radeon overlay components (if installed / iGPU active).", rx(r"radeon\s*settings:|desktop\s*overlay|amdrssrc")),
        TagRule("presentmon", "caution", "PresentMon frame capture/telemetry.", rx(r"presentmon")),
        TagRule("overwolf", "caution", "Overwolf overlay framework.", rx(r"overwolf")),

        # VR runtimes
        TagRule("oculus", "caution", "Oculus/Meta VR runtime services (OVR*).", rx(r"\bovr(server|service|redirmon|library)\b|oculus|meta\s*quest")),
        TagRule("steamvr", "caution", "SteamVR runtime.", rx(r"\bvrserver\b|\bvrmonitor\b|steamvr")),

        # VPN / network layers
        TagRule("nordvpn", "caution", "NordVPN services/drivers.", rx(r"nordvpn|nordsec")),
        TagRule("vpn", "caution", "VPN client/service.", rx(r"expressvpn|protonvpn|surfshark|pia\b|private\s*internet\s*access")),

        # Peripheral suites
        TagRule("logitech", "caution", "Logitech G HUB / Logi Options+ components.", rx(r"lghub|logi\s*options\+|logi\s*options|logitech")),
        TagRule("steelseries", "caution", "SteelSeries GG.", rx(r"steelseries|\bgg\.exe\b")),

        # Updaters / launchers (often safe to close while gaming)
        TagRule("updater", "info", "Updater/installer helper.", rx(r"updater|update\s*service|install\s*helper|\bautoupdate\b")),
        TagRule("launcher", "info", "Game launcher/background helper.", rx(r"epicgameslauncher|battle\.net|ubisoft|ea\s*app|riot\s*client|gog\s*galaxy")),
    ]


def tag_process(row: ProcRow, rules: Sequence[TagRule]) -> Tuple[Tuple[str, ...], Optional[str]]:
    """Return tags and highest-severity label (close/caution/info) based on tag rules."""
    hay = "\n".join([row.name or "", row.exe or "", " ".join(row.cmdline or ())]).lower()
    tags: List[str] = []
    severities: List[str] = []
    for r in rules:
        if r.pattern.search(hay):
            tags.append(r.tag)
            severities.append(r.severity)

    if not tags:
        return (), None

    order = {"close": 0, "caution": 1, "info": 2}
    best = sorted(severities, key=lambda s: order.get(s, 99))[0]
    return tuple(sorted(set(tags))), best


# ---------------------------
# Collection + sampling
# ---------------------------


def _safe_process(pid: int) -> Optional[psutil.Process]:
    try:
        return psutil.Process(pid)
    except Exception:
        return None


def collect_basic_rows(service_map: Dict[int, List[str]]) -> List[ProcRow]:
    rows: List[ProcRow] = []
    for p in psutil.process_iter(attrs=["pid", "ppid", "name", "exe", "cmdline", "username"]):
        try:
            info = p.info
            pid = int(info.get("pid"))
            rows.append(
                ProcRow(
                    pid=pid,
                    ppid=int(info.get("ppid") or 0),
                    name=str(info.get("name") or ""),
                    exe=str(info.get("exe") or ""),
                    cmdline=tuple(info.get("cmdline") or ()),
                    username=str(info.get("username") or ""),
                    services=tuple(service_map.get(pid, [])),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue
    return rows


def sample_metrics(rows: List[ProcRow], seconds: float) -> None:
    """Populate cpu_percent + io rates for each row (in-place)."""
    seconds = float(seconds)
    if seconds <= 0:
        seconds = 0.25

    # Build handles
    handles: Dict[int, psutil.Process] = {}
    for r in rows:
        h = _safe_process(r.pid)
        if h is not None:
            handles[r.pid] = h

    # Prime CPU sampling and IO baseline
    io0: Dict[int, Tuple[int, int]] = {}
    for pid, h in handles.items():
        try:
            h.cpu_percent(interval=None)
        except Exception:
            pass
        try:
            io = h.io_counters()
            io0[pid] = (int(getattr(io, "read_bytes", 0)), int(getattr(io, "write_bytes", 0)))
        except Exception:
            # AccessDenied or unsupported
            pass

    time.sleep(max(0.1, seconds))

    # Second sample
    for r in rows:
        h = handles.get(r.pid)
        if h is None:
            continue
        # CPU
        try:
            r.cpu_percent = float(h.cpu_percent(interval=None))
        except Exception:
            r.cpu_percent = None
        # RSS
        try:
            r.rss_bytes = int(getattr(h.memory_info(), "rss", 0))
        except Exception:
            r.rss_bytes = None
        # IO rate
        try:
            io = h.io_counters()
            rb1 = int(getattr(io, "read_bytes", 0))
            wb1 = int(getattr(io, "write_bytes", 0))
            if r.pid in io0:
                rb0, wb0 = io0[r.pid]
                r.read_bps = max(0.0, (rb1 - rb0) / seconds)
                r.write_bps = max(0.0, (wb1 - wb0) / seconds)
            else:
                r.read_bps = None
                r.write_bps = None
        except Exception:
            r.read_bps = None
            r.write_bps = None


# ---------------------------
# Rendering
# ---------------------------


def make_table(
    rows: Sequence[ProcRow],
    *,
    title: str,
    show_services: bool,
    show_path: bool,
    show_user: bool,
    show_tags: bool,
) -> Table:
    table = Table(
        title=title,
        box=box.SIMPLE_HEAVY,
        show_lines=False,
        header_style="bold",
    )

    table.add_column("PID", justify="right", no_wrap=True)
    table.add_column("TYPE", no_wrap=True)
    table.add_column("PROC", overflow="fold")
    table.add_column("CPU%", justify="right", no_wrap=True)
    table.add_column("RAM", justify="right", no_wrap=True)
    table.add_column("READ", justify="right", no_wrap=True)
    table.add_column("WRITE", justify="right", no_wrap=True)

    if show_tags:
        table.add_column("TAGS", overflow="fold")
    if show_services:
        table.add_column("SERVICE", overflow="fold")
    if show_user:
        table.add_column("USER", overflow="fold")
    if show_path:
        table.add_column("PATH", overflow="fold")

    for r in rows:
        proc_type = "svc" if r.is_serviceish else "user"
        # Colorize Windows vs 3rd party lightly
        proc_text = Text(r.name or "", style="")
        if r.is_windows:
            proc_text.stylize("dim")

        cpu = "" if r.cpu_percent is None else f"{r.cpu_percent:.1f}"
        ram = "" if r.rss_bytes is None else fmt_bytes(float(r.rss_bytes))
        read = fmt_rate(r.read_bps)
        write = fmt_rate(r.write_bps)

        row_cells: List[Any] = [str(r.pid), proc_type, proc_text, cpu, ram, read, write]

        if show_tags:
            row_cells.append(",".join(r.tags) if r.tags else ""
            )
        if show_services:
            row_cells.append("; ".join(r.services) if r.services else "")
        if show_user:
            row_cells.append(r.username or "")
        if show_path:
            row_cells.append(short_path(r.exe) if r.exe else "")

        table.add_row(*row_cells)

    return table


def to_json(rows: Sequence[ProcRow]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "pid": r.pid,
                "ppid": r.ppid,
                "name": r.name,
                "exe": r.exe,
                "cmdline": list(r.cmdline),
                "username": r.username,
                "cpu_percent": r.cpu_percent,
                "rss_bytes": r.rss_bytes,
                "read_bps": r.read_bps,
                "write_bps": r.write_bps,
                "is_windows": r.is_windows,
                "services": list(r.services),
                "tags": list(r.tags),
            }
        )
    return out


# ---------------------------
# Commands
# ---------------------------


def _prepare_rows(seconds: float, services: bool, tag: bool) -> List[ProcRow]:
    svc_map = get_service_map() if services else {}
    rows = collect_basic_rows(svc_map)
    sample_metrics(rows, seconds)

    if tag:
        rules = build_tag_rules()
        for r in rows:
            if _norm(r.name) in CRITICAL_NAMES:
                continue
            tags, _sev = tag_process(r, rules)
            r.tags = tags

    return rows


def _filter_rows(
    rows: List[ProcRow],
    *,
    non_windows: bool,
    include_windows: bool,
    query: Optional[str],
    min_cpu: float,
    min_ram_mb: float,
    min_read_mb_s: float,
    min_write_mb_s: float,
) -> List[ProcRow]:
    q = _norm(query or "")

    out: List[ProcRow] = []
    for r in rows:
        if non_windows and r.is_windows:
            continue
        if include_windows is False and non_windows is False:
            # default: show all
            pass
        # text query
        if q:
            hay = "\n".join([r.name or "", r.exe or "", " ".join(r.cmdline or ()), ",".join(r.tags or ())]).lower()
            if q not in hay:
                continue

        cpu = r.cpu_percent or 0.0
        ram_mb = (r.rss_bytes or 0) / (1024 * 1024)
        read_mb = (r.read_bps or 0.0) / (1024 * 1024)
        write_mb = (r.write_bps or 0.0) / (1024 * 1024)

        if cpu < min_cpu:
            continue
        if ram_mb < min_ram_mb:
            continue
        if read_mb < min_read_mb_s:
            continue
        if write_mb < min_write_mb_s:
            continue

        out.append(r)

    return out


@top_app.command("cpu")
def top_cpu(
    seconds: float = typer.Option(1.0, help="Sampling window in seconds."),
    limit: int = typer.Option(25, help="Max rows."),
    non_windows: bool = typer.Option(True, "--non-windows/--all", help="Hide core Windows binaries (C:\\Windows\\...)."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map processes to Windows Services (when possible)."),
    path: bool = typer.Option(False, "--path", help="Show executable path."),
    user: bool = typer.Option(False, "--user", help="Show username/service account."),
    tags: bool = typer.Option(True, "--tags/--no-tags", help="Tag common gamer clutter (RGB, overlays, VPN, VR, etc.)."),
    query: Optional[str] = typer.Option(None, "--q", help="Filter by substring across name/path/cmdline/tags."),
    min_cpu: float = typer.Option(0.1, help="Minimum CPU% to show."),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON to stdout instead of a table."),
):
    rows = _prepare_rows(seconds=seconds, services=services, tag=tags)
    rows = _filter_rows(
        rows,
        non_windows=non_windows,
        include_windows=not non_windows,
        query=query,
        min_cpu=min_cpu,
        min_ram_mb=0,
        min_read_mb_s=0,
        min_write_mb_s=0,
    )
    rows.sort(key=lambda r: (r.cpu_percent or 0.0), reverse=True)
    rows = rows[: max(1, limit)]

    if json_out:
        console.print_json(json.dumps(to_json(rows), ensure_ascii=False))
        raise typer.Exit(0)

    title = f"Top CPU ({seconds:.2f}s sample)"
    table = make_table(rows, title=title, show_services=services, show_path=path, show_user=user, show_tags=tags)
    console.print(table)


@top_app.command("mem")
def top_mem(
    seconds: float = typer.Option(0.5, help="Sampling window (used to also capture CPU/IO rates)."),
    limit: int = typer.Option(25, help="Max rows."),
    non_windows: bool = typer.Option(True, "--non-windows/--all", help="Hide core Windows binaries (C:\\Windows\\...)."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map processes to Windows Services (when possible)."),
    path: bool = typer.Option(False, "--path", help="Show executable path."),
    user: bool = typer.Option(False, "--user", help="Show username/service account."),
    tags: bool = typer.Option(True, "--tags/--no-tags", help="Tag common gamer clutter (RGB, overlays, VPN, VR, etc.)."),
    query: Optional[str] = typer.Option(None, "--q", help="Filter by substring across name/path/cmdline/tags."),
    min_ram_mb: float = typer.Option(50.0, help="Minimum RAM (MB) to show."),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON to stdout instead of a table."),
):
    rows = _prepare_rows(seconds=seconds, services=services, tag=tags)
    rows = _filter_rows(
        rows,
        non_windows=non_windows,
        include_windows=not non_windows,
        query=query,
        min_cpu=0,
        min_ram_mb=min_ram_mb,
        min_read_mb_s=0,
        min_write_mb_s=0,
    )
    rows.sort(key=lambda r: (r.rss_bytes or 0), reverse=True)
    rows = rows[: max(1, limit)]

    if json_out:
        console.print_json(json.dumps(to_json(rows), ensure_ascii=False))
        raise typer.Exit(0)

    title = f"Top RAM (sample {seconds:.2f}s)"
    table = make_table(rows, title=title, show_services=services, show_path=path, show_user=user, show_tags=tags)
    console.print(table)


@top_app.command("io")
def top_io(
    seconds: float = typer.Option(1.0, help="Sampling window in seconds."),
    limit: int = typer.Option(25, help="Max rows."),
    non_windows: bool = typer.Option(True, "--non-windows/--all", help="Hide core Windows binaries (C:\\Windows\\...)."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map processes to Windows Services (when possible)."),
    path: bool = typer.Option(False, "--path", help="Show executable path."),
    user: bool = typer.Option(False, "--user", help="Show username/service account."),
    tags: bool = typer.Option(True, "--tags/--no-tags", help="Tag common gamer clutter (RGB, overlays, VPN, VR, etc.)."),
    query: Optional[str] = typer.Option(None, "--q", help="Filter by substring across name/path/cmdline/tags."),
    min_mb_s: float = typer.Option(0.5, help="Minimum combined read+write MB/s to show."),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON to stdout instead of a table."),
):
    rows = _prepare_rows(seconds=seconds, services=services, tag=tags)

    # Filter by IO threshold
    out: List[ProcRow] = []
    for r in rows:
        if non_windows and r.is_windows:
            continue
        if query:
            q = _norm(query)
            hay = "\n".join([r.name or "", r.exe or "", " ".join(r.cmdline or ()), ",".join(r.tags or ())]).lower()
            if q not in hay:
                continue
        io_mb_s = ((r.read_bps or 0.0) + (r.write_bps or 0.0)) / (1024 * 1024)
        if io_mb_s >= float(min_mb_s):
            out.append(r)

    out.sort(key=lambda r: ((r.read_bps or 0.0) + (r.write_bps or 0.0)), reverse=True)
    out = out[: max(1, limit)]

    if json_out:
        console.print_json(json.dumps(to_json(out), ensure_ascii=False))
        raise typer.Exit(0)

    title = f"Top Disk I/O ({seconds:.2f}s sample)"
    table = make_table(out, title=title, show_services=services, show_path=path, show_user=user, show_tags=tags)
    console.print(table)


@app.command("scan")
def scan(
    seconds: float = typer.Option(0.8, help="Sampling window in seconds."),
    non_windows: bool = typer.Option(True, "--non-windows/--all", help="Hide core Windows binaries (C:\\Windows\\...)."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map processes to Windows Services (when possible)."),
    path: bool = typer.Option(False, "--path", help="Show executable path."),
    user: bool = typer.Option(False, "--user", help="Show username/service account."),
    json_out: bool = typer.Option(False, "--json", help="Emit JSON to stdout instead of a table."),
):
    """Tag common gamer clutter + show if it's consuming resources."""
    rows = _prepare_rows(seconds=seconds, services=services, tag=True)

    # Keep only tagged rows
    tagged = [r for r in rows if r.tags]
    if non_windows:
        tagged = [r for r in tagged if not r.is_windows]

    # Sort by "likely impact": CPU then IO then RAM
    tagged.sort(
        key=lambda r: (
            (r.cpu_percent or 0.0),
            ((r.read_bps or 0.0) + (r.write_bps or 0.0)),
            (r.rss_bytes or 0),
        ),
        reverse=True,
    )

    if json_out:
        console.print_json(json.dumps(to_json(tagged), ensure_ascii=False))
        raise typer.Exit(0)

    title = f"Scan (tagged clutter) — {seconds:.2f}s sample"
    table = make_table(tagged, title=title, show_services=services, show_path=path, show_user=user, show_tags=True)
    console.print(table)


@app.command("info")
def info(
    target: str = typer.Argument(..., help="PID (e.g. 1234) or process name (e.g. OVRServer_x64.exe)."),
    seconds: float = typer.Option(0.6, help="Sampling window to show CPU/IO rates."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map processes to Windows Services (when possible)."),
):
    """Explain what a process is by showing path, cmdline, parent, user, services and live rates."""
    svc_map = get_service_map() if services else {}

    # Resolve PID(s)
    pids: List[int] = []
    if target.isdigit():
        pids = [int(target)]
    else:
        name_q = _norm(target)
        for p in psutil.process_iter(attrs=["pid", "name"]):
            try:
                if _norm(p.info.get("name") or "") == name_q:
                    pids.append(int(p.info["pid"]))
            except Exception:
                continue

    if not pids:
        console.print(f"[bold red]No process found for[/bold red] {target}")
        raise typer.Exit(1)

    # Build rows for those PIDs
    rows: List[ProcRow] = []
    for pid in pids:
        h = _safe_process(pid)
        if h is None:
            continue
        try:
            name = h.name()
        except Exception:
            name = ""
        try:
            exe = h.exe()
        except Exception:
            exe = ""
        try:
            cmd = tuple(h.cmdline())
        except Exception:
            cmd = ()
        try:
            usern = h.username()
        except Exception:
            usern = ""
        try:
            ppid = int(h.ppid())
        except Exception:
            ppid = 0

        rows.append(
            ProcRow(
                pid=pid,
                ppid=ppid,
                name=name,
                exe=exe,
                cmdline=cmd,
                username=usern,
                services=tuple(svc_map.get(pid, [])),
            )
        )

    # Sample
    sample_metrics(rows, seconds)

    rules = build_tag_rules()
    for r in rows:
        tags, _ = tag_process(r, rules)
        r.tags = tags

    # Render a readable report
    for r in rows:
        console.rule(f"PID {r.pid} — {r.name}")
        console.print(f"[bold]Path:[/bold] {r.exe or '(unknown)'}")
        console.print(f"[bold]User:[/bold] {r.username or '(unknown)'}")
        console.print(f"[bold]Type:[/bold] {'service' if r.is_serviceish else 'user'}")
        console.print(f"[bold]Parent PID:[/bold] {r.ppid}")

        if r.services:
            console.print("[bold]Service(s):[/bold]")
            for s in r.services:
                console.print(f"  • {s}")

        if r.tags:
            console.print(f"[bold]Tags:[/bold] {', '.join(r.tags)}")

        console.print(
            f"[bold]Rates ({seconds:.2f}s):[/bold] CPU {'' if r.cpu_percent is None else f'{r.cpu_percent:.1f}%'}"
            f" | RAM {'' if r.rss_bytes is None else fmt_bytes(float(r.rss_bytes))}"
            f" | Read {fmt_rate(r.read_bps)} | Write {fmt_rate(r.write_bps)}"
        )

        if r.cmdline:
            console.print("[bold]Command line:[/bold]")
            console.print("  " + " ".join(r.cmdline))


@app.command("snapshot")
def snapshot(
    out_file: Path = typer.Argument(..., help="Where to write a JSON snapshot."),
    services: bool = typer.Option(True, "--services/--no-services", help="Include Windows service mapping."),
):
    """Save a snapshot of running processes (for later diff)."""
    svc_map = get_service_map() if services else {}
    rows = collect_basic_rows(svc_map)

    payload = {
        "created_at": time.time(),
        "created_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "windows_root": WINDOWS_ROOT,
        "processes": [
            {
                "pid": r.pid,
                "ppid": r.ppid,
                "name": r.name,
                "exe": r.exe,
                "cmdline": list(r.cmdline),
                "username": r.username,
                "services": list(r.services),
                "key": r.key,
                "is_windows": r.is_windows,
            }
            for r in rows
        ],
    }

    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    console.print(f"Wrote snapshot: [bold]{out_file}[/bold] ({len(rows)} processes)")


@app.command("diff")
def diff(
    baseline: Path = typer.Argument(..., help="A snapshot JSON created by the snapshot command."),
    services: bool = typer.Option(True, "--services/--no-services", help="Include Windows service mapping in current view."),
    non_windows: bool = typer.Option(True, "--non-windows/--all", help="Hide core Windows binaries when showing diffs."),
):
    """Diff current process list vs a snapshot to find new/background processes that started."""
    try:
        base = json.loads(baseline.read_text(encoding="utf-8"))
        base_procs = base.get("processes", [])
    except Exception as e:
        console.print(f"[bold red]Failed to read baseline:[/bold red] {e}")
        raise typer.Exit(1)

    base_keys: Dict[str, Dict[str, Any]] = {}
    for p in base_procs:
        k = _norm(p.get("key") or p.get("exe") or p.get("name") or "")
        if not k:
            continue
        base_keys[k] = p

    svc_map = get_service_map() if services else {}
    cur_rows = collect_basic_rows(svc_map)

    cur_keys: Dict[str, ProcRow] = {}
    for r in cur_rows:
        k = _norm(r.key)
        if not k:
            continue
        cur_keys[k] = r

    new_keys = sorted(set(cur_keys.keys()) - set(base_keys.keys()))
    gone_keys = sorted(set(base_keys.keys()) - set(cur_keys.keys()))

    # Render
    if new_keys:
        new_rows = [cur_keys[k] for k in new_keys]
        if non_windows:
            new_rows = [r for r in new_rows if not r.is_windows]
        new_rows.sort(key=lambda r: r.name.lower())
        t = make_table(
            new_rows,
            title=f"NEW since snapshot ({len(new_rows)})",
            show_services=services,
            show_path=True,
            show_user=False,
            show_tags=False,
        )
        console.print(t)
    else:
        console.print("No new processes since snapshot.")

    if gone_keys:
        # Show gone as a simple list (baseline has no runtime metrics)
        console.rule(f"GONE since snapshot ({len(gone_keys)})")
        for k in gone_keys[:150]:
            p = base_keys[k]
            if non_windows and bool(p.get("is_windows")):
                continue
            name = p.get("name") or ""
            exe = p.get("exe") or ""
            console.print(f"• {name} — {short_path(exe)}")
        if len(gone_keys) > 150:
            console.print(f"… plus {len(gone_keys) - 150} more")


@app.command("find")
def find(
    text: str = typer.Argument(..., help="Substring to search across name/path/cmdline."),
    services: bool = typer.Option(True, "--services/--no-services", help="Map processes to Windows Services (when possible)."),
    non_windows: bool = typer.Option(False, "--non-windows/--all", help="Optional: hide core Windows binaries."),
):
    """Search running processes by substring (quick 'what is this thing?')."""
    svc_map = get_service_map() if services else {}
    rows = collect_basic_rows(svc_map)

    q = _norm(text)
    hits: List[ProcRow] = []
    for r in rows:
        if non_windows and r.is_windows:
            continue
        hay = "\n".join([r.name or "", r.exe or "", " ".join(r.cmdline or ())]).lower()
        if q in hay:
            hits.append(r)

    # light sample for nicer output
    sample_metrics(hits, 0.4)

    title = f"Find: '{text}' ({len(hits)} match(es))"
    t = make_table(hits, title=title, show_services=services, show_path=True, show_user=True, show_tags=False)
    console.print(t)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
