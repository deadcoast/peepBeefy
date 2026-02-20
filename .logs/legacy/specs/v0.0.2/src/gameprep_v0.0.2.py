#!/usr/bin/env python3
"""gameprep.py

A Windows-focused CLI to *see* what's running (including background services that don't show
in the taskbar) and to flag common "gaming stutter" offenders.

What it does (working logic):
- Lists processes with CPU / RAM / disk I/O rates (sampled).
- Highlights non-Windows processes that are consuming resources.
- Maps Windows services -> PID (when available) so "invisible" service-backed processes are obvious.
- Flags known offenders (RGB suites, overlays, VR runtimes, VPNs, vendor utilities) with reasons.
- Saves snapshots and diffs them to catch "what started itself".

It does NOT kill processes by default.

Install:
  pip install psutil

Usage examples:
  python gameprep.py top cpu --seconds 1.0 --limit 15 --non-windows
  python gameprep.py top io  --seconds 1.0 --limit 15 --non-windows
  python gameprep.py scan --sample 1.0
  python gameprep.py info 1234
  python gameprep.py snapshot baseline.json
  python gameprep.py diff baseline.json

Notes:
- Some process fields may be unavailable without admin rights; the script handles AccessDenied.
- CPU% is per-process across all cores (so >100% is possible).
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import json
import os
import re
import sys
import time
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

try:
    import psutil  # type: ignore
except Exception:
    print("ERROR: psutil is required. Install it with: pip install psutil", file=sys.stderr)
    raise


# ---------------------------
# Models
# ---------------------------

@dataclasses.dataclass(frozen=True)
class Proc:
    pid: int
    ppid: int
    name: str
    exe: str
    cmdline: Tuple[str, ...]
    username: str

    @property
    def haystack(self) -> str:
        parts = [self.name or "", self.exe or "", " ".join(self.cmdline or ())]
        return "\n".join([p for p in parts if p]).lower()

    @property
    def is_service_account(self) -> bool:
        u = (self.username or "").lower()
        return (
            "nt authority\\system" in u
            or "nt authority\\local service" in u
            or "nt authority\\network service" in u
            or u.endswith("\\system")
            or u.endswith("\\local service")
            or u.endswith("\\network service")
        )


@dataclasses.dataclass(frozen=True)
class Rule:
    id: str
    category: str
    severity: str  # "close", "caution", "info"
    reason: str
    matcher: Callable[[Proc], bool]


@dataclasses.dataclass
class Finding:
    proc: Proc
    severities: List[str]
    categories: List[str]
    reasons: List[str]

    @property
    def severity(self) -> str:
        order = {"close": 0, "caution": 1, "info": 2}
        return sorted(self.severities, key=lambda s: order.get(s, 99))[0] if self.severities else "info"


@dataclasses.dataclass
class Sample:
    pid: int
    cpu_percent: float
    rss_bytes: int
    read_bps: float
    write_bps: float


# ---------------------------
# Matching helpers
# ---------------------------

def _contains_any(*needles: str) -> Callable[[Proc], bool]:
    needles_l = [n.lower() for n in needles if n]

    def _m(p: Proc) -> bool:
        h = p.haystack
        return any(n in h for n in needles_l)

    return _m


def _name_is(*names: str) -> Callable[[Proc], bool]:
    names_l = {n.lower() for n in names if n}

    def _m(p: Proc) -> bool:
        return (p.name or "").lower() in names_l

    return _m


def _regex(pattern: str) -> Callable[[Proc], bool]:
    rx = re.compile(pattern, re.IGNORECASE)

    def _m(p: Proc) -> bool:
        return bool(rx.search(p.haystack))

    return _m


# ---------------------------
# Rule set (focused on your screenshots + common stutter offenders)
# ---------------------------

def build_rules() -> List[Rule]:
    rules: List[Rule] = []

    # MSI / RGB
    rules += [
        Rule(
            "msi_center",
            "rgb_vendor",
            "close",
            "MSI Center & related background services (polling/telemetry/RGB control).",
            _contains_any(
                "msi center",
                "msi.centralserver",
                "msi_center_service",
                "msi companion",
                "msi_case_service",
                "msi_lan_manager",
                "msi_oled_service",
                "msi true color",
                "gamingintelligence",
            ),
        ),
        Rule(
            "msi_mystic_light",
            "rgb_vendor",
            "close",
            "MSI Mystic Light services (RGB control/polling).",
            _contains_any("mystic_light_service", "mysticlightcontroller", "ledkeeper", "lightkeeperservice"),
        ),
        Rule(
            "dynamic_lighting",
            "rgb_vendor",
            "caution",
            "Dynamic Lighting / RGB translation services — close if you don't use them.",
            _contains_any("ite dynamiclighting", "lamparray translation", "dynamic lighting"),
        ),
    ]

    # Logitech
    rules += [
        Rule(
            "logitech_ghub",
            "peripherals",
            "caution",
            "Logitech G HUB background components (profiles/updates; close if you don't need live switching).",
            _contains_any("lghub", "g hub"),
        ),
        Rule(
            "logi_options",
            "peripherals",
            "caution",
            "Logi Options+ background components (close if you don't need features/macros while gaming).",
            _contains_any("logi options", "logioptions", "logi ai prompt builder"),
        ),
    ]

    # VR
    rules += [
        Rule(
            "oculus_ovr",
            "vr",
            "close",
            "Oculus/Meta VR runtime (OVR*) — close/disable if you're not using VR.",
            _contains_any("ovrserver", "ovr service", "ovr redir", "oculus", "meta quest remote desktop"),
        ),
    ]

    # VPN
    rules += [
        Rule(
            "nordvpn",
            "vpn",
            "caution",
            "NordVPN services — close if not needed during gaming.",
            _contains_any("nordvpn", "nordsec"),
        ),
    ]

    # AMD Radeon (iGPU / Adrenalin UI/overlay bits)
    rules += [
        Rule(
            "amd_radeon_overlay",
            "overlay",
            "caution",
            "AMD Radeon Settings / overlay components (not needed if you game on the RTX GPU).",
            _contains_any("radeon settings:", "desktop overlay", "amdrssrc", "amdrsserv", "amdrssrv", "amdrssrc"),
        ),
        Rule(
            "amd_adlx",
            "vendor_telemetry",
            "caution",
            "AMD ADLX service (Adrenalin SDK hooks).",
            _contains_any("adlx service"),
        ),
    ]

    # Overlays / capture / hooks
    rules += [
        Rule(
            "presentmon",
            "overlay",
            "close",
            "PresentMon (frametime capture) — close unless you're benchmarking.",
            _contains_any("presentmon_x64", "presentmon"),
        ),
        Rule(
            "rtss",
            "overlay",
            "caution",
            "RTSS (RivaTuner) — keep if you use it; avoid stacking multiple overlays.",
            _contains_any("rtss", "rivatuner"),
        ),
        Rule(
            "xbox_gamebar",
            "overlay",
            "caution",
            "Xbox Game Bar components — can hook into games; disable if you don't use it.",
            _contains_any("gamebarpresencewriter", "xbox app"),
        ),
        Rule(
            "steam_overlay",
            "overlay",
            "caution",
            "Steam overlay helper — disable Steam Overlay if you don't need it.",
            _contains_any("gameoverlayui.exe"),
        ),
        Rule(
            "nvidia_overlay",
            "overlay",
            "caution",
            "NVIDIA overlay/ShadowPlay components — disable if you don't use recording/instant replay.",
            _contains_any("shadowplay", "nvidia share", "nvsphelper", "nvidia app", "nvfvs", "nvcontainer"),
        ),
    ]

    # Common extras
    rules += [
        Rule(
            "bonjour",
            "network_misc",
            "caution",
            "Bonjour service (Apple discovery) — close if you don't use it.",
            _contains_any("bonjour service"),
        ),
        Rule(
            "powertoys",
            "utility",
            "caution",
            "PowerToys modules — close if you don't need them while gaming.",
            _contains_any("powertoys."),
        ),
        Rule(
            "widgets",
            "utility",
            "caution",
            "Windows Widgets runtime — close if you don't use widgets.",
            _contains_any("widgetsplatformruntime", "windows widgets", "spotify widget"),
        ),
        Rule(
            "phone_link",
            "utility",
            "caution",
            "Phone Link — close if you don't need it.",
            _contains_any("phone link"),
        ),
        Rule(
            "samsung_magician",
            "utility",
            "caution",
            "Samsung Magician service — close if you aren't using it.",
            _contains_any("samsungmagiciansvc"),
        ),
    ]

    return rules


# Guardrails: processes we will never *flag* as close/caution.
CRITICAL_NAMES = {
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


# ---------------------------
# Process collection
# ---------------------------

def list_processes() -> List[Proc]:
    out: List[Proc] = []
    for p in psutil.process_iter(attrs=["pid", "ppid", "name", "exe", "cmdline", "username"]):
        try:
            info = p.info
            out.append(
                Proc(
                    pid=int(info.get("pid") or 0),
                    ppid=int(info.get("ppid") or 0),
                    name=str(info.get("name") or ""),
                    exe=str(info.get("exe") or ""),
                    cmdline=tuple(info.get("cmdline") or ()),
                    username=str(info.get("username") or ""),
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue
    return out


def get_windows_service_pid_map() -> Dict[int, List[Dict[str, str]]]:
    """Map PID -> list of services. Only works on Windows. Safe no-op elsewhere."""
    pid_map: Dict[int, List[Dict[str, str]]] = {}

    # psutil exposes win_service_iter on Windows.
    it = getattr(psutil, "win_service_iter", None)
    if it is None:
        return pid_map

    try:
        for svc in it():
            try:
                pid = int(svc.pid())
            except Exception:
                continue
            if pid <= 0:
                continue
            try:
                name = str(svc.name())
            except Exception:
                name = ""
            try:
                display = str(svc.display_name())
            except Exception:
                display = ""
            try:
                status = str(svc.status())
            except Exception:
                status = ""
            pid_map.setdefault(pid, []).append(
                {"name": name, "display": display, "status": status}
            )
    except Exception:
        # If services API is blocked, just skip.
        return pid_map

    return pid_map


# ---------------------------
# Sampling CPU / RAM / IO
# ---------------------------

def _safe_proc(pid: int) -> Optional[psutil.Process]:
    try:
        return psutil.Process(pid)
    except Exception:
        return None


def sample_all(seconds: float) -> Dict[int, Sample]:
    """Sample CPU%, RSS, disk read/write rates for all processes."""
    seconds = float(seconds)
    seconds = 1.0 if seconds <= 0 else seconds

    procs: Dict[int, psutil.Process] = {}
    for p in psutil.process_iter(attrs=["pid"]):
        try:
            procs[int(p.info["pid"])] = p
        except Exception:
            continue

    # Prime CPU counters and capture IO baseline
    io0: Dict[int, Tuple[int, int]] = {}
    for pid, p in list(procs.items()):
        try:
            p.cpu_percent(interval=None)
        except Exception:
            pass
        try:
            io = p.io_counters()
            io0[pid] = (int(getattr(io, "read_bytes", 0)), int(getattr(io, "write_bytes", 0)))
        except Exception:
            io0[pid] = (0, 0)

    time.sleep(seconds)

    out: Dict[int, Sample] = {}
    for pid, p in list(procs.items()):
        try:
            cpu = float(p.cpu_percent(interval=None))
        except Exception:
            cpu = float("nan")
        try:
            rss = int(getattr(p.memory_info(), "rss", 0))
        except Exception:
            rss = 0
        try:
            io = p.io_counters()
            r1 = int(getattr(io, "read_bytes", 0))
            w1 = int(getattr(io, "write_bytes", 0))
            r0, w0 = io0.get(pid, (0, 0))
            read_bps = max(0.0, (r1 - r0) / seconds)
            write_bps = max(0.0, (w1 - w0) / seconds)
        except Exception:
            read_bps = 0.0
            write_bps = 0.0

        out[pid] = Sample(pid=pid, cpu_percent=cpu, rss_bytes=rss, read_bps=read_bps, write_bps=write_bps)

    return out


# ---------------------------
# Heuristics / formatting
# ---------------------------

def _format_bytes(n: Union[int, float]) -> str:
    try:
        f = float(n)
    except Exception:
        return ""
    if f < 0:
        f = 0
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    return f"{f:.1f} {units[i]}" if i else f"{int(f)} {units[i]}"


def _short_path(path: str, max_len: int = 48) -> str:
    if not path:
        return ""
    p = path.replace("/", "\\")
    if len(p) <= max_len:
        return p
    return "…" + p[-(max_len - 1) :]


def _origin(exe: str) -> str:
    """Best-effort origin classification for Windows."""
    if not exe:
        return "unknown"
    p = exe.replace("/", "\\")

    win_dir = os.environ.get("WINDIR", "C:\\Windows").replace("/", "\\")
    pf = os.environ.get("ProgramFiles", "C:\\Program Files").replace("/", "\\")
    pfx86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)").replace("/", "\\")

    p_low = p.lower()
    if p_low.startswith(win_dir.lower() + "\\"):
        return "windows"
    if p_low.startswith(pf.lower() + "\\") or p_low.startswith(pfx86.lower() + "\\"):
        return "program_files"
    if "\\appdata\\" in p_low:
        return "appdata"
    return "other"


def _matches_globish(text: str, patterns: List[str]) -> bool:
    """Simple case-insensitive substring/regex hybrid.

    - If pattern starts and ends with /.../ it is treated as regex.
    - Otherwise it's a case-insensitive substring.
    """
    t = (text or "").lower()
    for pat in patterns:
        if not pat:
            continue
        if len(pat) >= 2 and pat.startswith("/") and pat.endswith("/"):
            try:
                if re.search(pat[1:-1], text, flags=re.IGNORECASE):
                    return True
            except re.error:
                continue
        else:
            if pat.lower() in t:
                return True
    return False


# ---------------------------
# Scan (rules)
# ---------------------------

def apply_rules(procs: Sequence[Proc], rules: Sequence[Rule]) -> List[Finding]:
    findings: Dict[int, Finding] = {}

    for pr in procs:
        name_l = (pr.name or "").lower()
        if name_l in CRITICAL_NAMES:
            continue
        if os.path.basename(pr.exe or "").lower() in CRITICAL_NAMES:
            continue

        matched = [r for r in rules if r.matcher(pr)]
        if not matched:
            continue

        f = findings.get(pr.pid)
        if f is None:
            f = Finding(proc=pr, severities=[], categories=[], reasons=[])
            findings[pr.pid] = f

        for r in matched:
            if r.severity not in f.severities:
                f.severities.append(r.severity)
            if r.category not in f.categories:
                f.categories.append(r.category)
            if r.reason not in f.reasons:
                f.reasons.append(r.reason)

    return list(findings.values())


def overlay_stack_summary(procs: Sequence[Proc]) -> Dict[str, List[Proc]]:
    overlay_keys: Dict[str, Callable[[Proc], bool]] = {
        "RTSS": _contains_any("rtss", "rivatuner"),
        "SteamOverlay": _contains_any("gameoverlayui.exe"),
        "XboxGameBar": _contains_any("gamebarpresencewriter", "xbox game bar"),
        "NVIDIAOverlay": _contains_any("shadowplay", "nvidia share", "nvsphelper", "nvidia app"),
        "AMDRadeonOverlay": _contains_any("radeon settings:", "desktop overlay"),
        "PresentMon": _contains_any("presentmon"),
    }
    found: Dict[str, List[Proc]] = {k: [] for k in overlay_keys}
    for pr in procs:
        for k, m in overlay_keys.items():
            try:
                if m(pr):
                    found[k].append(pr)
            except Exception:
                pass
    return {k: v for k, v in found.items() if v}


def _print_findings(findings: List[Finding], samples: Optional[Dict[int, Sample]] = None, svc_map: Optional[Dict[int, List[Dict[str, str]]]] = None) -> None:
    sev_order = {"close": 0, "caution": 1, "info": 2}
    findings_sorted = sorted(findings, key=lambda f: (sev_order.get(f.severity, 99), f.proc.name.lower(), f.proc.pid))

    header = ["SEV", "PID", "TYPE", "ORIGIN", "CPU%", "MEM", "R/s", "W/s", "PROC", "SERVICE", "WHY"]
    rows: List[List[str]] = []

    for f in findings_sorted:
        pid = f.proc.pid
        typ = "service" if f.proc.is_service_account else "user"
        origin = _origin(f.proc.exe)

        cpu_s = mem_s = r_s = w_s = ""
        if samples and pid in samples:
            s = samples[pid]
            if s.cpu_percent == s.cpu_percent:
                cpu_s = f"{s.cpu_percent:.1f}"
            mem_s = _format_bytes(s.rss_bytes)
            r_s = _format_bytes(s.read_bps) + "/s" if s.read_bps else ""
            w_s = _format_bytes(s.write_bps) + "/s" if s.write_bps else ""

        svc = ""
        if svc_map and pid in svc_map:
            # show first service display name
            items = svc_map[pid]
            if items:
                disp = items[0].get("display") or items[0].get("name") or ""
                svc = disp[:36]

        why = " | ".join(f.reasons)
        rows.append([
            f.severity.upper(),
            str(pid),
            typ,
            origin,
            cpu_s,
            mem_s,
            r_s,
            w_s,
            f.proc.name,
            svc,
            why,
        ])

    # column widths
    col_w = [len(h) for h in header]
    for r in rows:
        for i, c in enumerate(r):
            col_w[i] = max(col_w[i], len(c))

    def row(cells: Sequence[str]) -> str:
        return "  ".join(cells[i].ljust(col_w[i]) for i in range(len(header)))

    print(row(header))
    print("  ".join("-" * w for w in col_w))
    for r in rows:
        print(row(r))


# ---------------------------
# TOP (resource-driven discovery)
# ---------------------------

def cmd_top(args: argparse.Namespace) -> int:
    procs = list_processes()
    proc_by_pid = {p.pid: p for p in procs}
    svc_map = get_windows_service_pid_map() if args.services else {}

    samples = sample_all(args.seconds)

    # build entries
    entries: List[Tuple[str, int, Proc, Sample]] = []

    for pid, s in samples.items():
        pr = proc_by_pid.get(pid)
        if not pr:
            continue

        # filters
        if args.non_windows:
            if _origin(pr.exe) == "windows":
                continue

        if args.exclude and _matches_globish(pr.haystack, args.exclude):
            continue

        if args.include and not _matches_globish(pr.haystack, args.include):
            continue

        metric = args.metric
        if metric == "cpu":
            key = s.cpu_percent
        elif metric == "mem":
            key = float(s.rss_bytes)
        elif metric == "io":
            key = float(s.read_bps + s.write_bps)
        else:
            key = s.cpu_percent

        entries.append((metric, int(key) if key == key else 0, pr, s))

    # sort desc by metric key
    if args.metric == "cpu":
        entries.sort(key=lambda t: (t[3].cpu_percent if t[3].cpu_percent == t[3].cpu_percent else -1), reverse=True)
    elif args.metric == "mem":
        entries.sort(key=lambda t: t[3].rss_bytes, reverse=True)
    elif args.metric == "io":
        entries.sort(key=lambda t: (t[3].read_bps + t[3].write_bps), reverse=True)

    entries = entries[: int(args.limit)]

    if args.json:
        payload = {
            "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
            "metric": args.metric,
            "seconds": float(args.seconds),
            "non_windows": bool(args.non_windows),
            "processes": [
                {
                    "pid": pr.pid,
                    "ppid": pr.ppid,
                    "name": pr.name,
                    "exe": pr.exe,
                    "cmdline": list(pr.cmdline),
                    "username": pr.username,
                    "type": "service" if pr.is_service_account else "user",
                    "origin": _origin(pr.exe),
                    "cpu_percent": s.cpu_percent,
                    "rss_bytes": s.rss_bytes,
                    "read_bps": s.read_bps,
                    "write_bps": s.write_bps,
                    "services": svc_map.get(pr.pid, []),
                }
                for _, __, pr, s in entries
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    header = ["PID", "TYPE", "ORIGIN", "CPU%", "MEM", "R/s", "W/s", "PROC", "SERVICE", "EXE"]
    rows: List[List[str]] = []

    for _, __, pr, s in entries:
        typ = "service" if pr.is_service_account else "user"
        origin = _origin(pr.exe)
        cpu = "" if s.cpu_percent != s.cpu_percent else f"{s.cpu_percent:.1f}"
        mem = _format_bytes(s.rss_bytes)
        r_s = _format_bytes(s.read_bps) + "/s" if s.read_bps else ""
        w_s = _format_bytes(s.write_bps) + "/s" if s.write_bps else ""

        svc = ""
        if args.services and pr.pid in svc_map:
            items = svc_map[pr.pid]
            if items:
                svc = (items[0].get("display") or items[0].get("name") or "")[:36]

        rows.append([
            str(pr.pid),
            typ,
            origin,
            cpu,
            mem,
            r_s,
            w_s,
            pr.name,
            svc,
            _short_path(pr.exe, 44),
        ])

    # widths
    col_w = [len(h) for h in header]
    for r in rows:
        for i, c in enumerate(r):
            col_w[i] = max(col_w[i], len(c))

    def row(cells: Sequence[str]) -> str:
        return "  ".join(cells[i].ljust(col_w[i]) for i in range(len(header)))

    print(row(header))
    print("  ".join("-" * w for w in col_w))
    for r in rows:
        print(row(r))

    print("\nNotes:")
    if args.metric == "cpu":
        print("- CPU% is per-process across all cores (so values >100% are possible).")
    if args.non_windows:
        print("- '--non-windows' hides core Windows processes so you can focus on vendor/background stuff.")
    if args.services:
        print("- 'SERVICE' column shows the first Windows Service bound to that PID (if any).")

    return 0


# ---------------------------
# INFO (explain one process)
# ---------------------------

def cmd_info(args: argparse.Namespace) -> int:
    procs = list_processes()
    svc_map = get_windows_service_pid_map()

    target: Optional[Proc] = None
    if args.target.isdigit():
        pid = int(args.target)
        target = next((p for p in procs if p.pid == pid), None)
    else:
        name_l = args.target.lower()
        # prefer exact name match; otherwise substring
        target = next((p for p in procs if (p.name or "").lower() == name_l), None)
        if target is None:
            target = next((p for p in procs if name_l in (p.name or "").lower()), None)

    if not target:
        print(f"No process found matching: {args.target}")
        return 1

    s = sample_all(args.seconds).get(target.pid)

    print(f"PID: {target.pid}")
    print(f"PPID: {target.ppid}")
    print(f"Name: {target.name}")
    print(f"Type: {'service' if target.is_service_account else 'user'}")
    print(f"Origin: {_origin(target.exe)}")
    print(f"User: {target.username}")
    print(f"EXE: {target.exe}")
    if target.cmdline:
        print("CMD:")
        for part in target.cmdline:
            print(f"  {part}")

    if s:
        cpu = "" if s.cpu_percent != s.cpu_percent else f"{s.cpu_percent:.1f}%"
        print(f"CPU ({args.seconds:.1f}s sample): {cpu}")
        print(f"RAM (RSS): {_format_bytes(s.rss_bytes)}")
        print(f"Disk Read: {_format_bytes(s.read_bps)}/s")
        print(f"Disk Write: {_format_bytes(s.write_bps)}/s")

    if target.pid in svc_map:
        print("Services:")
        for item in svc_map[target.pid]:
            n = item.get("name") or ""
            d = item.get("display") or ""
            st = item.get("status") or ""
            print(f"  - {n}  ({d})  [{st}]")

    # show parent (best effort)
    try:
        parent = next((p for p in procs if p.pid == target.ppid), None)
        if parent:
            print(f"Parent: {parent.pid} {parent.name} ({_short_path(parent.exe, 60)})")
    except Exception:
        pass

    return 0


# ---------------------------
# SCAN (rules-based)
# ---------------------------

def cmd_scan(args: argparse.Namespace) -> int:
    rules = build_rules()
    procs = list_processes()
    findings = apply_rules(procs, rules)
    overlays = overlay_stack_summary(procs)

    svc_map = get_windows_service_pid_map() if args.services else {}

    samples: Optional[Dict[int, Sample]] = None
    if args.sample is not None:
        # sample_all returns all; keep subset
        all_s = sample_all(float(args.sample))
        samples = {f.proc.pid: all_s.get(f.proc.pid, Sample(f.proc.pid, float('nan'), 0, 0.0, 0.0)) for f in findings}

    if args.json:
        payload = {
            "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
            "overlay_stack": {k: [{"pid": p.pid, "name": p.name, "exe": p.exe} for p in v] for k, v in overlays.items()},
            "findings": [
                {
                    "pid": f.proc.pid,
                    "ppid": f.proc.ppid,
                    "name": f.proc.name,
                    "exe": f.proc.exe,
                    "cmdline": list(f.proc.cmdline),
                    "username": f.proc.username,
                    "type": "service" if f.proc.is_service_account else "user",
                    "origin": _origin(f.proc.exe),
                    "severity": f.severity,
                    "categories": f.categories,
                    "reasons": f.reasons,
                    "sample": (dataclasses.asdict(samples[f.proc.pid]) if samples and f.proc.pid in samples else None),
                    "services": (svc_map.get(f.proc.pid) if svc_map else None),
                }
                for f in findings
            ],
        }
        print(json.dumps(payload, indent=2))
        return 0

    if overlays:
        overlay_list = ", ".join([f"{k}({len(v)})" for k, v in overlays.items()])
        total = sum(len(v) for v in overlays.values())
        print(f"Overlay/hooks detected: {overlay_list}  | total={total}")
        if total >= 2:
            print("Note: multiple overlays stack hooks and can contribute to stutter/audio crackle.\n")
    else:
        print("Overlay/hooks detected: none (by our signatures)\n")

    if not findings:
        print("No matches found from the built-in offender rules.")
        print("Tip: use 'top cpu --non-windows' and 'top io --non-windows' to discover what's actually consuming resources.")
        return 0

    _print_findings(findings, samples=samples, svc_map=svc_map)

    print("\nTips:")
    print("- CLOSE = usually safe to exit for gaming sessions.")
    print("- CAUTION = usually safe, but may disable device features (RGB/peripheral/VPN/overlays).")
    print("- Use: 'python gameprep.py info <pid>' to see what a process is, where it lives, and if it's a service.")

    return 0


# ---------------------------
# Snapshot / Diff
# ---------------------------

def cmd_snapshot(args: argparse.Namespace) -> int:
    procs = list_processes()
    snap = {
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "processes": sorted(
            [
                {
                    "pid": p.pid,
                    "ppid": p.ppid,
                    "name": p.name,
                    "exe": p.exe,
                    "cmdline": list(p.cmdline),
                    "username": p.username,
                }
                for p in procs
            ],
            key=lambda x: (str(x.get("name") or "").lower(), int(x.get("pid") or 0)),
        ),
    }
    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(snap, f, indent=2)
    print(f"Wrote snapshot: {args.path} ({len(snap['processes'])} processes)")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    with open(args.path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    base = baseline.get("processes", [])
    base_set = {(str(p.get("name") or "").lower(), str(p.get("exe") or "").lower()) for p in base}

    now = list_processes()
    now_set = {(p.name.lower(), (p.exe or "").lower()) for p in now}

    started = sorted(now_set - base_set)
    stopped = sorted(base_set - now_set)

    print(f"Baseline: {baseline.get('timestamp', 'unknown')}  | Now: {_dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"New process names since baseline: {len(started)}")
    for (name, exe) in started[:200]:
        print(f"  + {name}  ::  {_short_path(exe, 90)}")
    if len(started) > 200:
        print(f"  ... ({len(started) - 200} more)")

    print(f"\nMissing since baseline: {len(stopped)}")
    for (name, exe) in stopped[:200]:
        print(f"  - {name}  ::  {_short_path(exe, 90)}")
    if len(stopped) > 200:
        print(f"  ... ({len(stopped) - 200} more)")

    return 0


# ---------------------------
# CLI
# ---------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gameprep", description="Discover and flag background processes that can affect gaming performance.")
    sub = p.add_subparsers(dest="cmd", required=True)

    # top
    t = sub.add_parser("top", help="Show top resource-consuming processes (discovery mode).")
    t.add_argument("metric", choices=["cpu", "mem", "io"], help="Sort by cpu, mem (RSS), or io (read+write bytes/s).")
    t.add_argument("--seconds", type=float, default=1.0, help="Sampling window in seconds (for cpu/io). Default: 1.0")
    t.add_argument("--limit", type=int, default=15, help="Number of rows to show. Default: 15")
    t.add_argument("--non-windows", action="store_true", help="Hide processes whose EXE lives under the Windows directory.")
    t.add_argument("--include", action="append", default=[], help="Only show processes matching substring or regex /.../. Can repeat.")
    t.add_argument("--exclude", action="append", default=[], help="Hide processes matching substring or regex /.../. Can repeat.")
    t.add_argument("--services", action="store_true", help="Try to map Windows services to PIDs (adds SERVICE column).")
    t.add_argument("--json", action="store_true", help="Output JSON.")
    t.set_defaults(func=cmd_top)

    # scan
    s = sub.add_parser("scan", help="Flag known offender/background stacks with reasons (rules mode).")
    s.add_argument("--sample", type=float, default=None, help="Sample CPU/RAM/IO for matched processes over N seconds.")
    s.add_argument("--services", action="store_true", help="Try to map Windows services to PIDs.")
    s.add_argument("--json", action="store_true", help="Output JSON.")
    s.set_defaults(func=cmd_scan)

    # info
    i = sub.add_parser("info", help="Explain one process by PID or name (what it is + where it lives + resource usage).")
    i.add_argument("target", help="PID (e.g. 1234) or process name (e.g. OVRServer_x64.exe).")
    i.add_argument("--seconds", type=float, default=1.0, help="Sampling window in seconds. Default: 1.0")
    i.set_defaults(func=cmd_info)

    # snapshot/diff
    sn = sub.add_parser("snapshot", help="Save a snapshot of running processes to JSON (for later diff).")
    sn.add_argument("path", help="Output JSON path")
    sn.set_defaults(func=cmd_snapshot)

    d = sub.add_parser("diff", help="Diff current running processes vs a snapshot JSON.")
    d.add_argument("path", help="Baseline snapshot JSON")
    d.set_defaults(func=cmd_diff)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
