import random
import json
import argparse
from typing import List, Tuple


def generate_random_bipartite(n_u: int, n_w: int, edge_probability: float = 0.3) -> Tuple[List, List, List]:
    """
    Generate a random bipartite graph.

    Args:
        n_u: Number of vertices in U partition
        n_w: Number of vertices in W partition
        edge_probability: Probability of edge between any u and w

    Returns:
        U, W, edges
    """
    U = [f"u{i}" for i in range(n_u)]
    W = [f"w{i}" for i in range(n_w)]
    edges = []

    for u in U:
        for w in W:
            if random.random() < edge_probability:
                edges.append((u, w))

    return U, W, edges


def generate_complete_bipartite(n_u: int, n_w: int) -> Tuple[List, List, List]:
    """
    Generate a complete bipartite graph K(n_u, n_w).

    Args:
        n_u: Number of vertices in U partition
        n_w: Number of vertices in W partition

    Returns:
        U, W, edges
    """
    U = [f"u{i}" for i in range(n_u)]
    W = [f"w{i}" for i in range(n_w)]
    edges = [(u, w) for u in U for w in W]

    return U, W, edges


def generate_regular_bipartite(n_u: int, n_w: int, degree: int) -> Tuple[List, List, List]:
    """
    Generate a regular bipartite graph where each vertex in U has the same degree.

    Args:
        n_u: Number of vertices in U partition
        n_w: Number of vertices in W partition
        degree: Degree for each vertex in U

    Returns:
        U, W, edges
    """
    if degree > n_w:
        raise ValueError(f"Degree {degree} cannot exceed n_w={n_w}")

    U = [f"u{i}" for i in range(n_u)]
    W = [f"w{i}" for i in range(n_w)]
    edges = []

    for u in U:
        # Randomly select 'degree' vertices from W
        selected_w = random.sample(W, degree)
        for w in selected_w:
            edges.append((u, w))

    return U, W, edges


def generate_star_graph(n_leaves: int) -> Tuple[List, List, List]:
    """
    Generate a star graph (one center connected to all leaves).

    Args:
        n_leaves: Number of leaf vertices

    Returns:
        U, W, edges
    """
    U = ["center"]
    W = [f"leaf{i}" for i in range(n_leaves)]
    edges = [(U[0], w) for w in W]

    return U, W, edges


def generate_path_bipartite(n_pairs: int) -> Tuple[List, List, List]:
    """
    Generate a path-like bipartite graph.

    Args:
        n_pairs: Number of pairs in the path

    Returns:
        U, W, edges
    """
    U = [f"u{i}" for i in range(n_pairs)]
    W = [f"w{i}" for i in range(n_pairs)]
    edges = []

    for i in range(n_pairs):
        edges.append((U[i], W[i]))
        if i < n_pairs - 1:
            edges.append((U[i], W[i + 1]))

    return U, W, edges


def generate_cycle_bipartite(n: int) -> Tuple[List, List, List]:
    """
    Generate a cycle graph (must be even length for bipartite).

    Args:
        n: Number of vertices (must be even)

    Returns:
        U, W, edges
    """
    if n % 2 != 0:
        raise ValueError("Cycle must have even number of vertices for bipartite graph")

    half = n // 2
    U = [f"u{i}" for i in range(half)]
    W = [f"w{i}" for i in range(half)]
    edges = []

    # Create cycle alternating between U and W
    for i in range(half):
        edges.append((U[i], W[i]))
        edges.append((U[i], W[(i - 1) % half]))

    return U, W, edges


def save_graph_to_file(U: List, W: List, edges: List, filename: str, format: str = 'json'):
    """
    Save bipartite graph to file.

    Args:
        U, W: Vertex partitions
        edges: List of edges
        filename: Output filename
        format: 'json' or 'txt'
    """
    if format == 'json':
        data = {
            'U': U,
            'W': W,
            'edges': edges,
            'stats': {
                'n_u': len(U),
                'n_w': len(W),
                'n_edges': len(edges),
                'density': len(edges) / (len(U) * len(W)) if U and W else 0
            }
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    elif format == 'txt':
        with open(filename, 'w') as f:
            f.write(f"{len(U)}\n")
            f.write(','.join(U) + '\n')
            f.write(f"\n{len(W)}\n")
            f.write(','.join(W) + '\n')
            f.write(f"\n{len(edges)}\n")
            for u, w in edges:
                f.write(f"{u}-{w}\n")

    print(f"Graph saved to {filename}")
    print(f"  |U| = {len(U)}, |W| = {len(W)}, |E| = {len(edges)}")


def main():
    parser = argparse.ArgumentParser(description='Generate large bipartite graphs')
    parser.add_argument('--type', choices=['random', 'complete', 'regular', 'star', 'path', 'cycle'],
                        default='random', help='Type of bipartite graph to generate')
    parser.add_argument('--n_u', type=int, default=100, help='Number of vertices in U partition')
    parser.add_argument('--n_w', type=int, default=100, help='Number of vertices in W partition')
    parser.add_argument('--probability', type=float, default=0.3,
                        help='Edge probability for random graphs')
    parser.add_argument('--degree', type=int, default=5,
                        help='Degree for regular bipartite graphs')
    parser.add_argument('--output', type=str, default='bipartite_graph.json',
                        help='Output filename')
    parser.add_argument('--format', choices=['json', 'txt'], default='json',
                        help='Output format')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')

    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    # Generate graph based on type
    if args.type == 'random':
        U, W, edges = generate_random_bipartite(args.n_u, args.n_w, args.probability)
    elif args.type == 'complete':
        U, W, edges = generate_complete_bipartite(args.n_u, args.n_w)
    elif args.type == 'regular':
        U, W, edges = generate_regular_bipartite(args.n_u, args.n_w, args.degree)
    elif args.type == 'star':
        U, W, edges = generate_star_graph(args.n_u)
    elif args.type == 'path':
        U, W, edges = generate_path_bipartite(args.n_u)
    elif args.type == 'cycle':
        U, W, edges = generate_cycle_bipartite(args.n_u * 2)  # Total vertices

    # Save to file
    save_graph_to_file(U, W, edges, args.output, args.format)


if __name__ == "__main__":
    # If run without arguments, generate some example graphs
    import sys

    if len(sys.argv) == 1:
        print("Generating example graphs...\n")

        # Small random graph
        U, W, edges = generate_random_bipartite(10, 10, 0.3)
        save_graph_to_file(U, W, edges, 'small_random.json', 'json')
        print()

        # Large random graph
        U, W, edges = generate_random_bipartite(1000, 1000, 0.05)
        save_graph_to_file(U, W, edges, 'large_random.json', 'json')
        print()

        # Complete bipartite
        U, W, edges = generate_complete_bipartite(50, 50)
        save_graph_to_file(U, W, edges, 'complete_50_50.json', 'json')
        print()

        # Regular bipartite
        U, W, edges = generate_regular_bipartite(200, 100, 10)
        save_graph_to_file(U, W, edges, 'regular_200_100_d10.json', 'json')
        print()

        # Star graph
        U, W, edges = generate_star_graph(500)
        save_graph_to_file(U, W, edges, 'star_500.json', 'json')
        print()

        # Text format example
        U, W, edges = generate_random_bipartite(20, 20, 0.4)
        save_graph_to_file(U, W, edges, 'example.txt', 'txt')
        print()

        print("Example graphs generated!")
        print("\nTo generate custom graphs, use command line arguments:")
        print("  python generate_bipartite.py --type random --n_u 1000 --n_w 1000 --probability 0.1")
        print("  python generate_bipartite.py --type complete --n_u 100 --n_w 100")
        print("  python generate_bipartite.py --type regular --n_u 500 --n_w 300 --degree 15")
    else:
        main()