# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is peepBeefy?

A Windows 11 CLI tool that helps gamers see what's running and what's hogging CPU/RAM/Disk, including "invisible" service-backed processes. The audience is gamers who are mostly opening a terminal for the first time — not developers.

## Running the app

```powershell
uv run src/main.py              # interactive mode (default)
uv run src/main.py peep all     # direct CLI command
```

The `.cmd` wrappers (`beefy.cmd`, `peepBeefy.cmd`) and `RUN_peepBeefy.bat` are user-facing launchers that call `uv run src/main.py`. Python 3.11 is pinned via `.python-version`. `uv` manages all dependencies — no manual pip installs.

## Type checking

```powershell
uv run mypy src/main.py
```

There is no test suite, no pytest config, and no Python linter config (ruff/flake8/pylint).

## Architecture

**Single-file application.** All logic lives in `src/main.py` (~1176 lines). There are no submodules or internal packages.

### Three-layer CLI design (critical invariant)

| Layer | Name | Entry | Audience |
|-------|------|-------|----------|
| CLI01 | Dev-spec | `beefy dev ...` | Developers / power users |
| CLI02 | peepBeefy shell | `beefy peep ...`, `beefy baseline ...` | Gamers who can type short commands |
| CLI03 | Interactive | `beefy` (no args) | First-time terminal users |

CLI03 is a menu-driven REPL that teaches CLI02 commands by displaying them as selectable options. CLI01 is the operational source-of-truth underneath. **Interactive mode MUST be the default when no subcommand is given** (invariant INV01).

### Typer app hierarchy

```plaintext
app (main)
├── peep_app ("peep") — peep all | cpu | io | mem | clutter | watch
├── baseline_app ("baseline") — baseline save | diff
└── dev_app ("dev") — dev dump | info | top {cpu,io,mem,beef}
```

### Core data pipeline

1. `collect_samples()` — primes CPU% via psutil, sleeps for sampling window, computes delta IO rates, builds `ProcRow` list
2. `get_services_by_pid()` — maps Windows service PIDs via `psutil.win_service_iter()`
3. `match_tags()` — applies regex `TAG_RULES` against name/exe/cmdline to classify processes (overlay, RGB, VR, VPN, etc.)
4. `compute_beef_score()` — weighted formula: `cpu * 2.0 + io_mb_s * 8.0 + ram_mb / 250.0` (disk spikes weighted heavily for stutter relevance)
5. `render_rows()` / `build_table()` — Rich tables with color-coded metrics
6. `interactive_loop()` — the CLI03 REPL dispatching to the same underlying functions

### Key data structures

- `ProcRow` dataclass: pid, name, exe, username, cpu_pct, rss_bytes, read_bps, write_bps, beef_score, kind, tags, services, cmdline
- `ServiceInfo` dataclass: name, display_name, start_type, status

## Design constraints (from ASOT.md and contract)

- **Visibility-first phase.** No process termination/kill features. The `trim`/`kill` command is explicitly shelved until safety guardrails are designed. Do not add it or expose it in help text.
- **Interactive-first UX.** The default experience must be menu-driven and guided. Minimal typing required. Output must use color and visual hierarchy — not "developer metric-spam."
- **Command mirroring.** Interactive menus must display the corresponding CLI02 command for each action, teaching users progression from interactive to CLI usage.
- **Windows-primary.** Uses `psutil.win_service_iter()`, Windows path detection, etc. Non-Windows gets empty service maps but core sampling still works.

## Key files

| File | Purpose |
|------|---------|
| `src/main.py` | Entire application |
| `docs/absolute-source-of-truth/ASOT.md` | Canonical product/UX/architecture contract — consult before any architectural changes |
| `docs/overview.md` | Feature spec, design rules (TSN/TSH), JSON rule glossary |
| `peepbeefy_contract.json` | Machine-readable design invariants and acceptance checks |
| `docs/shelved_features.md` | Planned but not-yet-built features |
| `docs/CHANGELOG.md` | Version history |

## Version notes

- `pyproject.toml` says version `0.0.4`; `src/main.py` has `VERSION = "0.0.3"` (version string in source hasn't been bumped yet)
- The package name in `pyproject.toml` is `milky-games` (publisher name), but the product is called `peepBeefy` everywhere
- Agents do NOT have version authority — only the human bumps versions (see README "Developer Notes")
