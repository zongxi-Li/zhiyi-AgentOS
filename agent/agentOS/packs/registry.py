from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PackManifest:
    """Metadata and registration entrypoint for an AgentOS workflow pack."""

    pack_id: str
    name: str
    version: str
    description: str
    module: str
    enabled: bool
    path: Path


def discover_pack_manifests(packs_dir: Path | None = None) -> tuple[PackManifest, ...]:
    root = packs_dir or Path(__file__).resolve().parent
    manifests = []
    for manifest_path in sorted(root.glob("*/manifest.yaml")):
        manifest = load_pack_manifest(manifest_path)
        if manifest.enabled:
            manifests.append(manifest)
    return tuple(manifests)


def load_pack_manifest(path: Path) -> PackManifest:
    data = _load_manifest_data(path)
    pack_id = str(data.get("id") or "").strip()
    if not pack_id:
        raise ValueError(f"pack manifest missing id: {path}")

    module = str(data.get("module") or f"agentos.packs.{pack_id}").strip()
    return PackManifest(
        pack_id=pack_id,
        name=str(data.get("name") or pack_id),
        version=str(data.get("version") or "0.0.0"),
        description=str(data.get("description") or ""),
        module=module,
        enabled=bool(data.get("enabled", True)),
        path=path,
    )


def register_installed_packs(
    *,
    agent_registry,
    workflow_registry,
    packs_dir: Path | None = None,
) -> tuple[PackManifest, ...]:
    registered = []
    for manifest in discover_pack_manifests(packs_dir):
        module = importlib.import_module(manifest.module)
        register_pack = getattr(module, "register_pack", None)
        if register_pack is None:
            raise ValueError(f"pack module missing register_pack: {manifest.module}")
        register_pack(agent_registry=agent_registry, workflow_registry=workflow_registry)
        registered.append(manifest)
    return tuple(registered)


def _load_manifest_data(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ModuleNotFoundError:
        data = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError(f"pack manifest must be an object: {path}")
    return data
