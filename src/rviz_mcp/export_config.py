"""Deterministic RViz-like YAML export for the mock backend.

Generates a simplified, human-inspectable ``.rviz``-compatible YAML document
from the current mock backend state.  The emitted YAML is a focused subset
covering:

  * Panels       — name, class, dock, visible
  * Displays     — name, class, enabled, topic
  * Global Options — Fixed Frame
  * Views / Current — class, distance, focal point (x/y/z), yaw, pitch

Design
------

* **Zero runtime dependency.**  The serializer is pure Python (stdlib only);
  PyYAML is an optional extra used only for validation in tests.

* **Deterministic output.**  Ordered dicts, stable key ordering and
  consistent float rounding guarantee byte-for-byte reproducibility.

* **YAML 1.2 subset.**  Block-style mappings/sequences, double-quoted
  strings (JSON-compatible, also valid YAML), booleans, finite numbers,
  nulls.

Limitations (documented in README)
-----------------------------------

* No ``Widgets`` tree (RViz property-tree serialisation).
* No TF prefix overrides.
* No ``Status`` blocks, ``Materials`` or ``Textures`` panels.
* PascalCase section names follow common RViz conventions but are not
  guaranteed to match every RViz2 version's exact schema.
* Mock ``load_config`` records a path but does not rehydrate an export
  into memory — this is an *export*, not a serialisation round-trip.

"""

from __future__ import annotations

import math
import os
import stat
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping, Sequence

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "build_rviz_document",
    "serialize_rviz_config",
    "export_config_to_yaml",
    "export_config_to_file",
]

SCHEMA_VERSION = "rviz-mcp-export-1"


def build_rviz_document(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Translate a ``config_snapshot()`` dict into a RViz-like mapping.

    Parameters
    ----------
    snapshot : Mapping
        Output of ``MockBackend.config_snapshot()``.  Must contain
        ``fixed_frame`` (str), ``view`` (mapping), ``displays`` (list),
        ``panels`` (list).

    Returns
    -------
    dict
        Ordered dict tree ready for YAML serialisation.
    """
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
    """Serialize a mock config snapshot as deterministic YAML text.

    Returns a UTF-8 string containing a block-style YAML document with
    no trailing blank line.
    """
    doc = build_rviz_document(snapshot)
    return "\n".join(_emit_node(doc, 0)) + "\n"


def export_config_to_yaml(backend: Any) -> str:
    """One-shot: get snapshot → build doc → serialize YAML.

    Raises ValueError if the backend does not support ``config_snapshot``.
    """
    snap = getattr(backend, "config_snapshot", None)
    if not callable(snap):
        raise ValueError(
            f"backend {getattr(backend, 'name', '?')} does not support config_snapshot"
        )
    return serialize_rviz_config(snap())


def export_config_to_file(
    backend: Any,
    path: str,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Export the current mock config as YAML to a local ``.rviz`` file.

    Safety rules
    ------------
    * Refuses paths that do not end with ``.rviz``.
    * Refuses to overwrite an existing file unless ``overwrite=True``.
    * Refuses paths whose parent directory is (or traverses) a symlink/junction.
    * Writes atomically: first to a temp file in the target directory,
      then renames into place.  Cleans up the temp file on failure.

    Returns
    -------
    dict
        ``{"ok": True, "path": ..., "bytes": ..., "format": "rviz-yaml", ...}``
        on success, or ``{"ok": False, "error": ...}`` on failure.
    """
    raw = path.strip()
    if not raw:
        return {"ok": False, "error": "export path must not be empty"}
    if "://" in raw:
        return {"ok": False, "error": "export path must be a local filesystem path"}

    output = Path(raw).expanduser().resolve()

    # --- Safety checks ---
    if output.is_dir():
        return {"ok": False, "error": f"export path is a directory: {output}"}
    if output.suffix.lower() != ".rviz":
        return {
            "ok": False,
            "error": "export path must use the .rviz extension",
        }
    if not overwrite and (output.exists() or output.is_symlink()):
        return {"ok": False, "error": f"export path already exists: {output}"}
    if _has_linked_parent(output):
        return {
            "ok": False,
            "error": "export path has a symlink/junction in its parent chain",
        }

    # --- Serialise ---
    try:
        yaml_text = export_config_to_yaml(backend)
    except (TypeError, ValueError, OSError) as exc:
        return {"ok": False, "error": f"could not serialise export: {exc}"}

    # --- Atomic write ---
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp: Path | None = None
    try:
        fd, tmp_name = tempfile.mkstemp(
            suffix=".rviz", prefix=".tmp-", dir=str(output.parent)
        )
        os.close(fd)
        tmp = Path(tmp_name)
        tmp.write_text(yaml_text, encoding="utf-8")
        if overwrite and output.exists():
            output.unlink()
        tmp.rename(output)
        tmp = None  # prevent cleanup
    except OSError as exc:
        if tmp is not None and tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return {"ok": False, "error": f"could not write export file: {exc}"}
    finally:
        if tmp is not None and tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass

    b = getattr(backend, "config_snapshot", None)
    snap = b() if callable(b) else {}

    return {
        "ok": True,
        "format": "rviz-yaml",
        "path": str(output),
        "bytes": output.stat().st_size,
        "fixed_frame": snap.get("fixed_frame"),
        "display_count": snap.get("display_count", 0),
    }


# ---------------------------------------------------------------------------
# Internal helpers — document construction
# ---------------------------------------------------------------------------


def _display_entry(display: Any) -> dict[str, Any]:
    if not isinstance(display, Mapping):
        raise ValueError("each display must be a mapping")
    return {
        "Class": display.get("class", ""),
        "Enabled": bool(display.get("enabled", True)),
        "Name": display.get("name", ""),
        "Topic": display.get("topic", ""),
    }


def _panel_entry(panel: Any) -> dict[str, Any]:
    if not isinstance(panel, Mapping):
        raise ValueError("each panel must be a mapping")
    return {
        "Class": panel.get("class", ""),
        "Name": panel.get("name", ""),
        "Dock": panel.get("dock", ""),
        "Visible": bool(panel.get("visible", True)),
    }


def _view_entry(view: Mapping[str, Any]) -> dict[str, Any]:
    fp = view.get("focal_point", {})
    return {
        "Class": view.get("class", ""),
        "Distance": _safe_float(view.get("distance")),
        "Focal Point": {
            "X": _safe_float(fp.get("x") if isinstance(fp, Mapping) else 0.0),
            "Y": _safe_float(fp.get("y") if isinstance(fp, Mapping) else 0.0),
            "Z": _safe_float(fp.get("z") if isinstance(fp, Mapping) else 0.0),
        },
        "Yaw": _safe_float(view.get("yaw")),
        "Pitch": _safe_float(view.get("pitch")),
    }


# ---------------------------------------------------------------------------
# Internal helpers — YAML emitter (pure Python, stdlib only)
# ---------------------------------------------------------------------------


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Cast to float, guard against NaN/Inf, round to 6 decimal places."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(v) or math.isinf(v):
        return default
    return round(v, 6)


def _emit_node(node: Any, indent: int) -> list[str]:
    """Recursively emit a node as block-style YAML lines."""
    if isinstance(node, Mapping):
        return _emit_mapping(node, indent)
    if isinstance(node, list):
        return _emit_sequence(node, indent)
    if isinstance(node, bool):
        return [_pad(indent) + ("true" if node else "false")]
    if isinstance(node, (int, float)):
        return [_pad(indent) + _format_number(node)]
    if node is None:
        return [_pad(indent) + "null"]
    # string
    return [_pad(indent) + _format_string(str(node))]


def _emit_mapping(mapping: Mapping[str, Any], indent: int) -> list[str]:
    lines: list[str] = []
    for key, value in mapping.items():
        if isinstance(value, (Mapping, Sequence)) and not isinstance(value, str):
            # complex value — key alone on its line, value indented underneath
            if _is_empty_collection(value):
                lines.append(f"{_pad(indent)}{key}: []" if isinstance(value, Sequence) else f"{_pad(indent)}{key}: {{}}")
            else:
                lines.append(f"{_pad(indent)}{key}:")
                lines.extend(_emit_node(value, indent + 2))
        else:
            # scalar value on same line
            scalar = _format_scalar(value)
            lines.append(f"{_pad(indent)}{key}: {scalar}")
    return lines


def _emit_sequence(seq: Sequence[Any], indent: int) -> list[str]:
    lines: list[str] = []
    for item in seq:
        if isinstance(item, (Mapping, Sequence)) and not isinstance(item, str):
            if _is_empty_collection(item):
                lines.append(f"{_pad(indent)}- []" if isinstance(item, Sequence) else f"{_pad(indent)}- {{}}")
            else:
                # First line: "- " then first key/value on same line
                first_key, first_val = list(item.items())[0] if isinstance(item, Mapping) else (None, None)
                if first_key is not None:
                    if isinstance(first_val, (Mapping, Sequence)) and not isinstance(first_val, str):
                        if _is_empty_collection(first_val):
                            lines.append(f"{_pad(indent)}- {first_key}: []" if isinstance(first_val, Sequence) else f"{_pad(indent)}- {first_key}: {{}}")
                        else:
                            lines.append(f"{_pad(indent)}- {first_key}:")
                            lines.extend(_emit_node(first_val, indent + 4))
                    else:
                        lines.append(f"{_pad(indent)}- {first_key}: {_format_scalar(first_val)}")
                    # Remaining keys at indent+2
                    for k, v in list(item.items())[1:]:
                        if isinstance(v, (Mapping, Sequence)) and not isinstance(v, str):
                            if _is_empty_collection(v):
                                lines.append(f"{_pad(indent+2)}{k}: []" if isinstance(v, Sequence) else f"{_pad(indent+2)}{k}: {{}}")
                            else:
                                lines.append(f"{_pad(indent+2)}{k}:")
                                lines.extend(_emit_node(v, indent + 4))
                        else:
                            lines.append(f"{_pad(indent+2)}{k}: {_format_scalar(v)}")
                else:
                    lines.extend(_emit_node(item, indent + 2))
        else:
            lines.append(f"{_pad(indent)}- {_format_scalar(item)}")
    return lines


def _is_empty_collection(val: Any) -> bool:
    if isinstance(val, str):
        return False
    if isinstance(val, (Mapping, Sequence)):
        return len(val) == 0  # type: ignore[arg-type]
    return False


def _pad(indent: int) -> str:
    return " " * indent


def _format_number(num: float | int) -> str:
    """Format a number for YAML emission."""
    if isinstance(num, int):
        return str(num)
    # Float — use repr for precision
    return repr(num)


def _format_string(s: str) -> str:
    """YAML double-quoted string (JSON-compatible, YAML 1.2 safe)."""
    # Escape backslashes and double quotes
    escaped = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _format_scalar(val: Any) -> str:
    """Format any scalar for inline YAML emission."""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return "null"
        return repr(val) if isinstance(val, float) else str(val)
    if val is None:
        return "null"
    return _format_string(str(val))


def _has_linked_parent(path: Path) -> bool:
    """True if any ancestor of *path* is a symlink or junction."""
    try:
        resolved = path.resolve()
    except OSError:
        return True
    for parent in resolved.parents:
        try:
            if parent.is_symlink() or (
                os.name == "nt" and _is_windows_junction(parent)
            ):
                return True
        except OSError:
            return True
    return False


def _is_windows_junction(path: Path) -> bool:
    """Detect a Windows junction (reparse point with IO_REPARSE_TAG_MOUNT_POINT)."""
    if os.name != "nt":
        return False
    try:
        attrs = path.stat().st_file_attributes
        if hasattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT"):
            return bool(attrs & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    except OSError:
        pass
    return False
