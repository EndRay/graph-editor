import threading
import time
import pygraphedit.graphics as graphics
import ipywidgets as widgets
import networkx as nx
from IPython.display import display
from ipycanvas import Canvas
from ipyevents import Event
from pygraphedit.graph_physics import GraphPhysics
from pygraphedit.settings import DRAGGED_NODE_RADIUS, NODE_CLICK_RADIUS, NODE_RADIUS, EDGE_CLICK_RADIUS
from pygraphedit.visual_graph import VisualGraph
from functools import partial
from enum import Enum
from pygraphedit.debug import debug_text
import traceback  #for debugging, can be removed

class Mode(Enum):
    STRUCTURE = 0
    PROPERTIES = 1


def mex(arr):
    result = 0
    while result in arr:
        result += 1
    return result


def edit(graph: nx.Graph):
    
    #logical properties of the graph
    ################################
    visual_graph = VisualGraph(graph, (800, 500))
    CLOSE = False
    mode = Mode.STRUCTURE
    edge_select = True
    vertex_select = True
    is_drag = False
    start_mouse_position = (0, 0)
    actions_to_perform = []
    EPS = 10
    #################################
    #################################

    style_label = graphics.get_style_label()
    canvas = Canvas(width=800, height=500)

    #main menu
    #################################
    mode_box = graphics.Menu()

    def close(button):
        # set child3ren = () for all displayed boxes
        nonlocal CLOSE, main_box
        CLOSE = True
        main_box.children = ()

    mode_box.close_button.on_click(close)

    def click_struct(button_widget):
        nonlocal mode, mode_box
        mode = Mode.STRUCTURE
        button_widget.style.button_color = 'LightBlue'
        mode_box.prop_button.style.button_color = None
        update_labels(labels_info, visual_graph)

    mode_box.struct_button.on_click(partial(click_struct))

    def click_prop(button_widget):
        nonlocal mode, mode_box
        mode = Mode.PROPERTIES
        button_widget.style.button_color = 'LightBlue'
        mode_box.struct_button.style.button_color = None
        update_labels(labels_info, visual_graph)

    mode_box.prop_button.on_click(partial(click_prop))

    def click_verts_select(button_widget):
        nonlocal vertex_select, visual_graph
        vertex_select = not vertex_select
        if vertex_select:
            button_widget.style.button_color = "LightGreen"
        else:
            visual_graph.selected_node = None
            update_labels(labels_info, visual_graph)
            button_widget.style.button_color = "lightcoral"

    mode_box.vert_button.on_click(partial(click_verts_select))

    def click_edge_select(button_widget):
        nonlocal edge_select, visual_graph
        edge_select = not edge_select
        if edge_select:
            button_widget.style.button_color = "LightGreen"
        else:
            visual_graph.selected_edge = None
            update_labels(labels_info, visual_graph)
            button_widget.style.button_color = "lightcoral"

    mode_box.edge_button.on_click(partial(click_edge_select))
    #######################
    
    #labels
    #######################
    
    labels_info = widgets.VBox()
    add_label_box = graphics.AddLabelBox()

    labels_info_scrollable = graphics.get_labels_info_scrollable()
    with labels_info_scrollable:
        display(labels_info)

    def add_label(button_widget, labels_info: widgets.VBox, visual_graph: VisualGraph, label_name: widgets.Textarea):
        new_label_name = str(label_name.value)
        if visual_graph.selected_node is not None:
            if new_label_name in visual_graph.vertex_labels:
                return
            else:
                visual_graph.new_node_label(new_label_name)

            new_label = graphics.LabelBox(str(label_name.value), "")

            def modify_label(change, visual_graph: VisualGraph):
                visual_graph.graph.nodes[visual_graph.selected_node][new_label_name] = change["new"]

            on_change = partial(modify_label, visual_graph=visual_graph)
            new_label.label_value.observe(on_change, names="value")
            labels_info.children = labels_info.children[:-1] + (new_label,) + labels_info.children[-1:]

        elif visual_graph.selected_edge is not None:
            if new_label_name in visual_graph.edge_labels:
                return
            else:
                visual_graph.new_edge_label(new_label_name)

            new_label = graphics.LabelBox(str(label_name.value), "")

            def modify_label(change, visual_graph: VisualGraph):
                visual_graph.graph.edges[visual_graph.selected_edge][new_label_name] = change["new"]

            on_change = partial(modify_label, visual_graph=visual_graph)
            new_label.label_value.observe(on_change, names="value")
            labels_info.children = labels_info.children[:-1] + (new_label,) + labels_info.children[-1:]

    on_click = partial(add_label, labels_info=labels_info, visual_graph=visual_graph, label_name=add_label_box.label_name_text_box)
    add_label_box.add_new_label_button.on_click(on_click)

    def update_labels(labels_info: widgets.VBox, visual_graph: VisualGraph):
        nonlocal mode
        if mode is Mode.PROPERTIES:
            if visual_graph.selected_node is not None:
                head_text=f"Node {repr(visual_graph.selected_node)}"
                labels_info.children = (graphics.get_head_label(head_text),)

                for i in visual_graph.graph.nodes[visual_graph.selected_node].keys():
                    value=str(visual_graph.graph.nodes[visual_graph.selected_node][i])
                    new_label = graphics.LabelBox(str(i),value)

                    def modify_label(change, visual_graph: VisualGraph):
                        visual_graph.graph.nodes[visual_graph.selected_node][i] = change["new"]

                    on_change = partial(modify_label, visual_graph=visual_graph)
                    new_label.label_value.observe(on_change, names="value")
                    labels_info.children += (new_label,)

                labels_info.children += (widgets.VBox([add_label_box]),)

            elif visual_graph.selected_edge is not None:
                head_text=f"Edge {repr(visual_graph.selected_edge)}"
                labels_info.children = (graphics.get_head_label(head_text),)

                for i in visual_graph.graph.edges[visual_graph.selected_edge].keys():
                    value=str(visual_graph.graph.edges[visual_graph.selected_edge][i])
                    new_label = graphics.LabelBox(str(i),value)

                    def modify_label(change, visual_graph: VisualGraph):
                        visual_graph.graph.edges[visual_graph.selected_edge][i] = change["new"]

                    on_change = partial(modify_label, visual_graph=visual_graph)
                    new_label.label_value.observe(on_change, names="value")
                    labels_info.children += (new_label,)
                labels_info.children += (widgets.VBox([add_label_box]),)

            else:
                labels_info.children = (graphics.get_head_label(f"Node labels: "),)
                for name in visual_graph.vertex_labels:
                    labels_info.children += (graphics.LabelListBox(name),)

                labels_info.children += (graphics.get_head_label(f"Edge labels: "),)
                for name in visual_graph.edge_labels:
                    labels_info.children += (graphics.LabelListBox(name),)
        else:
            labels_info.children = (graphics.get_some_other_label_that_i_dont_know_what_it_is(),)

    ##############################
    
    #canvas actions
    ##############################

    def node_click(node):
        visual_graph.selected_edge = None
        if visual_graph.selected_node is None or visual_graph.selected_node != node:
            visual_graph.selected_node = node
        else:
            visual_graph.selected_node = None

    def edge_click(edge):
        visual_graph.selected_node = None
        if visual_graph.selected_edge is None or visual_graph.selected_edge != edge:
            visual_graph.selected_edge = edge
        else:
            visual_graph.selected_edge = None

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
                    # we will select the edge also when dragging, this behaviour can be changed
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
        distance = abs(start_mouse_position[0] - event['relativeX']) + abs(start_mouse_position[1] - event['relativeY'])
        if mode is Mode.STRUCTURE:
            nonlocal is_drag
            if visual_graph.dragged_node is not None and distance > EPS:
                is_drag = True
                pos = (event['relativeX'], event['relativeY'])
                visual_graph.move_node(visual_graph.dragged_node, pos)


    def handle_mouseup(event):
        nonlocal mode
        # handling in PROPERTIES mode is handled with clicking, as we cannot drag in that mode
        if mode is Mode.STRUCTURE:
            nonlocal is_drag
            visual_graph.drag_end()
            if is_drag:
                is_drag = False
                return

            pos = (event['relativeX'], event['relativeY'])
            # selecting edges is handled with clicking, as we canot drag them
            # perhaps we should add the functionality of dragging edges as well and change that
            if vertex_select:
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
                    else:
                        visual_graph.selected_node = node
                        update_labels(labels_info, visual_graph)
                    return

            if edge_select:
                clicked_edge, dist = visual_graph.get_closest_edge((event['relativeX'], event['relativeY']))
                if dist < EDGE_CLICK_RADIUS:
                    # we will select the edge also when dragging, this behaviour can be changed
                    # for now the only thing that selecting an edge will do will be showing its properties
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
                    debug_text.value = str(clicked_edge)
        
    def perform_in_future(action):
        def event_consumer(*args, **kwargs):
            actions_to_perform.append((action, args, kwargs))

        return event_consumer

    Event(source=canvas, watched_events=['mousedown']).on_dom_event(perform_in_future(handle_mousedown))
    Event(source=canvas, watched_events=['mousemove'], wait=1000 // 60).on_dom_event(
        perform_in_future(handle_mousemove))
    Event(source=canvas, watched_events=['mouseup']).on_dom_event(perform_in_future(handle_mouseup))
    Event(source=canvas, watched_events=['dblclick']).on_dom_event(perform_in_future(handle_doubleclick))

    ##################################
    ##################################

    #main structure and main loop
    #############################

    main_box = widgets.HBox()
    debug_text = widgets.Textarea()

    main_box.children = ([widgets.VBox((mode_box, labels_info_scrollable)), canvas])
    display(main_box)

    output = widgets.Output()
    display(output)

    display(debug_text)
    update_labels(labels_info, visual_graph)
    graph_physics = GraphPhysics(visual_graph)

    def main_loop(visual_graph, physics_button):
        nonlocal CLOSE
        try:
            while not CLOSE:
                graph_physics.update_physics(1 / 60, physics_button.value)
                graph_physics.normalize_positions()
                graphics.draw_graph(canvas, visual_graph)
                time.sleep(1 / 60)
                for (action, args, kwargs) in actions_to_perform:
                    action(*args, **kwargs)
                actions_to_perform.clear()
        except Exception as e:
            debug_text.value = traceback.format_exc()

    thread = threading.Thread(target=main_loop, args=(visual_graph, mode_box.physics_button))
    thread.start()

    ################################
    ################################