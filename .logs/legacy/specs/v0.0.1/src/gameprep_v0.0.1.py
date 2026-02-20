#!/usr/bin/env python3
"""
gameprep.py — A small CLI to identify non-essential background processes that often
impact gaming performance (overlays, RGB suites, VR runtimes, VPN clients, vendor utilities).

- It does NOT blindly kill processes.
- Default action is to print a prioritized "close list" with reasons.
- Optional: output JSON, sample CPU usage over a short window, save/compare snapshots.

Windows-focused, but works on Linux/macOS for basic process listing.

Usage:
  python gameprep.py scan
  python gameprep.py scan --json
  python gameprep.py scan --sample 1.0
  python gameprep.py snapshot baseline.json
  python gameprep.py diff baseline.json

Requirements:
  pip install psutil
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
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import psutil  # type: ignore
except Exception as e:
    print("ERROR: psutil is required. Install it with: pip install psutil", file=sys.stderr)
    raise


# ---------------------------
# Models
# ---------------------------

@dataclasses.dataclass(frozen=True)
class Proc:
    pid: int
    name: str
    exe: str
    cmdline: Tuple[str, ...]
    username: str

    @property
    def haystack(self) -> str:
        # Use a normalized string for matching
        parts = [self.name, self.exe, " ".join(self.cmdline)]
        return "\n".join([p for p in parts if p]).lower()

    @property
    def is_service_account(self) -> bool:
        u = (self.username or "").lower()
        return ("nt authority\\system" in u) or ("nt authority\\local service" in u) or ("nt authority\\network service" in u) \
               or (u.endswith("\\system")) or (u.endswith("\\local service")) or (u.endswith("\\network service"))


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
        # Highest severity wins: close > caution > info
        order = {"close": 0, "caution": 1, "info": 2}
        return sorted(self.severities, key=lambda s: order.get(s, 99))[0] if self.severities else "info"

    @property
    def category(self) -> str:
        return self.categories[0] if self.categories else "other"


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
        return p.name.lower() in names_l
    return _m


def _regex(pattern: str) -> Callable[[Proc], bool]:
    rx = re.compile(pattern, re.IGNORECASE)
    def _m(p: Proc) -> bool:
        return bool(rx.search(p.haystack))
    return _m


# ---------------------------
# Rule set (focused on your screenshot + common gaming offenders)
# ---------------------------

def build_rules() -> List[Rule]:
    rules: List[Rule] = []

    # RGB / vendor control suites (MSI)
    rules += [
        Rule("msi_center", "rgb_vendor", "close",
             "MSI Center & related background services (polling/telemetry/RGB control).",
             _contains_any("msi center", "msi.centralserver", "msi_center_service", "msi companion", "msi_case_service",
                           "msi_lan_manager", "msi_oled_service", "msi true color", "gamingintelligence")),
        Rule("msi_mystic_light", "rgb_vendor", "close",
             "MSI Mystic Light services (RGB control/polling).",
             _contains_any("mystic_light_service", "mysticlightcontroller", "ledkeeper", "lightkeeperservice")),
        Rule("dynamic_lighting", "rgb_vendor", "caution",
             "Windows/third-party Dynamic Lighting services — can be closed if you don't use them.",
             _contains_any("ite dynamiclighting", "lamparray translation", "dynamic lighting")),
    ]

    # Logitech / peripheral suites
    rules += [
        Rule("logitech_ghub", "peripherals", "caution",
             "Logitech G HUB background components (profiles/updates; can be closed if you don't need live switching).",
             _contains_any("lghub", "g hub")),
        Rule("logi_options", "peripherals", "caution",
             "Logi Options+ background components (can be closed if you don't need features/macros while gaming).",
             _contains_any("logi options", "logioptions", "logi ai prompt builder")),
    ]

    # VR runtimes
    rules += [
        Rule("oculus_ovr", "vr", "close",
             "Oculus/Meta VR runtime (OVR*) — close/disable if you're not using VR.",
             _contains_any("ovrserver", "ovr service", "ovr redir", "oculus", "meta quest remote desktop")),
    ]

    # VPN
    rules += [
        Rule("nordvpn", "vpn", "caution",
             "NordVPN services — can add network/driver overhead; close if not needed for gaming.",
             _contains_any("nordvpn", "nordsec")),
    ]

    # AMD Radeon software stack (from iGPU / Adrenalin)
    # Note: Do NOT recommend removing AMD chipset drivers; this only flags the graphics UI/overlay stack.
    rules += [
        Rule("amd_radeon_overlay", "overlay", "caution",
             "AMD Radeon Settings / overlay components (not needed if you game on the RTX GPU).",
             _contains_any("radeon settings:", "amdrssrc", "amdow", "amdrsserv", "amdrssrv", "desktop overlay")),
        Rule("amd_adlx", "vendor_telemetry", "caution",
             "AMD ADLX service (Adrenalin SDK/telemetry hooks).",
             _contains_any("adlx service")),
    ]

    # Overlays / capture / frametime tools
    rules += [
        Rule("presentmon", "overlay", "close",
             "PresentMon (frametime capture) — close unless you're actively benchmarking.",
             _contains_any("presentmon_x64", "presentmon")),
        Rule("rtss", "overlay", "caution",
             "RTSS (RivaTuner overlay / frame limiter). Keep if you use it; avoid stacking multiple overlays.",
             _contains_any("rtss", "rivatuner")),
        Rule("xbox_gamebar", "overlay", "caution",
             "Xbox Game Bar components — can hook into games; disable if you don't use it.",
             _contains_any("gamebarpresencewriter", "xbox game bar", "xbox app")),
        Rule("steam_overlay", "overlay", "caution",
             "Steam overlay helper — disable Steam Overlay if you don't need it.",
             _contains_any("gameoverlayui.exe")),
        Rule("nvidia_overlay", "overlay", "caution",
             "NVIDIA overlay/ShadowPlay components — disable if you don't use recording/instant replay.",
             _contains_any("shadowplay", "nvidia share", "nvsphelper", "nvidia app", "nvfvs")),
    ]

    # Creative Cloud / content suites (optional)
    rules += [
        Rule("adobe_cc", "utility", "caution",
             "Adobe Creative Cloud background engine — close if you don't need it while gaming.",
             _contains_any("cc engine", "creative cloud")),
    ]

# Misc common background extras (safe-ish to close)
    rules += [
        Rule("bonjour", "network_misc", "caution",
             "Bonjour service (Apple discovery) — close if you don't use iTunes/AirPlay/AirPrint workflows.",
             _contains_any("bonjour service")),
        Rule("powertoys", "utility", "caution",
             "PowerToys modules — close if you don't need them while gaming.",
             _contains_any("powertoys.")),
        Rule("spotify_widget", "utility", "caution",
             "Spotify widget/background — close if not needed.",
             _contains_any("spotify widget")),
        Rule("samsung_magician", "utility", "caution",
             "Samsung Magician service — close if not actively using it.",
             _contains_any("samsungmagiciansvc")),
        Rule("phone_link", "utility", "caution",
             "Phone Link — close if not needed.",
             _contains_any("phone link")),
        Rule("windows_widgets", "utility", "caution",
             "Windows Widgets runtime — close if you don't use widgets.",
             _contains_any("widgetsplatformruntime", "windows widgets")),
    ]

    return rules


# Some things we NEVER recommend touching (basic guardrail).
# We keep this short and conservative; the rule set above is already specific.
CRITICAL_EXE = {
    "system", "system idle process", "csrss.exe", "wininit.exe", "winlogon.exe", "services.exe",
    "lsass.exe", "smss.exe", "svchost.exe", "dwm.exe", "explorer.exe", "audiodg.exe",
    "conhost.exe", "fontdrvhost.exe", "wudfhost.exe", "registry",
}


def list_processes() -> List[Proc]:
    procs: List[Proc] = []
    for p in psutil.process_iter(attrs=["pid", "name", "exe", "cmdline", "username"]):
        try:
            info = p.info
            name = info.get("name") or ""
            exe = info.get("exe") or ""
            cmdline = tuple(info.get("cmdline") or ())
            username = info.get("username") or ""
            procs.append(Proc(pid=int(info["pid"]), name=name, exe=exe, cmdline=cmdline, username=username))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue
    return procs


def apply_rules(procs: Sequence[Proc], rules: Sequence[Rule]) -> List[Finding]:
    findings: Dict[int, Finding] = {}
    for pr in procs:
        # Avoid flagging core OS processes by accident
        if pr.name.lower() in CRITICAL_EXE:
            continue
        if os.path.basename(pr.exe or "").lower() in CRITICAL_EXE:
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
    # Lightweight overlay detection (helps explain stutters)
    overlay_keys: Dict[str, Callable[[Proc], bool]] = {
        "RTSS": _contains_any("rtss", "rivatuner"),
        "SteamOverlay": _contains_any("gameoverlayui.exe"),
        "XboxGameBar": _contains_any("gamebarpresencewriter", "xbox game bar"),
        "NVIDIAOverlay": _contains_any("shadowplay", "nvidia share", "nvsphelper", "nvidia app"),
        "AMDRadeonOverlay": _contains_any("radeon settings:", "desktop overlay"),
        "PresentMon": _contains_any("presentmon"),
        "DiscordOverlay": _contains_any("discord", "overlayhook"),
    }
    found: Dict[str, List[Proc]] = {k: [] for k in overlay_keys}
    for pr in procs:
        for k, m in overlay_keys.items():
            try:
                if m(pr):
                    found[k].append(pr)
            except Exception:
                pass
    # Drop empties
    return {k: v for k, v in found.items() if v}


def _format_bytes(n: Optional[int]) -> str:
    if n is None:
        return ""
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    i = 0
    while f >= 1024 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    if i == 0:
        return f"{int(f)} {units[i]}"
    return f"{f:.1f} {units[i]}"


def _safe_proc_handle(pid: int):
    try:
        return psutil.Process(pid)
    except Exception:
        return None


def sample_usage(findings: List[Finding], sample_seconds: float) -> Dict[int, Dict[str, float]]:
    """
    Returns per-pid dict with cpu_percent and rss_bytes (rss is an instantaneous reading).
    CPU percent is sampled over sample_seconds.
    """
    handles = {f.proc.pid: _safe_proc_handle(f.proc.pid) for f in findings}
    handles = {pid: h for pid, h in handles.items() if h is not None}

    # Prime cpu_percent
    for h in handles.values():
        try:
            h.cpu_percent(interval=None)
        except Exception:
            pass

    time.sleep(max(0.1, float(sample_seconds)))

    out: Dict[int, Dict[str, float]] = {}
    for pid, h in handles.items():
        try:
            cpu = float(h.cpu_percent(interval=None))
        except Exception:
            cpu = float("nan")
        try:
            rss = float(getattr(h.memory_info(), "rss", 0))
        except Exception:
            rss = float("nan")
        out[pid] = {"cpu_percent": cpu, "rss_bytes": rss}
    return out


def print_findings(findings: List[Finding], sampled: Optional[Dict[int, Dict[str, float]]] = None) -> None:
    # Sort: severity then category then name
    sev_order = {"close": 0, "caution": 1, "info": 2}
    findings_sorted = sorted(
        findings,
        key=lambda f: (sev_order.get(f.severity, 99), f.category, f.proc.name.lower(), f.proc.pid)
    )

    # Build rows
    rows: List[List[str]] = []
    header = ["SEV", "CATEGORY", "PID", "TYPE", "PROCESS", "CPU%", "MEM", "REASON(S)"]
    for f in findings_sorted:
        pid = f.proc.pid
        proc_type = "service" if f.proc.is_service_account else "user"
        cpu_s = ""
        mem_s = ""
        if sampled and pid in sampled:
            cpu = sampled[pid].get("cpu_percent", float("nan"))
            rss = sampled[pid].get("rss_bytes", float("nan"))
            if cpu == cpu:  # not nan
                cpu_s = f"{cpu:.1f}"
            if rss == rss:
                mem_s = _format_bytes(int(rss))
        reasons = " | ".join(f.reasons)
        rows.append([f.severity.upper(), f.category, str(pid), proc_type, f.proc.name, cpu_s, mem_s, reasons])

    # Pretty print without external deps
    col_widths = [len(h) for h in header]
    for r in rows:
        for i, cell in enumerate(r):
            col_widths[i] = max(col_widths[i], len(cell))

    def _line(char: str = "-") -> str:
        return "+".join(char * (w + 2) for w in col_widths)

    def _row(cells: Sequence[str]) -> str:
        return " | ".join(cells[i].ljust(col_widths[i]) for i in range(len(header)))

    print(_row(header))
    print(_line("-"))
    for r in rows:
        print(_row(r))


def cmd_scan(args: argparse.Namespace) -> int:
    rules = build_rules()
    procs = list_processes()
    findings = apply_rules(procs, rules)

    overlays = overlay_stack_summary(procs)

    sampled = None
    if args.sample is not None:
        sampled = sample_usage(findings, float(args.sample))

    if args.json:
        payload = {
            "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
            "host": {"platform": platform_string()},
            "overlay_stack": {
                k: [{"pid": p.pid, "name": p.name, "exe": p.exe} for p in v] for k, v in overlays.items()
            },
            "findings": [
                {
                    "pid": f.proc.pid,
                    "name": f.proc.name,
                    "exe": f.proc.exe,
                    "username": f.proc.username,
                    "type": "service" if f.proc.is_service_account else "user",
                    "severity": f.severity,
                    "categories": f.categories,
                    "reasons": f.reasons,
                    "cpu_percent": (sampled.get(f.proc.pid, {}).get("cpu_percent") if sampled else None),
                    "rss_bytes": (sampled.get(f.proc.pid, {}).get("rss_bytes") if sampled else None),
                }
                for f in sorted(findings, key=lambda x: x.severity)
            ],
        }
        print(json.dumps(payload, indent=2))
    else:
        if overlays:
            overlay_list = ", ".join([f"{k}({len(v)})" for k, v in overlays.items()])
            count = sum(len(v) for v in overlays.values())
            print(f"Overlay/hooks detected: {overlay_list}  | total={count}")
            if count >= 2:
                print("Note: multiple overlays can stack hooks and contribute to stutter/audio crackle. Consider using only one.\n")
        else:
            print("Overlay/hooks detected: none (by our signatures)\n")

        if not findings:
            print("No matches found from the built-in rule set.")
            return 0

        print_findings(findings, sampled=sampled)

        print("\nTips:")
        print("- 'CLOSE' = usually safe to exit for gaming sessions.")
        print("- 'CAUTION' = safe for many people, but may disable device features (RGB/peripheral profiles/VPN/overlays).")
        print("- To customize, edit the RULES in gameprep.py (search for build_rules()).")

    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    procs = list_processes()
    snapshot = {
        "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
        "host": {"platform": platform_string()},
        "processes": sorted(
            [{"pid": p.pid, "name": p.name, "exe": p.exe, "cmdline": list(p.cmdline), "username": p.username} for p in procs],
            key=lambda x: (x["name"].lower(), x["pid"])
        ),
    }
    with open(args.path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Wrote snapshot: {args.path} ({len(snapshot['processes'])} processes)")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    with open(args.path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    base_names = {(p.get("name") or "").lower() for p in baseline.get("processes", [])}
    now = list_processes()
    now_names = {(p.name or "").lower() for p in now}

    started = sorted(now_names - base_names)
    stopped = sorted(base_names - now_names)

    print(f"Baseline: {baseline.get('timestamp', 'unknown')}  | Now: {_dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"New process names since baseline: {len(started)}")
    for n in started[:200]:
        print(f"  + {n}")
    if len(started) > 200:
        print(f"  ... ({len(started)-200} more)")

    print(f"\nMissing process names since baseline: {len(stopped)}")
    for n in stopped[:200]:
        print(f"  - {n}")
    if len(stopped) > 200:
        print(f"  ... ({len(stopped)-200} more)")
    return 0


def platform_string() -> str:
    try:
        import platform
        return f"{platform.system()} {platform.release()} ({platform.version()})"
    except Exception:
        return sys.platform


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gameprep",
        description="Detect common background processes that often impact gaming performance (Windows-focused)."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("scan", help="Scan running processes and print recommended close list.")
    s.add_argument("--json", action="store_true", help="Output results as JSON.")
    s.add_argument("--sample", type=float, default=None,
                   help="Sample CPU usage for matched processes over N seconds (e.g. 1.0).")
    s.set_defaults(func=cmd_scan)

    sn = sub.add_parser("snapshot", help="Save a snapshot of running processes to a JSON file.")
    sn.add_argument("path", help="Path to write snapshot JSON.")
    sn.set_defaults(func=cmd_snapshot)

    d = sub.add_parser("diff", help="Compare current processes to a snapshot JSON (by process name).")
    d.add_argument("path", help="Path to baseline snapshot JSON.")
    d.set_defaults(func=cmd_diff)

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
