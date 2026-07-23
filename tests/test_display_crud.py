"""CRUD tests for display operations in mock backend."""

from rviz_mcp.backend.mock import MockBackend


def test_add_display_basic():
    """Test adding a basic display."""
    b = MockBackend()
    initial_count = len(b.list_displays())
    
    result = b.add_display("TestDisplay", "rviz_default_plugins/Marker", "/test/topic")
    
    assert result["ok"] is True
    assert result["display"]["name"] == "TestDisplay"
    assert result["display"]["class"] == "rviz_default_plugins/Marker"
    assert result["display"]["topic"] == "/test/topic"
    assert result["display"]["enabled"] is True
    
    displays = b.list_displays()
    assert len(displays) == initial_count + 1
    assert any(d["name"] == "TestDisplay" for d in displays)


def test_add_display_custom_enabled():
    """Test adding display with custom enabled state."""
    b = MockBackend()
    
    # Disabled display
    result = b.add_display("DisabledDisplay", "rviz_default_plugins/Marker", "", enabled=False)
    assert result["ok"] is True
    assert result["display"]["enabled"] is False
    
    displays = b.list_displays()
    disp = next(d for d in displays if d["name"] == "DisabledDisplay")
    assert disp["enabled"] is False
    
    # Enabled display (explicit)
    result = b.add_display("EnabledDisplay", "rviz_default_plugins/Marker", "", enabled=True)
    assert result["ok"] is True
    assert result["display"]["enabled"] is True


def test_add_display_duplicate_name():
    """Test adding display with duplicate name fails."""
    b = MockBackend()
    
    # Add first display
    result1 = b.add_display("Duplicate", "rviz_default_plugins/Marker", "/topic1")
    assert result1["ok"] is True
    
    # Try to add duplicate
    result2 = b.add_display("Duplicate", "rviz_default_plugins/Marker", "/topic2")
    assert result2["ok"] is False
    assert "already exists" in result2["error"]


def test_remove_display_success():
    """Test removing an existing display."""
    b = MockBackend()
    
    # Add a display
    b.add_display("ToRemove", "rviz_default_plugins/Marker", "/remove/topic")
    assert len(b.list_displays()) == 4  # Grid, TF, RobotModel + ToRemove
    
    # Remove it
    result = b.remove_display("ToRemove")
    assert result["ok"] is True
    assert result["removed"] == "ToRemove"
    
    # Verify it's gone
    displays = b.list_displays()
    assert len(displays) == 3
    assert not any(d["name"] == "ToRemove" for d in displays)


def test_remove_display_nonexistent():
    """Test removing a non-existent display fails."""
    b = MockBackend()
    
    result = b.remove_display("DoesNotExist")
    assert result["ok"] is False
    assert "unknown display" in result["error"]


def test_remove_display_protected():
    """Test that protected displays cannot be removed."""
    b = MockBackend()
    
    # Try to remove Grid (protected in seed)
    result = b.remove_display("Grid")
    assert result["ok"] is False
    assert "cannot remove Grid in mock seed" in result["error"]
    
    # Verify Grid still exists
    displays = b.list_displays()
    assert any(d["name"] == "Grid" for d in displays)


def test_list_displays_structure():
    """Test that list_displays returns correct structure."""
    b = MockBackend()
    displays = b.list_displays()
    
    # Should have initial seeded displays
    assert len(displays) >= 3
    
    # Check each display has required fields
    for display in displays:
        assert "name" in display
        assert "class" in display
        assert "enabled" in display
        assert "topic" in display
        assert isinstance(display["name"], str)
        assert isinstance(display["class"], str)
        assert isinstance(display["enabled"], bool)
        assert isinstance(display["topic"], str)


def test_list_displays_after_add_remove():
    """Test list_displays reflects add/remove operations."""
    b = MockBackend()
    initial = b.list_displays()
    initial_names = {d["name"] for d in initial}
    
    # Add two displays
    b.add_display("DisplayA", "rviz_default_plugins/Marker", "/topic/a")
    b.add_display("DisplayB", "rviz_default_plugins/Marker", "/topic/b")
    
    after_add = b.list_displays()
    after_add_names = {d["name"] for d in after_add}
    assert after_add_names == initial_names | {"DisplayA", "DisplayB"}
    assert len(after_add) == len(initial) + 2
    
    # Remove one display
    b.remove_display("DisplayA")
    
    after_remove = b.list_displays()
    after_remove_names = {d["name"] for d in after_remove}
    assert after_remove_names == initial_names | {"DisplayB"}
    assert len(after_remove) == len(initial) + 1