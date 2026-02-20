# v0.0.4: README.md

## Summary

Goal:
  Show gamers what's actually running and what is hogging CPU / RAM / Disk,
  including "invisible" service-backed processes that don't show in the taskbar.

Quick start (Windows 11):

- Install Python 3 (from python.org) if you don't already have it.
- Install dependencies once:

```powershell
py -m pip install --user psutil rich typer # installs the python dependencies for peepBeefy
```

Start the interactive CLI (zero typing):
> [Double-click-RUN_peepBeefy.bat](RUN_peepBeefy.bat)

Alternatively from the CLI:
- Run the cli from the terminal(ensure run inside the root folder):

```powershell
beefy # call the application directly in the terminal
```

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

---

peepBeefy: `TRIM THE FAT, KILL THE PROCESSES`

---
