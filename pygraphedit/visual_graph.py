import random

import networkx as nx
import numpy as np

from pygraphedit.settings import NODE_RADIUS
from pygraphedit.subscribe import subscribable


class VisualGraph:
    def __init__(self, graph: nx.Graph, bounds: (int, int)):
        self.graph = graph
        self.bounds = bounds
        self.coordinates = {
            node: [random.randint(0, bounds[0]-1), random.randint(0, bounds[1]-1)]
            for node in graph.nodes
        }
        self.selected_node = None
        self.dragged_node = None

    @subscribable
    def add_node(self, node, pos: (int, int)):
        self.graph.add_node(node)
        self.coordinates[node] = pos

    @subscribable
    def add_edge(self, node1, node2):
        self.graph.add_edge(node1, node2)

    @subscribable
    def remove_node(self, node):
        self.graph.remove_node(node)
        del self.coordinates[node]

    @subscribable
    def remove_edge(self, node1, node2):
        self.graph.remove_edge(node1, node2)

    @subscribable
    def move_node(self, node, pos: (int, int)):
        if node not in self.graph.nodes:
            raise ValueError("Node not in graph")
        self.coordinates[node] = pos

    @subscribable
    def drag_start(self, node):
        self.dragged_node = node

    @subscribable
    def drag_end(self):
        self.dragged_node = None

    def get_closest_node(self, pos: (int, int)) -> (any, float):
        closest_node = None
        closest_dist = float("inf")
        for node, node_pos in self.coordinates.items():
            dist = np.linalg.norm(np.array(pos) - node_pos)
            if dist < closest_dist:
                closest_dist = dist
                closest_node = node
        return closest_node, closest_dist

    def normalize_positions(self):
        for node, node_pos in self.coordinates.items():
            if node_pos[0] < 0:
                node_pos[0] = NODE_RADIUS
            if node_pos[1] < 0:
                node_pos[1] = NODE_RADIUS
            if node_pos[0] > self.bounds[0]:
                node_pos[0] = self.bounds[0] - NODE_RADIUS
            if node_pos[1] > self.bounds[1]:
                node_pos[1] = self.bounds[1 ] - NODE_RADIUS
