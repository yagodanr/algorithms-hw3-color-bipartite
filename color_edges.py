"""
Bipartite Graph Edge Coloring Solver

This module reads bipartite graphs from files and computes optimal edge coloring.
Can import from generate_bipartite for graph generation capabilities.
"""

import argparse
import time
from typing import Dict
import networkx as nx
import sys






def bipartite_matching(U, W, adj, matchU, matchW):
    G = nx.Graph()

    for u in U:
        if u in adj:
            for w in adj[u]:
                G.add_edge(u, w)
    G.add_nodes_from(U, bipartite=0)
    G.add_nodes_from(W, bipartite=1)
    matching = nx.bipartite.maximum_matching(G, top_nodes=U)
    count = 0
    for u in U:
        if u in matching:
            w = matching[u]
            matchU[u] = w
            matchW[w] = u
            count += 1
    return count

def regularize_bipartite(adj, U, W):
    # Compute Δ
    U = set(U)
    W = set(W)
    degrees = {v: len(adj.get(v, [])) for v in U | W}
    Delta = max(degrees.values(), default=0)

    U = set(U)
    W = set(W)
    adj = {v: list(adj.get(v, [])) for v in U | W}

    # Compute deficits
    defU = []
    defW = []

    for u in U:
        defU.extend([u] * (Delta - len(adj[u])))
    for w in W:
        defW.extend([w] * (Delta - len(adj[w])))

    # Balance sides with dummy vertices
    dummy_id = 0
    while len(defU) < len(defW):
        du = f"_dummyU_{dummy_id}"
        dummy_id += 1
        U.add(du)
        adj[du] = []
        defU.extend([du] * Delta)

    while len(defW) < len(defU):
        dw = f"_dummyW_{dummy_id}"
        dummy_id += 1
        W.add(dw)
        adj[dw] = []
        defW.extend([dw] * Delta)

    # Add dummy edges
    for u, w in zip(defU, defW):
        adj[u].append(w)
        adj[w].append(u)

    return adj, U, W, Delta


def color_edges(all_edges: list[(str, str)], adj: dict[str: list[str]], U: set[str], W: set[str]):
    # for bipartite graph minimum number of colors is maximum degree
    max_degree = 0
    edge_color = {}
    U = sorted(U, key=lambda u: len(adj[u]))
    adj_dum, U_dum, W_dum, _ = regularize_bipartite(adj, U, W)
    if adj_dum:
        max_degree = max(len(neighbors) for neighbors in adj_dum.values())
    for color in range(max_degree+1):
        matchU = {}
        matchW = {}
        bipartite_matching(U_dum, W_dum, adj_dum, matchU, matchW)
        for u, w in matchU.items():
            # Always store in (u,w) order
            key = (u, w)

            # Remove the edge from adj_dum
            adj_dum[u].remove(w)
            adj_dum[w].remove(u)

            if u in U and w in W and key in all_edges:
                edge_color[key] = color
    return max_degree, edge_color


def save_solution_to_txt(edge_colors: Dict, num_colors: int,
                         stats: Dict, output_file: str):
    """Save coloring solution to text file."""
    with open(output_file, 'w') as f:
        f.write("STATISTICS:\n")
        for key, value in stats.items():
            f.write(f"  {key}: {value}\n")
        f.write(f"  minimum colors: {num_colors}\n")
        f.write("\n")

        f.write("EDGE COLORS:\n")
        f.write("-" * 70 + "\n")
        f.write(f"{'Edge':<30} {'Color':>10}\n")
        f.write("-" * 70 + "\n")

        for (u, w), color in sorted(edge_colors.items(), key=lambda x: (x[1], x[0])):
            edge_str = f"{u} - {w}"
            f.write(f"{edge_str:<30} {color:>10}\n")

        f.write("=" * 70 + "\n")

    print(f"\nSolution saved to: {output_file}")

# def read_graph_from_txt(filename: str) -> Tuple[List, List, List]:
#     """
#     Read bipartite graph from text file.

#     Expected format:
#     # Comments
#     u1,u2,u3  (U vertices)
#     w1,w2,w3  (W vertices)
#     u1-w1
#     u1-w2
#     ...

#     Args:
#         filename: Path to text file

#     Returns:
#         U, W, edges
#     """
#     with open(filename, 'r') as f:
#         lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]

#     if len(lines) < 2:
#         raise ValueError("File must contain at least U vertices and W vertices")

#     # First line: U vertices
#     U = [w.strip() for w in lines[0].split(',')]

#     # Second line: W vertices
#     W = [w.strip() for w in lines[1].split(',')]

#     # Remaining lines: edges
#     edges = []
#     for line in lines[2:]:
#         if '-' in line:
#             u, w = line.split('-')
#             edges.append((u.strip(), w.strip()))

#     return U, W, edges
def read_graph_from_txt(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        data.extend(line.split())

    if not data:
        raise ValueError("Empty input file")

    n1 = int(data[0])
    U = set(data[1].split(","))

    n2 = int(data[2])
    W = set(data[3].split(","))

    m = int(data[4])

    edges = []
    adj = {w: [] for w in U | W}

    for index in range(5, 5+m):
        if index >= len(data):
            raise ValueError("Not enough edge data")

        u, w = data[index].split("-")

        edges.append((u, w))
        adj[u].append(w)
        adj[w].append(u)

    return U, W, edges, adj

def main():
    parser = argparse.ArgumentParser(
        description='Color edges of a bipartite graph from file or generate new graph',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Solve from file
  python solve_bipartite.py input.txt
  python solve_bipartite.py input.txt -o solution.json
        """
    )
    # Input options
    parser.add_argument('input', type=str, nargs='?',
                       help='Input file containing bipartite graph')

    # Output options
    parser.add_argument('-o', '--output', type=str,
                       help='Output file for solution (default: auto-generated)')
    parser.add_argument('--no-save', action='store_true',
                       help='Do not save solution to file, only print')

    args = parser.parse_args()

    if args.input is None:
        parser.print_usage()
        sys.exit(1)

    input_file = args.input

    if args.output is None:
        output_file = input_file + '.out'
    else:
        output_file = args.output


    # Read time measurement
    read_start = time.time()
    U, W, edges, adj = read_graph_from_txt(input_file)
    read_time = time.time() - read_start

    # Coloring time measurement
    coloring_start = time.time()

    min_colors, edge_colors = color_edges(edges, adj, U, W)


    coloring_time = time.time() - coloring_start

    total_time = read_time + coloring_time

    # Prepare output string
    output_str = "Statistics:\n"
    output_str += "PERFORMANCE:\n"
    output_str += f"  Read time(seconds):     {read_time:.4f}\n"
    output_str += f"  Coloring time(seconds): {coloring_time:.4f}\n"
    output_str += f"  Total time(seconds):    {total_time:.4f}\n"
    output_str += f"  Minimum colors:         {min_colors}\n"
    output_str += "\n"
    output_str += "EDGE COLORS:\n"
    output_str += "----------------------------------------------------------------------\n"
    output_str += "Edge                               Color\n"
    output_str += "----------------------------------------------------------------------\n"
    for u, w in edges:

        color = edge_colors[(u, w)]
        edge_str = f"{u} - {w}"
        output_str += f"{edge_str.ljust(35)}{color}\n"
    output_str += "======================================================================\n"

    if args.no_save:
        print(output_str)
    else:
        with open(output_file, 'w') as f:
            f.write(output_str)


if __name__ == "__main__":
    # read_graph_from_txt("smallest_graph.txt")
    exit(main())