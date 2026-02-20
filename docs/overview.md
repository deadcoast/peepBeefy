# v0.0.4: Features

---

## Table of Contents

- [Revisions and Application Name](#revisions-and-application-name)
- [Rules](#rules)
  - [THOU_SHALL_NOT (TSN)](#thou_shall_not-tsn)
  - [THOU_SHALL (TSH)](#thou_shall-tsh)
- [Target Audience](#target-audience)
  - [Gamers](#gamers)
- [CLI Design](#cli-design)
  - [Command Schemes](#command-schemes)
- [JSON Rules (Global Definitions)](#json-rules-global-definitions)

---

## Revisions and Application Name

USER:

```plaintext
1. this is not an interactive cli. NO ONE is going to load up their terminal and manually type `py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json`. JUST ASKING USERS TO USE THE TERMINAL IS ALOT. 99% OF THE USERBASE OF COMPUTERS NEVER USE THE TERMINAL.
2. A) This needs to be an interactive cli, OVER DEVELOPED for user friendliness and quality of life. this cli application is designed to provide users ADVANCED UTILITY, in an EASY WAY.  The vast majority of gamers are not developers, gamers dont use the terminal.
2. B) We cannot ask a brand new userbase who have never used a terminal to type 6 flag commands + 2 numeric input options + the execution command from the shell. This is insanely terrible design.
3. The decision to integrate Rich/Typer was chosen for a reason, for the interactive cli, and to provide the user with a quality of life that is developed full scope, without losing quality or metrics. For example, if there is a metric on display, seperate the color of the number, so that rookie users can look at the output without being overwhelmed. That is just one example of MANY that will provide new users with a viable experience.
4. A) The audience for this application is gamers, and the development and design spec should be created for an audience that are technically savvy, but mostly opening a terminal for the first time.
```

**`peepBeefy`** — The application name is a rearrangement and combination of the core commands of the interactive CLI. The general meaning of `peepBeefy` is *"find and display heavy running processes."*

---

## Rules

### THOU_SHALL_NOT (`TSN`)

> DO NOT PRACTICE THE METHODS LISTED BELOW:

| ID        | Rule                                                                                                                                                        |
|-----------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `[TSN01]` | Design simplistic integration with native python commands like `py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json` |
| `[TSN02]` | Force design constraints to one response                                                                                                                    |

### THOU_SHALL (`TSH`)

> ALWAYS PRACTICE THE METHODS LISTED BELOW:

| ID        | Rule                                                                                                                 |
|-----------|----------------------------------------------------------------------------------------------------------------------|
| `[TSH01]` | Apply the `peepBeefy` brand application command scheme where relevant and populate the required interactive CLI data |
| `[TSH02]` | Utilize two responses minimum to completely design and generate the user's request                                   |

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

When developing and designing the application, minimize human-related error sequences by developing further quality of life into them. `[TSN01]`

**Example:** Instead of providing `py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json`, the user can type `peepBeefy` in their terminal, which begins the automated process of the interactive CLI. `[NOTE01]`

This takes longer — it is why we are mirroring the `peepBeefy` command scheme off of the already in-place `developer` spec commands. The `dev-spec` commands operate as a developer-friendly format: the absolute source of truth and the benchmark for the `peepBeefy` command scheme, which will require its own CLI commands that can be run both from the CLI and within the interactive CLI. `[TSH01]`

We want to encourage users of the interactive CLI to use the `peepBeefy` command scheme instead of the (more optimal, but less user-friendly) numerical input and minimal input such as `Yes or No = [Y/n]`. For numerical selections, instead of inputting the menu line number as the selection, provide the `peepBeefy` command as the option selection in the interactive CLI. Doing so will encourage and teach users how to operate the CLI without the interactive menu selections and automation.

**Progression path:**
`peepBeefy` interactive CLI `[CLI03]` → `peepBeefy` CLI-only usage `[CLI02]` → classic `dev-spec` (experienced developers) `[CLI01]`

#### Visual Output

Users of this calibre have no idea what goes into development, what is optimal, or what "works" for terminals. What they **do** have is short attention spans and expectations. `[REQ02]`

The CLI will require beautiful output that is easy to read and understand. This means output will need to be developed and formatted above and beyond what we would do in a normal CLI application.

> **THE OVERWHELMING MAJORITY OF CLI USERS ARE DEVELOPERS.** Developers understand optimization and CLI design. To a developer, visual design is an afterthought — optional.

> **GAMERS ARE NOT DEVELOPERS**, and would expect this to be visually stunning as it is someone's application. The human thought process is as follows:

| User Thought                                                                                              | Implication                                                                                                                                                                                         |
|-----------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| *"Why wouldn't they add color?"*                                                                          | The user sees the CLI as some ancient piece of software that should be extremely easy to customize — they just don't understand any fundamental of how terminals operate or development in general. |
| *"Why not add some sort of UI, or border?"*                                                               | Portrays negatively on the developer's ability to design and/or understand the userbase, even though it is the userbase that does not understand that it is not optimal.                            |
| *"This is hard to read — I wonder if this app even works if they didn't even care to make it look good?"* | A lot can be judged about a person in the little details. It separates a "good" application from one that shows attention and care to detail for the userbase.                                      |

#### Lessons

- **Optimization** is not always the best option, as seen in [Solution](#solution-over-develop) above. The optimal route would be to keep `dev-spec` only, but that defeats the purpose of the target audience, leading to an application with no userbase and no purpose.
- **Human Error** — Minimizing multi-channel input without direct on-screen instructions or help (interactive CLI) for rookie users involves developing an application with their needs in mind, not the optimal solution.
- **Over-Develop** doesn't always mean "bloated." It means providing the user with a quality of life that is developed full-scope, without losing quality, advanced features, or beautiful visual output and display.

> [!NOTE]
> `[REQ01]` **REQUIREMENT:**
> - This needs to be an interactive CLI, **over-developed** for user friendliness and quality of life. This CLI application is designed to provide users **advanced utility** in an **easy way**. The vast majority of gamers are not developers — gamers don't use the terminal.
>
> `[REQ02]` **RICH/TYPER INTEGRATION:**
> - The decision to integrate Rich/Typer was chosen for a reason: for the interactive CLI, and to provide the user with a quality of life that is developed full-scope without losing quality or metrics. For example, if there is a metric on display, separate the color of the number so that rookie users can look at the output without being overwhelmed. That is just one example of many that will provide new users with a viable experience.
>
> **TARGET AUDIENCE:**
> - The audience for this application is gamers, and the development and design spec should be created for an audience that is technically savvy but mostly opening a terminal for the first time.
> - We cannot ask a brand new userbase who have never used a terminal to type 6 flag commands + 2 numeric input options + the execution command from the shell. This is insanely terrible design. `[TSN01]`

---

## CLI Design

`[CLI01]`: **RETAIN** the current CLI design. It works, and *developers* will utilize it to understand its core foundations. Both `[CLI02]` (`peepBeefy`) and `[CLI03]` (`peepBeefy-interactive-cli`) will utilize the classic `[dev-design]` as their absolute source of truth for logic — **not** name schemes.

### Command Schemes

`[TODO01]`: Populate the data for the `peepBeefy` command scheme.

| Type                        | Value      | Description                                   |
| ---                         | ---        | ---                                           |
| **Main CLI call** (DEFAULT) | `beefy`    | Primary entry point                           |
| ---                         | ---        | ---                                           |
| **Sub-command**             |            |                                               |
|                             | `peep`     | General replacement for "check, search, find" |
| ---                         | ---        | ---                                           |
| **Flags**                   |            |                                               |
|                             | `--fat`    | Heavy running process (shelved: `trim fat`)   |
| ---                         | ---        | ---                                           |
| **Options**                 |            |                                               |
|                             | `[TODO01]` | *To be populated*                             |
| ---                         | ---        | ---                                           |

> TABLE_FORMATTING: [table-formatting](docs/table-formatting.md)
> - TYPE_COLUMN:
>   - Must have a line seperator above identifier to allow for multiple value types to be listed
>   - Must leave the "type" column blank for corresponding values, the type columns are identified and seperated by their lines `---`

---

> SHELVED FEATURES (Planned for after launch)
> These features are shelved for after launch, as they are not core to the application's functionality ALTHOUGH the applications foundations must include the ability to implement them.

| Type            | Value  | Description                            |
|-----------------|--------|----------------------------------------|
| **Sub-command** | `trim` | end process throug the interactive-CLI |

---

## JSON Rules (Global Definitions)

> **Purpose:** Machine-readable source of truth. Tags referenced throughout this document as `[TAG_ID]` resolve to their full definition below. An AI agent encountering an unfamiliar tag should open this section for complete context before continuing.

```json
{
  "_meta": {
    "version": "0.0.4",
    "usage": {
      "found_tag": "Do I have full understanding of the identified tag definition?",
      "if_no": "Open this JSON block and read the full context for the tag",
      "if_yes": "Continue current task"
    }
  },
  "thou_shall_not": {
    "TSN01": "Do not design simplistic integration with native python commands like `py .\\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json`",
    "TSN02": "Do not force design constraints to one response"
  },
  "thou_shall": {
    "TSH01": "Apply the `peepBeefy` brand application command scheme where relevant and populate the required interactive CLI data",
    "TSH02": "Utilize two responses minimum to completely design and generate the user's request"
  },
  "cli_design": {
    "CLI01": "RETAIN the current CLI design. It works, and developers will utilize it to understand its core foundations. Both [CLI02] and [CLI03] will utilize the classic [dev-design] as their absolute source of truth for logic, NOT name schemes.",
    "CLI02": "`peepBeefy` — CLI-only command scheme. User-friendly alternative to dev-spec, runnable directly from the shell without the interactive menu.",
    "CLI03": "`peepBeefy-interactive-cli` — Full interactive menu-driven experience. Entry point for new users. Teaches [CLI02] commands through usage."
  },
  "requirements": {
    "REQ01": "The CLI application is designed to provide users ADVANCED UTILITY in an EASY WAY. The interactive CLI must be over-developed for user friendliness and quality of life, without losing quality or metrics.",
    "REQ02": "Rich/Typer integration provides full-scope quality of life. Visual separation of metrics (e.g., color-coded numbers) ensures rookie users are not overwhelmed by output density."
  },
  "notes": {
    "NOTE01": "The `peepBeefy` command scheme is a mirror of the `dev-spec` command scheme, but is designed for user friendliness and ease of use for new users."
  },
  "todo": {
    "TODO01": "As you develop, populate the data for the peepBeefy command scheme (options, flags, sub-commands)."
  }
}
```

---

peepBeefy: `DESTROYER_OF_FAT-PROCESSES_5000`

---
-
