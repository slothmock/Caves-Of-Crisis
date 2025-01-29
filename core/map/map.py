import copy
import numpy as np
import random
import pygame
from core.camera import Camera
from core.items.item_factory import ItemFactory
from core.items.item_list import ItemList
from core.logging import logger
from core.map.tile_types import Tile, TileType
from core.map.tileset import MOSSY_WALL, CAVE_WALL, CAVE_FLOOR, WATER
from core.ui.loading import render_loading_screen

# 8 directions (octants) for shadowcasting
OCTANTS = [
    ( 1,  0,  0,  1),  # E-NE
    ( 1,  0,  0, -1),  # E-SE
    (-1,  0,  0,  1),  # W-NW
    (-1,  0,  0, -1),  # W-SW
    ( 0,  1,  1,  0),  # N-NE
    ( 0,  1, -1,  0),  # N-NW
    ( 0, -1,  1,  0),  # S-SE
    ( 0, -1, -1,  0)   # S-SW
]

# Item probability
RARITY_PROBABILITIES = {
    "common": 60,     
    "uncommon": 25,   
    "rare": 10,
    "epic": 4,       
    "legendary": 1,   
    "none": 10        
}

class Map:
    def __init__(self, tile_size: int, width: int = 100, height: int = 100):
        self.tile_size = tile_size
        self.item_size = 28
        self.width = width
        self.height = height

        # Using NumPy arrays for performance
        self.map_data = np.full((self.height, self.width), CAVE_WALL, dtype=object)
        self.visible_map = np.zeros((self.height, self.width), dtype=bool)
        self.explored_map = np.zeros((self.height, self.width), dtype=bool)

        self.is_revealed = False

    def create_tile(self, tile_type, x, y):
        """Create a new tile and set its coordinates."""
        tile = copy.deepcopy(tile_type)  # Ensure each tile is a unique object
        tile.x = x
        tile.y = y
        tile.items = []  # Initialize the items list for each tile
        return tile
    
    def place_item_at(self, x, y, item):
        """Place an item on a specific tile."""
        tile = self.map_data[y][x]
        if tile:
            tile.items.append(item)  # Safely append to the tile's items list
            logger.debug(f"Placed item '{item.name}' on tile at ({x}, {y})")

    def get_items_at(self, x, y):
        """Return the list of items at the given coordinates."""
        tile = self.map_data[y][x]
        if tile:
            return tile.items
        return []

    def remove_items(self, x, y, items):
        """Remove an item from the tile at (x, y)."""
        tile = self.map_data[y][x]
        for item in items:
            if tile and item in tile.items:
                tile.remove_item(item)

    # ------------------------------------------------------------------------
    # Cave Generation (Cellular Automata Base)
    # ------------------------------------------------------------------------

    def generate_cave(
        self,
        fill_percent: float = 0.45,
        seed: int = None,
        smoothing_iterations: int = 3,
        connect_regions: bool = True,
        add_moss: bool = True,
        add_water: bool = True,
        screen: pygame.Surface = None,
        font: pygame.font.Font = None,
        progress: float = 0.0
    ) -> float:
        """
        Generate the cave with a thematic loading screen.

        Args:
            screen (pygame.Surface): The screen to render the loading screen on.
            font (pygame.font.Font): Font for rendering text.
            progress (float): Current progress value.
        Returns:
            float: Final progress value after generation.
        """
        if seed is not None:
            random.seed(seed)

        logger.debug("Generating cave with fill=%.2f, seed=%s", fill_percent, seed)

        # Helper function to render the loading screen and update progress
        def update_progress(label, target_progress):
            nonlocal progress
            progress = render_loading_screen(screen, font, label, target_progress, progress)

        # 1 Fill the map with walls and floors
        update_progress("Carving the caverns...", 0.0)

        # Create a mask for the borders
        borders = np.zeros((self.height, self.width), dtype=bool)
        borders[0, :] = True
        borders[-1, :] = True
        borders[:, 0] = True
        borders[:, -1] = True

        # Create random noise for the interior
        random_fill = np.random.random((self.height, self.width)) < fill_percent

        # Combine borders and random_fill to determine wall positions
        walls = borders | random_fill

        # Process rows with progress updates
        for y in range(self.height):
            for x in range(self.width):
                tile_type = CAVE_WALL if walls[y, x] else CAVE_FLOOR
                self.map_data[y][x] = self.create_tile(tile_type, x, y)

            # Update progress for each row
            update_progress(f"Carving the caverns ({((y + 1) / self.height * 25):.2f}%)", (y + 1) / self.height * 0.25)

        # 2 Smooth the map
        for i in range(smoothing_iterations):
            update_progress(f"Shaping the underground paths ({i + 1}/{smoothing_iterations})", 0.3 + (i / smoothing_iterations) * 0.3)
            changed = self.smooth_map()
            if not changed:
                break

        # 3 Connect largest floor region
        if connect_regions:
            update_progress("Linking hidden passages", 0.5)
            self.connect_floor_regions()

        # 4 Add moss and water
        if add_moss:
            update_progress("Growing mossy textures", 0.7)
            self.add_moss_to_walls()
        if add_water:
            update_progress("Flooding subterranean pools", 0.8)
            self.add_water_pools(prob=0.02)

        # 5 Place items
        update_progress("Scattering treasures", 0.9)
        self.generate_items_on_map()

        # Finalize
        update_progress("Exploration begins soon", 1.0)
        return progress



    def smooth_map(self):
        """Smooth the map using cellular automata rules."""
        changed = False
        new_map = np.copy(self.map_data)

        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                wall_count = self.count_walls(x, y)
                old_tile = self.map_data[y, x]

                if wall_count > 4:
                    if old_tile.tile_type != TileType.WALL:
                        changed = True
                    new_map[y, x] = self.create_tile(CAVE_WALL, x, y)
                elif wall_count < 4:
                    if old_tile.tile_type != TileType.FLOOR:
                        changed = True
                    new_map[y, x] = self.create_tile(CAVE_FLOOR, x, y)
                else:
                    # Copy the current tile to retain its attributes
                    new_map[y, x] = copy.deepcopy(old_tile)

        self.map_data = new_map
        return changed

    def count_walls(self, x: int, y: int) -> int:
        cnt = 0
        for ny in range(y - 1, y + 2):
            for nx in range(x - 1, x + 2):
                if 0 <= ny < self.height and 0 <= nx < self.width:
                    if self.map_data[ny, nx].tile_type == TileType.WALL:
                        cnt += 1
        return cnt

    # ------------------------------------------------------------------------
    # Add items to map
    # ------------------------------------------------------------------------
    def generate_items_on_map(self):
        """
        Generate items on the map, with a density of 1 item per 500 tiles.
        """
        total_tiles = self.width * self.height
        items_to_generate = total_tiles // 500
        for _ in range(items_to_generate):
            x, y = self.find_walkable_tile()
            item = self.generate_item_by_rarity()
            if item:
                self.place_item_at(x, y, item)

    def random_select_rarity(self):
        """
        Randomly select a rarity or decide not to spawn an item.

        Returns:
            str: The selected rarity (e.g., 'common', 'uncommon', 'rare', 'legendary'), or 'none'.
        """
        total_probability = sum(RARITY_PROBABILITIES.values())
        random_value = random.uniform(0, total_probability)

        cumulative_probability = 0
        for rarity, probability in RARITY_PROBABILITIES.items():
            cumulative_probability += probability
            if random_value <= cumulative_probability:
                return rarity
        return "none"
    
    def generate_item_by_rarity(self):
        """
        Generate a random item based on rarity probabilities.

        Returns:
            Item: A randomly selected item instance, or None if no item is selected.
        """
        # Select a rarity or decide not to spawn an item
        rarity = self.random_select_rarity()
        if rarity == "none":
            return None  # No item is spawned

        # Filter items by the selected rarity
        items_of_rarity = [
            item_enum for item_enum in ItemList
            if ItemFactory.ITEM_DATA.get(item_enum.name, {}).get("rarity") == rarity
        ]

        if not items_of_rarity:
            return None  # No items available for the selected rarity

        # Randomly select an item from the filtered list
        selected_item_enum = random.choice(items_of_rarity)
        return ItemFactory.create_item_instance(selected_item_enum)



    # ------------------------------------------------------------------------
    # Connect Floor Regions
    # ------------------------------------------------------------------------
    def connect_floor_regions(self):
        """
        Identify and connect the largest floor region, turning all other isolated regions into walls.
        """
        visited = np.zeros((self.height, self.width), dtype=bool)
        regions = []

        # Flood-fill to find all floor regions
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y, x].tile_type == TileType.FLOOR and not visited[y, x]:
                    region = self.flood_fill(x, y, visited)
                    regions.append(region)

        if not regions:
            logger.warning("No floor regions found. Skipping connection step.")
            return

        # Find the largest region
        largest_region = max(regions, key=len)

        # Convert other regions to walls
        for region in regions:
            if region != largest_region:
                for (x, y) in region:
                    self.map_data[y, x] = self.create_tile(CAVE_WALL, x, y)

        for i, region in enumerate(regions):
            logger.debug(f"Region {i} size: {len(region)}")

    def flood_fill(self, x, y, visited):
        """Flood-fill (BFS/DFS) to find connected regions of floor tiles."""
        region = []
        stack = [(x, y)]
        visited[y, x] = True

        while stack:
            cx, cy = stack.pop()
            region.append((cx, cy))
            for nx, ny in self.get_neighbors(cx, cy):
                if self.map_data[ny, nx].tile_type == TileType.FLOOR and not visited[ny, nx]:
                    visited[ny, nx] = True
                    stack.append((nx, ny))
        return region

    def get_neighbors(self, x, y):
        """Get valid neighbors (up, down, left, right)."""
        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                neighbors.append((nx, ny))
        return neighbors

    # ------------------------------------------------------------------------
    # Add Moss to Walls (Clustered)
    # ------------------------------------------------------------------------
    # FIXME: Moss is not generated

    def add_moss_to_walls(self):
        """Add moss to random wall tiles, in clustered regions."""
        visited = np.zeros((self.height, self.width), dtype=bool)
        moss_probability = 0.05  # Probability of moss spreading from each starting point

        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y, x] == CAVE_WALL and not visited[y, x] and random.random() < moss_probability:
                    # Start a moss cluster from this wall tile
                    self.flood_fill_moss(x, y, visited)

    def flood_fill_moss(self, x, y, visited):
        """Flood-fill to create moss clusters on wall tiles."""
        cluster_size = random.randint(2, 12)  # Random cluster size
        stack = [(x, y)]
        visited[y, x] = True
        moss_count = 0

        while stack and moss_count < cluster_size:
            cx, cy = stack.pop()
            if self.map_data[cy, cx] == CAVE_WALL:
                self.map_data[cy, cx] = MOSSY_WALL  # Turn wall tile into mossy wall
                self.map_data[cy, cx].y = cy
                self.map_data[cy, cx].x = cx
                moss_count += 1

            for nx, ny in self.get_neighbors(cx, cy):
                if not visited[ny, nx] and self.map_data[ny, nx] == CAVE_WALL:
                    visited[ny, nx] = True
                    stack.append((nx, ny))

    # ------------------------------------------------------------------------
    # Add Water Pools (Infrequent and Larger Pools)
    # ------------------------------------------------------------------------
    # FIXME: Water pools not added

    def add_water_pools(self, prob=0.001):
        """Add infrequent, larger water pools to floor tiles."""
        visited = np.zeros((self.height, self.width), dtype=bool)

        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y, x] == CAVE_FLOOR and not visited[y, x] and random.random() < prob:
                    # Start a water pool here
                    self.flood_fill_water(x, y, visited)

    def flood_fill_water(self, x, y, visited):
            """Flood-fill to create rectangular water pools on floor tiles."""
            # Randomly choose the width and height of the water pool
            pool_width = random.randint(1, 3)  # Random width (adjustable)
            pool_height = random.randint(1, 3)  # Random height (adjustable)

            # Ensure the rectangle stays within bounds of the map
            min_x = max(x - pool_width // 2, 0)
            max_x = min(x + pool_width // 2, self.width - 1)
            min_y = max(y - pool_height // 2, 0)
            max_y = min(y + pool_height // 2, self.height - 1)

            # Mark the visited area and fill the rectangle with water
            for cy in range(min_y, max_y + 1):
                for cx in range(min_x, max_x + 1):
                    if self.map_data[cy, cx] == CAVE_FLOOR and not visited[cy, cx]:
                        self.map_data[cy, cx] = WATER  # Turn the floor tile into water
                        visited[cy, cx] = True  # Mark this tile as visited

    # ------------------------------------------------------------------------
    # Bresenham lines for line-of-sight
    # ------------------------------------------------------------------------
    def update_visibility_bresenham_soft(self, player):
        
        is_revealed =  getattr(self, "is_revealed")

        if is_revealed:
            self.visible_map.fill(True)
            return  # Exit early if the conditions are met
        
        # 1) Clear old visibility
        self.visible_map.fill(False)

        px, py = player.x, player.y

        if 0 <= px < self.width and 0 <= py < self.height:
            self.visible_map[py, px] = True
            self.explored_map[py, px] = True

        radius = player.view_radius

        # 2) For each tile in bounding circle
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                tx = px + dx
                ty = py + dy

                if dx * dx + dy * dy <= radius * radius:
                    if 0 <= tx < self.width and 0 <= ty < self.height:
                        visibility = 1.0
                        for (lx, ly) in self.bresenham_line(px, py, tx, ty):
                            if visibility <= 0:
                                break
                            # Mark tile visible
                            self.visible_map[ly, lx] = True
                            self.explored_map[ly, lx] = True

                            # If we've reached our target tile
                            if lx == tx and ly == ty:
                                break

                            # Multiply factor by the tile's transparency
                            tile = self.map_data[ly, lx]
                            visibility *= tile.transparency

                            # If fully opaque or factor too small
                            if tile.transparency <= 0.1 or visibility < 0.01:
                                break

    def bresenham_line(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        x, y = x0, y0
        while True:
            yield x, y
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    # ------------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------------
    def render(self, screen, camera: Camera):
        """
        Render all tiles and items within the camera's viewport.
        """
        camera_min_x = max(0, int(camera.offset_x // self.tile_size))
        camera_min_y = max(0, int(camera.offset_y // self.tile_size))
        tiles_across = camera.screen_width // self.tile_size + 1
        tiles_down = camera.screen_height // self.tile_size + 1
        camera_max_x = min(self.width, camera_min_x + tiles_across)
        camera_max_y = min(self.height, camera_min_y + tiles_down)

        for y in range(camera_min_y, camera_max_y):
            for x in range(camera_min_x, camera_max_x):
                tile = self.map_data[y][x]

                # Convert tile coords to screen coords
                screen_x, screen_y = camera.apply(x * self.tile_size, y * self.tile_size)
                rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)

                # Render tile
                if not self.explored_map[y][x]:
                    pygame.draw.rect(screen, (0, 0, 0), rect)  # Unexplored = black
                elif not self.visible_map[y][x]:
                    pygame.draw.rect(screen, tuple(int(c * 0.5) for c in tile.color), rect)  # Dimmed
                else:
                    pygame.draw.rect(screen, tile.color, rect)  # Bright color

                # Render items on visible tiles
                if len(tile.items) > 0 and self.visible_map[y][x]:
                    for item in tile.items:  # Render all items on the tile
                        if item.icon:
                            # Use precomputed offset or generate it if not already present
                            if not hasattr(item, "offset"):
                                item.offset = (
                                    random.randint(-self.tile_size // 8, self.tile_size // 8),
                                    random.randint(-self.tile_size // 8, self.tile_size // 8),
                                )

                            # Apply the precomputed offset
                            offset_x, offset_y = item.offset
                            final_x = screen_x + offset_x
                            final_y = screen_y + offset_y

                            # Render the item with the adjusted position
                            screen.blit(
                                pygame.transform.scale(item.icon, (self.item_size, self.item_size)),
                                (final_x, final_y)
                            )
                        else:
                            logger.warning(f"Item {item.name} does not have an icon.")


    # ------------------------------------------------------------
    # Utility Functions                                           
    # ------------------------------------------------------------

    def find_walkable_tile(self, attempts=1000):
        """Find a random walkable tile."""
        for _ in range(attempts):
            x = random.randint(1, self.width - 2)  # Avoid the border
            y = random.randint(1, self.height - 2)
            if not self.map_data[y, x].blocked:  # Check if the tile is walkable
                logger.debug(f"Found walkable tile at ({x}, {y})")
                return x, y
        logger.warning("Failed to find walkable tile after %d attempts.", attempts)
        return 1, 1  # Return a default tile if no walkable tile is found

    def get_tile_at_xy(self, x, y) -> Tile:
        """Get the tile at the given coordinates."""
        # Convert x and y to integers (casting them to avoid IndexError)
        x = int(x)
        y = int(y)

        
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.map_data[y, x]
        return None  # Return None if out of bounds

    def can_move(self, x: int, y: int) -> bool:
        """Check if the player can move to the given tile (i.e., tile is not blocked)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return not self.map_data[y, x].blocked  # Check if the tile is not a wall
        return False  # If out of bounds, return False
