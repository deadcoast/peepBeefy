# CHANGELOG

## v0.0.2

I updated the CLI so it works in **discovery mode**: it will **surface whatever is actually consuming CPU / RAM / disk I/O**, including “invisible” background/service-backed stuff, without you curating a list first.

## v0.0.3

## source code

[`entry-point`](src/main.py)

---

## What it does (today, working)

* **Top resource consumers**: CPU%, RAM, disk read/write *rate* (sampled over time)
* **Shows “invisible” stuff**: maps PIDs to **Windows Services** (when possible), so you can see which background processes are actually services
* **Gamer-oriented tagging** (optional but built-in): RGB suites, overlays/hooks, VR runtimes, VPNs, vendor utilities, updaters, launchers
* **Snapshot + diff**: catch “what launched itself” between a clean state and “now”
* Safe by default: **no process killing** in this version (your “end process from menu” feature can layer on cleanly afterward)

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

* Startup Apps ≠ Services. A ton of vendor junk runs as **services** or **scheduled tasks**.
* This tool shows a **TYPE** column and (optionally) a **SERVICE** column so you can see the service mapping.
* For best visibility, run Windows Terminal **as Administrator** (not mandatory, but you’ll see more cmdlines/paths).

---

## Output for automation

Every main command supports `--json`:

```powershell
py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json
```

That’s useful for your next phase (interactive Rich/Typer menu + terminate).

---

If you want the next iteration after you try it once: I can add a **single-screen “watch” mode** (live updating table every N seconds) using Rich’s live rendering, still keeping it aligned with the purpose (visibility, not fluff).
