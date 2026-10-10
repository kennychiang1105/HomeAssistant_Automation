"""Spatial Context & Perception for Home Assistant AI 4.0."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _load_spatial_data(hass: HomeAssistant) -> dict[str, Any]:
    config_dir = hass.config.path()
    scene_graph_path = os.path.join(config_dir, "spatial_scene_graph.json")
    spatial_context_path = os.path.join(config_dir, "memory", "spatial_context.md")

    scene_graph: dict[str, Any] = {}
    if os.path.exists(scene_graph_path):
        try:
            with open(scene_graph_path, "r", encoding="utf-8") as f:
                scene_graph = json.load(f)
            _LOGGER.debug("Loaded spatial_scene_graph with %d floors", len(scene_graph.get("floors", {})))
        except Exception as err:
            _LOGGER.error("Failed to load %s: %s", scene_graph_path, err)
    else:
        _LOGGER.warning("Spatial scene graph file not found at %s", scene_graph_path)

    spatial_context_md = ""
    if os.path.exists(spatial_context_path):
        try:
            with open(spatial_context_path, "r", encoding="utf-8") as f:
                spatial_context_md = f.read()
        except Exception as err:
            _LOGGER.error("Failed to load %s: %s", spatial_context_path, err)

    return {
        "scene_graph": scene_graph,
        "spatial_context_md": spatial_context_md,
    }


def _patch_stream_rtsps() -> None:
    """Patch stream worker to support RTSPS with self-signed TLS certificates (e.g. UniFi Protect)."""
    try:
        from homeassistant.components.stream import worker as stream_worker

        if not getattr(stream_worker, "_rtsps_tls_patched", False):
            orig_try_open = stream_worker.try_open_stream

            def patched_try_open_stream(source: str, pyav_options: dict[str, str]):
                if isinstance(source, str) and source.startswith("rtsps://"):
                    pyav_options = dict(pyav_options)
                    pyav_options.setdefault("tls_verify", "0")
                    pyav_options.setdefault("rtsp_flags", "prefer_tcp")
                    if "timeout" not in pyav_options and "stimeout" not in pyav_options:
                        pyav_options["timeout"] = "5000000"
                return orig_try_open(source, pyav_options)

            stream_worker.try_open_stream = patched_try_open_stream
            stream_worker._rtsps_tls_patched = True
            _LOGGER.info(
                "Successfully patched stream_worker for RTSPS self-signed certificates (tls_verify=0)"
            )
    except Exception as err:
        _LOGGER.warning("Could not patch stream_worker for RTSPS: %s", err)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the spatial_context integration."""
    _LOGGER.info("Initializing Spatial Context & AI Perception integration")

    _patch_stream_rtsps()

    data = await hass.async_add_executor_job(_load_spatial_data, hass)
    hass.data[DOMAIN] = data

    async def handle_reload(call: ServiceCall) -> None:
        """Reload spatial data from disk without restarting."""
        new_data = await hass.async_add_executor_job(_load_spatial_data, hass)
        hass.data[DOMAIN].update(new_data)
        _LOGGER.info("Spatial context data reloaded successfully")

    hass.services.async_register(DOMAIN, "reload", handle_reload)
    return True

