#!/usr/bin/env python3
"""
Performance testing module with multiple graph sizes.
Usage: python perf_test.py --sizes 100,500,1000 [--plot]
"""

import argparse
import time
import statistics
import subprocess
import os
from typing import List, Dict, Tuple
import matplotlib.pyplot as plt
import numpy as np


# Configuration
CPP_EXECUTABLE_PATH = "./build/color"
PYTHON_EXECUTABLE = "./color_edges.py"
GRAPH_GENERATOR = "./generate_bipartite.py"


def generate_test_graph(n_u: int, n_w: int, graph_type: str = "random",
                       probability: float = 0.5, output: str = "input.txt") -> str:
    """
    Generate a test graph using the bipartite graph generator.

    Args:
        n_u: Number of vertices in U partition
        n_w: Number of vertices in W partition
        graph_type: Type of graph (random, complete, regular, star, path, cycle)
        probability: Edge probability for random graphs
        output: Output filename

    Returns:
        Path to generated graph file
    """
    cmd = [
        "python", GRAPH_GENERATOR,
        "--type", graph_type,
        "--n_u", str(n_u),
        "--n_w", str(n_w),
        "--output", output,
        "--format", "txt"
    ]

    if graph_type == "random":
        cmd.extend(["--probability", str(probability)])

    try:
        subprocess.run(cmd)
        print(f"  Generated graph: U={n_u}, W={n_w}, type={graph_type}")
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error generating graph: {e}")
        print(f"stderr: {e.stderr.decode()}")
        raise


def function_1(input_path: str, output_path: str):
    """C++ implementation."""
    subprocess.run([CPP_EXECUTABLE_PATH, input_path, output_path])



def function_2(input_path: str, output_path: str):
    """Python implementation."""
    subprocess.run(["python", PYTHON_EXECUTABLE, input_path, "-o", output_path])


def measure_performance(func, input_path: str, output_path: str,
                       iterations: int) -> List[float]:
    """Measure performance over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(input_path, output_path)
        end = time.perf_counter()
        times.append(end - start)
    return times


def run_size_test(n_u: int, n_w: int, iterations: int, warmup: int,
                  graph_type: str = "random", probability: float = 0.5) -> Dict:
    """
    Run performance test for a specific graph size.

    Returns:
        Dictionary with timing results
    """
    # Generate test graph
    input_file = f"test_graph_{n_u}_{n_w}.txt"
    generate_test_graph(n_u, n_w, graph_type, probability, input_file)

    output_cpp = f"solution_cpp_{n_u}_{n_w}.txt"
    output_py = f"solution_py_{n_u}_{n_w}.txt"

    # Warmup
    if warmup > 0:
        for _ in range(warmup):
            function_1(input_file, output_cpp)
            function_2(input_file, output_py)

    # Measure performance
    print(f"  Testing C++ ({iterations} iterations)...", end=" ")
    times_cpp = measure_performance(function_1, input_file, output_cpp, iterations)
    print("Done")

    print(f"  Testing Python ({iterations} iterations)...", end=" ")
    times_py = measure_performance(function_2, input_file, output_py, iterations)
    print("Done")

    # Cleanup
    for f in [input_file, output_cpp, output_py]:
        if os.path.exists(f):
            os.remove(f)

    return {
        'n_u': n_u,
        'n_w': n_w,
        'size': n_u + n_w,
        'cpp_times': times_cpp,
        'py_times': times_py,
        'cpp_mean': statistics.mean(times_cpp),
        'cpp_std': statistics.stdev(times_cpp) if len(times_cpp) > 1 else 0,
        'py_mean': statistics.mean(times_py),
        'py_std': statistics.stdev(times_py) if len(times_py) > 1 else 0,
        'speedup': statistics.mean(times_py) / statistics.mean(times_cpp)
    }


def plot_size_comparison(results: List[Dict], output_file: str = "size_comparison.png"):
    """
    Plot performance across different graph sizes.

    Args:
        results: List of result dictionaries from run_size_test
        output_file: Output filename for the plot
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Performance Scaling: C++ vs Python', fontsize=16, fontweight='bold')

    sizes = [r['size'] for r in results]
    cpp_means = [r['cpp_mean'] for r in results]
    cpp_stds = [r['cpp_std'] for r in results]
    py_means = [r['py_mean'] for r in results]
    py_stds = [r['py_std'] for r in results]
    speedups = [r['speedup'] for r in results]

    # Plot 1: Mean execution time vs graph size
    ax1 = axes[0, 0]
    ax1.errorbar(sizes, cpp_means, yerr=cpp_stds, fmt='o-', linewidth=2,
                 markersize=8, capsize=5, label='C++', color='blue')
    ax1.errorbar(sizes, py_means, yerr=py_stds, fmt='s-', linewidth=2,
                 markersize=8, capsize=5, label='Python', color='red')
    ax1.set_xlabel('Graph Size (|U| + |W|)', fontsize=11)
    ax1.set_ylabel('Mean Execution Time (seconds)', fontsize=11)
    ax1.set_title('Execution Time vs Graph Size')
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Plot 2: Speedup vs graph size
    ax2 = axes[0, 1]
    ax2.plot(sizes, speedups, 'go-', linewidth=2, markersize=8)
    ax2.axhline(y=1, color='gray', linestyle='--', alpha=0.5, label='Equal performance')
    ax2.set_xlabel('Graph Size (|U| + |W|)', fontsize=11)
    ax2.set_ylabel('Speedup (Python time / C++ time)', fontsize=11)
    ax2.set_title('C++ Speedup Factor')
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Add speedup values as text
    for size, speedup in zip(sizes, speedups):
        ax2.text(size, speedup, f'{speedup:.1f}x',
                ha='center', va='bottom', fontsize=9)

    # Plot 3: Log scale comparison
    ax3 = axes[1, 0]
    ax3.semilogy(sizes, cpp_means, 'o-', linewidth=2, markersize=8,
                 label='C++', color='blue')
    ax3.semilogy(sizes, py_means, 's-', linewidth=2, markersize=8,
                 label='Python', color='red')
    ax3.set_xlabel('Graph Size (|U| + |W|)', fontsize=11)
    ax3.set_ylabel('Mean Execution Time (seconds, log scale)', fontsize=11)
    ax3.set_title('Execution Time (Logarithmic Scale)')
    ax3.legend()
    ax3.grid(True, alpha=0.3, which='both')

    # Plot 4: Performance table
    ax4 = axes[1, 1]
    ax4.axis('tight')
    ax4.axis('off')

    table_data = [['Size', 'C++ (s)', 'Python (s)', 'Speedup']]
    for r in results:
        table_data.append([
            f"{r['n_u']}+{r['n_w']}",
            f"{r['cpp_mean']:.4f}",
            f"{r['py_mean']:.4f}",
            f"{r['speedup']:.2f}x"
        ])

    table = ax4.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.2, 0.25, 0.25, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)

    # Style header row
    for i in range(4):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')

    # Alternate row colors
    for i in range(1, len(table_data)):
        color = '#f0f0f0' if i % 2 == 0 else 'white'
        for j in range(4):
            table[(i, j)].set_facecolor(color)

    ax4.set_title('Performance Summary Table', fontsize=12, fontweight='bold', pad=20)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n📊 Size comparison plot saved to: {output_file}")


def plot_detailed_distributions(results: List[Dict],
                                output_file: str = "detailed_distributions.png"):
    """
    Plot detailed distribution of execution times for each size.

    Args:
        results: List of result dictionaries
        output_file: Output filename
    """
    n_sizes = len(results)
    fig, axes = plt.subplots(n_sizes, 2, figsize=(12, 4 * n_sizes))

    if n_sizes == 1:
        axes = axes.reshape(1, -1)

    fig.suptitle('Execution Time Distributions by Graph Size',
                 fontsize=16, fontweight='bold')

    for idx, result in enumerate(results):
        size_label = f"Size: {result['n_u']}+{result['n_w']} = {result['size']}"

        # Box plot
        ax_box = axes[idx, 0]
        bp = ax_box.boxplot([result['cpp_times'], result['py_times']],
                            labels=['C++', 'Python'], patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        bp['boxes'][1].set_facecolor('lightcoral')
        ax_box.set_ylabel('Execution Time (seconds)')
        ax_box.set_title(f'{size_label} - Box Plot')
        ax_box.grid(True, alpha=0.3, axis='y')

        # Histogram
        ax_hist = axes[idx, 1]
        ax_hist.hist(result['cpp_times'], bins=20, alpha=0.6, color='blue',
                    label='C++', edgecolor='black')
        ax_hist.hist(result['py_times'], bins=20, alpha=0.6, color='red',
                    label='Python', edgecolor='black')
        ax_hist.set_xlabel('Execution Time (seconds)')
        ax_hist.set_ylabel('Frequency')
        ax_hist.set_title(f'{size_label} - Histogram')
        ax_hist.legend()
        ax_hist.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"📊 Detailed distributions plot saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Test performance across different graph sizes"
    )
    parser.add_argument(
        '--sizes',
        type=str,
        default='50,100,200,500',
        help='Comma-separated list of graph sizes (e.g., "50,100,200")'
    )
    parser.add_argument(
        '--equal-partitions',
        action='store_true',
        help='Use equal U and W partitions (size/2 each)'
    )
    parser.add_argument(
        '--iterations',
        type=int,
        default=20,
        help='Number of iterations per size (default: 20)'
    )
    parser.add_argument(
        '--warmup',
        type=int,
        default=3,
        help='Number of warmup runs per size (default: 3)'
    )
    parser.add_argument(
        '--graph-type',
        choices=['random', 'complete', 'regular', 'star', 'path', 'cycle'],
        default='random',
        help='Type of bipartite graph to generate (default: random)'
    )
    parser.add_argument(
        '--probability',
        type=float,
        default=0.5,
        help='Edge probability for random graphs (default: 0.5)'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate performance plots'
    )

    args = parser.parse_args()

    # Parse sizes
    sizes = [int(s.strip()) for s in args.sizes.split(',')]

    print("="*70)
    print("PERFORMANCE TESTING ACROSS MULTIPLE GRAPH SIZES")
    print("="*70)
    print(f"Graph type: {args.graph_type}")
    print(f"Sizes to test: {sizes}")
    print(f"Iterations per size: {args.iterations}")
    print(f"Warmup runs: {args.warmup}")
    print("="*70)

    results = []

    for size in sizes:
        print(f"\n{'='*70}")
        print(f"Testing graph size: {size}")
        print(f"{'='*70}")

        if args.equal_partitions:
            n_u = n_w = size // 2
        else:
            # Use 60/40 split by default
            n_u = int(size * 0.6)
            n_w = size - n_u

        result = run_size_test(
            n_u, n_w,
            args.iterations,
            args.warmup,
            args.graph_type,
            args.probability
        )
        results.append(result)

        print(f"\n  Results for size {size}:")
        print(f"    C++:    {result['cpp_mean']:.6f}s (±{result['cpp_std']:.6f}s)")
        print(f"    Python: {result['py_mean']:.6f}s (±{result['py_std']:.6f}s)")
        print(f"    Speedup: {result['speedup']:.2f}x (C++ is faster)" if result['speedup'] > 1
              else f"    Speedup: {1/result['speedup']:.2f}x (Python is faster)")

    # Print summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"{'Size':<15} {'C++ (s)':<15} {'Python (s)':<15} {'Speedup':<15}")
    print("-"*70)
    for r in results:
        print(f"{r['size']:<15} {r['cpp_mean']:<15.6f} {r['py_mean']:<15.6f} {r['speedup']:<15.2f}x")
    print("="*70)

    # Generate plots
    if args.plot:
        print("\nGenerating plots...")
        try:
            plot_size_comparison(results)
            plot_detailed_distributions(results)
            print("✓ All plots generated successfully!")
        except Exception as e:
            print(f"Error generating plots: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()