# v0.0.4: peepBeefy Overview

**v0.0.4** as an **interactive Rich/Typer CLI** named **peepBeefy**, with the **`beefy` → `peep`** command scheme baked into the interactive menu so new users don’t need to memorize flags.

## Previous Specs

- [v0.0.1:](specs/v0.0.1/)
- [v0.0.2:](specs/v0.0.2/)
- [v0.0.3:](specs/v0.0.3/)

Inside the zip:

- `peepBeefy.py` (the app)
- `RUN_peepBeefy.bat` (double-click launcher, **no typing**)
- `beefy.cmd` and `peepBeefy.cmd` (short commands from the same folder)
- `README_peepBeefy.txt`

---

## What this version does (core purpose)

**It identifies and displays what’s running and what’s “clogging” the system**, gamer-oriented:

- samples **CPU%**, **RAM**, **Disk Read/s**, **Disk Write/s**
- computes a combined **BEEF score** (weights disk spikes heavily because stutter)
- shows whether a process is likely a **Service** (the “hidden” stuff)
- maps **PID → Windows Service(s)** when possible (so you can see *what* that background process is hosting)
- tags common gamer clutter stacks: **RGB, overlays, VR, VPN, updaters, monitoring, audio enhancements**, etc.
- includes **baseline save/diff** to catch “what started itself” between “clean” and “now”

✅ **No placeholders**: the scanning, sampling, scoring, tagging, and service-mapping logic is implemented and working.

🚫 **No process killing yet** (as per your shelved feature plan). This version is visibility-first.

---

## One-time setup (required)

Run this once (PowerShell):

```powershell
py -m pip install --user psutil rich typer
```

---

## Launch options (rookie-friendly)

### Option A: Zero typing

Double-click:

- `RUN_peepBeefy.bat`

This opens the interactive CLI directly.

### Option B: Minimal typing (still beginner-friendly)

Open a terminal in the folder and run:

```powershell
beefy
```

---

## Interactive CLI design (CLI03)

When it opens, it shows a menu of **commands you can type exactly as shown**, e.g.:

- `beefy peep all`  → quick scan (recommended)
- `beefy peep io`   → disk hogs (stutter risk)
- `beefy peep cpu`  → CPU hogs
- `beefy peep mem`  → RAM hogs
- `beefy peep clutter` → tagged gamer clutter (RGB/VR/VPN/Overlays/etc.)
- `beefy peep watch` → live-refresh scoreboard
- `beefy baseline save` / `beefy baseline diff` → “what started itself?”

**Important detail for your spec:**
Inside the interactive CLI, you can type the *same* commands you’d type in the shell (`beefy …`). The app strips the `beefy` prefix internally so the command scheme stays consistent and teaches users CLI-only usage over time.

---

## CLI-only scheme (CLI02)

If/when users graduate from the interactive menu, they can run:

```powershell
beefy peep all
beefy peep io
beefy peep cpu
beefy peep clutter
```

Defaults are gamer-friendly (no flag soup).

---

## Dev-spec retained (CLI01)

For power users / your future development work, dev mode exists:

- `beefy dev dump` → full JSON dump (for building future “trim” safely)
- `beefy dev top cpu|io|mem|beef` → explicit metric tops with dev defaults
- `beefy dev info <PID or name>` → explain a process (path/cmdline/services + sampled metrics)

This is meant to remain the “source of truth” for logic and introspection while the branded scheme stays human-friendly.

---

## What you should do next (fast validation)

1. Launch `RUN_peepBeefy.bat`
2. Press Enter (defaults to `beefy peep all`)
3. Then run `beefy peep io` and see if anything is doing unexpected disk activity
4. If something looks cryptic, use:

   - `beefy dev info <pid>` (or process name)

If you want, paste a screenshot of the **peepBeefy Quick Scan table** (not Task Manager). I’ll tell you which entries are “expected background” vs “worth investigating,” *based on the actual resource rates it reports*.

---

peepBeefy: `TRIM THE FAT, KILL THE PROCESSES`

---
