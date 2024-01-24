from ipycanvas import Canvas, hold_canvas
from pygraphedit.settings import DRAGGED_NODE_RADIUS, NODE_CLICK_RADIUS, NODE_RADIUS
from pygraphedit.visual_graph import VisualGraph
import ipywidgets as widgets

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
            draw_edge(visual_graph.coordinates[edge[0]], visual_graph.coordinates[edge[1]],
                      colorcode=("red" if edge == visual_graph.selected_edge else "black"))
        for node, pos in visual_graph.coordinates.items():
            draw_vertex(pos,
                        size=(DRAGGED_NODE_RADIUS if node == visual_graph.dragged_node else NODE_RADIUS),
                        colorcode=("red" if node == visual_graph.selected_node else "black"))

class SimpleLabel(widgets.Label):
    def __init__(self):
        pass

class SmallButton(widgets.Button):
    def __init__(self, tooltip=None, icon=None, active_color=None, inactive_color=None):
        pass

class Menu(widgets.HBox):
    def __init__(self):
        super().__init__()
        self.close_button = widgets.Button(description="",
                                  tooltip='Exit',
                                  layout=widgets.Layout(width='39px', height='39px'),
                                  icon='window-close')
        self.physics_button = widgets.ToggleButton(
            value=True,
            tooltip='Turn physics on/off',
            disabled=False,
            indent=False,
            layout=widgets.Layout(width='39px', height='39px'), icon="wrench")

        self.struct_button = widgets.Button(tooltip='Click to activate edges and vertices creation/deletion', description="",
                                      layout=widgets.Layout(width='39px', height='39px'),
                                      icon="plus-circle")

        self.struct_button.style.button_color = "LightBlue"

        self.prop_button = widgets.Button(tooltip='Click to modify properties of edges and vertices', description="",
                                        layout=widgets.Layout(width='39px', height='39px'), icon="pencil")
        self.prop_button.style.button_color = None

        self.edge_button = widgets.Button(tooltip='Edges selection enabled/disabled', description="",
                                        layout=widgets.Layout(width='39px', height='39px'), icon="arrows-v")
        self.edge_button.style.button_color = "LightGreen"
        self.vert_button = widgets.Button(tooltip='Vertices selection enabled/disabled', description="",
                                        layout=widgets.Layout(width='39px', height='39px'), icon="circle")
        self.vert_button.style.button_color = "LightGreen"


        self.children = ([widgets.HBox((self.struct_button, self.prop_button),
                                          layout=widgets.Layout(border='0.5px solid #000000')),
                             self.vert_button, self.edge_button, self.physics_button, self.close_button])

def get_label_style():
    return dict(
        font_weight='bold',
        background='#d3d3d3',
        font_variant="small-caps")

class label_box(widgets.HBox):
    def __init__(self, index, str_value):
        super().__init__()
        self.label_value = widgets.Textarea(value=str_value,
            layout=widgets.Layout(width='100px', height='30px'),
            style=get_label_style())

        label_label = widgets.Label(value=index, 
            layout=widgets.Layout(width='150px', height='30px'))

        label_label.layout.border = '2px solid #000000'
        self.children=(label_label, self.label_value)



def get_style_label():
    style_label = widgets.Label()
    style_label.layout.border = '2px solid #000000'
    style_label.style.font_weight = 'bold'
    style_label.style.background = '#d3d3d3'
    style_label.style.font_variant = 'small-caps'
    return style_label

def get_head_label(text):
    return widgets.Label(value=text, layout=widgets.Layout(width='250px', height='30px',justify_content='center'))