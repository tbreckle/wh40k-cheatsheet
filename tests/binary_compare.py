"""Cheap, non-quadratic comparison helper for large binary test fixtures.

pytest's assertion rewriter hands a failed `==` on two byte sequences to
difflib, whose comparison is quadratic; on multi-hundred-KB PDFs that can
outrun a CI job's timeout instead of failing fast (see the "Gate — tests"
timeout on 2026-08-17). Use `assert_bytes_equal` in place of a bare
`assert a == b` for large binary blobs.
"""

import pytest


def assert_bytes_equal(label: str, a: bytes, b: bytes) -> None:
    """Fail fast with an O(n) mismatch summary instead of an O(n^2) diff."""
    if a == b:
        return
    length = min(len(a), len(b))
    first_diff = next((i for i in range(length) if a[i] != b[i]), length)
    pytest.fail(f"{label} differs (len {len(a)} vs {len(b)}, first differing byte at offset {first_diff})")
