from __future__ import annotations


def test_launcher_package_imports() -> None:
    import zagent_launcher
    from zagent_launcher.presentation.cli import app

    assert zagent_launcher.__doc__
    assert app is not None

