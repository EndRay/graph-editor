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
from enum import Enum
from pygraphedit.debug import debug_text
EDGE_CLICK_RADIUS =25


class Mode(Enum):
    STRUCTURE = 0
    PROPERTIES = 1

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
        for edge in visual_graph.graph.edges:
            draw_edge(visual_graph.coordinates[edge[0]], visual_graph.coordinates[edge[1]], colorcode=("red" if edge == visual_graph.selected_edge else "black"))
        for node, pos in visual_graph.coordinates.items():
            draw_vertex(pos,
                        size=(DRAGGED_NODE_RADIUS if node == visual_graph.dragged_node else NODE_RADIUS),
                        colorcode=("red" if node == visual_graph.selected_node else "black"))


def edit(graph: nx.Graph):
    visual_graph = VisualGraph(graph, (800, 500))

    # creating canvas
    canvas = Canvas(width=800, height=500)

    close_button = widgets.Button(description="", layout=widgets.Layout(width='50px', height='50px'), icon='window-close')
    physics_button = widgets.ToggleButton(
                                value=True,
                                description='',
                                disabled=False,
                                indent=False,
                                layout=widgets.Layout(width='50px', height='50px'), icon="wrench")

    def close(button):
        nonlocal main_box, CLOSE
        CLOSE = True
        main_box.children = ()

    close_button.on_click(close)



    struct_button = ipywidgets.Button(description="Structure mode", layout=widgets.Layout(width='125px', height='50px'))
    struct_button.style.button_color="LightBlue"
    prop_button = ipywidgets.Button(description="Properties mode", layout=widgets.Layout(width='125px', height='50px'))
    prop_button.style.button_color=None
    mode_box = widgets.HBox([struct_button, prop_button, close_button, physics_button])
    display(mode_box)

    edge_button = ipywidgets.Button(description="Edge select", layout=widgets.Layout(width='125px', height='50px'))
    edge_button.style.button_color="LimeGreen"
    vert_button = ipywidgets.Button(description="Node select", layout=widgets.Layout(width='125px', height='50px'))
    vert_button.style.button_color="LimeGreen"
    select_box = widgets.HBox([vert_button, edge_button])
    display(select_box)

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
        if visual_graph.selected_node is not None:
            if new_label_name in visual_graph.vertex_labels:
                return
            else:
                visual_graph.new_node_label(new_label_name)

            label_value = ipywidgets.Textarea(value="", layout=widgets.Layout(width='125px', height='50px'))
            label_label = ipywidgets.Label(value=str(label_name.value), layout=widgets.Layout(width='125px', height='50px'), justify_content='center')
            new_label = ipywidgets.HBox([label_label, label_value])

            def modify_label(change, visual_graph: VisualGraph):
                visual_graph.graph.nodes[visual_graph.selected_node][new_label_name] = change["new"]

            on_change = partial(modify_label, visual_graph=visual_graph)
            label_value.observe(on_change, names="value")
            labels_info.children = labels_info.children[:-1] + (new_label,) + labels_info.children[-1:]
        elif visual_graph.selected_edge is not None:
            if new_label_name in visual_graph.edge_labels:
                return
            else:
                visual_graph.new_edge_label(new_label_name)

            label_value = ipywidgets.Textarea(value="", layout=widgets.Layout(width='125px', height='50px'))
            label_label = ipywidgets.Label(value=str(label_name.value), layout=widgets.Layout(width='125px', height='50px'), justify_content='center')
            new_label = ipywidgets.HBox([label_label, label_value])

            def modify_label(change, visual_graph: VisualGraph):
                visual_graph.graph.edges[visual_graph.selected_edge][new_label_name] = change["new"]

            on_change = partial(modify_label, visual_graph=visual_graph)
            label_value.observe(on_change, names="value")
            labels_info.children = labels_info.children[:-1] + (new_label,) + labels_info.children[-1:]

    on_click = partial(add_label, labels_info=labels_info, visual_graph=visual_graph, label_name=label_name_text_box)
    add_new_label_button.on_click(on_click)
    mode = Mode.STRUCTURE
    edge_select=True
    vertex_select=True
    is_drag = False
    start_mouse_position = (0, 0)
    actions_to_perform = []
    EPS = 10

    def perform_in_future(action):
        def event_consumer(*args, **kwargs):
            actions_to_perform.append((action, args, kwargs))
        return event_consumer


    def click_struct(button_widget):
        nonlocal mode, prop_button
        mode=Mode.STRUCTURE
        button_widget.style.button_color='LightBlue'
        prop_button.style.button_color=None
        update_labels(labels_info, visual_graph)

    def click_prop(button_widget):
        nonlocal mode, struct_button
        mode=Mode.PROPERTIES
        button_widget.style.button_color='LightBlue'
        struct_button.style.button_color=None
        update_labels(labels_info, visual_graph)

    struct_button.on_click(partial(click_struct))
    prop_button.on_click(partial(click_prop))

    def click_verts_select(button_widget):
        nonlocal vertex_select, visual_graph
        vertex_select = not vertex_select
        if vertex_select:
            button_widget.style.button_color="LimeGreen"
        else:
            visual_graph.selected_node = None
            button_widget.style.button_color="Red"

    def click_edge_select(button_widget):
        nonlocal edge_select, visual_graph
        edge_select = not edge_select
        if edge_select:
            button_widget.style.button_color="LimeGreen"
        else:
            visual_graph.selected_edge=None
            button_widget.style.button_color="Red"

    edge_button.on_click(partial(click_edge_select))
    vert_button.on_click(partial(click_verts_select))

    def node_click(node):
        visual_graph.selected_edge=None
        if visual_graph.selected_node is None or visual_graph.selected_node!=node:
            visual_graph.selected_node = node
        else:
            visual_graph.selected_node = None

    def edge_click(edge):
        visual_graph.selected_node=None
        if visual_graph.selected_edge is None or visual_graph.selected_edge!=edge:
            visual_graph.selected_edge = edge
        else:
            visual_graph.selected_edge=None

    def handle_mousedown(event):
        nonlocal mode
        nonlocal start_mouse_position
        start_mouse_position = (event['relativeX'], event['relativeY'])
        if mode is Mode.PROPERTIES:
            if vertex_select:
                clicked_node, dist = visual_graph.get_closest_node((event['relativeX'], event['relativeY']))
                if dist < NODE_CLICK_RADIUS:
                    node_click(clicked_node)
                    update_labels(labels_info, visual_graph)
                    return

            if edge_select:
                clicked_edge, dist = visual_graph.get_closest_edge((event['relativeX'], event['relativeY']))
                if dist < EDGE_CLICK_RADIUS:
                    visual_graph.selected_node = None
                    #we will select the edge also when dragging, this behaviour can be changed
                    edge_click(clicked_edge)
                    update_labels(labels_info, visual_graph)

        else:
            if vertex_select:
                clicked_node, dist = visual_graph.get_closest_node((event['relativeX'], event['relativeY']))
                if dist < NODE_CLICK_RADIUS:
                    visual_graph.drag_start(clicked_node)
                    visual_graph.selected_edge = None
                    return

    def handle_mousemove(event):
        nonlocal mode, is_drag, EPS
        distance = abs(start_mouse_position[0] - event['relativeX']) + abs(start_mouse_position[1] -event['relativeY'])
        if mode is Mode.STRUCTURE:
            nonlocal is_drag
            if visual_graph.dragged_node is not None and distance > EPS:
                is_drag = True
                pos = (event['relativeX'], event['relativeY'])
                visual_graph.move_node(visual_graph.dragged_node, pos)


    def update_labels(labels_info: widgets.VBox, visual_graph: VisualGraph):
        nonlocal mode
        if mode is Mode.PROPERTIES:
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
            elif visual_graph.selected_edge is not None:
                labels_info.children = (ipywidgets.Label(value=f"Edge {repr(visual_graph.selected_edge)}", layout=widgets.Layout(width='250px', height='50px', justify_content='center')),)
                for i in visual_graph.graph.edges[visual_graph.selected_edge].keys():
                    label_value = ipywidgets.Textarea(value=str(visual_graph.graph.edges[visual_graph.selected_edge][i]),
                                                    layout=widgets.Layout(width='125px', height='50px'))
                    label_label = ipywidgets.Label(value=str(i), layout=widgets.Layout(width='125px', height='50px'))
                    new_label = ipywidgets.HBox([label_label, label_value])

                    def modify_label(change, visual_graph: VisualGraph):
                        visual_graph.graph.edges[visual_graph.selected_edge][i] = change["new"]

                    on_change = partial(modify_label, visual_graph=visual_graph)
                    label_value.observe(on_change, names="value")
                    labels_info.children += (new_label,)
                labels_info.children += (widgets.VBox([widgets.HBox([label_name_text_box, add_new_label_button])]),)
            else:
                labels_info.children = (ipywidgets.Label(value=f"Node labels: ", layout=widgets.Layout(width='250px', height='50px', justify_content='center')),)
                for name in visual_graph.vertex_labels:
                    label= ipywidgets.Label(value=name, layout=widgets.Layout(width='125px', height='50px'))
                    labels_info.children+=(label, )
                labels_info.children += (ipywidgets.Label(value=f"Edge labels: ", layout=widgets.Layout(width='250px', height='50px', justify_content='center')),)
                for name in visual_graph.edge_labels:
                    label= ipywidgets.Label(value=name, layout=widgets.Layout(width='125px', height='50px'))
                    labels_info.children+=(label, )
        else:
            labels_info.children = (ipywidgets.Label(value=f"Click on node to update labels",
                                                     layout=widgets.Layout(width='250px', height='50px',
                                                                           justify_content='center')),)

    def handle_mouseup(event):
        nonlocal mode
        #handling in PROPERTIES mode is handled with clicking, as we cannot drag in that mode
        if mode is Mode.STRUCTURE:
            nonlocal is_drag
            visual_graph.drag_end()
            if is_drag:
                is_drag = False
                return


            #selecting edges is handled with clicking, as we canot drag them
            #perhaps we should add the functionality of dragging edges as well and change that
            if vertex_select:
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

                    elif not visual_graph.graph.has_edge(visual_graph.selected_node, node):
                            visual_graph.add_edge(visual_graph.selected_node, node)
                            visual_graph.selected_node = None
                    else:
                        visual_graph.selected_node = node
                        update_labels(labels_info, visual_graph)
                    return

            if edge_select:
                clicked_edge, dist = visual_graph.get_closest_edge((event['relativeX'], event['relativeY']))
                if dist < EDGE_CLICK_RADIUS:
                    #we will select the edge also when dragging, this behaviour can be changed
                    #for now the only thing that selecting an edge will do will be showing its properties
                    edge_click(clicked_edge)
                    update_labels(labels_info, visual_graph)
                    return

            # if we didn't click vertex nor edge
            if visual_graph.selected_node is None:
                new_node = mex(visual_graph.graph.nodes)
                visual_graph.add_node(new_node, pos)
            else:
                visual_graph.selected_node = None
                update_labels(labels_info, visual_graph)

    CLOSE = False

    def handle_doubleclick(event):
        nonlocal mode
        if mode is Mode.STRUCTURE:
            pos = (event['relativeX'], event['relativeY'])
            if vertex_select:
                clicked_node, dist = visual_graph.get_closest_node(pos)
                if dist < NODE_CLICK_RADIUS:
                    visual_graph.remove_node(clicked_node)
                    visual_graph.selected_node = None
                    return

            if edge_select:
                clicked_edge, dist = visual_graph.get_closest_edge(pos)
                if dist < EDGE_CLICK_RADIUS:
                    visual_graph.selected_edge = None
                    visual_graph.remove_edge(clicked_edge[0], clicked_edge[1])
                    debug_text.value=str(clicked_edge)


    Event(source=canvas, watched_events=['mousedown']).on_dom_event(perform_in_future(handle_mousedown))
    Event(source=canvas, watched_events=['mousemove'], wait=1000 // 60).on_dom_event(
        perform_in_future(handle_mousemove))
    Event(source=canvas, watched_events=['mouseup']).on_dom_event(perform_in_future(handle_mouseup))
    Event(source=canvas, watched_events=['dblclick']).on_dom_event(perform_in_future(handle_doubleclick))

    main_box = widgets.HBox()
    debug_text = widgets.Textarea()

    # main widget view
    main_box.children = ([labels_info_scrollable, canvas])
    display(main_box)

    output = ipywidgets.Output()
    display(output)

    update_labels(labels_info, visual_graph)
    graph_physics = GraphPhysics(visual_graph)

    def main_loop(visual_graph, physics_button):
        nonlocal CLOSE
        try:
            while not CLOSE:
                graph_physics.update_physics(1 / 60, physics_button.value)
                graph_physics.normalize_positions()
                draw_graph(canvas, visual_graph)
                time.sleep(1 / 60)
                for (action, args, kwargs) in actions_to_perform:
                    action(*args, **kwargs)
                actions_to_perform.clear()
        except Exception as e:
            debug_text.value = repr(e)

    thread = threading.Thread(target=main_loop, args=(visual_graph, physics_button))
    thread.start()
