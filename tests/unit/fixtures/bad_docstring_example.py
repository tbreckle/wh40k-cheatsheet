"""Deliberately violates the docstring gate, for the gate self-test.

Never imported for its behavior — only run through `pylint` as a subprocess in
`tests/integration/test_docstring_gate_selftest.py` to prove the gate catches:
missing docstrings, an undocumented method, and Args that don't match the real signature.
"""


def undocumented_function(x: int) -> int:
    return x * 2


class UndocumentedMethodClass:
    """A class with its own docstring, but an undocumented method below."""

    def undocumented_method(self, x: int) -> int:
        return x + 1


def mismatched_args_function(x: int, y: int) -> int:
    """Add two numbers, but document the wrong parameters on purpose.

    Args:
        x: The first number.
        z: This parameter does not exist on the real signature.

    Returns:
        The sum of x and y.
    """
    return x + y
