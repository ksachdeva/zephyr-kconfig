import networkx as nx

from ._models import KConfigDoc


class CmdState:
    def __init__(self) -> None:
        self._doc: KConfigDoc | None = None
        self._graph: nx.DiGraph | None = None

    @property
    def graph(self) -> nx.DiGraph:
        if self._graph is None:
            raise ValueError("Graph has not been built yet")
        return self._graph

    @graph.setter
    def graph(self, value: nx.DiGraph) -> None:
        self._graph = value

    @property
    def doc(self) -> KConfigDoc:
        if self._doc is None:
            raise ValueError("KConfigDoc has not been set")
        return self._doc

    @doc.setter
    def doc(self, value: KConfigDoc) -> None:
        self._doc = value
