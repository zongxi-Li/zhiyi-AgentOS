"""AgentOS Core 的 Pack registry 模块，负责应用层 Pack 的发现、注册和资源定位。"""


from __future__ import annotations

import importlib
import inspect
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PackManifest:
    """AgentOS 工作流 Pack 的元数据和注册入口。"""

    pack_id: str
    name: str
    version: str
    description: str
    module: str
    enabled: bool
    capabilities: tuple[str, ...]
    path: Path


def discover_pack_manifests(packs_dir: Path | None = None) -> tuple[PackManifest, ...]:
    root = packs_dir or default_packs_dir()
    root = root.resolve()
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

    module = str(data.get("module") or f"packs.{pack_id}").strip()
    contributions = data.get("contributions") or {}
    if not isinstance(contributions, dict):
        raise ValueError(f"pack manifest contributions must be an object: {path}")
    capabilities = contributions.get("capabilities") or []
    if not isinstance(capabilities, list):
        raise ValueError(f"pack manifest capabilities must be an array: {path}")

    return PackManifest(
        pack_id=pack_id,
        name=str(data.get("name") or pack_id),
        version=str(data.get("version") or "0.0.0"),
        description=str(data.get("description") or ""),
        module=module,
        enabled=bool(data.get("enabled", True)),
        capabilities=tuple(str(item).strip() for item in capabilities if str(item).strip()),
        path=path,
    )


def register_installed_packs(
    *,
    agent_registry,
    workflow_registry,
    capability_catalog=None,
    packs_dir: Path | None = None,
) -> tuple[PackManifest, ...]:
    root = (packs_dir or default_packs_dir()).resolve()
    import_root = str(root.parent)
    if import_root not in sys.path:
        sys.path.insert(0, import_root)

    registered = []
    for manifest in discover_pack_manifests(root):
        module = importlib.import_module(manifest.module)
        register_pack = getattr(module, "register_pack", None)
        if register_pack is None:
            raise ValueError(f"pack module missing register_pack: {manifest.module}")
        kwargs = {
            "agent_registry": agent_registry,
            "workflow_registry": workflow_registry,
        }
        if "capability_catalog" in inspect.signature(register_pack).parameters:
            if capability_catalog is None:
                raise ValueError(
                    f"pack requires capability catalog: {manifest.module}"
                )
            kwargs["capability_catalog"] = capability_catalog
        register_pack(**kwargs)
        registered.append(manifest)
    return tuple(registered)


def default_packs_dir() -> Path:
    """返回应用层 Pack 目录。优先使用迁移后的 agent/packs 路径，旧路径仅作兜底。"""

    configured = os.getenv("AGENTOS_PACKS_DIR", "").strip()
    if configured:
        return Path(configured).resolve()
    project_root = Path(__file__).resolve().parents[4]
    return (project_root / "agent" / "packs").resolve()


def pack_path(pack_id: str, *parts: str) -> Path:
    """解析应用层 Pack 内部资源路径。"""

    return default_packs_dir().joinpath(pack_id, *parts)


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
