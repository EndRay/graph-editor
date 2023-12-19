import pymunk

from pygraphedit.debug import debug_text
from pygraphedit.visual_graph import VisualGraph

VERTEX_BODY_MASS = 1
VERTEX_BODY_MOMENT = 1

def create_border(space, bounds: (int, int)):
    width, height = bounds
    # Create the ground (static) segment
    ground = pymunk.Segment(space.static_body, (0, -20), (width, -20), 20)
    ground.friction = 1.0
    space.add(ground)

    # Create the ceiling (static) segment
    ceiling = pymunk.Segment(space.static_body, (0, height + 20), (width, height + 20), 20)
    ceiling.friction = 1.0
    space.add(ceiling)

    # Create the left (static) segment
    left_wall = pymunk.Segment(space.static_body, (0, -20), (-20, height), 20)
    left_wall.friction = 1.0
    space.add(left_wall)

    # Create the right (static) segment
    right_wall = pymunk.Segment(space.static_body, (width + 20, 0), (width + 20, height), 20)
    right_wall.friction = 1.0
    space.add(right_wall)

class GraphPhysics:
    def __init__(self, visual_graph: VisualGraph):
        self.visual_graph = visual_graph
        self.space = pymunk.Space()
        create_border(self.space, visual_graph.bounds)
        self.space.gravity = (0, 0)
        self.vertices_body = {}
        self.edge_body = {}
        self.connection_body = {}
        for node in visual_graph.graph.nodes:
            self.add_vert(node, visual_graph.coordinates[node])
        for edge in visual_graph.graph.edges:
            self.add_edge(edge[0], edge[1])
        visual_graph.add_node.subscribable.subscribe(self.add_vert)
        visual_graph.remove_node.subscribable.subscribe(self.remove_vert)
        visual_graph.add_edge.subscribable.subscribe(self.add_edge)
        visual_graph.remove_edge.subscribable.subscribe(self.remove_edge)
        visual_graph.move_node.subscribable.subscribe(self.move_node)

        visual_graph.drag_start.subscribable.subscribe(self.drag_start)
        visual_graph.drag_end.subscribable.subscribe(self.drag_end)

    def drag_start(self, node):
        self.vertices_body[node].body_type = pymunk.Body.STATIC

    def drag_end(self):
        node = self.visual_graph.dragged_node
        if node is not None:
            self.vertices_body[node].body_type = pymunk.Body.DYNAMIC
            self.vertices_body[node].mass = VERTEX_BODY_MASS
            self.vertices_body[node].moment = VERTEX_BODY_MOMENT

    def add_vert(self, node, pos: (int, int)):
        body = pymunk.Body(VERTEX_BODY_MASS, VERTEX_BODY_MOMENT)
        body.position = pos
        shape = pymunk.Circle(body, radius=10)  # Adjust the radius as needed
        shape.elasticity = 1.0  # Elasticity of collisions
        shape.friction = 0.0  # Friction of collisions
        self.space.add(body, shape)
        self.vertices_body[node] = body
        self.edge_body[node] = {}
        self.connection_body[node] = {}
        for node1, body1 in self.vertices_body.items():
            if node1 != node:
                connection_body = pymunk.DampedSpring(body, body1, (0, 0), (0, 0), rest_length=200, stiffness=10, damping=2)
                self.space.add(connection_body)
                self.connection_body[node][node1] = connection_body
                self.connection_body[node1][node] = connection_body

    def remove_vert(self, node):
        self.space.remove(self.vertices_body[node])
        del self.vertices_body[node]
        for other in self.edge_body[node]:
            self.space.remove(self.edge_body[node][other])
            del self.edge_body[other][node]
        for other in self.connection_body[node]:
            self.space.remove(self.connection_body[node][other])
            del self.connection_body[other][node]
        del self.edge_body[node]
        del self.connection_body[node]

    def add_edge(self, node1, node2):
        edge_body = pymunk.DampedSpring(self.vertices_body[node1], self.vertices_body[node2], (0, 0), (0, 0), rest_length=100, stiffness=500, damping=2)
        self.space.add(edge_body)
        self.edge_body[node1][node2] = edge_body
        self.edge_body[node2][node1] = edge_body

    def remove_edge(self, node1, node2):
        body = self.edge_body[node1][node2]
        self.space.remove(body)
        del self.edge_body[node1][node2]
        del self.edge_body[node2][node1]

    def move_node(self, node, pos: (int, int)):
        self.vertices_body[node].position = pos

    def update_physics(self, dt):
        self.space.step(dt)
        for node, body in self.vertices_body.items():
            self.visual_graph.move_node(node, body.position)
