"""
data_fetcher.py

Builds a road-network graph for the Las Vegas Metro Area.
- Geocodes each location using the Nominatim OpenStreetMap API.
- Retrieves real driving distances between connected locations using OSRM.
- Saves the resulting graph to map_data.json.

Run this once (or whenever you change the location/edge list) to regenerate
map_data.json. It is deliberately slow (rate-limited) to respect Nominatim's
usage policy (max 1 request/sec).
"""

import json
import time
import math
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "http://router.project-osrm.org/route/v1/driving"

HEADERS = {
    # Nominatim requires a descriptive User-Agent identifying the app.
    "User-Agent": "VegasMetroSearchVisualizer/1.0 (student-project)"
}

# ---------------------------------------------------------------------------
# 1. Locations (>= 20 required). Query strings are made specific to Nevada
#    to avoid Nominatim returning an ambiguous / wrong match.
# ---------------------------------------------------------------------------
LOCATIONS = {
    "Downtown Las Vegas": "Downtown Las Vegas, NV, USA",
    "The Strip": "Las Vegas Strip, Paradise, NV, USA",
    "Henderson": "Henderson, NV, USA",
    "North Las Vegas": "North Las Vegas, NV, USA",
    "Summerlin": "Summerlin, Las Vegas, NV, USA",
    "Spring Valley": "Spring Valley, NV, USA",
    "Enterprise": "Enterprise, NV, USA",
    "Whitney": "Whitney, NV, USA",
    "Sunrise Manor": "Sunrise Manor, NV, USA",
    "Winchester": "Winchester, NV, USA",
    "Boulder City": "Boulder City, NV, USA",
    "Blue Diamond": "Blue Diamond, NV, USA",
    "Mount Charleston": "Mount Charleston, NV, USA",
    "Nellis AFB": "Nellis Air Force Base, NV, USA",
    "Sloan": "Sloan, NV, USA",
    "Indian Springs": "Indian Springs, NV, USA",
    "Jean": "Jean, NV, USA",
    "Goodsprings": "Goodsprings, NV, USA",
    "Pahrump": "Pahrump, NV, USA",
    "Laughlin": "Laughlin, NV, USA",
    "Mesquite": "Mesquite, NV, USA",
    "Searchlight": "Searchlight, NV, USA",
}

# ---------------------------------------------------------------------------
# 2. Edges (undirected). Hub-and-spoke structure mirroring real Vegas roads:
#    - Core valley cities are densely interconnected.
#    - Nearby towns are spurs off one or two core cities.
#    - Far-out towns connect via a single logical link.
# ---------------------------------------------------------------------------
EDGES = [
    # Core cluster - densely connected
    ("Downtown Las Vegas", "The Strip"),
    ("Downtown Las Vegas", "North Las Vegas"),
    ("Downtown Las Vegas", "Sunrise Manor"),
    ("Downtown Las Vegas", "Winchester"),
    ("The Strip", "Winchester"),
    ("The Strip", "Enterprise"),
    ("The Strip", "Spring Valley"),
    ("The Strip", "Henderson"),
    ("Henderson", "Winchester"),
    ("Henderson", "Enterprise"),
    ("Henderson", "Whitney"),
    ("Summerlin", "Downtown Las Vegas"),
    ("Summerlin", "Spring Valley"),
    ("Summerlin", "North Las Vegas"),
    ("Spring Valley", "Enterprise"),
    ("Spring Valley", "Whitney"),
    ("Enterprise", "Whitney"),
    ("Enterprise", "Sloan"),
    ("Sunrise Manor", "North Las Vegas"),
    ("Sunrise Manor", "Nellis AFB"),
    ("Winchester", "Whitney"),

    # Spurs off the core
    ("Henderson", "Boulder City"),
    ("Spring Valley", "Blue Diamond"),
    ("Summerlin", "Mount Charleston"),
    ("North Las Vegas", "Nellis AFB"),
    ("Summerlin", "Indian Springs"),

    # Far nodes - single logical connection
    ("Sloan", "Jean"),
    ("Jean", "Goodsprings"),
    ("Blue Diamond", "Pahrump"),
    ("Boulder City", "Searchlight"),
    ("Searchlight", "Laughlin"),
    ("North Las Vegas", "Mesquite"),
]


def geocode(name, query):
    """Look up latitude/longitude for a location using Nominatim."""
    params = {"q": query, "format": "json", "limit": 1}
    resp = requests.get(NOMINATIM_URL, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"No geocoding result for '{name}' (query: '{query}')")
    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    return lat, lon


def haversine_km(coord_a, coord_b):
    """Straight-line great-circle distance in km, used as a fallback if
    OSRM routing is unavailable for a given pair of coordinates."""
    lat1, lon1 = math.radians(coord_a[0]), math.radians(coord_a[1])
    lat2, lon2 = math.radians(coord_b[0]), math.radians(coord_b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    R = 6371.0  # Earth radius in km
    return round(R * c, 2)


def get_road_distance(coord_a, coord_b):
    """Get driving distance (km) and duration (min) between two (lat, lon)
    coordinates using OSRM's public routing server. Falls back to
    straight-line (haversine) distance if OSRM fails or times out, so a
    single flaky request doesn't crash the whole graph build."""
    lon_a, lat_a = coord_a[1], coord_a[0]
    lon_b, lat_b = coord_b[1], coord_b[0]
    url = f"{OSRM_URL}/{lon_a},{lat_a};{lon_b},{lat_b}"
    params = {"overview": "false"}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "Ok":
            raise ValueError(f"OSRM routing failed: {data.get('code')}")
        route = data["routes"][0]
        distance_km = route["distance"] / 1000.0
        duration_min = route["duration"] / 60.0
        return round(distance_km, 2), round(duration_min, 2)
    except Exception as e:
        print(f"    [Warning] OSRM failed ({e}); using straight-line distance instead")
        distance_km = haversine_km(coord_a, coord_b)
        # Rough estimate: assume ~50 km/h average speed for the fallback duration
        duration_min = round(distance_km / 50.0 * 60.0, 2)
        return distance_km, duration_min


def build_graph():
    nodes = {}

    print("Geocoding locations...")
    for name, query in LOCATIONS.items():
        print(f"  -> {name}")
        lat, lon = geocode(name, query)
        nodes[name] = {"lat": lat, "lon": lon}
        time.sleep(1)  # respect Nominatim's 1 req/sec rate limit

    print("\nFetching road distances for edges...")
    # connections[node] = [{"node": neighbor, "distance": km}, ...]
    connections = {name: [] for name in nodes}
    edge_count = 0
    for a, b in EDGES:
        if a not in nodes or b not in nodes:
            print(f"  !! Skipping edge ({a}, {b}) - missing node")
            continue
        coord_a = (nodes[a]["lat"], nodes[a]["lon"])
        coord_b = (nodes[b]["lat"], nodes[b]["lon"])
        print(f"  -> {a} <-> {b}")
        distance_km, duration_min = get_road_distance(coord_a, coord_b)

        # Undirected: add the edge to both nodes' adjacency lists
        connections[a].append({
            "node": b, "distance": distance_km, "duration_min": duration_min
        })
        connections[b].append({
            "node": a, "distance": distance_km, "duration_min": duration_min
        })
        edge_count += 1
        time.sleep(0.5)  # be polite to the public OSRM demo server

    graph = {"nodes": nodes, "connections": connections}
    return graph, edge_count


def main():
    graph, edge_count = build_graph()
    with open("map_data.json", "w") as f:
        json.dump(graph, f, indent=2)
    print(f"\nSaved graph with {len(graph['nodes'])} nodes and "
          f"{edge_count} edges (undirected) to map_data.json")


if __name__ == "__main__":
    main()
