import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

from auto import circuit_pb2
import hcomponent

matplotlib.rc('figure', figsize=(16, 12))

def simplify_graph(G):
    """Removes nodes with can be merged by directly connecting the neighbors.

    Nodes like internal resistor (_ir) and redundant terminals (_t) are dropped.

    Args:
    G: A NetworkX graph.

    Returns:
    The simplified graph.
    """

    while True:
        nodes_to_remove = [node for node, degree in G.degree() if degree == 2 and (node.endswith("_ir") or node.endswith("_t"))]
        if len(nodes_to_remove) == 0:
            break
        for node in nodes_to_remove:
            neighbors = list(G.neighbors(node))
            G.remove_node(node)
            G.add_edge(neighbors[0], neighbors[1])

    return G

def create_circuit_image(fout, circuit, terminal_to_components):
    """
    Saves a circuit image using matplotlib and networkx for components.
    """
    G = nx.Graph()

    color_map = {}
    shape_map = {}
    for c in circuit.components:
        shape = 'd'
        if c.HasField("led"):
            color_map[c.name]=matplotlib.colors.to_rgba(circuit_pb2.Led.Color.Name(c.led.color), 1 if hcomponent.is_led_on(c) else 0.3)
            shape = 'o'
        elif c.HasField("button"):
            color_map[c.name]=matplotlib.colors.to_rgba("grey", 1 if c.button.input.is_pressed else 0.3)
            shape = 's'
        if shape not in shape_map:
            shape_map[shape] = []
        shape_map[shape].append(c.name)
        G.add_node(c.name)

    for t_id in terminal_to_components:
        t_name = f"{t_id}_t"
        G.add_node(t_name)
        for c in terminal_to_components[t_id]:
            G.add_edge(t_name, c.name)

    G = simplify_graph(G)
    pos = nx.spring_layout(G, iterations=1000, seed=200)

    nonvisual_components = [n for n in G.nodes if n.endswith("_t")]
    visual_components = [n for n in G.nodes if n not in nonvisual_components]

    nx.draw_networkx_labels(G, pos=pos, bbox=dict(facecolor='none', edgecolor='none'), font_size=10, labels={n:n for n in visual_components})
    for shape, cnames in shape_map.items():
        current_nodes = [n for n in visual_components if n in cnames]
        node_color = [color_map.get(node, 'lightgrey') for node in current_nodes]
        nx.draw_networkx_nodes(G, pos=pos, node_shape=shape, node_size=1024*2.5, nodelist=current_nodes, node_color=node_color)
    nx.draw_networkx_edges(G, pos=pos)

    plt.axis('off')
    plt.savefig(fout)
