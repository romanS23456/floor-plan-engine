"""Geometric validation for Floor Plan Engine.

MVP 4: Detects geometric issues like room overlaps, furniture placement, etc.
"""

from typing import List, Dict, Any
from app.models import Plan, Room
from app.geometry import calculate_polygon_area_m2
from app.connectivity import infer_room_type
import shapely.geometry as geom
import shapely.ops as ops


def get_room_polygons(plan: Plan) -> Dict[str, geom.Polygon]:
    """Create Shapely Polygon for each room.
    
    Returns dict mapping room_id to Polygon.
    Skips invalid polygons safely.
    """
    polygons = {}
    for room in plan.rooms:
        if len(room.polygon_mm) >= 3:
            try:
                poly = geom.Polygon(room.polygon_mm)
                if poly.is_valid:
                    polygons[room.id] = poly
            except (ValueError, Exception):
                # Skip invalid polygons - handled by basic validation
                pass
    return polygons


def detect_room_overlaps(plan: Plan) -> List[Dict[str, Any]]:
    """Detect overlapping rooms.
    
    Returns list of overlap dicts with:
    - code: ROOM_OVERLAP
    - room_ids: list of overlapping room ids
    - overlap_area_m2: area of overlap in m²
    - message: human-readable message
    """
    overlaps = []
    room_polys = get_room_polygons(plan)
    room_ids = list(room_polys.keys())
    
    for i, id1 in enumerate(room_ids):
        for id2 in room_ids[i+1:]:
            poly1 = room_polys[id1]
            poly2 = room_polys[id2]
            
            if poly1.intersects(poly2):
                intersection = poly1.intersection(poly2)
                # Check if intersection has area (not just touching)
                if intersection.area > 0:
                    overlap_area_m2 = intersection.area / 1_000_000  # mm² to m²
                    overlaps.append({
                        "code": "ROOM_OVERLAP",
                        "room_ids": [id1, id2],
                        "overlap_area_m2": round(overlap_area_m2, 4),
                        "message": f"Rooms '{id1}' and '{id2}' overlap by {overlap_area_m2:.2f} m²",
                    })
    
    return overlaps


def detect_furniture_outside_room(plan: Plan) -> List[Dict[str, Any]]:
    """Detect furniture placed outside its assigned room.
    
    Returns list of issue dicts with:
    - code: FURNITURE_OUTSIDE_ROOM or INVALID_FURNITURE_POLYGON
    - furniture_id: id of the furniture
    - room_id: id of the assigned room
    - message: human-readable message
    """
    issues = []
    room_polys = get_room_polygons(plan)
    room_by_id = {room.id: room for room in plan.rooms}
    
    for furn in plan.furniture:
        # Skip if room doesn't exist - handled by unknown references
        if furn.room_id not in room_by_id:
            continue
        
        # Check for invalid polygon
        if len(furn.polygon_mm) < 3:
            issues.append({
                "code": "INVALID_FURNITURE_POLYGON",
                "furniture_id": furn.id,
                "room_id": furn.room_id,
                "message": f"Furniture '{furn.id}' has invalid polygon (less than 3 points)",
            })
            continue
        
        # Check if furniture is inside room
        try:
            furn_poly = geom.Polygon(furn.polygon_mm)
            room_poly = room_polys.get(furn.room_id)
            
            if room_poly and not furn_poly.within(room_poly):
                # Check if at least touching/interior
                if not furn_poly.intersects(room_poly):
                    issues.append({
                        "code": "FURNITURE_OUTSIDE_ROOM",
                        "furniture_id": furn.id,
                        "room_id": furn.room_id,
                        "message": f"Furniture '{furn.id}' is outside room '{furn.room_id}'",
                    })
        except (ValueError, Exception):
            issues.append({
                "code": "INVALID_FURNITURE_POLYGON",
                "furniture_id": furn.id,
                "room_id": furn.room_id,
                "message": f"Furniture '{furn.id}' has invalid geometry",
            })
    
    return issues


def detect_unknown_references(plan: Plan) -> List[Dict[str, Any]]:
    """Detect references to non-existent rooms.
    
    Checks:
    - window.room_id exists
    - furniture.room_id exists
    
    Note: Door references are checked in basic validation.
    
    Returns list of issue dicts with:
    - code: UNKNOWN_WINDOW_ROOM_REFERENCE or UNKNOWN_FURNITURE_ROOM_REFERENCE
    - entity_refs: list of entity references
    - message: human-readable message
    """
    issues = []
    room_ids = {room.id for room in plan.rooms}
    
    # Check windows
    for window in plan.windows:
        if window.room_id not in room_ids:
            issues.append({
                "code": "UNKNOWN_WINDOW_ROOM_REFERENCE",
                "entity_refs": [
                    {"type": "window", "id": window.id},
                    {"type": "room", "id": window.room_id},
                ],
                "message": f"Window '{window.id}' references non-existent room '{window.room_id}'",
            })
    
    # Check furniture
    for furn in plan.furniture:
        if furn.room_id not in room_ids:
            issues.append({
                "code": "UNKNOWN_FURNITURE_ROOM_REFERENCE",
                "entity_refs": [
                    {"type": "furniture", "id": furn.id},
                    {"type": "room", "id": furn.room_id},
                ],
                "message": f"Furniture '{furn.id}' references non-existent room '{furn.room_id}'",
            })
    
    return issues


def detect_min_area_issues(plan: Plan) -> List[Dict[str, Any]]:
    """Detect rooms with area below minimum for their type.
    
    Minimum areas:
    - bathroom: 2.0 m²
    - pantry: 1.0 m²
    - private: 6.0 m²
    - public: 8.0 m²
    - entry: 2.0 m²
    - hall: 2.0 m²
    
    Returns list of issue dicts with:
    - code: ROOM_AREA_BELOW_MINIMUM
    - room_id: id of the room
    - area_m2: actual area
    - min_area_m2: required minimum
    - room_type: inferred type
    - message: human-readable message
    """
    issues = []
    
    min_areas = {
        "bathroom": 2.0,
        "pantry": 1.0,
        "private": 6.0,
        "public": 8.0,
        "entry": 2.0,
        "hall": 2.0,
        "service": 2.0,
    }
    
    for room in plan.rooms:
        if len(room.polygon_mm) < 3:
            continue
        
        try:
            area = calculate_polygon_area_m2(room.polygon_mm)
        except (ValueError, Exception):
            continue
        
        room_type = infer_room_type(room)
        min_area = min_areas.get(room_type, 0)
        
        if min_area > 0 and area < min_area:
            issues.append({
                "code": "ROOM_AREA_BELOW_MINIMUM",
                "room_id": room.id,
                "area_m2": round(area, 2),
                "min_area_m2": min_area,
                "room_type": room_type,
                "message": f"Room '{room.id}' ({room_type}) area {area:.2f} m² is below minimum {min_area} m²",
            })
    
    return issues


def detect_rough_door_furniture_conflicts(plan: Plan) -> List[Dict[str, Any]]:
    """Detect rough door-furniture conflicts.
    
    MVP heuristic:
    - Treat door.position_mm as a point
    - If point is inside furniture polygon OR
      distance to furniture polygon < max(300mm, door.width_mm/2)
    
    Returns list of issue dicts with:
    - code: ROUGH_DOOR_FURNITURE_CONFLICT
    - door_id: id of the door
    - furniture_id: id of the furniture
    - distance_mm: distance to furniture (if applicable)
    - confidence: "low" (approximate check)
    - message: human-readable message
    """
    issues = []
    
    for door in plan.doors:
        door_point = geom.Point(door.position_mm)
        clearance = max(300, door.width_mm / 2)
        
        for furn in plan.furniture:
            if len(furn.polygon_mm) < 3:
                continue
            
            try:
                furn_poly = geom.Polygon(furn.polygon_mm)
                
                # Check if door point is inside furniture
                if furn_poly.contains(door_point):
                    issues.append({
                        "code": "ROUGH_DOOR_FURNITURE_CONFLICT",
                        "door_id": door.id,
                        "furniture_id": furn.id,
                        "distance_mm": 0,
                        "confidence": "medium",
                        "message": f"Door '{door.id}' position is inside furniture '{furn.id}'",
                    })
                else:
                    # Check distance to furniture
                    distance = door_point.distance(furn_poly.boundary)
                    if distance < clearance:
                        issues.append({
                            "code": "ROUGH_DOOR_FURNITURE_CONFLICT",
                            "door_id": door.id,
                            "furniture_id": furn.id,
                            "distance_mm": round(distance, 2),
                            "confidence": "low",
                            "message": f"Door '{door.id}' is {distance:.0f}mm from furniture '{furn.id}' (clearance: {clearance:.0f}mm)",
                        })
            except (ValueError, Exception):
                continue
    
    return issues
