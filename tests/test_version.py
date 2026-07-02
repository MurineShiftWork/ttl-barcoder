"""Package version is discoverable via importlib.metadata."""

from importlib.metadata import version


def test_version_is_non_empty_str() -> None:
    v = version("ttl-barcoder")
    assert isinstance(v, str)
    assert v
