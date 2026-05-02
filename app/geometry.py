from shapely.geometry import Polygon


def calculate_polygon_area_m2(polygon_mm: list) -> float:
    """
    Calculate the area of a polygon in square meters.
    
    Args:
        polygon_mm: List of [x, y] coordinates in millimeters
        
    Returns:
        Area in square meters (float)
        
    Raises:
        ValueError: If polygon is invalid or has fewer than 3 points
    """
    if len(polygon_mm) < 3:
        raise ValueError("Polygon must have at least 3 points")
    
    try:
        geom = Polygon(polygon_mm)
        if not geom.is_valid:
            raise ValueError("Invalid polygon geometry")
        
        # Shapely returns area in the same units as coordinates (mm²)
        # Convert to m² by dividing by 1,000,000 (1000 * 1000)
        area_mm2 = geom.area
        area_m2 = area_mm2 / 1_000_000.0
        
        return area_m2
    except Exception as e:
        raise ValueError(f"Failed to calculate polygon area: {str(e)}")
