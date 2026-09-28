import os
import json
from flask import Flask, render_template, jsonify, request

from uninformed import bfs, dfs, ucs, ids
from informed import greedy_best_first, a_star

app = Flask(__name__)

MAP_DATA_FILE = "map_data.json"

# Maps the algorithm keys sent by the frontend dropdown to the actual
# search functions in uninformed.py / informed.py.
ALGORITHMS = {
    "bfs": bfs,
    "dfs": dfs,
    "ucs": ucs,
    "ids": ids,
    "greedy": greedy_best_first,
    "astar": a_star,
    # "memory_bounded" (SMA*) intentionally omitted - graduate-only requirement.
}


def load_map_data():
    """Load the graph from map_data.json, in the nodes/connections format
    produced by data_fetcher.py. This is the format uninformed.py and
    informed.py expect directly."""
    if os.path.exists(MAP_DATA_FILE):
        try:
            with open(MAP_DATA_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {MAP_DATA_FILE}: {e}")
    return {"nodes": {}, "connections": {}}


def to_frontend_format(map_data):
    """Convert the nodes/connections graph into the locations/graph
    nested-dict shape that index.html expects, for populating the city
    dropdowns and drawing the base map lines."""
    nodes = map_data.get("nodes", {})
    connections = map_data.get("connections", {})

    graph = {}
    for node, neighbors in connections.items():
        graph[node] = {n["node"]: n["distance"] for n in neighbors}

    total_edges = sum(len(v) for v in connections.values()) // 2  # undirected

    return {
        "region": map_data.get("region", "Las Vegas Metro Area, NV"),
        "total_cities": len(nodes),
        "total_edges": total_edges,
        "locations": nodes,
        "graph": graph,
    }


@app.route("/")
def index():
    """Renders the main deployment webpage."""
    return render_template("index.html")


@app.route("/api/map", methods=["GET"])
def get_map():
    """Returns map locations and graph connections in the format the
    frontend expects."""
    map_data = load_map_data()
    return jsonify(to_frontend_format(map_data))


@app.route("/api/search", methods=["POST"])
def search():
    """Runs the selected search algorithm between start and goal and
    returns the resulting path, cost, and number of nodes expanded."""
    payload = request.get_json() or {}
    start = payload.get("start", "")
    goal = payload.get("goal", "")
    algorithm = payload.get("algorithm", "")

    map_data = load_map_data()
    nodes = map_data.get("nodes", {})

    if algorithm not in ALGORITHMS:
        return jsonify({
            "status": "error",
            "message": f"Algorithm '{algorithm}' is not implemented in this project.",
            "path": [],
            "cost": 0,
            "nodes_expanded": 0
        }), 400

    if start not in nodes or goal not in nodes:
        return jsonify({
            "status": "error",
            "message": "Start or destination city not found in the graph.",
            "path": [],
            "cost": 0,
            "nodes_expanded": 0
        }), 400

    result = ALGORITHMS[algorithm](map_data, start, goal)

    if not result.get("path"):
        return jsonify({
            "status": "no_path",
            "message": f"No path found between '{start}' and '{goal}'.",
            "path": [],
            "cost": 0,
            "nodes_expanded": len(result.get("expanded", []))
        })

    return jsonify({
        "status": "ok",
        "message": f"{algorithm.upper()} search completed.",
        "path": result["path"],
        "cost": result["distance"],
        "nodes_expanded": len(result["expanded"])
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
