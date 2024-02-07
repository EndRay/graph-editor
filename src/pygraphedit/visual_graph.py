import random

import networkx as nx
import numpy as np

from .subscribe import subscribable


class VisualGraph:
    def __init__(self, graph: nx.Graph, bounds: (int, int)):
        self.graph = graph
        self.bounds = bounds

        self.edge_labels = set()
        self.vertex_labels = set()
        self.edge_edit = True
        self.vertex_edit = True

        self.coordinates = {
            node: [random.randint(0, bounds[0] - 1), random.randint(0, bounds[1] - 1)]
            for node in graph.nodes
        }
        self.selected_node = None
        self.selected_edge = None
        self.dragged_node = None

    @subscribable
    def add_node(self, node, pos: (int, int)):
        self.graph.add_node(node, **dict.fromkeys(self.vertex_labels, ""))
        self.coordinates[node] = pos

    @subscribable
    def add_edge(self, node1, node2):
        self.graph.add_edge(node1, node2, **dict.fromkeys(self.edge_labels, ""))

    @subscribable
    def remove_node(self, node):
        self.graph.remove_node(node)
        del self.coordinates[node]

    @subscribable
    def remove_edge(self, node1, node2):
        self.graph.remove_edge(node1, node2)

    def new_node_label(self, label):
        if label in self.vertex_labels:
            return
        else:
            self.vertex_labels.add(label)
            nx.set_node_attributes(self.graph, "", label)

    def new_edge_label(self, label):
        if label in self.edge_labels:
            return
        else:
            self.edge_labels.add(label)
            nx.set_edge_attributes(self.graph, "", label)
    
    def remove_edge_label(self, label):
        if not label in self.edge_labels:
            return
        else:
            self.edge_labels.remove(label)
            for v1, v2, d in self.graph.edges(data=True):
                del d[label]
            
    def remove_vertex_label(self, label):
        if not label in self.vertex_labels:
            return
        else:
            self.vertex_labels.remove(label)
            for v, d in self.graph.nodes(data=True):
                del d[label]
    
    def edit_edge_label(self, old_label, new_label):
        if (not old_label in self.edge_labels) or new_label in self.edge_labels:
            return
        else:
            self.edge_labels.remove(old_label)
            self.edge_labels.add(new_label)
            for v1,v2,d in self.graph.edges(data=True):
                d[new_label]=d[old_label]
                del d[old_label]

    def edit_node_label(self, old_label, new_label):
        if (not old_label in self.vertex_labels) or new_label in self.vertex_labels:
            return
        else:
            self.vertex_labels.remove(old_label)
            self.vertex_labels.add(new_label)
            for v, d in self.graph.nodes(data=True):
                d[new_label]=d[old_label]
                del d[old_label]

    
    def label_edge(self, edge, label, value):
        if label not in self.edge_labels:
            raise ValueError("Attribute for the label was not set")
        else:
            self.graph.edges[edge][label] = value

    def label_node(self, node, label, value):
        if label not in self.node_labels:
            raise ValueError("Attribute for the label was not set")
        else:
            self.graph.nodes[node][label] = value

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

    def get_closest_edge(self, pos: (int, int)) -> (any, float):
        closest_edge = None
        closest_dist = float("inf")
        for u, v in self.graph.edges:
            p1 = np.array(self.coordinates[u])
            p2 = np.array(self.coordinates[v])
            p3 = np.array(pos)
            if np.dot(p3 - p1, p2 - p1) > 0 and np.dot(p3 - p2, p1 - p2) > 0:
                dist = np.linalg.norm(np.cross(p2 - p1, p3 - p1) / np.linalg.norm(p2 - p1))
            else:
                dist = min(np.hypot(*(p3 - p1)), np.hypot(*(p3 - p2)))
            if dist < closest_dist:
                closest_dist = dist
                closest_edge = (u, v)
        return closest_edge, closest_dist
