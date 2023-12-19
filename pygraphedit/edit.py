import threading
import time

import ipywidgets
import ipywidgets as widgets
import networkx as nx
from IPython.display import display
from ipycanvas import Canvas, hold_canvas
from ipyevents import Event
from pygraphedit.graph_physics import GraphPhysics
from pygraphedit.settings import DRAGGED_NODE_RADIUS, NODE_CLICK_RADIUS, NODE_RADIUS
from pygraphedit.visual_graph import VisualGraph
from functools import partial


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

    def draw_vertex(pos, size=10, colorcode="black"):
        canvas.fill_style = colorcode
        canvas.fill_circle(pos[0], pos[1], size)

    def draw_edge(pos1, pos2, colorcode="black"):
        canvas.stroke_style = colorcode
        canvas.line_width = 2
        canvas.stroke_line(*pos1, *pos2)

    with hold_canvas():
        clear_canvas()
        for node1, node2 in visual_graph.graph.edges:
            draw_edge(visual_graph.coordinates[node1], visual_graph.coordinates[node2])
        for node, pos in visual_graph.coordinates.items():
            draw_vertex(pos,
                        size=(DRAGGED_NODE_RADIUS if node == visual_graph.dragged_node else NODE_RADIUS),
                        colorcode=("red" if node == visual_graph.selected_node else "black"))


def edit(graph: nx.Graph):
    visual_graph = VisualGraph(graph, (800, 500))

    # creating canvas
    canvas = Canvas(width=800, height=500)
    add_new_label_button = ipywidgets.Button(description="Add new label",
                                             layout=widgets.Layout(width='125px', height='50px'))
    label_name_text_box = ipywidgets.Textarea(placeholder='Label name',
                                              layout=widgets.Layout(width='125px', height='50px'))
    labels_info = widgets.VBox()

    labels_info_scrollable = widgets.Output(layout={'overflow_y': 'scroll', 'height': '500px'})
    with labels_info_scrollable:
        display(labels_info)

    def add_label(button_widget, labels_info: widgets.VBox, visual_graph: VisualGraph, label_name: widgets.Textarea):
        new_label_name = str(label_name.value)
        if new_label_name in visual_graph.graph.nodes[visual_graph.selected_node].keys():
            return
        else:
            visual_graph.graph.nodes[visual_graph.selected_node][new_label_name] = None
        label_value = ipywidgets.Textarea(value="", layout=widgets.Layout(width='125px', height='50px'))
        label_label = ipywidgets.Label(value=str(label_name.value), layout=widgets.Layout(width='125px', height='50px'), justify_content='center')
        new_label = ipywidgets.HBox([label_label, label_value])

        def modify_label(change, visual_graph: VisualGraph):
            visual_graph.graph.nodes[visual_graph.selected_node][new_label_name] = change["new"]

        on_change = partial(modify_label, visual_graph=visual_graph)
        label_value.observe(on_change, names="value")
        labels_info.children = labels_info.children[:-1] + (new_label,) + labels_info.children[-1:]

    on_click = partial(add_label, labels_info=labels_info, visual_graph=visual_graph, label_name=label_name_text_box)
    add_new_label_button.on_click(on_click)
    is_drag = False
    start_mouse_position = (0, 0)
    actions_to_perform = []
    EPS = 10

    def perform_in_future(action):
        def event_consumer(*args, **kwargs):
            actions_to_perform.append((action, args, kwargs))
        return event_consumer

    def handle_mousedown(event):
        nonlocal start_mouse_position
        start_mouse_position = (event['relativeX'], event['relativeY'])
        clicked_node, dist = visual_graph.get_closest_node((event['relativeX'], event['relativeY']))
        if dist < NODE_CLICK_RADIUS:
            # dragged_object = clicked_node
            visual_graph.drag_start(clicked_node)

    def handle_mousemove(event):
        nonlocal is_drag, EPS
        distance =  abs(start_mouse_position[0] - event['relativeX']) + abs(start_mouse_position[1] - event['relativeY'])
        if visual_graph.dragged_node is not None and distance > EPS:
            is_drag = True
            pos = (event['relativeX'], event['relativeY'])
            visual_graph.move_node(visual_graph.dragged_node, pos)

    def update_labels(labels_info: widgets.VBox, visual_graph: VisualGraph):
        if visual_graph.selected_node is not None:
            labels_info.children = (ipywidgets.Label(value=f"Node {repr(visual_graph.selected_node)}", layout=widgets.Layout(width='250px', height='50px', justify_content='center')),)
            for i in visual_graph.graph.nodes[visual_graph.selected_node].keys():
                label_value = ipywidgets.Textarea(value=str(visual_graph.graph.nodes[visual_graph.selected_node][i]),
                                                  layout=widgets.Layout(width='125px', height='50px'))
                label_label = ipywidgets.Label(value=str(i), layout=widgets.Layout(width='125px', height='50px'))
                new_label = ipywidgets.HBox([label_label, label_value])

                def modify_label(change, visual_graph: VisualGraph):
                    visual_graph.graph.nodes[visual_graph.selected_node][i] = change["new"]

                on_change = partial(modify_label, visual_graph=visual_graph)
                label_value.observe(on_change, names="value")
                labels_info.children += (new_label,)
            labels_info.children += (widgets.VBox([widgets.HBox([label_name_text_box, add_new_label_button])]),)
        else:
            labels_info.children = (ipywidgets.Label(value=f"Click on node to update labels", layout=widgets.Layout(width='250px', height='50px', justify_content='center')),)

    def handle_mouseup(event):
        nonlocal is_drag
        visual_graph.drag_end()
        if is_drag:
            is_drag = False
            return
        pos = (event['relativeX'], event['relativeY'])
        node, dist = visual_graph.get_closest_node(pos)
        if dist < NODE_CLICK_RADIUS:
            node = visual_graph.get_closest_node(pos)[0]

            if visual_graph.selected_node is None:
                visual_graph.selected_node = node
                update_labels(labels_info, visual_graph)

            elif visual_graph.selected_node == node:
                visual_graph.selected_node = None
                update_labels(labels_info, visual_graph)

            else:
                if visual_graph.graph.has_edge(visual_graph.selected_node, node):
                    visual_graph.remove_edge(visual_graph.selected_node, node)
                else:
                    visual_graph.add_edge(visual_graph.selected_node, node)
        else:
            if visual_graph.selected_node is None:
                new_node = mex(visual_graph.graph.nodes)
                visual_graph.add_node(new_node, pos)
            else:
                visual_graph.selected_node = None
                update_labels(labels_info, visual_graph)

    def handle_doubleclick(event):
        pos = (event['relativeX'], event['relativeY'])
        clicked_node, dist = visual_graph.get_closest_node(pos)
        if dist < NODE_CLICK_RADIUS:
            visual_graph.remove_node(clicked_node)
            visual_graph.selected_node = None

    Event(source=canvas, watched_events=['mousedown']).on_dom_event(perform_in_future(handle_mousedown))
    Event(source=canvas, watched_events=['mousemove'], wait=1000 // 60).on_dom_event(perform_in_future(handle_mousemove))
    Event(source=canvas, watched_events=['mouseup']).on_dom_event(perform_in_future(handle_mouseup))
    Event(source=canvas, watched_events=['dblclick']).on_dom_event(perform_in_future(handle_doubleclick))

    debug_text = widgets.Textarea()

    # main widget view
    main_box = widgets.HBox(
        [labels_info_scrollable, canvas]
    )

    # Display the widgets
    display(main_box)
    update_labels(labels_info, visual_graph)
    graph_physics = GraphPhysics(visual_graph)

    def main_loop(visual_graph):
        try:
            while True:
                graph_physics.update_physics(1 / 60)
                graph_physics.normalize_positions()
                draw_graph(canvas, visual_graph)
                time.sleep(1 / 60)
                for (action, args, kwargs) in actions_to_perform:
                    action(*args, **kwargs)
                actions_to_perform.clear()
        except Exception as e:
            debug_text.value = repr(e)


    thread = threading.Thread(target=main_loop, args=(visual_graph,))
    thread.start()
