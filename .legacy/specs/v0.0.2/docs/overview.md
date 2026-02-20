# Overview

## Download the updated CLI

[Download gameprep.py](sandbox:/mnt/data/gameprep.py)

---

## 1) Show the top CPU users (hide Windows core stuff)

Run this **while the stutter is happening** (or while the game is running):

```powershell
python .\gameprep.py top cpu --seconds 1.0 --limit 20 --non-windows --services
```

What this does:

* samples CPU usage for 1 second
* lists top 20
* hides anything whose EXE is under `C:\Windows\...`
* adds a **SERVICE** column where possible (this is what makes “hidden” stuff less cryptic)

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

* EXE path (where it lives)
* command line
* user/service account
* parent process
* CPU/RAM/Disk rates (sampled)
* mapped Windows services (if any)

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

## What I need from you to make this extremely effective

Run **one** of these while ARC Raiders is running:

```powershell
python .\gameprep.py top cpu --seconds 1.0 --limit 25 --non-windows --services
```

Paste the output here (just the text).
Then I can tell you exactly which entries are “leave it” vs “safe to close for gaming” **based on what’s actually using resources on your box**, without you needing to guess.
