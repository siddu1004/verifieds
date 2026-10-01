"""Smoke test for the verifieds package (S-00).

Replaced by real module tests from S-04 onward.
"""


def test_package_importable() -> None:
    """verifieds package must be importable."""
    import verifieds  # noqa: PLC0415

    assert verifieds is not None
