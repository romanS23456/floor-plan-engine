"""
SVG Debug Renderer for Floor Plan Engine.

Renders a floor plan as SVG for debug visualization.
This is API-first / GPT-first: SVG is only for human debug viewing.
Structured geometry remains the source of truth.
"""

import html
from typing import Optional
from app.models import Plan, Room, Door, Window, Furniture


def render_plan_svg(plan: Plan, width: int = 800, height: int = 600) -> str:
    """
    Render a floor plan as SVG string.
    
    Args:
        plan: The floor plan to render
        width: SVG width in pixels
        height: SVG height in pixels
    
    Returns:
        SVG string with rooms, labels, areas, doors, windows, furniture
    """
    from app.geometry import calculate_polygon_area_m2
    
    # Collect all points to determine bounds
    all_points = []
    for room in plan.rooms:
        all_points.extend(room.polygon_mm)
    for furniture in plan.furniture:
        all_points.extend(furniture.polygon_mm)
    
    if not all_points:
        return _empty_svg(width, height)
    
    # Calculate bounds
    min_x = min(p[0] for p in all_points)
    max_x = max(p[0] for p in all_points)
    min_y = min(p[1] for p in all_points)
    max_y = max(p[1] for p in all_points)
    
    # Add padding
    padding = 500  # mm
    min_x -= padding
    max_x += padding
    min_y -= padding
    max_y += padding
    
    # Calculate scale to fit SVG
    plan_width = max_x - min_x
    plan_height = max_y - min_y
    
    if plan_width == 0 or plan_height == 0:
        return _empty_svg(width, height)
    
    scale_x = (width - 40) / plan_width  # 20px margin each side
    scale_y = (height - 40) / plan_height
    scale = min(scale_x, scale_y)
    
    def transform(x: float, y: float) -> tuple:
        """Transform mm coordinates to SVG pixels."""
        px = 20 + (x - min_x) * scale
        py = 20 + (y - min_y) * scale
        # Flip Y axis so (0,0) is bottom-left
        py = height - py
        return (px, py)
    
    def polygon_to_points(polygon_mm: list) -> str:
        """Convert polygon_mm to SVG points string."""
        transformed = [transform(p[0], p[1]) for p in polygon_mm]
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in transformed)
    
    # Build SVG
    svg_parts = [
        f'<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '  <style>',
        '    .room { fill: #e8f4f8; stroke: #2c5282; stroke-width: 2; }',
        '    .room-label { font-family: Arial, sans-serif; font-size: 12px; fill: #2d3748; }',
        '    .room-area { font-family: Arial, sans-serif; font-size: 10px; fill: #718096; }',
        '    .door { fill: #ed8936; stroke: #c05621; stroke-width: 1; }',
        '    .window { fill: #63b3ed; stroke: #3182ce; stroke-width: 1; }',
        '    .furniture { fill: #fbd38d; stroke: #d69e2e; stroke-width: 1; }',
        '    .external-door { fill: #48bb78; stroke: #38a169; stroke-width: 1; }',
        '  </style>',
    ]
    
    # Render rooms
    for room in plan.rooms:
        points = polygon_to_points(room.polygon_mm)
        
        # Calculate area
        try:
            area = calculate_polygon_area_m2(room.polygon_mm)
            area_str = f"{area:.1f} m²"
        except ValueError:
            area_str = "invalid"
        
        # Room polygon
        svg_parts.append(
            f'  <polygon class="room" data-id="{html.escape(room.id)}" data-entity-type="room" points="{points}"/>'
        )
        
        # Room label (center of polygon)
        center_x = sum(p[0] for p in room.polygon_mm) / len(room.polygon_mm)
        center_y = sum(p[1] for p in room.polygon_mm) / len(room.polygon_mm)
        cx, cy = transform(center_x, center_y)
        
        escaped_name = html.escape(room.name)
        svg_parts.append(
            f'  <text class="room-label" x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle">{escaped_name}</text>'
        )
        svg_parts.append(
            f'  <text class="room-area" x="{cx:.1f}" y="{cy + 14:.1f}" text-anchor="middle">{area_str}</text>'
        )
    
    # Render doors
    for door in plan.doors:
        px, py = transform(door.position_mm[0], door.position_mm[1])
        
        # Door width in pixels
        door_width_px = door.width_mm * scale
        
        # Determine if external door
        is_external = door.to_room_id is None
        
        css_class = "external-door" if is_external else "door"
        
        svg_parts.append(
            f'  <rect class="{css_class}" data-id="{html.escape(door.id)}" data-entity-type="door" '
            f'x="{px - door_width_px/2:.1f}" y="{py - 4:.1f}" width="{door_width_px:.1f}" height="8"/>'
        )
    
    # Render windows
    for window in plan.windows:
        px, py = transform(window.position_mm[0], window.position_mm[1])
        
        # Window width in pixels
        window_width_px = window.width_mm * scale
        
        svg_parts.append(
            f'  <rect class="window" data-id="{html.escape(window.id)}" data-entity-type="window" '
            f'x="{px - window_width_px/2:.1f}" y="{py - 3:.1f}" width="{window_width_px:.1f}" height="6"/>'
        )
    
    # Render furniture
    for furn in plan.furniture:
        points = polygon_to_points(furn.polygon_mm)
        escaped_type = html.escape(furn.type)
        svg_parts.append(
            f'  <polygon class="furniture" data-id="{html.escape(furn.id)}" data-entity-type="furniture" data-furniture-type="{escaped_type}" points="{points}"/>'
        )
    
    svg_parts.append('</svg>')
    
    return "\n".join(svg_parts)


def _empty_svg(width: int, height: int) -> str:
    """Return an empty SVG with a message."""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <text x="{width//2}" y="{height//2}" text-anchor="middle" font-family="Arial" font-size="14" fill="#718096">No geometry to render</text>
</svg>'''
