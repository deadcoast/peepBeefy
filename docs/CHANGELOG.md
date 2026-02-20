# CHANGELOG

## v0.0.4

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

## v0.0.3

## source code

[`entry-point`](.legacy/specs/v0.0.3/src/main.py)

---

## What it does (today, working)

- **Top resource consumers**: CPU%, RAM, disk read/write *rate* (sampled over time)
- **Shows “invisible” stuff**: maps PIDs to **Windows Services** (when possible), so you can see which background processes are actually services
- **Gamer-oriented tagging** (optional but built-in): RGB suites, overlays/hooks, VR runtimes, VPNs, vendor utilities, updaters, launchers
- **Snapshot + diff**: catch “what launched itself” between a clean state and “now”
- Safe by default: **no process killing** in this version (your “end process from menu” feature can layer on cleanly afterward)

It uses **Typer + Rich** for output/UI.

---

## Install requirements (on your Windows 11 box)

```powershell
py -m pip install psutil rich typer
```

Run it from the folder you downloaded it to:

```powershell
py .\gameprep.py --help
```

---

## The 4 commands you’ll actually use

### 1) “What’s clogging my system right now?” (CPU)

```powershell
py .\gameprep.py top cpu --seconds 1.0 --limit 25 --non-windows --services
```

### 2) “What’s causing stutter?” (Disk I/O is a huge culprit)

```powershell
py .\gameprep.py top io --seconds 1.0 --limit 25 --non-windows --services
```

### 3) “What background gamer clutter is running?” (RGB/overlay/VR/VPN/etc)

```powershell
py .\gameprep.py scan --seconds 0.8 --non-windows --services
```

### 4) “What is this thing?” (path/cmdline/parent/user/services + live rates)

```powershell
py .\gameprep.py info OVRServer_x64.exe
# or
py .\gameprep.py info 1234
```

---

## Catch “what started itself” (this directly addresses your Windows 11 complaint)

Take a baseline when things look clean:

```powershell
py .\gameprep.py snapshot baseline.json
```

Later, when you feel “stuff is running again”:

```powershell
py .\gameprep.py diff baseline.json
```

It will show **new processes** that appeared since the baseline.

---

## Notes that matter for your “hidden services” problem

- Startup Apps ≠ Services. A ton of vendor junk runs as **services** or **scheduled tasks**.
- This tool shows a **TYPE** column and (optionally) a **SERVICE** column so you can see the service mapping.
- For best visibility, run Windows Terminal **as Administrator** (not mandatory, but you’ll see more cmdlines/paths).

---

## Output for automation

Every main command supports `--json`:

```powershell
py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json
```

That’s useful for your next phase (interactive Rich/Typer menu + terminate).

---

## v0.0.2

I updated the CLI so it works in **discovery mode**: it will **surface whatever is actually consuming CPU / RAM / disk I/O**, including “invisible” background/service-backed stuff, without you curating a list first.

## Download the updated CLI

[Download gameprep.py](sandbox:/mnt/data/gameprep.py)

---

## 1) Show the top CPU users (hide Windows core stuff)

Run this **while the stutter is happening** (or while the game is running):

```powershell
python .\gameprep.py top cpu --seconds 1.0 --limit 20 --non-windows --services
```

What this does:

- samples CPU usage for 1 second
- lists top 20
- hides anything whose EXE is under `C:\Windows\...`
- adds a **SERVICE** column where possible (this is what makes “hidden” stuff less cryptic)

## 2) Show the top disk I/O users (common stutter cause)

```powershell
python .\gameprep.py top io --seconds 1.0 --limit 20 --non-windows --services
```

This catches “something is hammering the SSD” moments (indexing, update services, launchers, telemetry, etc.).

## 3) Show the top memory users (less likely to cause spikes, but useful)

```powershell
python .\gameprep.py top mem --seconds 1.0 --limit 20 --non-windows --services
```

---

## When you see something unfamiliar: explain it

If the `top` output shows a process you don’t recognize, run:

```powershell
python .\gameprep.py info 1234
```

(or by name)

```powershell
python .\gameprep.py info OVRServer_x64.exe
```

It prints:

- EXE path (where it lives)
- command line
- user/service account
- parent process
- CPU/RAM/Disk rates (sampled)
- mapped Windows services (if any)

This is the “what is this thing?” tool.

---

## Catch “what started itself” without guessing

Take a baseline when the system feels clean:

```powershell
python .\gameprep.py snapshot baseline.json
```

Later, after something feels off:

```powershell
python .\gameprep.py diff baseline.json
```

That shows **new processes** (by name + exe path) that appeared since the baseline.

---

## Bonus: rules-based “known offenders” list (optional)

This is separate from discovery mode. It flags common stacks (MSI Center/Mystic Light, Logitech, VR, VPN, overlays, PresentMon, etc.):

```powershell
python .\gameprep.py scan --sample 1.0 --services
```

---

peepBeefy: `DESTROYER_OF_FAT-PROCESSES_5000`

---
