# Shelved Features

## Revisions and Application Name

`peepBeefy`: The application name that is a rearrangement and combination of the core commands of the interactive cli. The general meaning of `peepBeefy` is "find and desplay heavy running processes"

## Official

> 1. Add a single-screen “watch” mode (live updating table every N seconds) using Rich’s live rendering, still keeping it aligned with the purpose (visibility, not fluff)

---

## RULES

### THOU_SHALL_NOT(`TSN`)

> [TSN01]
> [TSN02]

### THOU SHALL(`TSH`)

> [TSH01]
> [TSH02]

## TARGET AUDIENCE

### Gamers

> "technical_understanding":
- Good, with significantly higher scale in computer users compared to console users
- Can operate a terminal, if given the correct steering and instructions

> "problem":
- The vast majority of gamers, or general computer users for that matter understand how to utilize a terminal.
- Just asking users to open and or utilize the terminal for a command line interface is a barrier.

> "solution":
- "over-develop": When developing and designing the application, minimize human related error sequences by developing further quality of life into them, for example. Instead of providing the `py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json`, the user can type "peepBeefy" in their terminal, which begins the automated process of the interactive cli. Yes, this takes longer, it is why we are mirroring the `peepBeefy` command scheme off of the already inplace `developer` spec commands. The `dev-spec` commands operate as a developer friendly format, the absolute source of truth and the benchmark for the `peepBeefy` command scheme, which will require its own cli commands that can be run from the cli and with the interactive cli. We want to encourage the users utilizing the interactive cli to use the `peepBeefy` command scheme instead of the (more optimal, but less user friendly) numerical input and minimal input such as: `Yes or No = [Y/n]`. For Numerical, instead of inputting the menu line as the selection, provide the `peepBeefy` command as the option selection in the interactive cli. Doing so will encourage and teach the users how to operate the cli without the interactive menu selections and automation. This will lead to `peepBeefy` only cli usage, then eventually the classic `dev-spec` that experienced developers use.

> "visual_output":
- Users of this calibre have no idea what goes into development, what is optimal or what `works` for terminals. What they DO have, is short attention spans and expectations.
- The CLI will require a beautiful output that is easy to read and understand. This means that the output will need to be developed and formatted above and beyond what we would do in a normal cli application.
- THE OVERWELMING MAJORITY OF CLI USERS ARE DEVELOPERS. DEVELOPERS UNDERSTAND OPTIMIZATION AND CLI DESIGN. TO A DEVELOPER, VISUAL DESIGN IS AN AFTER THOUGHT, AND OPTIONAL.
- GAMERS ARE NOT DEVELOPERS, AND WOULD EXPECT THIS TO BE VISUALLY STUNNING AS IT IS SOMEONES APPLICATION, THE HUMAN THOUGHT PROCESS TO THIS IS AS FOLLOWS:
  - "*WHY WOULDNT THEY ADD COLOR?*"
    - The user would see the cli as some ancient piece of software that should be extremely easy to customize, they just dont understand any fundemental of how terminals operate or development in general.
  - "*WHY NOT ADD SOME SORT OF UI, OR BORDER?*"
    - Portrays negatively on the developers ability to design and or understand the userbase, even though it is the userbase that does not understand that it is not optimal.
  - "*THIS IS HARD TO READ, I WONDER IF THIS APP EVEN WORKS IF THEY DIDNT EVEN CARE TO MAKE IT LOOK GOOD?*
    - Alot can be judged about a person in the little details, it seperates a 'good' application, from one that shows attention and care to detail for their userbase; such is the purpose of the points above.

> "lessons":
- "Optimization":
  - Is not always the best option as seen in `Solution` above.(The optimal route would be to keep `dev-spec` only, but that defeats the purpose of the target audience usage, therefore leading to an application with no user base, and no purpose.)
- "Human Error":
  - Minimizing multi channel input without direct on screen instructions or help (interactive-cli) for rooking users involves developing an application with their needs in mind, not the optimal solution.
- "Over-Develop"
  - Doesnt always mean 'bloated', it means providing the user with a quality of life that is developed full scope, without losing quality, advanced features or beautiful visual output and display.
target_audence:
  - The audience for this application is gamers, and the development and design spec should be created for an audience that are technically savvy, but mostly opening a terminal for the first time
  - We cannot ask a brand new userbase who have never used a terminal to type 6 flag commands + 2 numeric input options + the execution command from the shell. This is insanely terrible design

> [!NOTE]
> REQ01:
> - This needs to be an interactive cli, OVER DEVELOPED for user friendliness and quality of life. this cli application is designed to provide users ADVANCED UTILITY, in an EASY WAY. 
> REQ02:
> - The decision to integrate Rich/Typer was chosen for a reason, for the interactive cli, and to provide the user with a quality of life that is developed full scope, without losing quality or metrics. For example, if there is a metric on display, seperate the color of the number, so that rookie users can look at the output without being overwhelmed. That is just one example of MANY that will provide new users with a viable experience

## CLI DESIGN

[CLI01]

### command schemes [TODO-01:"POPULATE"]

main-cli-call-command:(**DEFAULT**)
- `beefy`

sub-commands:
- `peep`: the general repacement for "check, search, find"

options:
[TODO-01]
flags:
[TODO-01]

### JSON RULES

```json
{
    "thou_shall_not": [
        "TS01":"Design simplistic integration with native python commands like `py .\gameprep.py top io --seconds 1.0 --limit 50 --non-windows --services --json > io.json`",
        "TS02":"Force design constraints to one response"
    ],
    "thou_shall": [
        "TS01":"Apply the `peepBeefy` brand application command scheme where relevant and populate the required interactive cli data",
        "TS02":"Utilize two responses minimum to completely design and generate the users request"
    ],
    "todo": [
        "TODO01":"As you develop, populate the data for the peepBeefy command scheme"
    ],
    "note": [
        "NOTE01":"The `peepBeefy` command scheme is a mirror of the `dev-spec` command scheme, but is designed for user friendliness and ease of use for new users"
    ],
    "cli_design": [
        "CLI01":"RETAIN the current cli design. it works, and *DEVELOPERS* WILL utilize it to understand its core foundations. BOTH [CL02](`peepBeefy`), [CL03](`peepBeefy-interactive-cli`) will utilize the classic [dev-design] as their absolute source of truth for logic **NOT** name schemes."
    ],
    "requirements": [
        "REQ01":"The cli application is designed to provide users ADVANCED UTILITY, in an EASY WAY. The interactive cli is designed to provide users with a quality of life that is developed full scope, without losing quality or metrics."
    ]
}
```
