import ipywidgets as widgets
import networkx as nx
from IPython.display import display
from ipycanvas import Canvas, hold_canvas
from ipyevents import Event

from pygraphedit.visual_graph import VisualGraph

NODE_CLICK_RADIUS = 15


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

    with hold_canvas():
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

    dragged_object = None
    is_drag = False

    def handle_mousedown(event):
        nonlocal dragged_object
        clicked_node, dist = visual_graph.get_closest_node((event['relativeX'], event['relativeY']))
        if dist < NODE_CLICK_RADIUS:
            dragged_object = clicked_node

    def handle_mousemove(event):
        nonlocal dragged_object, is_drag
        if dragged_object is not None:
            is_drag = True
            pos = (event['relativeX'], event['relativeY'])
            visual_graph.move_node(dragged_object, pos)
            draw_graph(canvas, visual_graph)

    def handle_mouseup(event):
        nonlocal dragged_object, is_drag
        dragged_object = None
        if is_drag:
            is_drag = False
            return
        pos = (event['relativeX'], event['relativeY'])
        node, dist = visual_graph.get_closest_node(pos)
        if dist < NODE_CLICK_RADIUS:
            node = visual_graph.get_closest_node(pos)[0]

            if visual_graph.selected_node is None:
                visual_graph.selected_node = node

            elif visual_graph.selected_node == node:
                visual_graph.selected_node = None

            else:
                if visual_graph.graph.has_edge(visual_graph.selected_node, node):
                    visual_graph.remove_edge(visual_graph.selected_node, node)
                else:
                    visual_graph.add_edge(visual_graph.selected_node, node)
                visual_graph.selected_node = None
        else:
            visual_graph.add_node(mex(visual_graph.graph.nodes), pos)
            visual_graph.selected_node = None

        draw_graph(canvas, visual_graph)

    def handle_doubleclick(event):
        pos = (event['relativeX'], event['relativeY'])
        clicked_node, dist = visual_graph.get_closest_node(pos)
        debug_text.value = str(clicked_node)
        if dist < NODE_CLICK_RADIUS:
            visual_graph.remove_node(clicked_node)
            visual_graph.selected_node = None
            draw_graph(canvas, visual_graph)

    Event(source=canvas, watched_events=['mousedown']).on_dom_event(handle_mousedown)
    Event(source=canvas, watched_events=['mousemove'], wait=1000//60).on_dom_event(handle_mousemove)
    Event(source=canvas, watched_events=['mouseup']).on_dom_event(handle_mouseup)
    Event(source=canvas, watched_events=['dblclick']).on_dom_event(handle_doubleclick)

    draw_graph(canvas, visual_graph)

    # main widget view
    main_box = widgets.HBox(
        [debug_text, canvas]
    )
    # Display the widgets
    display(main_box)
