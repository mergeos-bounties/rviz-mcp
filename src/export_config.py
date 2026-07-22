import yaml
from .config import MockConfig

def export_config(config: MockConfig, output_path: str) -> None:
    """
    Export a mock configuration to a simplified YAML format compatible with RViz2.

    Args:
        config: The mock configuration to export
        output_path: Path to save the YAML file

    Raises:
        ValueError: If the configuration cannot be exported
    """
    try:
        # Convert the mock config to a simplified dictionary structure
        export_data = {
            'displays': [],
            'fixed_frames': [],
            'views': []
        }

        # Add displays
        for display in config.displays:
            export_data['displays'].append({
                'name': display.name,
                'type': display.type,
                'enabled': display.enabled
            })

        # Add fixed frames
        for frame in config.fixed_frames:
            export_data['fixed_frames'].append({
                'name': frame.name,
                'parent': frame.parent
            })

        # Add views
        for view in config.views:
            export_data['views'].append({
                'name': view.name,
                'type': view.type,
                'properties': view.properties
            })

        # Write to YAML file
        with open(output_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False)

    except Exception as e:
        raise ValueError(f"Failed to export configuration: {str(e)}")