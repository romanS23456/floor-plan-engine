"""
Connectivity analysis for floor plans.

This module provides functions to analyze room connectivity through doors,
detect entry points, find unreachable rooms, and identify privacy issues.
"""

from typing import List, Dict, Set, Optional
import networkx as nx
from app.models import Plan, Room


def infer_room_type(room: Room) -> str:
    """
    Infer room type from room id or name.
    
    Returns one of:
    - entry
    - hall
    - bathroom
    - pantry
    - private
    - public
    - service
    - unknown
    """
    # Combine id and name for matching (case-insensitive)
    identifier = f"{room.id} {room.name}".lower()
    
    # Check for entry/hall
    if any(kw in identifier for kw in ["entry", "entrance"]):
        return "entry"
    if "hall" in identifier:
        return "hall"
    
    # Check for bathroom
    if any(kw in identifier for kw in ["bath", "wc", "toilet"]):
        return "bathroom"
    
    # Check for pantry/storage
    if any(kw in identifier for kw in ["pantry", "storage"]):
        return "pantry"
    
    # Check for private rooms (bedrooms)
    if any(kw in identifier for kw in ["bedroom", "master", "child"]):
        return "private"
    
    # Check for public rooms (kitchen, living, dining)
    if any(kw in identifier for kw in ["kitchen", "living", "dining"]):
        return "public"
    
    # Check for service rooms
    if any(kw in identifier for kw in ["laundry", "utility", "mechanical"]):
        return "service"
    
    return "unknown"


def build_room_graph(plan: Plan) -> nx.Graph:
    """
    Build a NetworkX graph representing room connectivity.
    
    Nodes are room IDs.
    Edges represent doors connecting rooms.
    
    Doors with to_room_id = null are external doors but don't add 
    an 'exterior' node - they just indicate the from_room has external access.
    
    Invalid room references are silently skipped (validation should catch them).
    
    Returns:
        networkx.Graph with room IDs as nodes
    """
    graph = nx.Graph()
    
    # Add all rooms as nodes
    room_ids = set(room.id for room in plan.rooms)
    for room_id in room_ids:
        graph.add_node(room_id)
    
    # Add edges for doors
    for door in plan.doors:
        # Skip if from_room doesn't exist
        if door.from_room_id not in room_ids:
            continue
        
        # If to_room exists, add edge between them
        if door.to_room_id is not None and door.to_room_id in room_ids:
            graph.add_edge(door.from_room_id, door.to_room_id)
        # If to_room is null, this is an external door - no edge added
        # but the from_room will be identified as entry later
    
    return graph


def get_entry_room_ids(plan: Plan) -> List[str]:
    """
    Find entry rooms in the plan.
    
    Entry rooms are:
    - Rooms with a door that has to_room_id = null (external door)
    - Rooms with inferred type 'entry'
    
    Returns:
        List of unique room IDs that are entry points
    """
    entry_rooms: Set[str] = set()
    
    # Find rooms with external doors (to_room_id = null)
    for door in plan.doors:
        if door.to_room_id is None:
            entry_rooms.add(door.from_room_id)
    
    # Find rooms with inferred type 'entry'
    for room in plan.rooms:
        if infer_room_type(room) == "entry":
            entry_rooms.add(room.id)
    
    return list(entry_rooms)


def find_unreachable_rooms(plan: Plan) -> List[str]:
    """
    Find rooms that are not reachable from any entry room.
    
    If there are no entry rooms, returns empty list (validate_plan 
    will add NO_ENTRY_ROOM warning instead).
    
    Returns:
        List of room IDs that cannot be reached from any entry room
    """
    graph = build_room_graph(plan)
    entry_rooms = get_entry_room_ids(plan)
    
    # If no entry rooms, return empty list
    if not entry_rooms:
        return []
    
    # Filter entry rooms to only those that exist in the graph
    valid_entry_rooms = [r for r in entry_rooms if r in graph.nodes()]
    if not valid_entry_rooms:
        return []
    
    # Find all rooms reachable from any entry room
    reachable: Set[str] = set()
    for entry_room in valid_entry_rooms:
        try:
            reachable.update(nx.single_source_shortest_path(graph, entry_room).keys())
        except nx.NetworkXError:
            continue
    
    # Find unreachable rooms
    all_rooms = set(graph.nodes())
    unreachable = all_rooms - reachable
    
    return list(unreachable)


def detect_pantry_through_bathroom(plan: Plan) -> List[str]:
    """
    Detect pantries that are only accessible through a bathroom.
    
    Warning conditions:
    - Pantry has only one connection and it leads to a bathroom
    - All paths from entry rooms to pantry pass through a bathroom
    
    Returns:
        List of pantry room IDs with problematic access
    """
    graph = build_room_graph(plan)
    entry_rooms = get_entry_room_ids(plan)
    
    # Get all pantry rooms
    pantry_rooms = [
        room.id for room in plan.rooms 
        if infer_room_type(room) == "pantry"
    ]
    
    # Get all bathroom rooms
    bathroom_rooms = set(
        room.id for room in plan.rooms 
        if infer_room_type(room) == "bathroom"
    )
    
    problematic_pantry_rooms: List[str] = []
    
    for pantry_id in pantry_rooms:
        if pantry_id not in graph.nodes():
            continue
        
        # Check if pantry has only one connection and it's to a bathroom
        neighbors = list(graph.neighbors(pantry_id))
        if len(neighbors) == 1 and neighbors[0] in bathroom_rooms:
            problematic_pantry_rooms.append(pantry_id)
            continue
        
        # Check if all paths from entry rooms to pantry pass through bathroom
        if entry_rooms:
            all_paths_through_bathroom = True
            
            for entry_room in entry_rooms:
                if entry_room not in graph.nodes():
                    continue
                if entry_room == pantry_id:
                    continue
                
                try:
                    # Get all simple paths from entry to pantry
                    paths = list(nx.all_simple_paths(graph, entry_room, pantry_id))
                    
                    # Check if any path avoids bathrooms
                    has_clean_path = False
                    for path in paths:
                        # Path includes start and end, check intermediate nodes
                        intermediate = path[1:-1]  # Exclude entry and pantry
                        if not any(node in bathroom_rooms for node in intermediate):
                            has_clean_path = True
                            break
                    
                    if has_clean_path:
                        all_paths_through_bathroom = False
                        break
                except (nx.NetworkXNoPath, nx.NetworkXError):
                    continue
            
            if all_paths_through_bathroom and pantry_id not in problematic_pantry_rooms:
                problematic_pantry_rooms.append(pantry_id)
    
    return problematic_pantry_rooms


def detect_privacy_warnings(plan: Plan) -> List[Dict[str, str]]:
    """
    Detect privacy-related warnings in the plan.
    
    Warning conditions:
    - Private room directly connected to public room
    - Bathroom directly connected to pantry
    - Private room is a pass-through (degree > 1 and paths go through it)
    
    Returns:
        List of dicts with keys:
        - type: warning type
        - room_id: affected room
        - details: description
    """
    graph = build_room_graph(plan)
    
    warnings: List[Dict[str, str]] = []
    
    # Build room type mapping
    room_types: Dict[str, str] = {}
    for room in plan.rooms:
        room_types[room.id] = infer_room_type(room)
    
    bathroom_rooms = set(rid for rid, rtype in room_types.items() if rtype == "bathroom")
    pantry_rooms = set(rid for rid, rtype in room_types.items() if rtype == "pantry")
    private_rooms = set(rid for rid, rtype in room_types.items() if rtype == "private")
    public_rooms = set(rid for rid, rtype in room_types.items() if rtype == "public")
    
    # Check each edge in the graph
    for edge in graph.edges():
        room_a, room_b = edge
        type_a = room_types.get(room_a, "unknown")
        type_b = room_types.get(room_b, "unknown")
        
        # Warning: private directly connected to public
        if (type_a == "private" and type_b == "public") or \
           (type_a == "public" and type_b == "private"):
            private_room = room_a if type_a == "private" else room_b
            warnings.append({
                "type": "PRIVACY_DIRECT_PUBLIC_PRIVATE",
                "room_id": private_room,
                "details": f"Private room '{private_room}' directly connected to public room"
            })
        
        # Warning: bathroom connected to pantry
        if (room_a in bathroom_rooms and room_b in pantry_rooms) or \
           (room_a in pantry_rooms and room_b in bathroom_rooms):
            pantry_room = room_a if room_a in pantry_rooms else room_b
            warnings.append({
                "type": "BATHROOM_CONNECTED_TO_PANTRY",
                "room_id": pantry_room,
                "details": f"Bathroom directly connected to pantry '{pantry_room}'"
            })
    
    # Check for pass-through private rooms
    for private_room in private_rooms:
        if private_room not in graph.nodes():
            continue
        
        degree = graph.degree(private_room)
        if degree > 1:
            # Check if this room is on paths between other rooms
            # Simple heuristic: if removing this room disconnects the graph
            # or if there are paths that go through it
            neighbors = list(graph.neighbors(private_room))
            if len(neighbors) >= 2:
                # Check if there's a path between any two neighbors that doesn't go through this room
                is_pass_through = False
                for i, neighbor_a in enumerate(neighbors):
                    for neighbor_b in neighbors[i+1:]:
                        try:
                            # Try to find path without going through private_room
                            # Since we're checking neighbors, any path between them
                            # that doesn't use private_room means it's not purely pass-through
                            # But if private_room is the ONLY connection, it's pass-through
                            paths = list(nx.all_simple_paths(graph, neighbor_a, neighbor_b))
                            # If all paths go through private_room, it's a pass-through
                            all_through_private = True
                            for path in paths:
                                if private_room not in path:
                                    all_through_private = False
                                    break
                            if all_through_private:
                                is_pass_through = True
                                break
                        except (nx.NetworkXNoPath, nx.NetworkXError):
                            # No path between neighbors except through private_room
                            is_pass_through = True
                            break
                    if is_pass_through:
                        break
                
                if is_pass_through:
                    warnings.append({
                        "type": "PRIVACY_PASS_THROUGH_PRIVATE_ROOM",
                        "room_id": private_room,
                        "details": f"Private room '{private_room}' is a pass-through room (degree={degree})"
                    })
    
    return warnings
