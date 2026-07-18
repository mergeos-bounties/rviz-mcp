"""RViz YAML export utilities."""

import yaml
from typing import Dict, Any, List


def config_to_rviz_yaml(config: Dict[str, Any]) -> str:
    """
    Convert a config_snapshot dict to RViz YAML format.
    
    Args:
        config: The config_snapshot dict from MockBackend.config_snapshot()
        
    Returns:
        YAML string representing the RViz configuration
    """
    if not config.get("ok", False):
        raise ValueError("Invalid config snapshot")
    
    # Build the RViz config structure
    rviz_config = {
        "Panels": [],
        "Visualization Manager": {
            "Class": "",
            "Displays": [],
            "Enabled": True,
            "Global Options": {
                "Background Color": [48, 48, 48],
                "Fixed Frame": config.get("fixed_frame", "map"),
                "Frame Rate": 30,
                "Sync": True
            },
            "Help": {},
            "Name": "Root",
            "Network Style": "",
            "Recent Topics": "",
            "Selection": "",
            "Sim Time": True,
            "Tools": [
                {
                    "Class": "rviz_default_plugins/Select",
                    "Enable": True,
                    "Hide Inactive Tools": True,
                    "Name": "Select"
                },
                {
                    "Class": "rviz_default_plugins/Focus",
                    "Enable": True,
                    "Hide Inactive Tools": True,
                    "Name": "Focus"
                },
                {
                    "Class": "rviz_default_plugins/MoveCamera",
                    "Enable": True,
                    "Hide Inactive Tools": True,
                    "Name": "Move Camera"
                },
                {
                    "Class": "rviz_default_plugins/Measure",
                    "Enable": True,
                    "Hide Inactive Tools": True,
                    "Name": "Measure"
                }
            ],
            "Tree": {
                "Filter Expanding": "",
                "Hide Empty Properties": True,
                "Hide Inactive Properties": True,
                "Resize Column Contents": True,
                "Show Hidden Properties": False
            },
            "Value": True
        },
        "Toolbars": []
    }
    
    # Add panels
    panels = config.get("panels", [])
    for panel in panels:
        rviz_config["Panels"].append({
            "Class": panel.get("class", "rviz_common/Panel"),
            "Embedded": False,
            "Floating": False,
            "Name": panel.get("name", "Panel"),
            "Title": panel.get("name", "Panel"),
            "Visible": panel.get("visible", True)
        })
    
    # Add displays
    displays = config.get("displays", [])
    for display in displays:
        rviz_config["Visualization Manager"]["Displays"].append({
            "Alpha": 1.0,
            "Autocompute Intensity Bounds": True,
            "Autocompute Value Bounds": {
                "Max Value": True,
                "Min Value": True
            },
            "Axis": "Z",
            "Channel Name": "",
            "Class": display.get("class", ""),
            "Color": [255, 255, 255],
            "Color Transformer": "FlatColor",
            "Enabled": display.get("enabled", True),
            "Alpha": 1.0,
            "Name": display.get("name", "Display"),
            "Status": {
                "Status": None
            },
            "Topic": display.get("topic", ""),
            "Value": True
        })
    
    # Set view controller
    view = config.get("view", {})
    if view:
        rviz_config["Visualization Manager"]["View Controllers"] = [{
            "Class": view.get("class", "rviz_default_plugins/Orbit"),
            "Distance": view.get("distance", 10.0),
            "Enable": True,
            "Focal Point": {
                "X": view.get("focal_point", {}).get("x", 0.0),
                "Y": view.get("focal_point", {}).get("y", 0.0),
                "Z": view.get("focal_point", {}).get("z", 0.0)
            },
            "Name": "View",
            "Pitch": view.get("pitch", 0.4),
            "Target Frame": "<Fixed Frame>",
            "Yaw": view.get("yaw", 0.5)
        }]
    
    # Convert to YAML
    return yaml.dump(rviz_config, default_flow_style=False, indent=2, sort_keys=False)


def save_rviz_config(config: Dict[str, Any], filepath: str) -> Dict[str, Any]:
    """
    Save config_snapshot as RViz YAML file.
    
    Args:
        config: The config_snapshot dict from MockBackend.config_snapshot()
        filepath: Path to save the RViz config file
        
    Returns:
        Dict with success status and file info
    """
    try:
        yaml_content = config_to_rviz_yaml(config)
        with open(filepath, 'w') as f:
            f.write(yaml_content)
        
        return {
            "ok": True,
            "saved": filepath,
            "format": "rviz_yaml",
            "display_count": config.get("display_count", 0)
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }