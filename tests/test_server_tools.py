import asyncio
import json

from rviz_mcp import server as srv


def test_tools_registered():
    assert callable(srv.rviz_doctor)
    assert callable(srv.rviz_add_display)
    assert callable(srv.rviz_list_panels)
    assert callable(srv.rviz_add_panel)
    assert callable(srv.rviz_remove_panel)
    assert "mock" in srv.rviz_mode()


def test_config_resource_registered():
    resources = asyncio.run(srv.mcp.list_resources())
    uris = {str(r.uri) for r in resources}
    assert "rviz://config" in uris


def test_config_resource_read():
    contents = asyncio.run(srv.mcp.read_resource("rviz://config"))
    # read_resource returns an iterable of content parts; take the first text.
    parts = list(contents)
    assert parts, "resource returned no content"
    payload = json.loads(parts[0].content)
    assert payload["ok"] is True
    assert "fixed_frame" in payload
    assert isinstance(payload["displays"], list)
    assert payload["display_count"] == len(payload["displays"])
