class Camera:
    def __init__(self, screen_width: int, screen_height: int, tile_size: int, buffer: int = 5, smoothing: float = 0.1):
        """
        Initialize the camera.
        :param screen_width: Width of the screen in pixels.
        :param screen_height: Height of the screen in pixels.
        :param tile_size: Size of each tile in pixels.
        :param buffer: Buffer zone in tiles around the player.
        :param smoothing: Smoothing factor for camera movement.
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.tile_size = tile_size

        # Viewport dimensions in tiles
        self.width = screen_width // tile_size
        self.height = screen_height // tile_size

        # Camera position offsets (in pixels)
        self.offset_x = 0
        self.offset_y = 0
        self.smoothing = smoothing

        # Buffer zone (tiles from the center)
        self.buffer = buffer

    def update(self, player, map_width: int, map_height: int, message_log_height: int, right_margin: int):
        # Center of the camera in screen coordinates
        center_x = self.offset_x + self.screen_width // 2
        center_y = self.offset_y + self.screen_height // 2

        # Player position in pixel coordinates
        player_screen_x = player.x * self.tile_size
        player_screen_y = player.y * self.tile_size

        # Calculate buffer boundaries
        buffer_min_x = center_x - self.buffer * self.tile_size
        buffer_max_x = center_x + self.buffer * self.tile_size
        buffer_min_y = center_y - self.buffer * self.tile_size
        buffer_max_y = center_y + self.buffer * self.tile_size

        # Determine the target camera position
        target_x = self.offset_x
        target_y = self.offset_y

        if player_screen_x < buffer_min_x:
            target_x -= (buffer_min_x - player_screen_x)
        elif player_screen_x > buffer_max_x:
            target_x += (player_screen_x - buffer_max_x)

        if player_screen_y < buffer_min_y:
            target_y -= (buffer_min_y - player_screen_y)
        elif player_screen_y > buffer_max_y:
            target_y += (player_screen_y - buffer_max_y)

        # Clamp the target position to map boundaries,
        # reserving message_log_height at the bottom of the screen
        # and right_margin for character ui
        target_x = max(
            0, 
            min(target_x, (map_width * self.tile_size) - self.screen_width - right_margin)
        )
        target_y = max(
            0, 
            min(
                target_y, 
                (map_height * self.tile_size) - (self.screen_height - message_log_height)
            )
        )

        # Smoothly interpolate the camera position
        self.offset_x += (target_x - self.offset_x) * self.smoothing
        self.offset_y += (target_y - self.offset_y) * self.smoothing


    def screen_to_grid(self, screen_x: int, screen_y: int) -> tuple:
        """
        Convert screen coordinates to map grid coordinates.
        :param screen_x: X-coordinate in screen space (e.g., mouse position).
        :param screen_y: Y-coordinate in screen space (e.g., mouse position).
        :return: A tuple of grid coordinates (tile_x, tile_y).
        """
        # Convert screen coordinates to world coordinates
        world_x = screen_x + int(self.offset_x)
        world_y = screen_y + int(self.offset_y)

        # Convert world coordinates to grid indices
        tile_x = world_x // self.tile_size
        tile_y = world_y // self.tile_size

        return tile_x, tile_y

    def apply(self, x: int, y: int) -> tuple:
        """
        Convert world coordinates to screen coordinates.
        :param x: X-coordinate in world space.
        :param y: Y-coordinate in world space.
        :return: A tuple of screen coordinates (x, y).
        """
        return x - int(self.offset_x), y - int(self.offset_y)

    def in_view(self, x: int, y: int) -> bool:
        """
        Check if a given world coordinate is within the camera's viewport.
        :param x: X-coordinate in world space.
        :param y: Y-coordinate in world space.
        :return: True if the position is visible within the viewport, False otherwise.
        """
        screen_x, screen_y = self.apply(x * self.tile_size, y * self.tile_size)
        return (
            0 <= screen_x < self.screen_width and
            0 <= screen_y < self.screen_height
        )
