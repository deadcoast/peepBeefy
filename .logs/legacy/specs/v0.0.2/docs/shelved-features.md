# v0.0.3: Shelved Features

---

## Table of Contents

- [Revisions and Application Name](#revisions-and-application-name)
- [Official Shelved](#official-shelved)
- [Rules](#rules)
  - [THOU_SHALL_NOT (TSN)](#thou_shall_not-tsn)
  - [THOU_SHALL (TSH)](#thou_shall-tsh)
- [Target Audience](#target-audience)
  - [Gamers](#gamers)
- [CLI Design](#cli-design)
  - [Command Schemes](#command-schemes-todo-01)
- [JSON Rules](#json-rules)

---

## Revisions and Application Name

**`peepBeefy`** — The application name is a rearrangement and combination of the core commands of the interactive CLI. The general meaning of `peepBeefy` is *"find and display heavy running processes."*

---

## Official Shelved

> **1.** Add a single-screen "watch" mode (live updating table every N seconds) using Rich's live rendering, still keeping it aligned with the purpose (visibility, not fluff).

---

## Rules

### THOU_SHALL_NOT (`TSN`)

| ID       | Rule |
|----------|------|
| `TSN01`  |      |
| `TSN02`  |      |

### THOU_SHALL (`TSH`)

| ID       | Rule |
|----------|------|
| `TSH01`  |      |
| `TSH02`  |      |

---

## Target Audience

### Gamers

#### Technical Knowledge

- Good, with a significantly higher scale in computer users compared to console users.
- Can operate a terminal if given the correct steering and instructions.

#### Problem

- The vast majority of gamers — or general computer users for that matter — do not understand how to utilize a terminal.
- Just asking users to open and/or utilize the terminal for a command line interface is a barrier.

#### Solution: "Over-Develop"

When developing and designing the application, minimize human-related error sequences by developing further quality of life into them.

**Example:** Instead of providing `py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json`, the user can type `peepBeefy` in their terminal, which begins the automated process of the interactive CLI.

This takes longer — it is why we are mirroring the `peepBeefy` command scheme off of the already in-place `developer` spec commands. The `dev-spec` commands operate as a developer-friendly format: the absolute source of truth and the benchmark for the `peepBeefy` command scheme, which will require its own CLI commands that can be run both from the CLI and within the interactive CLI.

We want to encourage users of the interactive CLI to use the `peepBeefy` command scheme instead of the (more optimal, but less user-friendly) numerical input and minimal input such as `Yes or No = [Y/n]`. For numerical selections, instead of inputting the menu line number as the selection, provide the `peepBeefy` command as the option selection in the interactive CLI. Doing so will encourage and teach users how to operate the CLI without the interactive menu selections and automation.

**Progression path:**
`peepBeefy` interactive CLI → `peepBeefy` CLI-only usage → classic `dev-spec` (experienced developers)

#### Visual Output

Users of this calibre have no idea what goes into development, what is optimal, or what "works" for terminals. What they **do** have is short attention spans and expectations.

The CLI will require beautiful output that is easy to read and understand. This means output will need to be developed and formatted above and beyond what we would do in a normal CLI application.

> **THE OVERWHELMING MAJORITY OF CLI USERS ARE DEVELOPERS.** Developers understand optimization and CLI design. To a developer, visual design is an afterthought — optional.

> **GAMERS ARE NOT DEVELOPERS**, and would expect this to be visually stunning as it is someone's application. The human thought process is as follows:

| User Thought | Implication |
|---|---|
| *"Why wouldn't they add color?"* | The user sees the CLI as some ancient piece of software that should be extremely easy to customize — they just don't understand any fundamental of how terminals operate or development in general. |
| *"Why not add some sort of UI, or border?"* | Portrays negatively on the developer's ability to design and/or understand the userbase, even though it is the userbase that does not understand that it is not optimal. |
| *"This is hard to read — I wonder if this app even works if they didn't even care to make it look good?"* | A lot can be judged about a person in the little details. It separates a "good" application from one that shows attention and care to detail for the userbase. |

#### Lessons

- **Optimization** is not always the best option, as seen in [Solution](#solution-over-develop) above. The optimal route would be to keep `dev-spec` only, but that defeats the purpose of the target audience, leading to an application with no userbase and no purpose.
- **Human Error** — Minimizing multi-channel input without direct on-screen instructions or help (interactive CLI) for rookie users involves developing an application with their needs in mind, not the optimal solution.
- **Over-Develop** doesn't always mean "bloated." It means providing the user with a quality of life that is developed full-scope, without losing quality, advanced features, or beautiful visual output and display.

> [!NOTE]
> **REQUIREMENT:**
> - This needs to be an interactive CLI, **over-developed** for user friendliness and quality of life. This CLI application is designed to provide users **advanced utility** in an **easy way**. The vast majority of gamers are not developers — gamers don't use the terminal.
> - The decision to integrate Rich/Typer was chosen for a reason: for the interactive CLI, and to provide the user with a quality of life that is developed full-scope without losing quality or metrics. For example, if there is a metric on display, separate the color of the number so that rookie users can look at the output without being overwhelmed. That is just one example of many that will provide new users with a viable experience.
>
> **TARGET AUDIENCE:**
> - The audience for this application is gamers, and the development and design spec should be created for an audience that is technically savvy but mostly opening a terminal for the first time.
> - We cannot ask a brand new userbase who have never used a terminal to type 6 flag commands + 2 numeric input options + the execution command from the shell. This is insanely terrible design.

---

## CLI Design

`[CLI01]`: **RETAIN** the current CLI design. It works, and *developers* will utilize it to understand its core foundations. Both `[CLI02]` (`peepBeefy`) and `[CLI03]` (`peepBeefy-interactive-cli`) will utilize the classic `[dev-design]` as their absolute source of truth for logic — **not** name schemes.

### Command Schemes `[TODO-01]`

| Type | Value | Description |
|------|-------|-------------|
| **Main CLI call** (DEFAULT) | `beefy` | Primary entry point |
| **Sub-command** | `peep` | General replacement for "check, search, find" |
| **Options** | `[TODO-01]` | *To be populated* |
| **Flags** | `[TODO-01]` | *To be populated* |

---

## JSON Rules

```json
{
  "thou_shall_not": {
    "TSN01": "Design simplistic integration with native python commands like `py .\\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json`",
    "TSN02": "Force design constraints to one response"
  },
  "thou_shall": {
    "TSH01": "Apply the `peepBeefy` brand application command scheme where relevant and populate the required interactive CLI data",
    "TSH02": "Utilize two responses minimum to completely design and generate the user's request"
  },
  "todo": {
    "TODO01": "As you develop, populate the data for the peepBeefy command scheme"
  }
}
```
