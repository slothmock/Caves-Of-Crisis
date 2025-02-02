from core import logging
from core.entities.player import Player
from core.settings import TILE_SIZE
from core.status_effects.status_effects import StatSeverityDescriptions, StatusSeverity


class Developer(Player):
    """
    A specialized Player class for developers with additional debug functionality.
    """
    def __init__(self, x, y, char, color, game_time, message_log, tile_size=TILE_SIZE, is_invincible=True, unlimited_resources=True):
        super().__init__(x, y, char, color, game_time, message_log, tile_size)
        self.name = "Developer"
        self.is_dev = True
        self.view_radius = 20  # Maximum view radius
        self.movement_interval = self.get_movement_interval()
        self.is_invincible = is_invincible  # Developer mode: no damage
        self.unlimited_resources = unlimited_resources  # Unlimited food, water, stamina

        self.status_effects.add_or_update_effect(
            "Dev", StatusSeverity.PERMANENT, StatSeverityDescriptions.DEV
        )

    def update_stats(self):
        if self.is_invincible or self.unlimited_resources:
            return
        else:
            return super().update_stats()

    def update_status_effects(self):
        """Update status effects depending on invincibility"""
        if self.is_invincible or self.unlimited_resources:
            return
        else:
            return super().update_status_effects()
        
    def log_stat_changes_debug(self):
        return super().log_stat_changes_debug()


    # ------------------------------------------------------------------------
    # Developer Privileges
    # ------------------------------------------------------------------------

    def toggle_invincibility(self):
        """Toggle invincibility/godmode for testing purposes."""
        self.is_invincible = not self.is_invincible
        self.unlimited_resources = not self.unlimited_resources
        self.message_log.add_message(f"Godmode {'enabled' if self.is_invincible else 'disabled'}.")

    def fill_resources(self):
        """Refill all resources for testing."""
        self.recover_food(self.max_food)
        self.recover_water(self.max_water)
        self.recover_stamina(self.max_stamina)
        self.recover_sleep(self.max_sleep)

        self.message_log.add_message("[DevTools] All resources refilled to maximum.")

    def set_resource(self, resource: str, amount: str):
        """
        Set a specific resource value for the character.
        :param resource: The name of the resource to update (e.g., "food", "health").
        :param amount: The value to set for the resource.
        """
        int(amount)
        if hasattr(self, resource):  # Ensure the resource exists
            max_attr = f"max_{resource}"  # Determine the corresponding max attribute
            if hasattr(self, max_attr):  # Ensure the max attribute exists
                max_value = getattr(self, max_attr)
                
                setattr(self, resource, max(0, min(max_value, int(amount))))  # Clamp the value
            else:
                logging.logger.error(f"No maximum value defined for resource '{resource}'.")
        else:
            logging.logger.error(f"Resource '{resource}' does not exist.")

        
        self.message_log.add_message(f"[DevTools] {resource.capitalize()} set to {amount}.")

    def set_resource_max(self, resource: str, amount: str):
        """
        Set the maximum value of a specific resource for the character.
        :param resource: The name of the resource to update (e.g., "food", "health").
        :param amount: The new maximum value to set for the resource.
        """

        max_attr = f"max_{resource}"  # Determine the corresponding max attribute
        if hasattr(self, max_attr):  # Ensure the max attribute exists
            setattr(self, max_attr, max(0, int(amount)))  # Set the maximum value, ensuring it is non-negative
            if hasattr(self, resource):  # If the current resource value exists, clamp it to the new max
                current_value = getattr(self, resource)
                new_value = min(current_value, int(amount))
                setattr(self, resource, new_value)
                self.message_log.add_message(f"[DevTools] Maximum {resource.capitalize()} set to {int(amount)}.")
        else:
            raise ValueError(f"Resource '{resource}' or its maximum value does not exist.")

    def apply_effect_dev(self, effect, severity, duration):
        """Apply the desired effect to the player for the assigned duration"""
        self.status_effects.update_add_effect(name=effect, severity=StatusSeverity.__getitem__(severity), description="Added by DevTools", duration=duration)

    def clear_effects(self):
        """Clear all status effects and reset resources."""
        self.status_effects.effects.clear()
        self.fill_resources()

    def timefactor(self, seconds=5):
        """Set the amount of seconds for 1 in-game minutes"""

        self.game_time.time_scale = int(seconds)
        self.message_log.add_message(f"[DevTools] Time scaling set to {seconds} seconds / 1 in-game minutes.")

    def teleport(self, x, y):
        """Teleport the player to a specific location."""
        self.x = x
        self.y = y
        self.message_log.add_message(f"Teleported to ({x}, {y}).")

    def grant_item(self, item_name=None, quantity=1):
        """Grant an item directly to the inventory."""
        if item_name is None:
            return
        self.add_to_inventory(item_name, quantity)
        self.message_log.add_message(f"Granted {quantity} x {item_name}.")

    def reveal_map(self, game_map):
        """Reveal the entire map."""
        for y in range(game_map.height):
            for x in range(game_map.width):
                game_map.visible_map[y, x] = True
                game_map.explored_map[y, x] = True
        self.message_log.add_message("Revealed the entire map.")
        game_map.is_revealed = True

    # ------------------------------------------------------------------------
    # Overridden Methods
    # ------------------------------------------------------------------------

    def update(self):
        if not self.is_invincible:
            return super().update()

    def take_damage(self, amount):
        """Override damage logic to account for invincibility."""
        if not self.is_invincible:
            super().take_damage(amount)
        else:
            self.message_log.add_message("Invincibility active: No damage taken.")

    def expend_food(self, amount):
        """Prevent food from depleting if unlimited resources are enabled."""
        if not self.unlimited_resources:
            super().expend_food(amount)

    def expend_water(self, amount):
        """Prevent water from depleting if unlimited resources are enabled."""
        if not self.unlimited_resources:
            super().expend_water(amount)

    def expend_stamina(self, amount):
        """Prevent stamina from depleting if unlimited resources are enabled."""
        if not self.unlimited_resources:
            super().expend_stamina(amount)

    def get_movement_interval(self):
        """
        Get the movement interval based on the type of player and status.
        Returns 50 for DeveloperPlayer and 100 for standard Player.
        """
        if isinstance(self, Developer):
            return 50  # Faster movement for developers
        return 100  # Standard movement interval for players
    
