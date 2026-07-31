"""Tests for rviz2_bridge module."""
import pytest
from rviz_mcp.rviz2_bridge import MockRViz2Backend, RViz2RemoteClient


class TestMockRViz2Backend:
    
    def setup_method(self):
        self.mock = MockRViz2Backend()
    
    def test_set_view(self):
        result = self.mock.set_view([1, 2, 3], [0, 0, 0, 1])
        assert result["ok"] is True
        assert result["point"] == [1, 2, 3]
        assert result["orientation"] == [0, 0, 0, 1]
    
    def test_add_and_remove_marker(self):
        pose = {"position": {"x": 1, "y": 2, "z": 3}, "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}}
        result = self.mock.add_marker("test_topic", "sphere", pose, {"x": 0.5, "y": 0.5, "z": 0.5}, [1, 0, 0])
        assert result["ok"] is True
        assert result["topic"] == "test_topic"
        
        marker_id = result["marker_id"]
        result2 = self.mock.remove_marker("test_topic", marker_id)
        assert result2["ok"] is True
    
    def test_clear_all_markers(self):
        pose = {"position": {"x": 0}, "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}}
        self.mock.add_marker("topic1", "cube", pose, {"x": 1}, [0, 1, 0])
        self.mock.add_marker("topic2", "sphere", pose, {"x": 1}, [0, 0, 1])
        
        result = self.mock.clear_all_markers()
        assert result["ok"] is True
        assert result["count"] == 2
    
    def test_set_display_type(self):
        result = self.mock.set_display_type("laser_scan", "points")
        assert result["ok"] is True
        assert result["display_type"] == "points"
    
    def test_get_display_list(self):
        self.mock.set_display_type("topic_a", "lines")
        self.mock.set_display_type("topic_b", "mesh")
        result = self.mock.get_display_list()
        assert result["ok"] is True
        assert len(result["displays"]) == 2
    
    def test_clip_planes(self):
        assert self.mock.set_clip_near(0.01)["ok"] is True
        assert self.mock.set_clip_far(1000.0)["ok"] is True
    
    def test_reset(self):
        self.mock.add_marker("t", "cube", {"position": {"x": 0}, "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}}, {"x": 1}, [1, 1, 1])
        result = self.mock.reset()
        assert result["ok"] is True
        displays = self.mock.get_display_list()
        assert len(displays["displays"]) == 0


class TestRViz2RemoteClient:
    
    def test_client_lifecycle(self):
        client = RViz2RemoteClient(host="localhost", port=9090)
        assert client.connect() is True
        assert client.connected is True
        client.disconnect()
        assert client.connected is False
    
    def test_set_view(self):
        client = RViz2RemoteClient()
        client.connect()
        result = client.set_view([10, 20, 30], [0, 0, 0, 1])
        assert result["ok"] is True
        client.disconnect()
    
    def test_add_marker(self):
        client = RViz2RemoteClient()
        client.connect()
        pose = {"position": {"x": 0}, "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}}
        result = client.add_marker("topic", "sphere", pose, {"x": 1}, [1, 0, 0])
        assert result["ok"] is True
        assert "marker_id" in result
        client.disconnect()
