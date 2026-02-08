"""Build a NetworkX graph from KConfig items)"""

import re
from enum import StrEnum
from pathlib import Path

import networkx as nx

from ._models import KConfigDoc


class RelationType(StrEnum):
    DEFINES = "defines"
    SELECTS = "selects"
    IMPLIES = "implies"
    DEPENDS_ON = "depends_on"


# Regex to find tokens starting with CONFIG_
# \b ensures we don't match partial words if that ever happens
SYMBOL_PATTERN = re.compile(r"\bCONFIG_[A-Z0-9_]+\b")


def _parse_deps(logic_str: str) -> list[str]:
    if not logic_str:
        return []

    # 2. Find all matches
    matches = SYMBOL_PATTERN.findall(logic_str)

    # 3. Return unique list (set comprehension) to avoid duplicate edges
    return list(set(matches))


def _safe_add_edge(
    G: nx.DiGraph,
    source_def_id: str,
    target_symbol_name: str,
    relation_type: RelationType,
) -> None:
    additional_props = {}

    symbol_name = target_symbol_name

    if relation_type in [RelationType.SELECTS, RelationType.IMPLIES]:
        if "if" in target_symbol_name:
            sel_name, _, condition = target_symbol_name.partition(" if ")
            sel_name = sel_name.strip()
            condition = condition.strip()
            symbol_name = sel_name  # The actual symbol being selected/implied
            additional_props["condition"] = condition

    # Ensure the target symbol exists with the correct label
    if not G.has_node(symbol_name):
        G.add_node(symbol_name, node_type="symbol")

    G.add_edge(
        source_def_id,
        symbol_name,
        relation=relation_type.value,
        **additional_props,
    )


def build_split_graph(kconfig_doc: KConfigDoc) -> nx.DiGraph:
    G = nx.DiGraph()

    for item in kconfig_doc.symbols:
        # 1. The Definition Node (The Source of Logic)
        # ID includes file/line to be unique
        def_id = f"{item.name}::{item.filename}:{item.linenr}"

        # All metadata (help, prompt, type) lives HERE, not on the symbol
        G.add_node(
            def_id,
            data_type=item.type,
            node_type="definition",
            prompt=item.prompt or "",
            help=item.help or "",
            filename=item.filename,
            raw_dependencies=item.dependencies or "",
        )

        # Connection: Definition -> Symbol
        _safe_add_edge(G, def_id, item.name, RelationType.DEFINES)

        # Handle Selects (with optional conditions)
        for sel in item.selects:
            _safe_add_edge(G, def_id, sel, RelationType.SELECTS)

        # Implies
        for imp in item.implies:
            _safe_add_edge(G, def_id, imp, RelationType.IMPLIES)

        # Dependencies
        for dep in _parse_deps(item.dependencies):
            _safe_add_edge(G, def_id, dep, RelationType.DEPENDS_ON)

    return G


def write_graphml(G: nx.DiGraph, output_path: Path) -> None:
    """Write the graph to a GraphML file."""
    nx.write_graphml(G, output_path)
