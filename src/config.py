# Add this import at the top of the file
from .export_config import export_config

# Add this method to the MockConfig class
def export_to_yaml(self, output_path: str) -> None:
    """
    Export this configuration to a YAML file.

    Args:
        output_path: Path to save the YAML file

    Raises:
        ValueError: If the export fails
    """
    export_config(self, output_path)