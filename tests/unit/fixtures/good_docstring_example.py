"""Fully Google-style-compliant fixture, for the gate self-test.

Mirrors the same shapes as `bad_docstring_example.py` — a plain function, a class with a
method, and a function with accurate `Args:`/`Returns:` — to prove the gate passes clean
when the docstring contract is actually followed.
"""


def documented_function(x: int) -> int:
    """Double a number.

    Args:
        x: The number to double.

    Returns:
        Twice `x`.
    """
    return x * 2


class DocumentedMethodClass:
    """A class whose method is also documented."""

    def documented_method(self, x: int) -> int:
        """Increment a number by one.

        Args:
            x: The number to increment.

        Returns:
            `x` plus one.
        """
        return x + 1


def accurate_args_function(x: int, y: int) -> int:
    """Add two numbers, with Args that match the real signature exactly.

    Args:
        x: The first number.
        y: The second number.

    Returns:
        The sum of x and y.
    """
    return x + y
