"""RemoteBridge stub — full API surface, returns ok:false for all endpoints."""

from __future__ import annotations

from typing import Any


class RemoteBridge:
    """Stub HTTP client for the remote RViz2 bridge.

    All methods return {"ok": False, "stub": True, ...}. In the next
    phase, these will be replaced with real HTTP calls to the bridge server.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8765",
        token: str | None = None,
        timeout: float = 5.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _stub(self, endpoint: str, **extra: Any) -> dict[str, Any]:
        return {
            "ok": False,
            "stub": True,
            "endpoint": endpoint,
            "message": "RemoteBridge stub — real HTTP client not yet wired",
            **extra,
        }

    # -- health --

    def health(self) -> dict[str, Any]:
        return self._stub("GET /health")

    # -- display CRUD --

    def list_displays(self) -> dict[str, Any]:
        return self._stub("GET /displays")

    def add_display(
        self,
        name: str,
        class_name: str = "rviz_default_plugins/Marker",
        topic: str = "",
        enabled: bool = True,
    ) -> dict[str, Any]:
        return self._stub("POST /displays", name=name)

    def remove_display(self, name: str) -> dict[str, Any]:
        return self._stub(f"DELETE /displays/{name}", name=name)

    def get_display(self, name: str) -> dict[str, Any]:
        return self._stub(f"GET /displays/{name}", name=name)

    def update_display(self, name: str, **props: Any) -> dict[str, Any]:
        return self._stub(f"PATCH /displays/{name}", name=name, props=props)

    # -- panels --

    def list_panels(self) -> dict[str, Any]:
        return self._stub("GET /panels")

    def add_panel(
        self,
        name: str,
        class_name: str = "rviz_common/Panel",
        dock: str = "left",
        visible: bool = True,
    ) -> dict[str, Any]:
        return self._stub("POST /panels", name=name)

    def remove_panel(self, name: str) -> dict[str, Any]:
        return self._stub(f"DELETE /panels/{name}", name=name)

    # -- fixed frame / view --

    def set_fixed_frame(self, frame: str) -> dict[str, Any]:
        return self._stub("PUT /fixed_frame", frame=frame)

    def set_view(
        self,
        view_class: str = "rviz_default_plugins/Orbit",
        distance: float = 10.0,
        yaw: float = 0.5,
        pitch: float = 0.4,
    ) -> dict[str, Any]:
        return self._stub("PUT /view", view_class=view_class)

    def view_presets(self) -> dict[str, Any]:
        return self._stub("GET /view/presets")

    def set_view_preset(self, name: str) -> dict[str, Any]:
        return self._stub(f"PUT /view/preset/{name}", name=name)

    # -- config I/O --

    def load_config(self, path: str) -> dict[str, Any]:
        return self._stub("POST /config/load", path=path)

    def save_config(self, path: str) -> dict[str, Any]:
        return self._stub("POST /config/save", path=path)

    # -- screenshot --

    def screenshot(self, path: str | None = None) -> dict[str, Any]:
        return self._stub("POST /screenshot", path=path)

    # -- topics --

    def list_topics(self) -> dict[str, Any]:
        return self._stub("GET /topics")

    def toggle_topic_visibility(self, display_name: str, topic: str) -> dict[str, Any]:
        return self._stub(
            f"POST /topics/{display_name}/visibility",
            display_name=display_name,
            topic=topic,
        )

    def get_topic_visibility(self, display_name: str) -> dict[str, Any]:
        return self._stub(
            f"GET /topics/{display_name}/visibility",
            display_name=display_name,
        )

    # -- display properties --

    def display_properties(self, display_name: str) -> dict[str, Any]:
        return self._stub(
            f"GET /displays/{display_name}/properties",
            display_name=display_name,
        )

    def update_display_properties(
        self,
        display_name: str,
        color: list[float] | None = None,
        size: float | None = None,
        alpha: float | None = None,
    ) -> dict[str, Any]:
        return self._stub(
            f"PATCH /displays/{display_name}/properties",
            display_name=display_name,
        )
