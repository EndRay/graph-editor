import ipywidgets as widgets
from ipyevents import Event
from IPython.display import display
from ipycanvas import Canvas
import numpy as np
import networkx as nx
from scipy.spatial import distance

def edit(G: nx.Graph):
    vert_coordinates = np.empty((0, 2))

    vert_tool = True
    selected_node = -1

    # creating toolbox
    tools = widgets.RadioButtons(
        value='Vertices',
        options=['Vertices', 'Edges'],
        description='Tools:'
    )

    def tool_change(change):
        nonlocal vert_tool
        nonlocal selected_node
        if change['type'] != 'change' or change['name'] != 'value':
            return
        elif change['new'] == 'Vertices':
            vert_tool = True
            selected_node = -1
        else:
            vert_tool = False

    tools.observe(tool_change)

    toolbox = widgets.VBox(
        [tools]
    )

    # creating canvas
    canvas = Canvas(width=800, height=500)
    canvas.stroke_rect(0, 0, 800, 500)

    # click event handling
    d = Event(source=canvas, watched_events=['click'])  # , 'keydown', 'mouseenter'

    def draw_vertex(x, y, colorcode="black"):
        canvas.fill_style = colorcode
        canvas.fill_circle(x, y, 3)
        canvas.fill_style = "black"

    def handle_event(event):
        nonlocal G
        nonlocal vert_coordinates
        ev_x = event['relativeX']
        ev_y = event['relativeY']
        if vert_tool:
            vert_coordinates = np.append(vert_coordinates, [[ev_x, ev_y]], axis=0)
            draw_vertex(ev_x, ev_y)
            G.add_node(G.number_of_nodes(), x=ev_x, y=ev_y)
        else:
            nonlocal selected_node
            clicked_node = distance.cdist(np.array([[ev_x, ev_y]]), vert_coordinates).argmin()

            if selected_node == -1:
                selected_node = clicked_node
                draw_vertex(*vert_coordinates[selected_node], "blue")

            elif selected_node == clicked_node:
                draw_vertex(*vert_coordinates[selected_node])
                selected_node = -1

            else:
                G.add_edge(selected_node, clicked_node)
                canvas.stroke_line(*vert_coordinates[selected_node], *vert_coordinates[clicked_node])

                draw_vertex(*vert_coordinates[clicked_node])
                draw_vertex(*vert_coordinates[selected_node])
                selected_node = -1

    d.on_dom_event(handle_event)

    # main widget view
    main_box = widgets.HBox(
        [toolbox, canvas]
    )
    # Display the widgets
    display(main_box)
