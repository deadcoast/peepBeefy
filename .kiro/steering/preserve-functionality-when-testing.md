---
inclusion: always
---

# Non-negotiable engineering rule: do not degrade functionality to pass tests

## Absolute rule

- NEVER remove, stub, bypass, or "simplify away" real module functionality just to make tests pass.
- NEVER delete or de-scope features that already exist unless the task explicitly says the feature is being removed.
- "Make tests pass" is not permission to reduce scope.

## Allowed actions when tests fail

When tests fail, do ONLY these actions (in order):

1) Fix the bug in the implementation while preserving all existing capabilities.

2) If the failure is due to mismatched interfaces/assumptions, adapt the code in a backward-compatible way (accept both old and new inputs), OR update the tests/spec to match the intended interface.

3) If an optional dependency (e.g., terminal capability detection) causes issues in isolation:
   - keep the feature, but make it optional/defensive (try/except import, safe defaults),
   - AND preserve the public attributes/behavior (e.g., `_use_rgb` must still exist).

4) If a feature seems unnecessary, STOP and ask for explicit approval before removing it.

## Explicitly forbidden "test hacks"

- Disabling validations, logging, fallbacks, metadata hooks, or compatibility layers to reduce test surface area.
- Replacing featureful code with a minimal version that only satisfies current tests.
- Changing runtime behavior (e.g., dropping RGB/8-bit fallback) unless requirements explicitly changed.

## Output expectations

- If you change behavior, list it as a "Behavior Change" and justify it against requirements.
- If you remove anything, it must be written as: "Feature Removed: <name> — Approved by user: YES/NO". If NO, do not remove it.
