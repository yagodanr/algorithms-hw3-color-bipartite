#include <iostream>
#include <iomanip>
#include <fstream>
#include <sstream>
#include <string>
#include <chrono>
#include <cassert>

#include <vector>
#include <unordered_set>
#include <unordered_map>
#include <map>
#include <algorithm>
#include <queue>

const int INF = std::numeric_limits<int>::max();


struct Edge {
    std::string u, w;
    int color;
	Edge() : u{0}, w{0}, color{-1} {}
    Edge(std::string u, std::string w, int color=-1) : u(u), w(w), color(color) {}
};


// BFS to find augmenting paths and compute levels
bool bfs(const std::unordered_set<std::string>& U,
         const std::unordered_map<std::string, std::vector<std::string>>& adj,
         const std::unordered_map<std::string, std::string>& matchU,
         const std::unordered_map<std::string, std::string>& matchW,
         std::unordered_map<std::string, int>& dist) {

    std::queue<std::string> q;

    // Initialize distances and enqueue unmatched U vertices
    for (const auto& u : U) {
        if (matchU.find(u) == matchU.end()) {
            dist[u] = 0;
            q.push(u);
        } else {
            dist[u] = INF;
        }
    }

    dist["NIL"] = INF;

    // BFS to build level graph
    while (!q.empty()) {
        std::string u = q.front();
        q.pop();

        if (dist[u] < dist["NIL"]) {
            // Check all adjacent vertices in W
            auto it = adj.find(u);
            if (it != adj.end()) {
                for (const auto& w : it->second) {
                    // Get the vertex matched to w (or "NIL" if unmatched)
                    std::string matchedU = "NIL";
                    auto matchIt = matchW.find(w);
                    if (matchIt != matchW.end()) {
                        matchedU = matchIt->second;
                    }

                    // If matched vertex hasn't been visited
                    if (dist[matchedU] == INF) {
                        dist[matchedU] = dist[u] + 1;
                        if (matchedU != "NIL") {
                            q.push(matchedU);
                        }
                    }
                }
            }
        }
    }

    // Return true if we found an augmenting path to an unmatched W vertex
    return dist["NIL"] != INF;
}

// DFS to find and augment along a path
bool dfs(const std::string& u,
         const std::unordered_map<std::string, std::vector<std::string>>& adj,
         std::unordered_map<std::string, std::string>& matchU,
         std::unordered_map<std::string, std::string>& matchW,
         std::unordered_map<std::string, int>& dist) {

    if (u == "NIL") {
        return true;
    }

    // Try all adjacent vertices in W
    auto it = adj.find(u);
    if (it != adj.end()) {
        for (const auto& w : it->second) {
            // Get the vertex matched to w (or "NIL" if unmatched)
            std::string matchedU = "NIL";
            auto matchIt = matchW.find(w);
            if (matchIt != matchW.end()) {
                matchedU = matchIt->second;
            }

            // Check if this edge is in the level graph and we can augment
            if (dist[matchedU] == dist[u] + 1) {
                if (dfs(matchedU, adj, matchU, matchW, dist)) {
                    // Augment the matching
                    matchU[u] = w;
                    matchW[w] = u;
                    return true;
                }
            }
        }
    }

    // No augmenting path found from this vertex
    dist[u] = INF;
    return false;
}

int bipartite_matching(const std::unordered_set<std::string>& U,
                       const std::unordered_map<std::string, std::vector<std::string>>& adj,
                       std::unordered_map<std::string, std::string>& matchU,
                       std::unordered_map<std::string, std::string>& matchW) {

    matchU.clear();
    matchW.clear();

    int matching = 0;
    std::unordered_map<std::string, int> dist;

    // Keep finding augmenting paths until none exist
    while (bfs(U, adj, matchU, matchW, dist)) {
        // Try to find augmenting paths from all unmatched U vertices
        for (const auto& u : U) {
            if (matchU.find(u) == matchU.end()) {
                if (dfs(u, adj, matchU, matchW, dist)) {
                    matching++;
                }
            }
        }
        dist.clear();
    }

    return matching;
}

void regularize_bipartite(
    std::unordered_map<std::string, std::vector<std::string>>& adj,
    std::unordered_set<std::string>& U,
    std::unordered_set<std::string>& W,
    int& Delta
) {
    // Compute Δ
    Delta = 0;
    for (const auto& p : adj)
        Delta = std::max(Delta, (int)p.second.size());

    // Degree deficits
    std::vector<std::string> defU, defW;

    for (const auto& u : U)
        defU.insert(defU.end(), Delta - adj[u].size(), u);

    for (const auto& w : W)
        defW.insert(defW.end(), Delta - adj[w].size(), w);

    int dummy_id = 0;

    // Balance sides by adding dummy vertices
    while (defU.size() < defW.size()) {
        std::string du = "_DUMMY_U_" + std::to_string(dummy_id++);
        U.insert(du);
        adj[du] = {};
        defU.insert(defU.end(), Delta, du);
    }

    while (defW.size() < defU.size()) {
        std::string dw = "_DUMMY_W_" + std::to_string(dummy_id++);
        W.insert(dw);
        adj[dw] = {};
        defW.insert(defW.end(), Delta, dw);
    }

    // Add dummy edges to fill deficits
    for (size_t i = 0; i < defU.size(); ++i) {
        const std::string& u = defU[i];
        const std::string& w = defW[i];
        adj[u].push_back(w);
        adj[w].push_back(u);
    }
}

int color_edges(std::vector<Edge>& all_edges, const std::unordered_map<std::string, std::vector<std::string>>& adj,
                 const std::unordered_set<std::string>& U, const std::unordered_set<std::string>& W) {

    std::unordered_map<std::string, std::vector<std::string>> adj_dum = adj;
    std::unordered_set<std::string> U_dum = U;
    std::unordered_set<std::string> W_dum = W;
    int max_degree;
    regularize_bipartite(adj_dum, U_dum, W_dum, max_degree);
    assert(U_dum.size() == W_dum.size());


    std::map<std::pair<std::string, std::string>, Edge*> edge_map;
    for(auto &ed: all_edges) {
        edge_map[{ed.u, ed.w}] = &ed;
    }

    for (int col = 0; col <= max_degree; ++col) {
        std::unordered_map<std::string, std::string> matchU, matchW;
        bipartite_matching(U_dum, adj_dum, matchU, matchW);

        for (const auto& p : matchU) {
            std::string u = p.first;
            std::string w = p.second;
            // for (auto& e : all_edges) {
            //     if (e.u == u && e.w == w) {
            //         e.color = col;
            //         break;
            //     }
            // }
            if(U.count(u) && W.count(w)) {
                edge_map[{u, w}]->color = col;
            }
            // Remove the edge from adj
            std::vector<std::string>& neighbors_u = adj_dum[u];
            neighbors_u.erase(std::remove(neighbors_u.begin(), neighbors_u.end(), w), neighbors_u.end());
            std::vector<std::string>& neighbors_v = adj_dum[w];
            neighbors_v.erase(std::remove(neighbors_v.begin(), neighbors_v.end(), u), neighbors_v.end());
        }

    }
    return max_degree;
}


/**
 * Read bipartite graph from text file.
 *
 * Expected format:
 * Line 1: n1 (number of U vertices)
 * Line 2: u1,u2,u3,...  (U vertices, comma-separated)
 * Line 3: (empty line or whitespace)
 * Line 4: n2 (number of W vertices)
 * Line 5: w1,w2,w3,...  (W vertices, comma-separated)
 * Line 6: (empty line or whitespace)
 * Line 7: m (number of edges)
 * Line 8+: u-w (edges, one per line)
 *
 * Lines starting with # are treated as comments and ignored.
 */
bool read_graph_from_txt(
    const std::string& filepath,
    std::unordered_set<std::string>& U,
    std::unordered_set<std::string>& W,
    std::vector<Edge>& all_edges,
    std::unordered_map<std::string, std::vector<std::string>>& adj
) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open file " << filepath << std::endl;
        return false;
    }

    U.clear();
    W.clear();
    all_edges.clear();
    adj.clear();

    std::string line;

    // Read n1 (number of U vertices)
    int n1 = 0;
    while (std::getline(file, line)) {
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        if (!line.empty() && line[0] != '#') {
            n1 = std::stoi(line);
            break;
        }
    }

    // Read U vertices (comma-separated line)
    while (std::getline(file, line)) {
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        if (!line.empty() && line[0] != '#') {
            std::stringstream ss_u(line);
            std::string vertex;
            while (std::getline(ss_u, vertex, ',')) {
                vertex.erase(0, vertex.find_first_not_of(" \t"));
                vertex.erase(vertex.find_last_not_of(" \t") + 1);
                if (!vertex.empty()) {
                    U.insert(vertex);
                }
            }
            break;
        }
    }

    // Read n2 (number of W vertices)
    int n2 = 0;
    while (std::getline(file, line)) {
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        if (!line.empty() && line[0] != '#') {
            n2 = std::stoi(line);
            break;
        }
    }

    // Read W vertices (comma-separated line)
    while (std::getline(file, line)) {
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        if (!line.empty() && line[0] != '#') {
            std::stringstream ss_w(line);
            std::string vertex;
            while (std::getline(ss_w, vertex, ',')) {
                vertex.erase(0, vertex.find_first_not_of(" \t"));
                vertex.erase(vertex.find_last_not_of(" \t") + 1);
                if (!vertex.empty()) {
                    W.insert(vertex);
                }
            }
            break;
        }
    }

    // Read m (number of edges)
    int m = 0;
    while (std::getline(file, line)) {
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);
        if (!line.empty() && line[0] != '#') {
            m = std::stoi(line);
            break;
        }
    }

    // Read edges
    int edge_count = 0;
    while (std::getline(file, line) && edge_count < m) {
        line.erase(0, line.find_first_not_of(" \t\r\n"));
        line.erase(line.find_last_not_of(" \t\r\n") + 1);

        if (line.empty() || line[0] == '#') {
            continue;
        }

        size_t dash_pos = line.find('-');
        if (dash_pos == std::string::npos) {
            std::cerr << "Warning: Invalid edge format: " << line << std::endl;
            continue;
        }

        std::string a = line.substr(0, dash_pos);
        std::string b = line.substr(dash_pos + 1);

        // Trim whitespace
        a.erase(0, a.find_first_not_of(" \t"));
        a.erase(a.find_last_not_of(" \t") + 1);
        b.erase(0, b.find_first_not_of(" \t"));
        b.erase(b.find_last_not_of(" \t") + 1);

        // Validate and add edge
        if (U.count(a) && W.count(b)) {
            all_edges.push_back({a, b, -1});
            adj[a].push_back(b);
            adj[b].push_back(a);
            edge_count++;
        } else if (U.count(b) && W.count(a)) {
            all_edges.push_back({b, a, -1});
            adj[b].push_back(a);
            adj[a].push_back(b);
            edge_count++;
        } else {
            std::cerr << "Warning: Invalid edge: " << a << "-" << b
                      << " (vertices not in U or W)" << std::endl;
        }
    }

    file.close();

    // Validation
    if (U.size() != static_cast<size_t>(n1)) {
        std::cerr << "Warning: Expected " << n1 << " U vertices, but read "
                  << U.size() << std::endl;
    }
    if (W.size() != static_cast<size_t>(n2)) {
        std::cerr << "Warning: Expected " << n2 << " W vertices, but read "
                  << W.size() << std::endl;
    }
    if (all_edges.size() != static_cast<size_t>(m)) {
        std::cerr << "Warning: Expected " << m << " edges, but read "
                  << all_edges.size() << std::endl;
    }

    return true;
}

/**
 * Write edge coloring solution to text file.
 *
 * Format:
 * STATISTICS:
 *   Read time(seconds):     0.0234
 *   Coloring time(seconds): 0.1567
 *   Total time(seconds):    0.1890
 *   Minimum colors:         42
 *
 * EDGE COLORS:
 * ----------------------------------------------------------------------
 * Edge                           Color
 * ----------------------------------------------------------------------
 * u0 - w0                            0
 * u0 - w5                            1
 * ...
 */
bool write_solution_to_file(
    const std::string& filepath,
    const std::unordered_set<std::string>& U,
    const std::unordered_set<std::string>& W,
    const std::vector<Edge>& all_edges,
    int num_colors,
    double read_time = 0.0,
    double color_time = 0.0,
    double total_time = 0.0
) {
    std::ofstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open file " << filepath << " for writing" << std::endl;
        return false;
    }

    // Solution information
    file << "Statistics:\n";
    // Performance statistics
    if (total_time > 0.0) {
        file << "PERFORMANCE:\n";
        file << std::fixed << std::setprecision(4);
        file << "  Read time(seconds):     " << read_time <<  "\n";
        file << "  Coloring time(seconds): " << color_time << "\n";
        file << "  Total time(seconds):    " << total_time << "\n";
    }
    file <<     "  Minimum colors:         " << num_colors << "\n";

    // Color distribution
    std::unordered_map<int, int> color_counts;
    int used_colors = 0;
    for (const auto& edge : all_edges) {
        used_colors = std::max(used_colors, edge.color+1);
        if (edge.color >= 0) {
            color_counts[edge.color]++;
        }
        else {
            std::cerr << "WRONG COLOR -1" << std::endl;
            // return 1;
        }
    }
    if(used_colors != num_colors) {
        file <<     "  Used colors:         " << used_colors << "\n";
    }
    file << "\n";


    // Edge colors table
    file << "EDGE COLORS:\n";
    file << "----------------------------------------------------------------------\n";
    file << std::left << std::setw(30) << "Edge"
         << std::right << std::setw(10) << "Color" << "\n";
    file << "----------------------------------------------------------------------\n";

    // Sort edges by color, then by edge name for consistent output
    // std::vector<Edge> sorted_edges = all_edges;
    // std::sort(sorted_edges.begin(), sorted_edges.end(),
    //     [](const Edge& a, const Edge& b) {
    //         if (a.color != b.color) return a.color < b.color;
    //         if (a.u != b.u) return a.u < b.u;
    //         return a.w < b.w;
    //     });

    for (const auto& edge : all_edges) {
        std::string edge_str = edge.u + " - " + edge.w;
        file << std::left << std::setw(30) << edge_str
             << std::right << std::setw(10) << edge.color << "\n";
    }

    file << "======================================================================\n";
    file.close();

    std::cout << "Solution written to: " << filepath << std::endl;
    return true;
}

int main(int argc, char* argv[]) {

	// std::unordered_set<std::string> U, W;
	// int n1;
	// std::cin >> n1;
	// for (int i = 0; i < n1; i++) {
	// 	std::string x;
	// 	std::cin >> x;
	// 	U.insert(x);
	// }
	// std::cout << "First set U (" << n1 << " vertices): ";
	// for (auto& w : U) std::cout << w << " ";
	// std::cout << std::endl;

	// int n2;
	// std::cin >> n2;
	// for (int i = 0; i < n2; i++) {
	// 	std::string x;
	// 	std::cin >> x;
	// 	W.insert(x);
	// }
	// std::cout << "Second set W (" << n2 << " vertices): ";
	// for (auto& w : W) std::cout << w << " ";
	// std::cout << std::endl;


	// int m;
	// std::cin >> m;
	// std::vector<Edge> all_edges(m);
	// std::unordered_map<std::string, std::vector<std::string>> adj;
	// std::cout << "Edges (" << m << "):" << std::endl;
	// for (int i = 0; i < m; i++) {
	// 	std::string a, b;
	// 	std::cin >> a >> b;
	// 	if (U.count(a) && W.count(b)) {
	// 		all_edges[i] = {a, b, -1};
	// 		adj[a].push_back(b);
	// 		adj[b].push_back(a);
	// 		std::cout << a << " " << b << std::endl;
	// 	}
	// 	else if (U.count(b) && W.count(a)) {
	// 		all_edges[i] = {b, a, -1};
	// 		adj[b].push_back(a);
	// 		adj[a].push_back(b);
	// 		std::cout << b << " " << a << std::endl;
	// 	}
	// 	else {
	// 		std::cerr << "Invalid edge" << std::endl;
	// 		return 1;
	// 	}
	// }

    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <graph_path> <solution_path to write>" << std::endl;
        return 1;
    }

    std::unordered_set<std::string> U, W;
    std::vector<Edge> all_edges;
    std::unordered_map<std::string, std::vector<std::string>> adj;

    std::string filepath = argv[1];
    std::string solutionPath = argv[2];
    // std::string filepath = "./test_graph_30_20.txt";
    // std::string solutionPath = "./test_graph_30_20_cpp.txt";

    std::cout << "Reading graph from: " << filepath << std::endl;
// Start total timer
    auto start_total = std::chrono::high_resolution_clock::now();

    // Read graph
    std::cout << "Reading graph from: " << filepath << std::endl;
    auto start_read = std::chrono::high_resolution_clock::now();

    if (!read_graph_from_txt(filepath, U, W, all_edges, adj)) {
        std::cerr << "Failed to read graph from file" << std::endl;
        return 1;
    }

    auto end_read = std::chrono::high_resolution_clock::now();
    double read_time = std::chrono::duration<double>(end_read - start_read).count();

    std::cout << "Graph loaded in " << std::fixed
              << read_time << " seconds" << std::endl;

    // Color edges
    std::cout << "Computing edge coloring..." << std::endl;
    auto start_color = std::chrono::high_resolution_clock::now();

    int num_colors = color_edges(all_edges, adj, U, W);

    auto end_color = std::chrono::high_resolution_clock::now();
    double color_time = std::chrono::duration<double>(end_color - start_color).count();

    std::cout << "Edge coloring completed in " << std::fixed << std::setprecision(4)
              << color_time << " seconds" << std::endl;


    // std::cout << "Edges with colors:" << std::endl;
    // for (const auto& e : all_edges) {
    //     std::cout << e.u << " " << e.w << " " << e.color << std::endl;
    // }

    // Write solution to file
    std::cout << "\nWriting solution to file..." << std::endl;
    auto start_write = std::chrono::high_resolution_clock::now();

    if (!write_solution_to_file(solutionPath, U, W, all_edges, num_colors,
                                read_time, color_time, read_time+color_time)) {
        std::cerr << "Failed to write solution to file" << std::endl;
        return 1;
    }

    auto end_write = std::chrono::high_resolution_clock::now();
    double write_time = std::chrono::duration<double>(end_write - start_write).count();

    // End total timer
    auto end_total = std::chrono::high_resolution_clock::now();
    double total_time = std::chrono::duration<double>(end_total - start_total).count();

    // Performance statistics
    std::cout << "\nPerformance Statistics:" << std::endl;
    std::cout << "  Read time:     " << std::fixed << std::setprecision(4)
              << read_time << " seconds" << std::endl;
    std::cout << "  Coloring time: " << std::fixed << std::setprecision(4)
              << color_time << " seconds" << std::endl;
    std::cout << "  Write time:    " << std::fixed << std::setprecision(4)
              << write_time << " seconds" << std::endl;
    std::cout << "  Total time:    " << std::fixed << std::setprecision(4)
              << total_time << " seconds" << std::endl;


	return 0;
}