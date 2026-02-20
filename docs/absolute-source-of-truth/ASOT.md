# peepBeefy Source of Truth

**Document type:** Product + UX + Architecture “contract” (chat-derived)
**Scope:** Everything agreed so far about purpose, audience, UX, command language, output standards, safety boundaries, and planned evolution—written to stay stable across revisions.

---

## 0) Why this document exists

This is the **canonical reference** you can point to after refactors, renames, new versions, or feature additions to answer:

* *What is peepBeefy supposed to do?*
* *Who is it for?*
* *What UX constraints are non-negotiable?*
* *What is the layering of interactive vs CLI-only vs dev-spec?*
* *What is “done” for the current phase and what is explicitly shelved?*

It is **not a repeat** of previous writeups; it is a **contract** that prevents drift.

---

## 1) Product definition

### 1.1 One-sentence purpose

**peepBeefy helps gamers quickly see what’s running and what’s heavy (CPU/RAM/Disk/overlay/service clutter), in a way that is readable and usable even if they’re opening a terminal for the first time.**

### 1.2 The real problem being solved

Modern Windows systems accumulate:

* background vendor utilities (often as services),
* overlays and monitoring hooks,
* auto-updaters and helper processes,
* VR/VPN/audio stacks,

…that **do not present as “startup apps”** and often **don’t show in the taskbar**. This creates a “cryptic” system where users cannot easily answer:

* “What’s running?”
* “What’s heavy?”
* “What changed since yesterday?”
* “What should I close before gaming?”

peepBeefy exists to make that visible and actionable.

---

## 2) Audience contract

### 2.1 Primary audience

**Gamers** who are generally PC-capable but **not developers**.

### 2.2 UX consequence

The app must treat “opening a terminal” as already a hurdle. Therefore:

* **The default experience must be interactive** and guided.
* **Minimal typing** is required for primary tasks.
* The UI must be **visually legible** (color + layout + progressive disclosure) so it doesn’t feel like an overwhelming debug tool.

---

## 3) Experience layers

peepBeefy is explicitly a **3-layer experience**, with progressive learning baked in.

### 3.1 Layer A: CLI01 (Developer / “source-of-truth operations”)

* Exists as the **logic and introspection foundation**.
* May expose full parameters and raw outputs.
* Used for debugging, testing, power users, and to anchor correctness.

### 3.2 Layer B: CLI02 (“peepBeefy command scheme”)

* A **human-friendly command vocabulary** that maps cleanly onto CLI01 logic.
* Designed to be easier than dev-spec while still runnable from shell.
* Acts as the **bridge** between interactive-first users and advanced usage.

### 3.3 Layer C: CLI03 (Interactive-first experience)

* **Default entry** for new users.
* Menu-driven, guided, and “over-developed” for QoL.
* Teaches CLI02 commands by showing them as the choices (users learn by repetition).

**Invariant:** CLI03 should not be a totally separate app; it should be a front-end that triggers the same underlying actions as CLI01, and it should teach CLI02.

---

## 4) Brand language and command vocabulary contract

### 4.1 Naming intent

The brand language is not cosmetic; it is a usability tool. The vocabulary must be consistent in:

* menu options,
* help text,
* CLI-only commands,
* documentation.

### 4.2 Command “shape”

* There is a **single “main entry”** concept (e.g., `beefy`), which starts either:

  * the interactive menu (default), or
  * a direct command when supplied.
* “peep” is the primary verb for visibility/discovery operations.

### 4.3 Design requirement for interactive menus

Menu selections should:

* display the corresponding **peepBeefy command** (not just “1/2/3”),
* allow selection by typing the command (to teach CLI02 organically),
* still allow simple selection patterns for true beginners.

---

## 5) Core capabilities contract

These are the **must-have functional pillars** of the current product.

### 5.1 Process discovery that includes “hidden” stuff

peepBeefy must show processes that commonly evade user awareness:

* services with no UI,
* vendor helper stacks,
* overlay hooks,
* updaters.

### 5.2 “What’s heavy?” measurement model

The app must support identifying “clogging” by:

* CPU activity (instant + sampled),
* RAM footprint,
* disk read/write activity (sampled rate),
* optionally GPU/frametime in later phases (not required right now unless you explicitly re-scope).

**Key principle:** The user cares about “what is heavy now” and “what causes stutter.” Disk spikes and overlay hooks matter disproportionately for gaming experience.

### 5.3 Clear tagging that is gamer-relevant

The app must categorize/label processes into user-meaningful buckets (examples of buckets, not an exhaustive list):

* overlays/hooks
* RGB / vendor suites
* VR runtime
* VPN/network stack
* launchers
* updaters
* monitoring tools

This isn’t just data—this is translation.

### 5.4 “What changed?” baseline + diff

The app must provide:

* save a baseline snapshot (clean state)
* diff later to show newly introduced processes

This is core to solving the “Windows is a mess and stuff starts itself” complaint.

---

## 6) Output and readability standards

This section is the contract that prevents the app from regressing into “developer output.”

### 6.1 Visual hierarchy rules

The UI must:

* highlight the **few** things that matter most (top offenders) before dumping detail,
* use color to separate metric value from label,
* avoid making a rookie parse dense text.

### 6.2 Metric presentation standards

* Consistent units and formatting:

  * CPU: percent with sensible precision
  * RAM: human-readable (MB/GB)
  * Disk: human-readable per-second rates
* Clear thresholds / emphasis:

  * “hot” values visually stand out
  * “idle” values visually fade

### 6.3 Tables must remain readable

* Columns must not explode into “40 metrics.”
* Default views focus on **top N** and a small set of key columns.
* Deeper views (details drill-down) are allowed but not forced.

---

## 7) Safety and permission model

### 7.1 Current phase safety boundary

**Current phase is visibility-first.**
The app must not require or encourage reckless process termination.

### 7.2 Shelved feature implications

Future “trim/kill” features must be built with guardrails:

* explicit confirmation step(s),
* “do not touch” protections for Windows core processes,
* ideally a “recommended” list that is conservative and explainable.

### 7.3 Admin expectations

* Some insights (service mapping, full command lines) are better with admin.
* The app must still run non-admin, but should clearly indicate when data is partial.

---

## 8) Rules and heuristics system

### 8.1 Two complementary detection modes

peepBeefy must support both:

1. **Discovery mode** (resource-driven): “show me what’s heavy now” without requiring prior knowledge.
2. **Heuristic mode** (pattern-driven): “flag known gamer clutter stacks” (vendor services, overlays, etc.).

These modes should complement each other rather than compete.

### 8.2 Explainability requirement

When the app flags something as clutter/heavy, it should provide at least one of:

* a category tag,
* a service association,
* executable path,
* parent process,
* short “why this matters” hint.

This reduces the “cryptic” feeling.

---

## 9) Interaction contract for the interactive CLI

### 9.1 The “default run” must be effortless

A new user should be able to:

* launch the app,
* press Enter / choose a visible option,
* immediately see a useful “what’s heavy” view.

No flag memorization required.

### 9.2 Progressive learning

The interactive menu must:

* display the matching peepBeefy command for each action,
* encourage learning those commands naturally,
* without forcing terminal expertise.

### 9.3 No feature vanity

Rich/Typer must be used **only when it improves comprehension and reduces user error**.
“Fancy for fancy’s sake” is out of scope.

---

## 10) Packaging and launch expectations

This is part of usability (especially for terminal-first-time users).

### 10.1 Launch ergonomics

There must exist a “rookie-friendly” launch path (examples of acceptable patterns):

* double-click launcher that opens the interactive UI,
* simple alias command (short, memorable) that starts interactive UI.

### 10.2 Dependency friction

Install steps must be minimized and clearly guided. If Python dependency installation is required, the app should:

* detect missing deps,
* print a single copy/paste install command.

---

## 11) Shelved features contract

These are planned, **not** required for current completion, but **architecture must not block them**.

### 11.1 “Trim” actions from inside the interactive UI

* interactive selection of a process
* guided confirmation
* safe kill / close flow
* optional “create a gaming session profile” idea (future)

### 11.2 Security posture for trim

* strong defaults
* allowlists/denylists
* “never kill” protections

---

## 12) “Non-negotiables” checklist for future revisions

Any version bump or major refactor must re-verify:

1. **Interactive-first flow still exists and is the default.**
2. A beginner can get value with **near-zero typing**.
3. Output is **readable and not metric-spam** by default.
4. “Hidden/service-backed” processes are still surfaced meaningfully.
5. Baseline + diff still works (or is explicitly version-gated with migration).
6. CLI02 remains consistent and teachable from CLI03.
7. CLI01 remains the operational truth underneath.
8. No drift into “developer-only flags everywhere” as the primary path.

---

## 13) Completion criteria for the current phase

The current phase is “visibility + clarity” (not termination).

You can call this phase complete when:

* The interactive UI shows:

  * top heavy processes (CPU/RAM/Disk),
  * tags for common gamer clutter,
  * service-awareness where possible,
  * a drill-down “what is this?” detail view.
* Baseline snapshot + diff works end-to-end.
* The default UI is beginner-friendly: launch → one action → useful results.

---

## 14) Change log rules for the Source of Truth

To keep this document “absolute,” updates must be handled explicitly:

* When you add a feature, add it as:

  * **New capability** (Section 5) or **Shelved** (Section 11).
* When you change behavior, record it as:

  * an updated invariant in Section 12
  * and a revised completion criterion in Section 13 if needed.
* Avoid “silent” UX drift by treating Section 6 and 9 as contractual.

---

If you want this source of truth also in a **machine-readable registry** (so your app can validate “required commands exist” or “interactive default is enabled”), I can produce a compact `peepbeefy_contract.json` that encodes only the invariants and acceptance checks—without re-embedding the long prose.
