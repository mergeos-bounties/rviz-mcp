import os
import stat
from pathlib import Path

import pytest

from rviz_mcp.backend import mock as mock_module
from rviz_mcp.backend.mock import MockBackend
from rviz_mcp.yaml_export import build_rviz_document, serialize_rviz_config


FIXTURES = Path(__file__).parent / "fixtures"


def test_default_export_matches_golden_fixture():
    backend = MockBackend()

    result = backend.export_config()

    assert result["ok"] is True
    assert result["format"] == "rviz-yaml"
    assert result["yaml"] == (FIXTURES / "default_export.rviz").read_text(encoding="utf-8")
    assert result["bytes"] == len(result["yaml"].encode("utf-8"))


def test_export_round_trips_core_mock_state():
    backend = MockBackend()
    backend.seed_demo("nav")
    backend.set_fixed_frame("odom")
    backend.set_view(distance=4.5, yaw=1.25, pitch=0.2)

    document = build_rviz_document(backend.config_snapshot())
    manager = document["Visualization Manager"]

    assert manager["Global Options"]["Fixed Frame"] == "odom"
    assert manager["Views"]["Current"]["Distance"] == 4.5
    assert manager["Views"]["Current"]["Yaw"] == 1.25
    assert {display["Name"] for display in manager["Displays"]} >= {
        "Grid",
        "Map",
        "LaserScan",
        "GlobalPath",
    }


def test_export_writes_file_and_creates_parent(tmp_path: Path):
    backend = MockBackend()
    output = tmp_path / "nested" / "mock.rviz"

    result = backend.export_config(str(output))

    assert result == {
        "ok": True,
        "format": "rviz-yaml",
        "fixed_frame": "map",
        "display_count": 3,
        "path": str(output),
        "bytes": output.stat().st_size,
    }
    assert output.read_text(encoding="utf-8").startswith("Panels:\n")


@pytest.mark.parametrize("path", ["", "   ", "mock://saved.rviz", "export.yaml"])
def test_export_rejects_non_file_paths(path: str):
    result = MockBackend().export_config(path)

    assert result["ok"] is False
    assert "path" in result["error"]


def test_export_reports_directory_write_error(tmp_path: Path):
    result = MockBackend().export_config(str(tmp_path))

    assert result["ok"] is False
    assert "directory" in result["error"]


def test_export_never_overwrites_existing_file(tmp_path: Path):
    output = tmp_path / "existing.rviz"
    output.write_text("keep me", encoding="utf-8")

    result = MockBackend().export_config(str(output))

    assert result["ok"] is False
    assert "already exists" in result["error"]
    assert output.read_text(encoding="utf-8") == "keep me"


def test_export_rejects_symlink_parent(tmp_path: Path):
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked"
    try:
        linked_parent.symlink_to(real_parent, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlinks unavailable: {exc}")

    result = MockBackend().export_config(str(linked_parent / "export.rviz"))

    assert result["ok"] is False
    assert "symlink or junction" in result["error"]
    assert not (real_parent / "export.rviz").exists()


@pytest.mark.skipif(
    not hasattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT"),
    reason="Windows reparse attributes are unavailable",
)
def test_python311_reparse_point_detection(tmp_path: Path, monkeypatch):
    class ReparseStat:
        st_file_attributes = stat.FILE_ATTRIBUTE_REPARSE_POINT

    monkeypatch.setattr(Path, "is_symlink", lambda path: False)
    monkeypatch.setattr(mock_module.os, "lstat", lambda path: ReparseStat())

    assert mock_module._is_link_or_reparse_point(tmp_path) is True


def test_export_failure_leaves_no_partial_file(tmp_path: Path, monkeypatch):
    output = tmp_path / "atomic.rviz"

    def fail_link(source, destination):
        raise OSError("simulated publish failure")

    monkeypatch.setattr(os, "link", fail_link)
    result = MockBackend().export_config(str(output))

    assert result["ok"] is False
    assert "simulated publish failure" in result["error"]
    assert not output.exists()
    assert list(tmp_path.glob(".atomic.rviz.*.tmp")) == []


def test_serializer_validates_required_snapshot_shape():
    with pytest.raises(ValueError, match="fixed_frame"):
        build_rviz_document({})
    with pytest.raises(ValueError, match="display"):
        serialize_rviz_config(
            {"fixed_frame": "map", "view": {}, "displays": ["bad"], "panels": []}
        )


def test_serializer_quotes_ambiguous_and_special_strings():
    backend = MockBackend()
    backend._displays["special"] = {
        "name": "yes: no\nnext",
        "class": 'plugin/"Quoted"',
        "enabled": False,
        "topic": "null",
        "properties": {
            "Label": "true",
            "Unset": None,
            "bad:key": "value",
            "Values": ["one", 2, False, None],
            "Nested": {"rate": 1.5},
        },
    }

    output = backend.export_config()["yaml"]

    assert 'Name: "yes: no\\nnext"' in output
    assert 'Class: "plugin/\\"Quoted\\""' in output
    assert 'Topic: "null"' in output
    assert 'Label: "true"' in output
    assert "Unset: null" in output
    assert '"bad:key": "value"' in output
    assert 'Values:\n          - "one"\n          - 2\n          - false\n          - null' in output
    assert "Nested:\n          rate: 1.5" in output


def test_serializer_quotes_unsafe_property_keys():
    backend = MockBackend()
    backend._displays["keys"] = {
        "name": "keys",
        "class": "plugin/Keys",
        "properties": {"trailing ": "value", "true": "value", "safe key": "value"},
    }

    output = backend.export_config()["yaml"]

    assert '"trailing ": "value"' in output
    assert '"true": "value"' in output
    assert 'safe key: "value"' in output


def test_serializer_escapes_yaml_line_separator_characters():
    backend = MockBackend()
    backend._displays["unicode"] = {
        "name": "next\u0085line\u2028paragraph\u2029end",
        "class": "plugin/Unicode",
    }

    output = backend.export_config()["yaml"]

    assert 'Name: "next\\u0085line\\u2028paragraph\\u2029end"' in output


def test_serializer_rejects_non_finite_numbers():
    backend = MockBackend()
    backend._displays["bad"] = {
        "name": "bad",
        "class": "plugin/Bad",
        "enabled": True,
        "topic": "",
        "properties": {"alpha": float("inf")},
    }

    result = backend.export_config()

    assert result["ok"] is False
    assert "finite" in result["error"]
