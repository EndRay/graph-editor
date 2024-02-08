import threading
import time
import ipywidgets as widgets
import networkx as nx
from IPython.display import display
from ipycanvas import Canvas
from ipyevents import Event

from . import graphics
from .graph_physics import GraphPhysics
from .settings import NODE_CLICK_RADIUS, EDGE_CLICK_RADIUS
from .visual_graph import VisualGraph
from functools import partial
from enum import Enum


class Mode(Enum):
    STRUCTURE = 0
    PROPERTIES = 1


def mex(arr):
    result = 0
    while result in arr:
        result += 1
    return result

def edit(graph: nx.Graph):
    """
    An interactive graph editor function designed for Jupyter.

    This function enables users to manipulate a graph by creating vertices, edges and adding labels.


    Parameters
    ----------
    - graph (networkx.Graph): The graph object to be edited. It should be an instance of the
      NetworkX Graph class or a subclass.

    Functions of buttons in order from left to right
    ------------------------------------------------
    1-2: Select whether you want to edit graph structure (1) or labels (2).
    3. Select if you want for nodes to be clickable.
       Deselecting this should make easier to operate on edges in a large graph.
    4. Select if you want for edges to be clickable.
       Deselecting this should make easier to operate on nodes in a large graph.
    5. Close editing window.

    Mouse functions
    ---------------
    1. Click and drag vertices to move them around the canvas.
    2. To create an edge, click on one vertex and then click on another vertex.
       An edge will be created between the two selected vertices.
    3. To create a vertex, click on empty space of a canvas.
    3. To delete an object, double-click on it.

    Dependencies
    ------------
    - Jupyter notebook web environment.
    - NetworkX library for graph manipulation.

    Notes
    -----
    This function relies on Jupyter ipywidgets, so it should work only in web versions of Jupyter.

    Examples
    --------
    >>> import networkx as nx
    >>> from pygraphedit import edit

    Create a sample graph

    >>> G = nx.Graph()
    >>> G.add_nodes_from([1, 2, 3])
    >>> G.add_edges_from([(1, 2), (2, 3)])

    Call the interactive graph editor

    >>> edit(G)
    """
    visual_graph = VisualGraph(graph, (800, 500))
    CLOSE = False
    mode = Mode.STRUCTURE
    is_drag = False
    start_mouse_position = (0, 0)
    actions_to_perform = []
    EPS = 10
    canvas = Canvas(width=800, height=500)
    mode_box = graphics.Menu()

    def close(button):
        nonlocal CLOSE, main_box
        CLOSE = True
        main_box.children = ()

    mode_box.close_button.on_click(close)

    def click_struct(new_mode, button_widget):
        nonlocal mode, mode_box
        if not button_widget.active:
            mode = new_mode
            mode_box.struct_button.toggle()
            mode_box.prop_button.toggle()
        update_labels(labels_info, visual_graph)

    mode_box.struct_button.on_click(partial(click_struct, Mode.STRUCTURE))
    mode_box.prop_button.on_click(partial(click_struct, Mode.PROPERTIES))

    def click_verts_select(button_widget):
        nonlocal visual_graph
        button_widget.toggle()
        if not button_widget.active:
            visual_graph.selected_node = None
            update_labels(labels_info, visual_graph)

    mode_box.vert_button.on_click(click_verts_select)

    def click_edge_select(button_widget):
        nonlocal visual_graph
        button_widget.toggle()
        if not button_widget.active:
            visual_graph.selected_edge = None
            update_labels(labels_info, visual_graph)

    mode_box.edge_button.on_click(click_edge_select)
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

            update_labels(labels_info=labels_info, visual_graph=visual_graph)

        elif visual_graph.selected_edge is not None:
            if new_label_name in visual_graph.edge_labels:
                return
            else:
                visual_graph.new_edge_label(new_label_name)

            update_labels(labels_info=labels_info, visual_graph=visual_graph)

    on_click = partial(add_label, labels_info=labels_info, visual_graph=visual_graph,
                       label_name=add_label_box.label_name_text_box)
    add_label_box.add_new_label_button.on_click(on_click)

    def update_labels(labels_info: widgets.VBox, visual_graph: VisualGraph):
        nonlocal mode, add_label_box
        add_label_box.label_name_text_box.value=''
        if mode is Mode.PROPERTIES:
            if visual_graph.selected_node is not None:
                head_text = f"Node {repr(visual_graph.selected_node)}"
                labels_info.children = (graphics.get_head_label(head_text),)

                for i in visual_graph.graph.nodes[visual_graph.selected_node].keys():
                    value = str(visual_graph.graph.nodes[visual_graph.selected_node][i])
                    new_label = graphics.LabelBox(str(i), value)

                    def modify_label(change, visual_graph: VisualGraph):
                        visual_graph.graph.nodes[visual_graph.selected_node][i] = change["new"]

                    on_change = partial(modify_label, visual_graph=visual_graph)
                    new_label.label_value.observe(on_change, names="value")
                    labels_info.children += (new_label,)

                labels_info.children += (widgets.VBox([add_label_box]),)

            elif visual_graph.selected_edge is not None:
                head_text = f"Edge {repr(visual_graph.selected_edge)}"
                labels_info.children = (graphics.get_head_label(head_text),)

                for i in visual_graph.graph.edges[visual_graph.selected_edge].keys():
                    value = str(visual_graph.graph.edges[visual_graph.selected_edge][i])
                    new_label = graphics.LabelBox(str(i), value)
                    def modify_label(change, visual_graph: VisualGraph):
                        visual_graph.graph.edges[visual_graph.selected_edge][i] = change["new"]

                    on_change = partial(modify_label, visual_graph=visual_graph)
                    new_label.label_value.observe(on_change, names="value")
                    labels_info.children += (new_label,)
                labels_info.children += (widgets.VBox([add_label_box]),)

            else:
                labels_info.children = (graphics.get_head_label(f"Node labels: "),)
                def edit(button, name_label):
                    name_label.show_edit()

                def escape_edit(button, name_label):
                    name_label.hide_edit()

                def remove_vertex_label(button, visual_graph, label, labels_info):
                    visual_graph.remove_vertex_label(label)
                    update_labels(labels_info=labels_info, visual_graph=visual_graph)

                def edit_vertex_label(button, visual_graph, name_label, old_name, labels_info):
                    visual_graph.edit_node_label(old_label=old_name, new_label=str(name_label.edit_label_value.value))
                    update_labels(labels_info=labels_info, visual_graph=visual_graph)

                for name in visual_graph.vertex_labels:
                    name_label= graphics.LabelListBox(name)
                    name_label.delete_button.on_click(partial(remove_vertex_label, label=name,visual_graph=visual_graph, labels_info=labels_info))
                    name_label.edit_button.on_click(partial(edit, name_label=name_label))
                    name_label.escape_edit_button.on_click(partial(escape_edit,name_label=name_label))
                    name_label.confirm_edit_button.on_click(partial(edit_vertex_label, visual_graph=visual_graph, name_label=name_label, old_name=name, labels_info=labels_info))
                    labels_info.children += (name_label,)

                def remove_edge_label(button,visual_graph, label, labels_info):
                    visual_graph.remove_edge_label(label)
                    update_labels(labels_info=labels_info, visual_graph=visual_graph)

                def edit_edge_label(button, visual_graph, name_label, old_name, labels_info):
                    visual_graph.edit_edge_label(old_label=old_name, new_label=str(name_label.edit_label_value.value))
                    update_labels(labels_info=labels_info, visual_graph=visual_graph)

                labels_info.children += (graphics.get_head_label(f"Edge labels: "),)
                for name in visual_graph.edge_labels:
                    name_label= graphics.LabelListBox(name)
                    name_label.delete_button.on_click(partial(remove_edge_label, label=name, visual_graph=visual_graph, labels_info=labels_info))
                    name_label.edit_button.on_click(partial(edit, name_label=name_label))
                    name_label.escape_edit_button.on_click(partial(escape_edit, name_label=name_label))
                    name_label.confirm_edit_button.on_click(partial(edit_edge_label, visual_graph=visual_graph, name_label=name_label, old_name=name, labels_info=labels_info))
                    labels_info.children += (name_label,)
        else:
            labels_info.children = (graphics.get_some_other_label_that_i_dont_know_what_it_is(),)

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
            if mode_box.vert_button.active:
                clicked_node, dist = visual_graph.get_closest_node((event['relativeX'], event['relativeY']))
                if dist < NODE_CLICK_RADIUS:
                    node_click(clicked_node)
                    update_labels(labels_info, visual_graph)
                    return

            if mode_box.edge_button.active:
                clicked_edge, dist = visual_graph.get_closest_edge((event['relativeX'], event['relativeY']))
                if dist < EDGE_CLICK_RADIUS:
                    visual_graph.selected_node = None
                    # we will select the edge also when dragging, this behaviour can be changed
                    edge_click(clicked_edge)
                    update_labels(labels_info, visual_graph)
                else:
                    visual_graph.selected_edge=None
                    visual_graph.selected_node=None
                    update_labels(labels_info, visual_graph)

        else:
            if mode_box.vert_button.active:
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
        if mode is Mode.STRUCTURE:
            nonlocal is_drag
            visual_graph.drag_end()
            if is_drag:
                is_drag = False
                return

            pos = (event['relativeX'], event['relativeY'])
            if mode_box.vert_button.active:
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

            if mode_box.edge_button.active:
                clicked_edge, dist = visual_graph.get_closest_edge((event['relativeX'], event['relativeY']))
                if dist < EDGE_CLICK_RADIUS:
                    edge_click(clicked_edge)
                    update_labels(labels_info, visual_graph)
                    return

            if visual_graph.selected_node is None and visual_graph.selected_edge is None:
                new_node = mex(visual_graph.graph.nodes)
                visual_graph.add_node(new_node, pos)
            else:
                visual_graph.selected_node = None
                visual_graph.selected_edge = None
                update_labels(labels_info, visual_graph)

    def handle_doubleclick(event):
        nonlocal mode
        if mode is Mode.STRUCTURE:
            pos = (event['relativeX'], event['relativeY'])
            if mode_box.vert_button.active:
                clicked_node, dist = visual_graph.get_closest_node(pos)
                if dist < NODE_CLICK_RADIUS:
                    visual_graph.remove_node(clicked_node)
                    visual_graph.selected_node = None
                    return

            if mode_box.edge_button.active:
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

    main_box = widgets.HBox()
    debug_text = widgets.Textarea()

    main_box.children = ([widgets.VBox((mode_box, labels_info_scrollable)), canvas])
    display(main_box)
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
            debug_text.value = repr(e)

    thread = threading.Thread(target=main_loop, args=(visual_graph, mode_box.physics_button))
    thread.start()
