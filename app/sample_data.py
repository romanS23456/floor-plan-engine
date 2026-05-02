from app.models import Plan, Room, Door, Window, Furniture


def get_valid_sample_plan() -> Plan:
    """
    Returns a valid sample floor plan with rooms:
    - entry hall
    - kitchen-living
    - pantry
    - guest bathroom
    - bedroom
    """
    
    # Define rooms with polygon coordinates in millimeters
    rooms = [
        Room(
            id="entry-hall",
            name="Entry Hall",
            polygon_mm=[
                [0, 0],
                [2000, 0],
                [2000, 3000],
                [0, 3000]
            ],
            target_area_m2=6.0
        ),
        Room(
            id="kitchen-living",
            name="Kitchen-Living",
            polygon_mm=[
                [2000, 0],
                [7000, 0],
                [7000, 5000],
                [2000, 5000]
            ],
            target_area_m2=25.0
        ),
        Room(
            id="pantry",
            name="Pantry",
            polygon_mm=[
                [7000, 0],
                [8500, 0],
                [8500, 2000],
                [7000, 2000]
            ],
            target_area_m2=3.0
        ),
        Room(
            id="guest-bathroom",
            name="Guest Bathroom",
            polygon_mm=[
                [0, 3000],
                [2000, 3000],
                [2000, 4500],
                [0, 4500]
            ],
            target_area_m2=3.0
        ),
        Room(
            id="bedroom",
            name="Bedroom",
            polygon_mm=[
                [2000, 5000],
                [7000, 5000],
                [7000, 8000],
                [2000, 8000]
            ],
            target_area_m2=15.0
        )
    ]
    
    # Define doors connecting rooms
    doors = [
        Door(
            id="door-0",
            from_room_id="entry-hall",
            to_room_id=None,  # External entrance door
            position_mm=[1000, 0],
            width_mm=900,
            swing="out"
        ),
        Door(
            id="door-1",
            from_room_id="entry-hall",
            to_room_id="kitchen-living",
            position_mm=[2000, 1500],
            width_mm=900,
            swing="right"
        ),
        Door(
            id="door-2",
            from_room_id="entry-hall",
            to_room_id="guest-bathroom",
            position_mm=[1000, 3000],
            width_mm=800,
            swing="left"
        ),
        Door(
            id="door-3",
            from_room_id="kitchen-living",
            to_room_id="pantry",
            position_mm=[7000, 1000],
            width_mm=700,
            swing="right"
        ),
        Door(
            id="door-4",
            from_room_id="kitchen-living",
            to_room_id="bedroom",
            position_mm=[4500, 5000],
            width_mm=900,
            swing="left"
        )
    ]
    
    # Define windows
    windows = [
        Window(
            id="window-1",
            room_id="kitchen-living",
            position_mm=[7000, 2500],
            width_mm=1200
        ),
        Window(
            id="window-2",
            room_id="bedroom",
            position_mm=[7000, 6500],
            width_mm=1500
        ),
        Window(
            id="window-3",
            room_id="entry-hall",
            position_mm=[0, 1500],
            width_mm=800
        )
    ]
    
    # Define furniture
    furniture = [
        Furniture(
            id="sofa-1",
            room_id="kitchen-living",
            type="sofa",
            polygon_mm=[
                [2500, 4500],
                [4500, 4500],
                [4500, 5000],
                [2500, 5000]
            ]
        ),
        Furniture(
            id="table-1",
            room_id="kitchen-living",
            type="dining-table",
            polygon_mm=[
                [5000, 2000],
                [6500, 2000],
                [6500, 3000],
                [5000, 3000]
            ]
        ),
        Furniture(
            id="bed-1",
            room_id="bedroom",
            type="bed",
            polygon_mm=[
                [3000, 6000],
                [5000, 6000],
                [5000, 7500],
                [3000, 7500]
            ]
        )
    ]
    
    return Plan(
        rooms=rooms,
        doors=doors,
        windows=windows,
        furniture=furniture
    )
