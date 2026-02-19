from __future__ import annotations
import re
from typing import Dict, Iterable, List
from .schemas import Component, DesignResponse


def _format_node_id(name: str) -> str:
    # sanitize names to valid Mermaid identifiers while guaranteeing uniqueness
    cleaned = re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_")
    return cleaned.lower() or "node"


def _build_flowchart_from_components(components: Iterable[Component]) -> str:
    flowchart: List[str] = ["flowchart LR"]
    ids: Dict[str, str] = {}
    used_ids: set[str] = set()

    def _unique_id(raw_name: str) -> str:
        base = _format_node_id(raw_name)
        candidate = base
        idx = 2
        while candidate in used_ids:
            candidate = f"{base}_{idx}"
            idx += 1
        used_ids.add(candidate)
        return candidate

    for component in components:
        node_id = _unique_id(component.name)
        ids[component.name] = node_id
        flowchart.append(f"    {node_id}[{component.name}]")

    for component in components:
        source_id = ids[component.name]
        for connection in component.connections:
            target_id = ids.get(connection, _format_node_id(connection))
            flowchart.append(f"    {source_id} --> {target_id}")

    return "\n".join(flowchart)


def build_diagram(response: DesignResponse) -> str:
    # Prefer the diagram authored by the LLM, fallback to component graph if missing.
    candidate = response.mermaid_diagram.strip()
    if candidate:
        return candidate
    return _build_flowchart_from_components(response.components)
