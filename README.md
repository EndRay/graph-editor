## Interactive Graph Editor for Jupyter

An interactive graph editor function designed for Jupyter notebooks. ```edit(graph: nx.Graph)``` function allows users <br>
to manipulate a graph by creating vertices, edges, and adding labels directly within a Jupyter environment.

### Parameters
- **graph** (*networkx.Graph*): The graph object to be edited.
  It should be an instance of the NetworkX Graph class or a subclass.

### Functions of buttons (from left to right)
1. Select whether you want to edit graph structure.
2. Select whether you want to edit labels.
3. Toggle nodes clickable option.
4. Toggle edges clickable option.
5. Close editing window.

### Mouse Functions
1. Click and drag vertices to move them around the canvas.
2. To create an edge, click on one vertex and then click on another vertex.<br>
An edge will be created between the two selected vertices.
3. To create a vertex, click on empty space of a canvas.
4. To delete an object, double-click on it.

### Dependencies
- Jupyter notebook web environment.
- NetworkX library for graph manipulation.

### Notes
This function relies on Jupyter ipywidgets, so it should work only in web versions of Jupyter.

### Examples
```python
import networkx as nx
from pygraphedit import edit

# Create a sample graph
G = nx.Graph()
G.add_nodes_from([1, 2, 3])
G.add_edges_from([(1, 2), (2, 3)])

# Call the interactive graph editor
edit(G)
