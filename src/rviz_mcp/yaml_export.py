"""Deterministic serializer for the mock backend's simplified RViz YAML format."""

from __future__ import annotations

from copy import deepcopy
import json
import math
import re
from typing import Any, Mapping


def build_rviz_document(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Translate a mock config snapshot into a human-readable RViz-like mapping."""
    fixed_frame = snapshot.get("fixed_frame")
    view = snapshot.get("view")
    displays = snapshot.get("displays")
    panels = snapshot.get("panels")
    if not isinstance(fixed_frame, str) or not fixed_frame.strip():
        raise ValueError("snapshot fixed_frame must be a non-empty string")
    if not isinstance(view, Mapping):
        raise ValueError("snapshot view must be a mapping")
    if not isinstance(displays, list):
        raise ValueError("snapshot displays must be a list")
    if not isinstance(panels, list):
        raise ValueError("snapshot panels must be a list")

    return {
        "Panels": [_panel_entry(panel) for panel in panels],
        "Visualization Manager": {
            "Class": "",
            "Displays": [_display_entry(display) for display in displays],
            "Global Options": {"Fixed Frame": fixed_frame},
            "Views": {"Current": _view_entry(view)},
        },
    }


def serialize_rviz_config(snapshot: Mapping[str, Any]) -> str:
    """Serialize a snapshot as a deterministic, safe YAML 1.2 subset.

    The emitted block-style subset supports mappings, sequences, booleans,
    finite numbers, nulls, and strings. String values use JSON-compatible
    double quoting, which is also valid YAML 1.2 and avoids implicit typing.
    """
    return "\n".join(_emit_node(build_rviz_document(snapshot), 0)) + "\n"


def _display_entry(display: Any) -> dict[str, Any]:
    if not isinstance(display, Mapping):
        raise ValueError("each display must be a mapping")
    entry = {
        "Class": str(display.get("class", "")),
        "Enabled": bool(display.get("enabled", True)),
        "Name": str(display.get("name", "")),
        "Topic": str(display.get("topic", "")),
    }
    properties = display.get("properties")
    if isinstance(properties, Mapping) and properties:
        entry["Properties"] = deepcopy(dict(properties))
    return entry


def _panel_entry(panel: Any) -> dict[str, Any]:
    if not isinstance(panel, Mapping):
        raise ValueError("each panel must be a mapping")
    return {
        "Class": str(panel.get("class", "")),
        "Name": str(panel.get("name", "")),
        "Dock": str(panel.get("dock", "left")),
        "Visible": bool(panel.get("visible", True)),
    }


def _view_entry(view: Mapping[str, Any]) -> dict[str, Any]:
    focal = view.get("focal_point", {})
    if not isinstance(focal, Mapping):
        raise ValueError("view focal_point must be a mapping")
    return {
        "Class": str(view.get("class", "rviz_default_plugins/Orbit")),
        "Distance": float(view.get("distance", 10.0)),
        "Focal Point": {
            "X": float(focal.get("x", 0.0)),
            "Y": float(focal.get("y", 0.0)),
            "Z": float(focal.get("z", 0.0)),
        },
        "Yaw": float(view.get("yaw", 0.5)),
        "Pitch": float(view.get("pitch", 0.4)),
    }


def _emit_node(value: Any, indent: int) -> list[str]:
    if isinstance(value, Mapping):
        if not value:
            return [" " * indent + "{}"]
        lines: list[str] = []
        for key, child in value.items():
            if not isinstance(key, str):
                raise TypeError("YAML mapping keys must be strings")
            prefix = f"{' ' * indent}{_format_key(key)}:"
            if _is_collection(child):
                if not child:
                    lines.append(f"{prefix} {_empty_collection(child)}")
                else:
                    lines.append(prefix)
                    lines.extend(_emit_node(child, indent + 2))
            else:
                lines.append(f"{prefix} {_scalar(child)}")
        return lines

    if isinstance(value, list):
        if not value:
            return [" " * indent + "[]"]
        lines = []
        for child in value:
            if _is_collection(child) and child:
                child_lines = _emit_node(child, indent + 2)
                marker_width = indent + 2
                lines.append(" " * indent + "- " + child_lines[0][marker_width:])
                lines.extend(child_lines[1:])
            elif _is_collection(child):
                lines.append(" " * indent + "- " + _empty_collection(child))
            else:
                lines.append(" " * indent + "- " + _scalar(child))
        return lines

    return [" " * indent + _scalar(value)]


def _is_collection(value: Any) -> bool:
    return isinstance(value, (Mapping, list))


def _empty_collection(value: Any) -> str:
    return "{}" if isinstance(value, Mapping) else "[]"


def _scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return _quote_string(value)
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("YAML numbers must be finite")
        return repr(value)
    raise TypeError(f"unsupported YAML value type: {type(value).__name__}")


def _quote_string(value: str) -> str:
    encoded = json.dumps(value, ensure_ascii=False)
    # JSON permits these characters literally, while YAML treats them as line
    # breaks. Escaping them keeps every string on one deterministic YAML line.
    return (
        encoded.replace("\u0085", "\\u0085")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


_PLAIN_KEY = re.compile(r"^[A-Za-z_](?:[A-Za-z0-9 _-]*[A-Za-z0-9_])?$")
_RESERVED_KEYS = {"true", "false", "null", "~"}


def _format_key(value: str) -> str:
    if _PLAIN_KEY.fullmatch(value) and value.lower() not in _RESERVED_KEYS:
        return value
    return _quote_string(value)
