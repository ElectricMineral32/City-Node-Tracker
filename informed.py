import math
import heapq

def haversine(coord1, coord2):
    """
    Calculate the great-circle distance between two points
    on the Earth's surface in kilometers.
    """
    R = 6371.0  # Earth radius in kilometers
    
    lat1, lon1 = math.radians(coord1["lat"]), math.radians(coord1["lon"])
    lat2, lon2 = math.radians(coord2["lat"]), math.radians(coord2["lon"])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def greedy_best_first(graph, start, goal):
    """
    Greedy Best-First Search
    Returns: {"path": list, "expanded": list, "distance": float}
    """
    nodes_coords = graph.get("nodes", {})
    if start not in nodes_coords or goal not in nodes_coords:
        return {"path": None, "expanded": [], "distance": 0.0}
        
    goal_coord = nodes_coords[goal]
    
    pq = []
    # Entry: (heuristic, counter, node, path, path_cost)
    counter = 0
    h_start = haversine(nodes_coords[start], goal_coord)
    heapq.heappush(pq, (h_start, counter, start, [start], 0.0))
    
    visited = set()
    expanded = []
    
    while pq:
        _, _, node, path, cost = heapq.heappop(pq)
        
        if node in visited:
            continue
            
        visited.add(node)
        expanded.append(node)
        
        if node == goal:
            return {"path": path, "expanded": expanded, "distance": round(cost, 2)}
            
        neighbors = sorted(graph.get("connections", {}).get(node, []), key=lambda x: x["node"])
        for neighbor in neighbors:
            n_name = neighbor["node"]
            n_dist = neighbor["distance"]
            if n_name not in visited:
                counter += 1
                h_val = haversine(nodes_coords[n_name], goal_coord)
                heapq.heappush(pq, (h_val, counter, n_name, path + [n_name], cost + n_dist))
                
    return {"path": None, "expanded": expanded, "distance": 0.0}

def a_star(graph, start, goal):
    """
    A* Search
    Returns: {"path": list, "expanded": list, "distance": float}
    """
    nodes_coords = graph.get("nodes", {})
    if start not in nodes_coords or goal not in nodes_coords:
        return {"path": None, "expanded": [], "distance": 0.0}
        
    goal_coord = nodes_coords[goal]
    
    pq = []
    # Entry: (f_cost, counter, node, path, g_cost)
    counter = 0
    h_start = haversine(nodes_coords[start], goal_coord)
    heapq.heappush(pq, (h_start, counter, start, [start], 0.0))
    
    visited = set()
    expanded = []
    
    while pq:
        f_cost, _, node, path, g_cost = heapq.heappop(pq)
        
        if node in visited:
            continue
            
        visited.add(node)
        expanded.append(node)
        
        if node == goal:
            return {"path": path, "expanded": expanded, "distance": round(g_cost, 2)}
            
        neighbors = sorted(graph.get("connections", {}).get(node, []), key=lambda x: x["node"])
        for neighbor in neighbors:
            n_name = neighbor["node"]
            n_dist = neighbor["distance"]
            if n_name not in visited:
                counter += 1
                g_new = g_cost + n_dist
                h_val = haversine(nodes_coords[n_name], goal_coord)
                f_new = g_new + h_val
                heapq.heappush(pq, (f_new, counter, n_name, path + [n_name], g_new))
                
    return {"path": None, "expanded": expanded, "distance": 0.0}
