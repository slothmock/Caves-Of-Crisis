from core.map.tile_types import Tile, TileType, WaterTile

CAVE_WALL = Tile(
    name="Cave Wall",
    color=(70, 70, 70),
    blocked=True,
    transparency=0.1,  # 0.1 => almost fully opaque (blocks most light to allow for shadows)
    description="The walls close in around you, rough and unyielding. Their cold, gray surface whispers of the darkness that dwells within.",
    tile_type=TileType.WALL
)

CAVE_FLOOR = Tile(
    name="Cave Floor",
    color=(120, 100, 90),
    blocked=False,
    transparency=1.0,  # 1.0 => fully transparent (no light blocked)
    description="The ground is uneven, scattered with rocks. Every step echoes like a distant footstep in the vast, empty cavern.",
    tile_type=TileType.FLOOR
)

MOSSY_WALL = Tile(
    name="Mossy Wall",
    color=(50, 100, 50),
    blocked=True,
    transparency=0.0,  # Fully opaque (no transparency)
    description="A thick layer of moss clings to the wall, cold and slick. You feel an unnatural dampness creeping along the stone.",
    tile_type=TileType.WALL
)

WATER = WaterTile(
    name="Water",
    color=(30, 60, 100),
    blocked=False,
    transparency=0.4,  # partially blocks light
    description="The surface of the water reflects the faintest light, but something stirs beneath, waiting for the right moment to rise.",
    tile_type=TileType.WATER
)
