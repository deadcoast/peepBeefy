# Table Formatting Rules

## Overview

Format: **structured hierarchy**
- Essentially using the table to create "category headers" within the rows, using horizontal separators to define the scope of each command element.

---

### Table Formatting Specifications

To maintain consistency across the **Command Schemes** documentation, please adhere to the following row-blocking rules:

- **Category Isolation:** Each new element type (e.g., *Sub-command*, *Flags*) must be preceded by a separator row (`--- | |`) to visually group related values.
- **Type Labeling:** The **Type** column should only contain the category identifier (in bold) on the first line of its respective section.
- **Value Mapping:** All subsequent rows belonging to that category must leave the **Type** column **blank**. This indicates that the values and descriptions in those rows "belong" to the category defined above them.
- **Structural Integrity:** Every section block must be closed or separated by a dashed line to ensure the table remains scannable.

### EXCEPTIONS

`Main CLI call`: There is only one command for this entry point, and that will never change, thus this acts as the single one line rule.
- `APPLICABLE_ANALOGY`: Markdown `#` Title header

---

### Refined Example

Based on your rules, here is how the `peepBeefy` scheme looks when strictly following that logic:

| Type              | Value      | Description                                   |
|-------------------|------------|-----------------------------------------------|
| **Main CLI call** | `beefy`    | Primary entry point                           |
| ---               | ---        | ---                                           |
| **Sub-command**   |            |                                               |
|                   | `peep`     | General replacement for "check, search, find" |
| ---               | ---        | ---                                           |
| **Flags**         |            |                                               |
|                   | `--fat`    | Heavy running process                         |
| ---               | ---        | ---                                           |
| **Options**       |            |                                               |
|                   | `[TODO01]` | *To be populated*                             |

---

peepBeefy: `DESTROYER_OF_FAT-PROCESSES_5000`

---
