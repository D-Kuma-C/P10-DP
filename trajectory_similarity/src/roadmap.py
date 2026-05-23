import pandas as pd
import networkx as nx
from tqdm import tqdm
from collections import OrderedDict


class RoadMap:
    def __init__(self):
        self.graph = nx.Graph()
        self.segment_lengths = {}
        self.segment_to_nodes = {}
        self.node_positions = {}

        # Small pair cache.
        self._distance_cache = {}

        # Source-node cache, but bounded.
        self._source_distance_cache = OrderedDict()

        # Important for memory:
        # Distances beyond this are treated as "far away".
        self.max_distance_m = 10000.0

        # Number of source-node Dijkstra results to keep in memory.
        self.max_cached_sources = 128

    @classmethod
    def from_files(cls, nodes_file: str, edges_file: str):
        roadmap = cls()

        nodes = pd.read_csv(nodes_file)
        edges = pd.read_csv(edges_file)

        for _, row in nodes.iterrows():
            node_id = int(row["node_id"])
            roadmap.node_positions[node_id] = (float(row["lon"]), float(row["lat"]))
            roadmap.graph.add_node(node_id)

        for _, row in edges.iterrows():
            edge_id = int(row["edge_id"])
            u = int(row["start_node"])
            v = int(row["end_node"])
            length = float(row["length"])

            roadmap.graph.add_edge(u, v, weight=length, segment_id=edge_id)
            roadmap.segment_lengths[edge_id] = length
            roadmap.segment_to_nodes[edge_id] = (u, v)

        return roadmap

    @classmethod
    def from_osmnx_graph(cls, graph, edges_gdf):
        roadmap = cls()

        for node_id, data in graph.nodes(data=True):
            roadmap.node_positions[int(node_id)] = (float(data.get("x")), float(data.get("y")))
            roadmap.graph.add_node(int(node_id))

        for segment_id, (edge_key, row) in enumerate(edges_gdf.iterrows()):
            u, v, key = edge_key
            length = float(row.get("length", 0.0))

            roadmap.graph.add_edge(int(u), int(v), weight=length, segment_id=segment_id)
            roadmap.segment_lengths[segment_id] = length
            roadmap.segment_to_nodes[segment_id] = (int(u), int(v))

        return roadmap

    def shortest_path_distance(self, node_a: int, node_b: int) -> float:
        if node_a == node_b:
            return 0.0

        node_a = int(node_a)
        node_b = int(node_b)

        # Pair-level cache.
        pair_key = (node_a, node_b) if node_a <= node_b else (node_b, node_a)
        if pair_key in self._distance_cache:
            return self._distance_cache[pair_key]

        # Source-level cache with LRU behavior.
        if node_a in self._source_distance_cache:
            lengths = self._source_distance_cache.pop(node_a)
            self._source_distance_cache[node_a] = lengths
        else:
            try:
                lengths = nx.single_source_dijkstra_path_length(
                    self.graph,
                    node_a,
                    cutoff=self.max_distance_m,
                    weight="weight",
                )
            except nx.NodeNotFound:
                lengths = {}

            self._source_distance_cache[node_a] = lengths

            while len(self._source_distance_cache) > self.max_cached_sources:
                self._source_distance_cache.popitem(last=False)

        # If not reachable within cutoff, treat as far away.
        dist = float(lengths.get(node_b, self.max_distance_m))

        self._distance_cache[pair_key] = dist

        # Also bound pair cache.
        if len(self._distance_cache) > 500000:
            self._distance_cache.clear()

        return dist
