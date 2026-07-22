import os
import tempfile
import yaml
import pytest
from src.config import MockConfig
from src.export_config import export_config

def test_export_config():
    # Create a test configuration
    config = MockConfig()
    config.add_display("test_display", "test_type", True)
    config.add_fixed_frame("test_frame", "parent_frame")
    config.add_view("test_view", "test_type", {"property": "value"})

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name

    try:
        # Export the configuration
        export_config(config, temp_path)

        # Verify the exported file
        with open(temp_path, 'r') as f:
            exported_data = yaml.safe_load(f)

        assert 'displays' in exported_data
        assert 'fixed_frames' in exported_data
        assert 'views' in exported_data
        assert len(exported_data['displays']) == 1
        assert len(exported_data['fixed_frames']) == 1
        assert len(exported_data['views']) == 1

    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_export_config_error_handling():
    # Test with invalid configuration
    with pytest.raises(ValueError):
        export_config(None, "invalid_path.yaml")