import pytest
from app.geometry import calculate_polygon_area_m2


def test_rectangle_area_3000x4000():
    """Test area calculation for a rectangle 3000 x 4000 mm = 12.0 m²"""
    polygon_mm = [
        [0, 0],
        [3000, 0],
        [3000, 4000],
        [0, 4000]
    ]
    
    area = calculate_polygon_area_m2(polygon_mm)
    assert area == 12.0


def test_polygon_less_than_3_points_raises_error():
    """Test that polygon with fewer than 3 points raises ValueError"""
    with pytest.raises(ValueError):
        calculate_polygon_area_m2([[0, 0], [1000, 0]])


def test_invalid_polygon_raises_error():
    """Test that invalid polygon geometry raises ValueError"""
    # Self-intersecting polygon (bowtie shape)
    polygon_mm = [
        [0, 0],
        [1000, 1000],
        [1000, 0],
        [0, 1000]
    ]
    
    with pytest.raises(ValueError):
        calculate_polygon_area_m2(polygon_mm)
