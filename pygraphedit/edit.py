import ipywidgets as widgets
from ipyevents import Event
from IPython.display import display
from ipycanvas import Canvas
import numpy as np
import networkx as nx
from scipy.spatial import distance

from pygraphedit.visual_graph import VisualGraph


def edit(graph: nx.Graph):
    visual_graph = VisualGraph(graph, (800, 500))

    vert_tool = True

    # creating toolbox
    tools = widgets.RadioButtons(
        value='Vertices',
        options=['Vertices', 'Edges'],
        description='Tools:'
    )

    debug_text = widgets.Textarea(
        value='',
        placeholder='Debug',
    )

    def tool_change(change):
        nonlocal vert_tool
        if change['type'] != 'change' or change['name'] != 'value':
            return
        elif change['new'] == 'Vertices':
            vert_tool = True
            visual_graph.selected_node = None
        else:
            vert_tool = False

    tools.observe(tool_change)

    toolbox = widgets.VBox(
        [tools]
    )

    # creating canvas
    canvas = Canvas(width=800, height=500)

    # click event handling
    d = Event(source=canvas, watched_events=['click', 'drag'])  # , 'keydown', 'mouseenter'

    def draw_graph(canvas: Canvas, visual_graph: VisualGraph):
        def clear_canvas():
            canvas.clear()
            canvas.stroke_style = "black"
            canvas.stroke_rect(0, 0, 800, 500)

        def draw_vertex(pos, colorcode="black"):
            canvas.fill_style = colorcode
            canvas.fill_circle(pos[0], pos[1], 5)

        def draw_edge(pos1, pos2, colorcode="black"):
            canvas.stroke_style = colorcode
            canvas.line_width = 2
            canvas.stroke_line(*pos1, *pos2)

        clear_canvas()
        for node1, node2 in visual_graph.graph.edges:
            draw_edge(visual_graph.coordinates[node1], visual_graph.coordinates[node2])
        for node, pos in visual_graph.coordinates.items():
            if node == visual_graph.selected_node:
                draw_vertex(pos, "red")
            else:
                draw_vertex(pos)

    def mex(arr):
        result = 0
        while result in arr:
            result += 1
        return result

    def handle_event(event):
        ev_x = event['relativeX']
        ev_y = event['relativeY']
        pos = (ev_x, ev_y)
        if vert_tool:
            clicked_node, dist = visual_graph.get_closest_node(pos)
            if dist < 10:
                visual_graph.remove_node(clicked_node)
            else:
                visual_graph.add_node(mex(visual_graph.graph.nodes), pos)
        else:
            clicked_node = visual_graph.get_closest_node(pos)[0]

            if visual_graph.selected_node is None:
                visual_graph.selected_node = clicked_node

            elif visual_graph.selected_node == clicked_node:
                visual_graph.selected_node = None

            else:
                if visual_graph.graph.has_edge(visual_graph.selected_node, clicked_node):
                    visual_graph.remove_edge(visual_graph.selected_node, clicked_node)
                else:
                    visual_graph.add_edge(visual_graph.selected_node, clicked_node)
                visual_graph.selected_node = None
        draw_graph(canvas, visual_graph)

    draw_graph(canvas, visual_graph)
    d.on_dom_event(handle_event)

    # main widget view
    main_box = widgets.HBox(
        [widgets.VBox([toolbox, debug_text]), canvas]
    )
    # Display the widgets
    display(main_box)
