from __future__ import annotations


def test_runtime_package_imports() -> None:
    import zagent_runtime
    from zagent_runtime.presentation.cli import app

    assert zagent_runtime.__doc__
    assert app is not None

