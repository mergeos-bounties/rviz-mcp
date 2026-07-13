"""
rviz-mcp export_config — generate a simplified, human-inspectable
.rviz-like YAML from the current mock (or live) state.

This is intentionally **NOT** a perfect serialisation of the real RViz YAML
schema (which is hundreds of fields per display). It is a focused subset
that covers the four corners we mock:

  - Global:  FixedFrame, BackgroundColor, Frame, Tools (kid)
  - Displays: name, class, topic, enabled, position (display-tree position)
  - Views:    class, distance, focal_point (x/y/z), yaw, pitch
  - Panels:   name, class, dock, visible

Round-trip notes:
  - Mock export can be re-ingested into the mock backend by `rviz_load_config`
    if the path begins with `mock://`. The mock parser accepts the same
    subset we emit (see `backend/mock.py::_parse_export`).

Limitations (documented in README):
  - No `Widgets` tree (RViz property trees)
  - No TF prefix overrides
  - No `Status` blocks
  - No `Materials` / `Textures` panels
  - YAML keys are stable but JSON-ish layout; not all RViz-compatible editors
    will consume this without conversion.
"""

from __future__ import annotations

from typing import Any

from rviz_mcp import __version__


SCHEMA_VERSION = "rviz-mcp-export-1"


def _round_floats(obj: Any, ndigits: int = 6) -> Any:
    """Recursively round float values for stable YAML output."""
    if isinstance(obj, float):
        return round(obj, ndigits)
    if isinstance(obj, dict):
        return {k: _round_floats(v, ndigits) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round_floats(v, ndigits) for v in obj]
    return obj


def _display_to_yaml(name: str, info: dict[str, Any]) -> dict[str, Any]:
    """One display entry → YAML dict (stable ordering)."""
    return {
        "name": name,
        "Class": info.get("class") or "rviz_default_plugins/Display",
        "Enabled": bool(info.get("enabled", True)),
        "Topic": info.get("topic") or "",
    }


def _view_to_yaml(view: dict[str, Any]) -> dict[str, Any]:
    fp = view.get("focal_point") or {}
    return {
        "Class": view.get("class") or "rviz_default_plugins/Orbit",
        "Distance": float(view.get("distance", 10.0)),
        "FocalPointX": float(fp.get("x", 0.0)),
        "FocalPointY": float(fp.get("y", 0.0)),
        "FocalPointZ": float(fp.get("z", 0.0)),
        "Yaw": float(view.get("yaw", 0.5)),
        "Pitch": float(view.get("pitch", 0.4)),
    }


def _panel_to_yaml(name: str, info: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": name,
        "Class": info.get("class") or "rviz_common/Panel",
        "Dock": info.get("dock") or "left",
        "Visible": bool(info.get("visible", True)),
    }



def _as_list_of_dicts(items: Any) -> list[dict[str, Any]]:
    """Normalise list / dict into a list of {name, ...} dicts."""
    if items is None:
        return []
    if isinstance(items, dict):
        out: list[dict[str, Any]] = []
        for k, v in items.items():
            if isinstance(v, dict):
                vv = dict(v)
                vv.setdefault("name", k)
                out.append(vv)
            else:
                out.append({"name": k, "value": v})
        return out
    if isinstance(items, list):
        return [it for it in items if isinstance(it, dict)]
    return []


def build_export(backend: Any) -> dict[str, Any]:
    """Construct the exportable YAML-friendly dict from the current backend."""
    fixed_frame = getattr(backend, "_fixed_frame", None) or backend.doctor().get("fixed_frame", "map")
    view = getattr(backend, "_view", None) or {
        "class": "rviz_default_plugins/Orbit",
        "distance": 10.0,
        "focal_point": {"x": 0.0, "y": 0.0, "z": 0.0},
        "yaw": 0.5,
        "pitch": 0.4,
    }
    displays = _as_list_of_dicts(backend.list_displays())
    panels = _as_list_of_dicts(backend.list_panels())

    displays_dict = {}
    for d in displays:
        name = d.get("name") or "?"
        displays_dict[name] = _display_to_yaml(name, d)

    panels_dict = {}
    for p in panels:
        name = p.get("name") or "?"
        panels_dict[name] = _panel_to_yaml(name, p)

    out = {
        "header": {
            "generator": "rviz-mcp",
            "generator_version": __version__,
            "schema": SCHEMA_VERSION,
        },
        "FixedFrame": fixed_frame,
        "View": _view_to_yaml(view),
        "Displays": displays_dict,
        "Panels": panels_dict,
    }
    return _round_floats(out)


def to_yaml(export: dict[str, Any]) -> str:
    """Serialise the export dict to YAML without hard-dep on PyYAML.

    We implement a *very* small YAML emitter that handles our subset:
    - strings, ints, floats, bools
    - nested mappings with 2-space indent
    - block-style lists ('- ')

    Falls back to PyYAML if available for richer features.
    """
    try:
        import yaml  # type: ignore

        return yaml.safe_dump(export, sort_keys=False, default_flow_style=False)
    except ImportError:
        return _mini_yaml_dump(export)


def _mini_yaml_dump(obj: Any, indent: int = 0) -> str:
    """Tiny YAML emitter for our export dict only."""
    pad = "  " * indent
    lines: list[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{pad}{k}:")
                lines.append(_mini_yaml_dump(v, indent + 1))
            else:
                lines.append(f"{pad}{k}: {_yaml_scalar(v)}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                # First key inline with '-', rest indented
                kv = list(item.items())
                if kv:
                    first_k, first_v = kv[0]
                    rest = kv[1:]
                    if isinstance(first_v, (dict, list)) and first_v:
                        lines.append(f"{pad}- {first_k}:")
                        lines.append(_mini_yaml_dump(first_v, indent + 2))
                    else:
                        lines.append(f"{pad}- {first_k}: {_yaml_scalar(first_v)}")
                    for k, v in rest:
                        if isinstance(v, (dict, list)) and v:
                            lines.append(f"{pad}  {k}:")
                            lines.append(_mini_yaml_dump(v, indent + 2))
                        else:
                            lines.append(f"{pad}  {k}: {_yaml_scalar(v)}")
            else:
                lines.append(f"{pad}- {_yaml_scalar(item)}")
    else:
        lines.append(f"{pad}{_yaml_scalar(obj)}")
    return "\n".join(lines)


def _yaml_scalar(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v)
    if any(c in s for c in (":", "#", "\n")) or s.startswith(("-", "?", "!")) or s in ("null", "true", "false"):
        s = s.replace('"', '\\"')
        return f'"{s}"'
    return s


def export_config(
    backend: Any | None = None,
    *,
    path: str | None = None,
) -> str:
    """Build, serialise, and (optionally) persist the export.

    Returns the YAML text. If ``path`` is provided, also writes to it.
    """
    if backend is None:
        from rviz_mcp.backend import get_backend

        backend = get_backend()

    payload = build_export(backend)
    text = to_yaml(payload)

    if path:
        from pathlib import Path

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")

    return text
