import random
import torch
import numpy as np
import time
import pdb


def remove_node_feature(graph):
    graph.node_feature = torch.ones(graph.num_nodes, 1)


# get networks for mini batch node/graph prediction tasks
def ego_nets(graph, radius=3, netlib=None, **kwargs):
    if netlib is None:
        import networkx as netlib

    # color center
    egos = []
    n = graph.num_nodes
    # A proper deepsnap.G should have nodes indexed from 0 to n-1
    for i in range(n):
        egos.append(netlib.ego_graph(graph.G, i, radius=radius))
    # relabel egos: keep center node ID, relabel other node IDs
    G = graph.G.__class__()
    id_bias = n
    for i in range(len(egos)):
        G.add_node(i, **egos[i].nodes(data=True)[i])
    for i in range(len(egos)):
        keys = list(egos[i].nodes)
        keys.remove(i)
        id_cur = egos[i].number_of_nodes() - 1
        vals = range(id_bias, id_bias + id_cur)
        id_bias += id_cur
        mapping = dict(zip(keys, vals))
        ego = netlib.relabel_nodes(egos[i], mapping, copy=True)
        G.add_nodes_from(ego.nodes(data=True))
        G.add_edges_from(ego.edges(data=True))
    graph.G = G
    graph.node_id_index = torch.arange(len(egos))


# get networks for mini batch shortest path prediction tasks
def path_len(graph, netlib=None, **kwargs):
    if netlib is None:
        import networkx as netlib

    n = graph.num_nodes
    # shortest path label
    num_label = 1000
    edge_label_index = torch.randint(n, size=(2, num_label), device=graph.edge_index.device)
    path_dict = dict(netlib.all_pairs_shortest_path_length(graph.G))
    edge_label = []
    index_keep = []
    for i in range(num_label):
        start, end = edge_label_index[0, i].item(), edge_label_index[1, i].item()
        try:
            dist = path_dict[start][end]
        except:
            continue
        edge_label.append(min(dist, 4))
        index_keep.append(i)

    edge_label = torch.tensor(edge_label, device=edge_label_index.device)
    graph.edge_label_index, graph.edge_label = edge_label_index[:, index_keep], edge_label


