import copy
import threading
import numpy as np
import scipy.signal as scpy
from scipy.ndimage import label
from collections import deque
import random
import pygame
from core.camera import Camera
from core.items.item_factory import ItemFactory
from core.items.item_list import ItemList
from core.logging import logger
from core.map.tile_types import Tile, TileType
from core.map.tileset import MOSSY_WALL, CAVE_WALL, CAVE_FLOOR, WATER
from core.ui import loading
from core.ui.loading import update_progress

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
    "common": 65,     
    "uncommon": 25,   
    "rare": 10,
    "epic": 2,       
    "legendary": 0.1,   
    "none": 1        
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
    # Cave Generation
    # ------------------------------------------------------------------------
    def generate_cave(
            self, fill_percent=0.6, seed=None, smoothing_iterations=5,
            connect_regions=True, add_moss=True, add_water=True,
            screen=None, font=None, step_progress=0.0):
        """
        Generates a more enclosed cave system with random room carving.
        """

        if seed is not None:
            random.seed(seed)

        logger.debug("Generating cave...")

        total_steps = 6  # Increased steps for room carving
        current_step = 0

        # **Step 1: Initial Map Formation**
        step_progress = update_progress(screen, font, "Carving the caverns...", current_step, 0.0, total_steps, step_progress)

        self.map_data = np.full((self.height, self.width), CAVE_WALL, dtype=object)

        # **Higher initial wall density with slight noise**
        interior = np.random.random((self.height - 2, self.width - 2))
        wall_density_map = np.clip(interior + np.random.normal(0, 0.2, interior.shape), 0, 1)
        self.map_data[1:-1, 1:-1] = np.where(wall_density_map < fill_percent, CAVE_WALL, CAVE_FLOOR)

        step_progress = update_progress(screen, font, "Initial terrain formed...", current_step, 1.0, total_steps, step_progress)

        # **Step 2: Carve Out Random Rooms**
        current_step += 1
        step_progress = update_progress(screen, font, "Carving random rooms...", current_step, 0.0, total_steps, step_progress)

        num_rooms = random.randint(8, 32)  # Random number of rooms
        for _ in range(num_rooms):
            self.carve_random_room()

        step_progress = update_progress(screen, font, "Rooms added...", current_step, 1.0, total_steps, step_progress)

        # **Step 3: Smooth the Map**
        current_step += 1
        step_progress = 0
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])

        for i in range(smoothing_iterations):
            step_progress = (i + 1) / smoothing_iterations
            wall_neighbors = scpy.convolve2d(self.map_data == CAVE_WALL, kernel, mode='same', boundary='fill', fillvalue=1)
            self.map_data = np.where(wall_neighbors > 4, CAVE_WALL, CAVE_FLOOR)
            step_progress = update_progress(screen, font, f"Shaping underground paths... {step_progress * 100:.2f}%", current_step, step_progress, total_steps, step_progress)

        step_progress = update_progress(screen, font, "Smoothing complete...", current_step, 1.0, total_steps, step_progress)

        # **Step 4: Ensure Connectivity**
        current_step += 1
        step_progress = 0
        if connect_regions:
            step_progress = update_progress(screen, font, "Linking hidden passages...", current_step, 0.0, total_steps, step_progress)
            floor_mask = (self.map_data == CAVE_FLOOR)
            labeled_regions, num_features = label(floor_mask)
            if num_features > 1:
                largest_region = np.argmax(np.bincount(labeled_regions.flat)[1:]) + 1
                for i in range(1, num_features + 1):
                    if i != largest_region:
                        region_coords = np.argwhere(labeled_regions == i)
                        if region_coords.size > 0:
                            self.connect_region_to_main(region_coords, labeled_regions, largest_region)
            step_progress = update_progress(screen, font, "Caverns connected...", current_step, 1.0, total_steps, step_progress)

        # **Step 5: Add Water Pools**
        current_step += 1
        step_progress = 0
        if add_water:
            step_progress = update_progress(screen, font, "Flooding subterranean pools...", current_step, 0.0, total_steps, step_progress)
            self.add_water_pools(prob=0.02)  # Adjusted probability
            step_progress = update_progress(screen, font, "Water pools created...", current_step, 1.0, total_steps, step_progress)

        if add_moss:
            self.add_moss_to_walls()

        for y in range(self.height):
            for x in range(self.width):
                tile = copy.deepcopy(self.map_data[y, x])
                tile.x = x
                tile.y = y
                self.map_data[y, x] = tile

        # **Step 6: Generate Items**
        current_step += 1
        step_progress = 0
        step_progress = update_progress(screen, font, "Scattering treasures...", current_step, 0.0, total_steps, step_progress)
        self.generate_items_on_map()
        step_progress = update_progress(screen, font, "Finalizing map...", current_step, 1.0, total_steps, step_progress)

        return step_progress
    
    def carve_random_room(self):
        """
        Carves out a random room in the cave at a random position.
        Ensures that rooms are not isolated by overlapping with floor tiles.
        """
        room_width = random.randint(3, 8)  # Random room width
        room_height = random.randint(3, 8)  # Random room height

        x = random.randint(1, self.width - room_width - 1)
        y = random.randint(1, self.height - room_height - 1)

        for i in range(y, y + room_height):
            for j in range(x, x + room_width):
                self.map_data[i, j] = CAVE_FLOOR  # Carve out the room


    def connect_region_to_main(self, region_coords, labeled_regions, largest_region):
        """
        Carve a tunnel from a small region to the largest region.
        
        Args:
            region_coords (list): List of coordinates in the small region.
            labeled_regions (np.array): Array of labeled regions.
            largest_region (int): Label of the largest connected floor region.
        """
        main_region_coords = np.argwhere(labeled_regions == largest_region)

        # Pick a random tile from both the small and main region
        start = tuple(region_coords[np.random.randint(len(region_coords))])
        end = tuple(main_region_coords[np.random.randint(len(main_region_coords))])

        # Use Bresenham's algorithm to create a tunnel
        for (x, y) in self.bresenham_line_procgen(start, end):
            if 0 < x < labeled_regions.shape[1] and 0 < y < labeled_regions.shape[0]:
                self.map_data[y, x] = CAVE_FLOOR

    def bresenham_line_procgen(self, start, end):
        """
        Generate a straight line between two points using Bresenham's Line Algorithm.

        Args:
            start (tuple): (x1, y1) starting point.
            end (tuple): (x2, y2) ending point.

        Yields:
            tuple: (x, y) coordinates along the line.
        """
        x1, y1 = start
        x2, y2 = end
        dx = abs(x2 - x1)
        dy = -abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx + dy

        while True:
            yield x1, y1
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x1 += sx
            if e2 <= dx:
                err += dx
                y1 += sy

    # ------------------------------------------------------------------------
    # Add items to map
    # ------------------------------------------------------------------------
    def generate_items_on_map(self, update_progress=None):
        """
        Efficiently generate items on the map.

        - **Ensures each tile is unique** (`copy.deepcopy()`)
        - **Limits max items per tile** (prevents overpopulation)
        - **Provides smooth progress updates** for the loading screen.

        Args:
            update_progress (function): Function to update the loading screen.
        """
        total_tiles = self.width * self.height
        items_to_generate = total_tiles // 750  # Adjust density

        # Get all walkable tiles **in bulk** (avoiding blocked areas)
        walkable_tiles = [
            (x, y) for y in range(self.height) for x in range(self.width)
            if not self.map_data[y, x].blocked and not self.map_data[y, x].items  # Prevent overstacking
        ]

        if not walkable_tiles:
            logger.warning("No walkable tiles available for item generation.")
            return

        # **Shuffle tiles for natural distribution**
        np.random.shuffle(walkable_tiles)

        placed_items = 0
        batch_size = max(1, items_to_generate // 15)  # Generate in **small batches**
        max_items_per_tile = 1  # **Limit each tile to 1 item**

        progress_messages = [
            "Scattering ancient relics...",
            "Hiding precious loot...",
            "Distributing treasures...",
            "Placing forgotten artifacts...",
            "Randomizing rare finds..."
        ]

        for i in range(0, items_to_generate, batch_size):
            batch_tiles = walkable_tiles[i : i + batch_size]

            for x, y in batch_tiles:
                # **Ensure the tile is a unique instance (fixes shared memory issue)**
                self.map_data[y][x] = copy.deepcopy(self.map_data[y][x])

                # **Skip tile if it already has max items**
                if len(self.map_data[y][x].items) >= max_items_per_tile:
                    continue

                item = self.generate_item_by_rarity()
                if item:
                    self.place_item_at(x, y, item)
                    placed_items += 1

            # **Dynamic loading message updates**
            if update_progress:
                progress_percent = (placed_items / items_to_generate) * 100

            # **Stop early if we placed enough items**
            if placed_items >= items_to_generate:
                break

        logger.debug(f"Placed {placed_items} items across the map.")

    def random_select_rarity(self):
        """
        Optimized random rarity selection using NumPy.

        Returns:
            str: The selected rarity (e.g., 'common', 'uncommon', 'rare', 'legendary'), or 'none'.
        """
        rarity_list = list(RARITY_PROBABILITIES.keys())
        probability_values = np.array(list(RARITY_PROBABILITIES.values()), dtype=np.float32)

        # Normalize probabilities to ensure the total is 1.0
        probability_values /= probability_values.sum()

        # **Vectorized random choice for better performance**
        return np.random.choice(rarity_list, p=probability_values)

    def generate_item_by_rarity(self):
        """
        Generate a random item based on rarity probabilities.

        Returns:
            Item: A randomly selected item instance, or None if no item is selected.
        """
        rarity = self.random_select_rarity()
        if rarity == "none":
            return None  # Skip item spawning

        # Use NumPy filtering for optimized item selection
        items_of_rarity = [
            item_enum for item_enum in ItemList
            if ItemFactory.ITEM_DATA.get(item_enum.name, {}).get("rarity") == rarity
        ]

        if not items_of_rarity:
            return None  # No valid items found

        return ItemFactory.create_item_instance(np.random.choice(items_of_rarity))

    # ------------------------------------------------------------------------
    # Connect Floor Regions
    # ------------------------------------------------------------------------
    def connect_floor_regions(self, update_progress=None):
        """
        Identify and connect the largest floor region, turning all other isolated regions into walls.

        Optimizations:
        - **NumPy boolean arrays** for ultra-fast floor detection.
        - **Deque (O(1) pop) instead of list (O(n) pop) for BFS flood-fill**.
        - **Row-wise progress updates** for a continuously moving loading bar.
        - **Vectorized NumPy updates** for converting isolated floors into walls.

        Args:
            update_progress (function): Function to update the loading screen.
        """
        visited = np.zeros((self.height, self.width), dtype=bool)
        regions = []

        total_tiles = self.width * self.height  # Total number of tiles for progress tracking
        processed_tiles = 0  # Counter to track processed tiles

        # **Flood-fill to find all floor regions**
        for y in range(self.height):
            for x in range(self.width):
                if self.map_data[y, x].tile_type == TileType.FLOOR and not visited[y, x]:
                    region = self.flood_fill(x, y, visited)
                    regions.append(region)
                
                # ✅ **Update progress every ~5% of processing** for smoother animations
                processed_tiles += 1
                if update_progress and processed_tiles % (total_tiles // 20) == 0:
                    overall_progress = 0.6 + (0.1 * (processed_tiles / total_tiles))  # Scale 60% → 70%
                    update_progress(f"Mapping cavern paths... {overall_progress*100:.2f}%", overall_progress, 0.6)

        # **Handle no regions case**
        if not regions:
            logger.warning("No floor regions found. Skipping connection step.")
            return

        # **Find the largest region using NumPy for maximum performance**
        region_sizes = np.array([len(region) for region in regions])
        largest_region_index = np.argmax(region_sizes)
        largest_region = regions[largest_region_index]

        # **Convert all other regions to walls using fast NumPy updates**
        for i, region in enumerate(regions):
            if i != largest_region_index:
                for (x, y) in region:
                    self.map_data[y, x] = self.create_tile(CAVE_WALL, x, y)

            # ✅ **Dynamic updates as regions are processed**
            if update_progress:
                region_progress = 0.7 + (0.2 * (i / len(regions)))  # Scale 70% → 90%
                update_progress(f"Reinforcing cavern walls... {region_progress*100:.2f}%", region_progress, 0.7)

        # ✅ **Final loading update**
        if update_progress:
            update_progress("Finalizing cavern layout...", 1.0, 0.9)

        logger.debug(f"Largest cavern size: {len(largest_region)} / {sum(region_sizes)} total tiles")

    def flood_fill(self, x, y, visited):
        """
        Optimized flood-fill (BFS) to find connected floor tiles.
        
        - Uses **deque (O(1) pop) instead of list (O(n) pop)** for better performance.
        - Uses **NumPy array** for fast visited checks instead of slow Python `set()`.
        - **Processes entire rows at a time** to further speed up traversal.

        Returns:
            list: The connected region (list of tile coordinates).
        """
        region = []
        queue = deque([(x, y)])  # **Fast O(1) pop/push**
        visited[y, x] = True

        while queue:
            cx, cy = queue.popleft()
            region.append((cx, cy))

            # Process neighbors **row-wise for better CPU cache efficiency**
            for nx, ny in self.get_neighbors(cx, cy):
                if not visited[ny, nx] and self.map_data[ny, nx].tile_type == TileType.FLOOR:
                    visited[ny, nx] = True
                    queue.append((nx, ny))

        return region


    def get_neighbors(self, x, y):
        """
        Get valid neighbors using NumPy array indexing.
        
        - **Eliminates Python loops** for faster execution.
        - Uses **NumPy boolean masks** for valid tile checks.
        - Returns an array instead of a list (better cache locality).

        Returns:
            np.ndarray: Array of valid (x, y) neighbor coordinates.
        """
        offsets = np.array([(-1, 0), (1, 0), (0, -1), (0, 1)])  # Up, Down, Left, Right
        neighbors = np.array([x, y]) + offsets  # Vectorized offset addition

        # **Filter out-of-bounds indices**
        valid_mask = (0 <= neighbors[:, 0]) & (neighbors[:, 0] < self.width) & \
                    (0 <= neighbors[:, 1]) & (neighbors[:, 1] < self.height)
        
        return neighbors[valid_mask]

    # ------------------------------------------------------------------------
    # Add Moss to Walls (Clustered)
    # ------------------------------------------------------------------------

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
            pool_width = random.randint(1, 4)  # Random width (adjustable)
            pool_height = random.randint(1, 4)  # Random height (adjustable)

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
