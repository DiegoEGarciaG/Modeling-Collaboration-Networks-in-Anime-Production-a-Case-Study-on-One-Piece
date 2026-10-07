import networkx as nx
import pandas as pd
import ast
import matplotlib.pyplot as plt
import powerlaw

@nx._dispatchable(
    graphs="B", preserve_node_attrs=True, preserve_graph_attrs=True, returns_graph=True
)
def projected_graph_custom(B, nodes, multigraph=False):
    """
    Genera la proyección de B a uno de sus sets de nodos. Los nodos
    eliminados mantienen sus atributos en forma de arista.
    """
    if B.is_multigraph():
        raise nx.NetworkXError("not defined for multigraphs")
    directed = False
    G = nx.MultiGraph()
    G.graph.update(B.graph)
    G.add_nodes_from((n, B.nodes[n]) for n in nodes)
    for u in nodes:
        nbrs2 = {v for nbr in B[u] for v in B[nbr] if v != u}
        for n in nbrs2:
            if directed:
                links = set(B[u]) & set(B.pred[n])
            else:
                links = set(B[u]) & set(B[n])
            for l in links:
                if not G.has_edge(u, n, l):
                    d_attr = B.nodes[l]
                    G.add_edge(u, n, key=l)
                    nx.set_edge_attributes(G, {(u, n, l): d_attr})
    if not multigraph:
        directed = False
        G2 = nx.Graph()
        G2.graph.update(B.graph)
        G2.add_nodes_from((n, B.nodes[n]) for n in nodes)
        g_nodes = G.nodes()
        for u in g_nodes:
            # revisar los links de u
            for n in G.neighbors(u):
                if not G2.has_edge(u, n):
                    votes = 0
                    pages = 0
                    rating = 0
                    episodes = set()
                    edge_data = G.get_edge_data(u, n)
                    for edge_key, attrs in edge_data.items():
                        pages += attrs["n de paginas"]
                        votes += attrs["votos"]
                        rating += attrs["votos"]*attrs["rating"]
                        episodes.add(edge_key)
                    d_attr = {"n de paginas": pages, "rating": rating/votes, "votos": votes, "n_episodios": len(episodes)}
                    G2.add_edge(u, n)
                    nx.set_edge_attributes(G2, {(u, n): d_attr})
        return G2
    return G

# Función para convertir string de lista a lista real
def parse_list(x):
    if pd.isna(x):
        return []
    try:
        return ast.literal_eval(x)
    except:
        return []

def bipartite_graph(df, gexf=False):
    """Function to create a bipartite graph between episodes and participant directors in said episode.
    Can store the generated graph in a GEXF format for further visualization or analysis. """

    # Participant columns
    staff_columns = ["guion", "arte", "animacion", "direccion"]
    # Value columns
    value_columns = ["n de paginas", "rating", "votos"]

    # Creates bipartite base graph
    bipartite_graph = nx.Graph()

    for _, row in df.iterrows():
        episodio = f"ep_{int(row['episodio'])}"
        
        # Add new episode node
        bipartite_graph.add_node(episodio, bipartite="episode")

        value_dict = {}
        for val in value_columns:
            value_dict[val] = row[val]
        
        nx.set_node_attributes(bipartite_graph, {episodio: value_dict})

        # Do iterations for all director types (screenwriter, art, animation, direction)
        for col in staff_columns:
            personas = parse_list(row[col])
            
            for persona in personas:
                persona_clean = persona.split("(")[0].strip()

                # Add participant node
                if persona_clean == '':
                    continue
                bipartite_graph.add_node(persona_clean, bipartite="staff")

                # Add edge
                bipartite_graph.add_edge(persona_clean, episodio)


    print(f"Number of nodes: {bipartite_graph.number_of_nodes()}, Number of edges: {bipartite_graph.number_of_edges()}")
    if gexf:
        nx.write_gexf(bipartite_graph, "one_piece.gexf")
    return bipartite_graph


def modified_fast_chung_lu_bipartite(prev_graph, d_i, current_j, diff_m, rng):
    """
    Function to 
    """
    colabs = []
    for i in range(diff_m):
        random_i = rng.choice(d_i)
        prev_graph.add_node(random_i, bipartite="staff")
        prev_graph.add_edge(random_i, current_j)
        colabs.append(random_i)
    
    return prev_graph, colabs


"""Funciones para calcular frecuencias de valores en data, tanto para valores crudos como para bins."""
def raw_frequency(data: list[float]):
  value_frequency = []
  # sacar valores distintos y ordenarlos
  distinct_values = list(set(data))
  distinct_values.sort()
  # contar valores en data
  for value in distinct_values:
    value_frequency.append(data.count(value))
  return distinct_values, value_frequency

def bin_frequency(data: list[float], logaritmic_bins=False):
  if logaritmic_bins:
    x, y = powerlaw.pdf(data, linear_bins=False)
  else:
    x, y = powerlaw.pdf(data, linear_bins=True)
  x = x[0:-1] # se descarta el último porque es la posición donde iría el siguiente bin
  return x, y


def plot_distribution(values, title):

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # Sin bins
    x, y = raw_frequency(values)
    axes[0,0].scatter(x, y)
    axes[0,0].set_title("Sin bins")

    # Bins lineales
    x, y = bin_frequency(values)
    axes[0,1].scatter(x, y)
    axes[0,1].set_title("Bins lineales")

    # Bins log
    x, y = bin_frequency(values, logaritmic_bins=True)
    axes[0,2].scatter(x, y)
    axes[0,2].set_title("Bins log")

    # Sin bins + loglog
    x, y = raw_frequency(values)
    axes[1,0].scatter(x, y)
    axes[1,0].loglog()
    axes[1,0].set_title("Sin bins (log-log)")

    # Bins lineales + loglog
    x, y = bin_frequency(values)
    axes[1,1].scatter(x, y)
    axes[1,1].loglog()
    axes[1,1].set_title("Bins lineales (log-log)")

    # Bins log + loglog
    x, y = bin_frequency(values, logaritmic_bins=True)
    axes[1,2].scatter(x, y)
    axes[1,2].loglog()
    axes[1,2].set_title("Bins log (log-log)")

    fig.suptitle(title)
    plt.show()

def plot_metric_vs_metric(
    metric1,
    metric2,
    metric1_name="Metric1",
    metric2_name="Metric2",
    vertical_lines=None
):
    """
    metric1, metric2 : listas o arrays de valores
    metric1_name     : nombre eje X
    metric2_name     : nombre eje Y
    vertical_lines   : lista de valores x donde dibujar líneas verticales
    """

    fig, axes = plt.subplots(2, 2, figsize=(12, 10))

    configs = [
        ("Linear-Linear", False, False),
        ("Log X", True, False),
        ("Log Y", False, True),
        ("Log X + Log Y", True, True)
    ]

    for ax, (title, logx, logy) in zip(axes.flatten(), configs):

        ax.scatter(metric1, metric2)

        if vertical_lines is not None:
            for v in vertical_lines:
                ax.axvline(
                    x=v,
                    linestyle="--",
                    linewidth=1,
                    alpha=0.8,
                    color="red"
                )

        if logx:
            ax.set_xscale("log")

        if logy:
            ax.set_yscale("log")

        ax.set_title(title)
        ax.set_xlabel(metric1_name)
        ax.set_ylabel(metric2_name)
        ax.grid(True)

    plt.suptitle(f"{metric1_name} vs {metric2_name}", fontsize=14)
    plt.tight_layout()
    plt.show()

def get_members_combination(nodes):
    largo = len(nodes)
    nodes_2 = []
    for i in range(largo):
        if i == (largo - 1):
            break
        for l in range(i + 1, largo):
            if l == largo:
                break
            nodes_2.append((nodes[i], nodes[l]))
    return nodes_2

def avg_previous_team_rating(B, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if B.has_node(u):
            updated_nodes.append(u)
    for u in updated_nodes:
        suma_temp = 0
        for ep in B[u]:
            suma_temp += B.nodes[ep]["rating"]
        suma += (suma_temp/len(B[u]))
    
    return (suma/largo)

def avg_previous_individual_exp(B, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if B.has_node(u):
            updated_nodes.append(u)
    for u in updated_nodes:
        suma += len(B[u])
    
    return (suma/largo)

def avg_previous_tm_exp(G, nodes_2, largo):
    """ Calcula la experiencia promedio previa de un set de nodos."""
    if largo == 0:
        return 0
    suma = 0
    for u, v in nodes_2:
        if not G.has_node(u) or not G.has_node(v):
            continue
        if G.has_edge(u, v):
            node_attrs = G.get_edge_data(u, v)
            suma += node_attrs["n_episodios"]
    
    return (suma/largo)

def avg_previous_tm_shared_colabs(G, nodes_2, largo):
    if largo == 0:
        return 0
    suma = 0
    for u, v in nodes_2:
        if not G.has_node(u) or not G.has_node(v):
            continue
        suma += len(nx.common_neighbors(G, u, v))
    
    return (suma/largo)

def avg_previous_tm_clustering_coeff(G, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if G.has_node(u):
            updated_nodes.append(u)
    clustering = nx.clustering(G, nodes)
    for u in updated_nodes:
        suma += clustering[u]
    
    return (suma/largo)

def avg_previous_tm_closeness(G, nodes, largo):
    if largo == 0:
        return 0
    suma = 0
    for u in nodes:
        if G.has_node(u):
            suma += nx.closeness_centrality(G, u)
    
    return (suma/largo)

def avg_previous_tm_betweenness(G, nodes, prev_betweenness, largo):
    if largo == 0:
        return 0
    suma = 0
    updated_nodes = []
    for u in nodes:
        if G.has_node(u):
            updated_nodes.append(u)
    for u in updated_nodes:
        suma += prev_betweenness[u]
    
    return (suma/largo)