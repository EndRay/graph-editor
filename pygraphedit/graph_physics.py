import pymunk

class GraphPhysics:
    def __init__(self, visual_graph):
        self.visual_graph = visual_graph
        self.space = pymunk.Space()
        self.space.gravity = (0, 0)
        self.verticesBody = {}
        self.edgeBody = {}
        visual_graph.add_node.subscribable.subscribe(self.add_vert)
        visual_graph.remove_node.subscribable.subscribe(self.remove_vert)
        visual_graph.add_edge.subscribable.subscribe(self.add_edge)
        visual_graph.remove_edge.subscribable.subscribe(self.remove_edge)

    def add_vert(self, node, pos: (int, int)):
        body = pymunk.Body(1, float('inf'))  # Mass and moment of inertia are infinite for static bodies
        body.position = pos
        shape = pymunk.Circle(body, radius=10)  # Adjust the radius as needed
        shape.elasticity = 1.0  # Elasticity of collisions
        shape.friction = 0.0  # Friction of collisions
        self.space.add(body, shape)
        self.verticesBody[node] = body
        self.edgeBody[node] = {}

    def remove_vert(self, node):
        self.space.remove(self.verticesBody[node])
        del self.verticesBody[node]
        del self.edgeBody[node]

    def add_edge(self, node1, node2):
        edgeBody = pymunk.DampedSpring(self.verticesBody[node1], self.verticesBody[node2], rest_length=50, stiffness=1, damping=0.5)
        self.space.add(edgeBody)
        self.edgeBody[node1][node2] = edgeBody
        self.edgeBody[node2][node1] = edgeBody

    def remove_edge(self, node1, node2):
        body = self.edgeBody[node1][node2]
        self.space.remove(body)
        del self.edgeBody[node1][node2]
        del self.edgeBody[node2][node1]

    def update_physics(self, dt):
        self.space.step(dt)
        for node, body in self.verticesBody.items():
            self.visual_graph.move_node(node, body.position)
