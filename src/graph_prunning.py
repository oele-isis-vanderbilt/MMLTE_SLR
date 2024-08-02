# Dependencies
import pathlib
import collections

# Third-party Imports
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
import numpy as np

# Constants
CWD = pathlib.Path.cwd()
DATA_DIR = CWD / "data"
PAPERS_FILE = DATA_DIR / "S4.xlsx"

assert PAPERS_FILE.exists()

def construct_graph(papers_df: pd.DataFrame, must_include: bool = False) -> nx.Graph:

    G = nx.DiGraph()

    # Add node and edges
    for i, row in papers_df.iterrows():

        # Add node with all its attributes
        data = {k: v for k, v in row.to_dict().items() if k != "uuid"}
        G.add_node(row["uuid"], **data)

        # Add edge
        adjacent_nodes = row["cited_by"]

        # for adjacent_node, adjacent_name in zip(
        #     adjacent_nodes, row["cited_by_short_name"]
        # ):
        #     label_dict[adjacent_node] = adjacent_name

        if len(adjacent_nodes) >= 1:
            for other in adjacent_nodes:
                if not must_include:
                    G.add_edge(other, row["uuid"])
                else:
                    if other in papers_df.values:
                        G.add_edge(other, row["uuid"])

    return G

def get_node_weights(G: nx.Graph) -> list:

    # Node weights
    node_weights = []
    for node, node_data in G.nodes(data=True):
        if "cited_by" in node_data:
            node_weights.append(max(0.5, len(node_data["cited_by"])))
        else:
            node_weights.append(0.5)

    return node_weights

def graph_to_df(G: nx.Graph) -> pd.DataFrame:

    df = collections.defaultdict(list)
    for node_name, node_data in G.nodes(data=True):
        df["uuid"].append(node_name)
        for k, v in node_data.items():
            if v and v != "":
                df[k].append(v)
            else:
                df[k].append("NA")

    df = pd.DataFrame(df)
    df = df.fillna("NA")

    return df


def graph_to_excel(G: nx.Graph, filepath: pathlib.Path):

    df = graph_to_df(G)
    df.to_excel(str(filepath), index=False)


def show_graph(G, node_weights):

    # Show the graph
    fig = plt.figure(figsize=(20, 20))
    nx.draw(
        G,
        # nx.circular_layout(G),
        node_color="red",
        node_size=np.array(node_weights),
        arrowstyle="-",
    )
    plt.show()


def subconnected_graph_prunning(G):
    # S = [G.subgraph(c).copy() for c in nx.connected_components(G)]
    S = [G.subgraph(c).copy() for c in nx.connected_components(G.to_undirected())]
    print("subconnected graph sizes", [len(x) for x in S])
    max_cc = max(S, key=len)
    return G.subgraph(max_cc).copy()


def minimally_connected_node_prunning(G, deg):
    to_be_removed = [x for x in G.nodes() if G.degree(x) <= deg]
    n_G = G.copy()
    n_G.remove_nodes_from(to_be_removed)
    return n_G


def step(G, remove_n):
    # Prun
    print(f"Before step: {G.number_of_nodes()}")
    n_G = minimally_connected_node_prunning(G, remove_n)
    print(f"After removing minimially connected: {n_G.number_of_nodes()}")

    n_G.remove_nodes_from(list(nx.isolates(n_G)))
    print(f"After new 0-deg nodes: {n_G.number_of_nodes()}")

    n_G = subconnected_graph_prunning(n_G)
    print(f"After removing subcomponents: {n_G.number_of_nodes()}")

    # Report
    node_weights = get_node_weights(n_G)
    # show_graph(n_G, node_weights)
    print(f"Number of nodes is {n_G.number_of_nodes()}")

    return n_G


def recursive_prunning(G):

    # Iterative removal
    prev_G = G.copy()
    while True:

        # Apply (<1) prunning
        new_G = minimally_connected_node_prunning(prev_G, 1)
        print(new_G.number_of_nodes())

        if prev_G.number_of_nodes() == new_G.number_of_nodes():
            break
        else:
            prev_G = new_G.copy()

    return new_G

if __name__ == "__main__":

    # Load the data
    papers_df = pd.read_excel(str(PAPERS_FILE))
    papers_df["cited_by"] = [eval(x[1]["cited_by"]) for x in papers_df.iterrows()]
    papers_df["cited_by_short_name"] = [
        eval(x[1]["cited_by_short_name"]) for x in papers_df.iterrows()
    ]

    G = construct_graph(papers_df)
    node_weights = get_node_weights(G)

    # Show the initial graph
    # show_graph(G, node_weights)

    # Let's describe the graph's information
    print(f"Number of nodes is {G.number_of_nodes()}")

    # Now let's try removing the zero-degree nodes
    G2 = G.copy()

    # Removing 0-deg nodes
    G2.remove_nodes_from(list(nx.isolates(G2)))
    print(f"G2 after removing 0-deg nodes: {G2.number_of_nodes()}")

    G2 = subconnected_graph_prunning(G2)
    print(f"G2 after disconnected component removal: {G2.number_of_nodes()}")

    # node_weights = mxs.get_node_weights(G2)
    # show_graph(G2, node_weights)

    # Let's describe the graph's information
    # print(f"Number of nodes is {G2.number_of_nodes()}")

    # Save the new graph
    G3 = recursive_prunning(G2)

    # After iterative prunning
    print(f"Number of nodes after iterative prunning: {G3.number_of_nodes()}")

    # Save graph
    graph_to_excel(G3, DATA_DIR/'S8.xlsx')