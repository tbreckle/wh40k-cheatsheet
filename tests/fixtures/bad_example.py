"""Seeded fixture with one deliberate violation per quality-gate category.

Used only by `tests/test_gate_selftest.py` to prove `poe check`'s four gates each fire on
their own category of defect. Excluded from the real build via `[tool.ruff] extend-exclude`
(ruff) and by never being passed to pylint/bandit/ty, which only ever scan `src/` — so this
file's deliberate violations never fail the actual `poe check` run; the self-test checks it
by passing its path to each tool explicitly.
"""

import os  # unused import — seeded style/lint violation (ruff F401); no noqa, meant to be caught


def add_item(item, items=[]):  # seeded mutable-default-argument bug (ruff/bugbear B006)
    items.append(item)
    return items


password = "hunter2"  # seeded hard-coded secret (bandit B105 hardcoded_password_string)


def bad_return_type() -> int:
    return "not an int"  # seeded type error (ty)
