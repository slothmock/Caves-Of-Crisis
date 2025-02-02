import pygame
from core.entities.components.base_character import BaseCharacter

from core.entities.components.inventory import Inventory
from core.items.item import Item
from core.map.map import Map

from core.map.tile_types import TileType
from core.settings import PLAYER_MOVE_INTERVAL, TILE_SIZE
from core.logging import logger
from core.status_effects.status_effects import StatSeverityDescriptions, StatusEffects, StatusSeverity


class Player(BaseCharacter):
    def __init__(self, x, y, char, color, game_time, message_log, tile_size=TILE_SIZE):
        super().__init__(x, y, char, color, message_log, tile_size)
        self.name = "Player"
        self.inventory = Inventory(max_weight=20)
        self.view_radius = 2
        self.game_time = game_time
        self.message_log = message_log
        self.status_effects = StatusEffects(message_log, game_time)
        self.is_wet = False


    def update(self):
        """Update player stats and perform actions."""

        self.update_stats()  # Check food, water, stamina, etc.
        self.update_status_effects()

    def update_stats(self):
        """
        Update the player's stats based on in-game time and current conditions.

        Args:
            in_game_time (InGameTime): The in-game time system.
        """
        # Get the elapsed in-game time since the last update in minutes
        current_time_minutes = self.game_time.get_time_in_minutes()
        if not hasattr(self, "last_update_time"):
            self.last_update_time = current_time_minutes

        elapsed_minutes = current_time_minutes - self.last_update_time
        if elapsed_minutes <= 0:
            return  # No time has passed, no updates needed

        self.last_update_time = current_time_minutes  # Update the last tracked time

        # Base depletion rates (adjusted per minute elapsed)
        food_depletion_rate = 0.125  # Food depletes slowly
        water_depletion_rate = 0.175  # Water depletes faster
        sleep_depletion_rate = 0.1  # Sleep depletes over a 24-hour cycle

        # Adjust depletion based on conditions
        sleep_deprivation_factor = 1.5 if self.sleep < 50 else 1.0

        # Deplete stats over elapsed in-game minutes
        self.expend_food(elapsed_minutes * food_depletion_rate * sleep_deprivation_factor)
        self.expend_water(elapsed_minutes * water_depletion_rate * sleep_deprivation_factor)
        self.expend_sleep(elapsed_minutes * sleep_depletion_rate)

        # Handle critical conditions
        if self.food <= 0 or self.water <= 0:
            damage = elapsed_minutes * 0.5  # Damage per minute of starvation or dehydration
            self.take_damage(damage)
            self.message_log.add_message("You are taking damage due to hunger or dehydration!")

        # Handle exhaustion
        if self.sleep <= 0:
            self.message_log.add_message("You are completely exhausted!")
            self.pass_out()

        # Health recovery based on food and water levels
        if self.food > 50 and self.water > 75:
            self.recover_health(elapsed_minutes * 1.0)  # Higher recovery rate
        elif self.water > 50:
            self.recover_health(elapsed_minutes * 0.5)  # Moderate recovery rate

    def pass_out(self):
        """Handle the player passing out due to exhaustion."""
        self.message_log.add_message("You passed out from exhaustion!")
        self.recover_sleep(30)  # Recover some sleep

    def log_stat_changes_debug(self):
        """
        Log the current state of the player's stats for debugging.
        """
        logger.debug(
            f"Stats -> Food: {self.food:.2f}, Water: {self.water:.2f}, Sleep: {self.sleep:.2f}, "
            f"Stamina: {self.stamina:.2f}, Health: {self.health:.2f}"
        )

    def render(self, screen: pygame.Surface, screen_x: int, screen_y: int, debug: bool = False) -> None:
        """
        Render the player or entity on the screen.
        :param screen: The Pygame surface to draw on.
        :param screen_x: The x-coordinate on the screen to draw the entity.
        :param screen_y: The y-coordinate on the screen to draw the entity.
        :param debug: Whether to show debug information (e.g., grid position).
        """
        # Render the main entity
        pygame.draw.rect(
            screen,
            self.color,
            pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size),
        )

        # Optional: Render debug information
        if debug:
            font = pygame.font.Font(None, 24)
            debug_text = f"({self.x}, {self.y})"
            text_surface = font.render(debug_text, True, (255, 255, 255))  # White text
            screen.blit(text_surface, (screen_x - 10, screen_y - 20))  # Render above the entity


    # ------------------------------------------------------------------------
    # Movement Logic
    # ------------------------------------------------------------------------
    def handle_movement_input(self, keys, now, game_map, other_entities):
        """Handle player movement with collision detection."""

        dx, dy = self.get_direction_from_keys(keys)
        if dx != 0 or dy != 0:
            new_x, new_y = self.x + dx, self.y + dy
            self.attempt_move(new_x, new_y, game_map, other_entities)

    def get_direction_from_keys(self, keys):
        dx = (keys[pygame.K_d] - keys[pygame.K_a])
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) 
        return dx, dy

    def attempt_move(self, x: int, y: int, game_map, other_entities: list) -> None:
        """
        Attempt to move the player to the specified coordinates.
        :param x: Target x-coordinate.
        :param y: Target y-coordinate.
        :param game_map: Reference to the game map.
        :param other_entities: List of other entities for collision checks.
        """
        tile = game_map.get_tile_at_xy(x, y)

        if not tile.blocked:
            # Move the player
            self.x, self.y = x, y

            if tile.tile_type == TileType.WATER:
                self.get_wet()

            # Handle collisions with other entities
            self.handle_entity_collisions(other_entities)

            return True

        else:
            # Handle collisions with blocked tiles
            self.handle_tile_collisions(tile)

        # Recalculate the field of view
        self.compute_fov(game_map)

        return False

    def handle_entity_collisions(self, other_entities):
        """Check for and handle collisions with other entities."""
        collided_entity = self.check_collision(other_entities)
        if collided_entity:
            logger.debug(f"{self.name} collided with {collided_entity.name}!")
            self.revert_movement()

    def handle_tile_collisions(self, other):
        if isinstance(other, BaseCharacter):
            logger.debug(f"Player collided with a {other.name}!")
        else:
            # Check if it's a tile
            if getattr(other, "tile_type", None) == TileType.WALL:
                logger.debug("Player collided with a wall!")
            
    def get_wet(self):
        """
        Apply the 'Wet' effect when moving through water.
        """
        self.is_wet = True
        self.status_effects.add_or_update_effect(
            "Wet",
            StatusSeverity.CRITICAL,
            StatSeverityDescriptions.WET,
            30,
        )
        self.message_log.add_message(f"[Effect] You are {StatSeverityDescriptions.WET.get_feeling(StatusSeverity.CRITICAL)}", color=StatusSeverity.CRITICAL.color)

    def compute_fov(self, game_map: Map) -> None:
        """
        Compute the player's field of view after movement.
        Update the visibility and exploration state of the map.
        """
        game_map.update_visibility_bresenham_soft(self)

    def revert_movement(self, dx: int, dy: int) -> None:
        """Revert player movement in case of a collision."""
        self.x -= dx
        self.y -= dy

    # ------------------------------------------------------
    # Inventory Management + Items
    # ------------------------------------------------------

    def add_to_inventory(self, items: list[Item]):
        """
        Add a list of items to the player's inventory.

        Args:
            items (list[Item]): A list of `Item` instances to add to the inventory.

        Returns:
            list[Item]: A list of items that could not be added due to inventory being full.
        """
        not_added = []  # Track items that couldn't be added

        for item in items:
            if not self.inventory.add_item(item, quantity=1):
                not_added.append(item)

        return not_added


    def remove_from_inventory(self, item_name, quantity=1):
        """
        Remove an item from the player's inventory.

        Args:
            item_name (str): Name of the item to remove.
            quantity (int): Quantity of the item to remove.

        Returns:
            str: Success message or an error message if removal is not possible.
        """
        result = self.inventory.remove_item(item_name, quantity)
        if result:
            return f"Removed {quantity}x {item_name} from inventory."
        return f"Not enough {item_name} in inventory to remove, or item not found."


    def pick_up_items_from_tile(self, tile):
        """
        Pick up all items from the given tile.

        Args:
            tile (Tile): The tile from which to pick up items.
        """
        # Ensure the player is on the correct tile
        if self.x != tile.x or self.y != tile.y:
            self.message_log.add_message("You aren't standing on that tile.")
            return

        if not tile.items:
            self.message_log.add_message("There's nothing here to pick up.")
            return

        for item in tile.items[:]:  # Iterate over a copy of the item list
            remaining_quantity = self.inventory.add_item(item, quantity=1)

            if remaining_quantity == 0:  # Successfully added the item
                tile.items.remove(item)
                self.message_log.add_message(f"Picked up {item.name}.")
            else:  # Inventory is full or cannot add the item
                self.message_log.add_message(f"No room for {item.name}.")




    def use_item(self, item_name):
        """
        Use an item from the inventory on the given tile.

        Args:
            item_name (str): Name of the item to use.
            tile (Tile): The tile to interact with.
        """
        stacks = self.inventory.find_item(item_name)
        if not stacks:
            self.message_log.add_message(f"{item_name} is not in your inventory.")
            return

        # Use the first available stack
        item, quantity = stacks[0]

        # Apply the item's effects to the player
        if item.effects:
            for effect, value in item.effects.items():
                if hasattr(self, effect):
                    setattr(self, effect, getattr(self, effect) + value)
                    self.message_log.add_message(f"{effect.capitalize()} +{value}")
                else:
                    self.message_log.add_message(f"Cannot apply effect '{effect}'.")

        # Remove one instance of the item from the inventory
        self.inventory.remove_item(item_name, quantity=1)


    def drop_item(self, item_name, tile):
        """
        Drop an item from the inventory onto a tile.

        Args:
            item_name (str): Name of the item to drop.
            tile (Tile): The tile to drop the item onto.
        """
        stacks = self.inventory.find_item(item_name)
        if stacks:
            item, quantity = stacks[0]  # Use the first available stack
            tile.add_item(item)
            self.inventory.remove_item(item_name, quantity=1)
            self.message_log.add_message(f"Dropped {item_name} on the tile.")
        else:
            self.message_log.add_message(f"{item_name} is not in your inventory.")


    # ------------------------------------------------------------------------
    # Status Effects
    # ------------------------------------------------------------------------

    def update_status_effects(self):
        """
        Update the player's status effects based on current stat values and debuffs.
        """
        # Define stats and their severity rules
        stats = [
            ("Hunger", StatSeverityDescriptions.FOOD, self.food, self.max_food, self.determine_basestat_severity),
            ("Thirst", StatSeverityDescriptions.THIRST, self.water, self.max_water, self.determine_basestat_severity),
            ("Stamina", StatSeverityDescriptions.STAMINA, self.stamina, self.max_stamina, self.determine_basestat_severity),
            ("Sleep", StatSeverityDescriptions.SLEEP, self.sleep, self.max_sleep, self.determine_basestat_severity),
        ]
        effects = [
            ("Wet", StatSeverityDescriptions.WET, self.is_wet, 30, self.determine_debuff_severity),
        ]

        # Update stats
        for name, stat_feeling, value, max_value, severity_func in stats:
            severity = severity_func(value, max_value)

            # Update or add the effect
            self.status_effects.add_or_update_effect(
                name=name,
                severity=severity,
                stat_feeling=stat_feeling,
            )

        # Update debuffs
        for name, stat_feeling, is_active, duration, severity_func in effects:
            # Get time remaining for active debuff
            time_remaining = self.status_effects.get_time_remaining(name)

            # Only update active debuffs
            if is_active:
                severity = severity_func(time_remaining, duration) if time_remaining else StatusSeverity.NONE

                self.status_effects.add_or_update_effect(
                    name=name,
                    severity=severity,
                    stat_feeling=stat_feeling,
                    duration=time_remaining,
                )

        # Remove expired effects
        self.status_effects.remove_expired_effects()

    def determine_basestat_severity(self, level: int, max_level: int) -> StatusSeverity:
        """
        Determine the severity of a base stat based on its value percentage.
        """
        percentage = (level / max_level) * 100
        if percentage <= 5:
            return StatusSeverity.CRITICAL
        elif percentage <= 25:
            return StatusSeverity.SEVERE
        elif percentage <= 50:
            return StatusSeverity.MODERATE
        elif percentage <= 85:
            return StatusSeverity.MINOR
        else:
            return StatusSeverity.NONE

    def determine_debuff_severity(self, time_remaining: int, duration: int) -> StatusSeverity:
        """
        Determine the severity of a debuff based on its time remaing.
        """
        if time_remaining is None:
            return StatusSeverity.NONE

        percentage = (time_remaining / duration) * 100

        if percentage >= 75:
            return StatusSeverity.CRITICAL
        elif percentage >= 50:
            return StatusSeverity.SEVERE
        elif percentage >= 25:
            return StatusSeverity.MODERATE
        elif percentage >= 0:
            return StatusSeverity.MINOR
        else:
            return StatusSeverity.NONE

