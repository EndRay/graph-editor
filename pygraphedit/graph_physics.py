import pymunk

from pygraphedit.debug import debug_text
from pygraphedit.visual_graph import VisualGraph

def create_border(space, width, height):
    # Create the ground (static) segment
    ground = pymunk.Segment(space.static_body, (0, 0), (width, 0), 5)
    ground.friction = 1.0
    space.add(ground)

    # Create the ceiling (static) segment
    ceiling = pymunk.Segment(space.static_body, (0, height), (width, height), 5)
    ceiling.friction = 1.0
    space.add(ceiling)

    # Create the left (static) segment
    left_wall = pymunk.Segment(space.static_body, (0, 0), (0, height), 5)
    left_wall.friction = 1.0
    space.add(left_wall)

    # Create the right (static) segment
    right_wall = pymunk.Segment(space.static_body, (width, 0), (width, height), 5)
    right_wall.friction = 1.0
    space.add(right_wall)

class GraphPhysics:
    def __init__(self, visual_graph: VisualGraph):
        self.visual_graph = visual_graph
        self.space = pymunk.Space()
        create_border(self.space, 800, 500)
        self.space.gravity = (0, 0)
        self.verticesBody = {}
        self.edgeBody = {}
        for node in visual_graph.graph.nodes:
            self.add_vert(node, visual_graph.coordinates[node])
        visual_graph.add_node.subscribable.subscribe(self.add_vert)
        visual_graph.remove_node.subscribable.subscribe(self.remove_vert)
        visual_graph.add_edge.subscribable.subscribe(self.add_edge)
        visual_graph.remove_edge.subscribable.subscribe(self.remove_edge)
        visual_graph.move_node.subscribable.subscribe(self.move_node)

    def add_vert(self, node, pos: (int, int)):
        body = pymunk.Body(1, 1)
        body.position = pos
        shape = pymunk.Circle(body, radius=10)  # Adjust the radius as needed
        shape.elasticity = 1.0  # Elasticity of collisions
        shape.friction = 0.0  # Friction of collisions
        self.space.add(body, shape)
        self.verticesBody[node] = body
        self.edgeBody[node] = {}
        for node1, body1 in self.verticesBody.items():
            if node1 != node:
                self.space.add(
                    pymunk.DampedSpring(body, body1, (0, 0), (0, 0), rest_length=200, stiffness=10, damping=2))

    def remove_vert(self, node):
        self.space.remove(self.verticesBody[node])
        del self.verticesBody[node]
        del self.edgeBody[node]

    def add_edge(self, node1, node2):
        edgeBody = pymunk.DampedSpring(self.verticesBody[node1], self.verticesBody[node2], (0, 0), (0, 0), rest_length=100, stiffness=500, damping=2)
        self.space.add(edgeBody)
        self.edgeBody[node1][node2] = edgeBody
        self.edgeBody[node2][node1] = edgeBody

    def remove_edge(self, node1, node2):
        body = self.edgeBody[node1][node2]
        self.space.remove(body)
        del self.edgeBody[node1][node2]
        del self.edgeBody[node2][node1]

    def move_node(self, node, pos: (int, int)):
        self.verticesBody[node].position = pos

    def update_physics(self, dt):
        self.space.step(dt)
        for node, body in self.verticesBody.items():
            self.visual_graph.move_node(node, body.position)
