"""tools/app_parity.py reports byte parity between the package and app copies."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

TOOL = Path(__file__).resolve().parent.parent / "tools" / "app_parity.py"
_spec = importlib.util.spec_from_file_location("app_parity", TOOL)
app_parity = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(app_parity)


def _tree(root: Path, files: dict[str, bytes]) -> Path:
    root.mkdir()
    for name, data in files.items():
        (root / name).write_bytes(data)
    return root


@pytest.fixture
def layout(tmp_path):
    package = _tree(tmp_path / "pkg", {"__init__.py": b"", "a.py": b"A", "b.py": b"B", "c.py": b"C"})
    one = _tree(tmp_path / "one", {"a.py": b"A", "b.py": b"B-one", "c.py": b"C-one"})
    two = _tree(tmp_path / "two", {"a.py": b"A-two", "b.py": b"B-one"})
    return package, one, two


def test_compare_reports_package_and_cross_app_parity(layout):
    package, one, two = layout
    report = app_parity.compare({"one": one, "two": two}, package_dir=package)
    assert report["modules"] == 3
    assert report["apps"]["one"]["identical"] == ["a.py"]
    assert report["apps"]["one"]["different"] == ["b.py", "c.py"]
    assert report["apps"]["two"]["identical"] == []
    assert report["apps"]["two"]["missing"] == ["c.py"]
    assert report["between_apps"]["one~two"] == {"identical": ["b.py"], "different": ["a.py"]}
    assert "1/3 byte-identical to the package" in app_parity.render(report)


def test_cli_prints_json_and_rejects_bad_arguments(layout, capsys, tmp_path, monkeypatch):
    package, one, _two = layout
    monkeypatch.setattr(app_parity, "PACKAGE_DIR", package)
    assert app_parity.main([f"one={one}", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["apps"]["one"]["identical"] == ["a.py"]
    for bad in (["one"], [f"one={tmp_path / 'absent'}"], [f"one={one}", f"one={one}"]):
        with pytest.raises(SystemExit) as exc:
            app_parity.main(bad)
        assert exc.value.code == 2


def test_package_ships_the_68_modules_the_readme_counts():
    assert len(app_parity.package_modules()) == 68
