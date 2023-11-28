import ipywidgets as widgets
import networkx as nx
from IPython.display import display
from ipycanvas import Canvas
from ipyevents import Event

from pygraphedit.visual_graph import VisualGraph


def mex(arr):
    result = 0
    while result in arr:
        result += 1
    return result


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


def edit(graph: nx.Graph):
    visual_graph = VisualGraph(graph, (800, 500))

    debug_text = widgets.Textarea(
        value='',
        placeholder='Debug',
    )

    # creating canvas
    canvas = Canvas(width=800, height=500)

    canvas.auto_refresh = False

    # click event handling
    d = Event(source=canvas, watched_events=['click', 'dblclick'])  # , 'keydown', 'mouseenter'

    def handle_event(event):
        ev_x = event['relativeX']
        ev_y = event['relativeY']
        pos = (ev_x, ev_y)
        clicked_node, dist = visual_graph.get_closest_node(pos)
        if event['type'] == 'dblclick':
            if dist < 15:
                visual_graph.remove_node(clicked_node)
                visual_graph.selected_node = None
        elif event['type'] == 'click':
            if dist < 15:
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
            else:
                visual_graph.add_node(mex(visual_graph.graph.nodes), pos)

        draw_graph(canvas, visual_graph)

    draw_graph(canvas, visual_graph)
    d.on_dom_event(handle_event)

    # main widget view
    main_box = widgets.HBox(
        [debug_text, canvas]
    )
    # Display the widgets
    display(main_box)
