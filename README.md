# v0.0.4: README.md

## Summary

Goal:
  Show gamers what's actually running and what is hogging CPU / RAM / Disk,
  including "invisible" service-backed processes that don't show in the taskbar.

Quick start (Windows 11):

- Install uv if you don't already have it:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Start the interactive CLI (zero typing):
> [Double-click RUN_peepBeefy.bat](install.bat)

Or from the terminal (run inside the root folder):

```powershell
beefy                # interactive mode
beefy peep all       # direct CLI
```

> uv handles Python and all dependencies automatically — no manual pip installs needed.

---

## Usage

```ps1
beefy peep all         # Quick Scan (recommended)
beefy peep io          # Disk hogs (stutter risk)
beefy peep cpu         # CPU hogs
beefy peep clutter     # Tagged gamer background stacks (RGB/VR/VPN/Overlays)
beefy baseline save    # save a baseline snapshot
beefy baseline diff    # see what started itself.
```

> [!NOTE]
> This version does NOT yet integrate the `trim fat` command option with the `--kill` flag to end processes.

## Develeoper Notes

### Version Control System

> ATTN: agents

```toml
[agents]
version_authority: false

[human]
version_authority: true
```

> [!NOTE]
> EXCEPTION: Up to and including v0.0.4, the source code WAS part of the documentation, as it was still contained. From v0.0.5 specifications the source code will be versioned separately, and github will be the primary version control system for the SOURCE CODE.

1. A legacy-spec-directory is created in the [specs-archive](\.legacy\specs\) with its working version as the directory title.
2. The new version will now take effect in the continued development of the ongoing project files.

---

peepBeefy: `FATBOI_PROCESSES_DESTROYER_5000`

---
