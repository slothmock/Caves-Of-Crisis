import random

from core.entities.components.entity_base import Entity
from core.settings import TILE_SIZE

class BaseCharacter(Entity):
    """
    Base class for all characters, including the player and enemies.
    Inherits positional and rendering properties from Entity.
    """

    def __init__(
        self,
        x: int,
        y: int,
        symbol: str,
        color: tuple,
        name: str = "BaseChar",
        tile_size: int = TILE_SIZE,
        health: int = 100,
        food: int = 100,
        water: int = 100,
        stamina: int = 100,
        sleep: int = 100,
        view_radius: int = 5,
        level: int = 1,
        experience: int = 0,
        next_level_experience: int = 100,
        
    ):
        """
        Initialize the base character with stats, leveling, and world position.
        """
        super().__init__(x, y, symbol, color, tile_size)
        
        # Character name and stats
        self.name = name
        self.health = health
        self.max_health = health
        self.food = food
        self.max_food = food
        self.water = water
        self.max_water = water
        self.stamina = stamina
        self.max_stamina = stamina
        self.sleep = sleep
        self.max_sleep = sleep
        self.wetness_level = 0
        self.is_resting = False

        # Leveling and experience
        self.view_radius = view_radius
        self.level = level
        self.experience = experience
        self.next_level_experience = next_level_experience

        # Status effects
        self.status_effects = []  # List of active status effects (e.g., "Poisoned")


    def update_stats(self):
        """Update stats based on the current conditions and interactions."""

        if self.sleep <= 0:
            ...
            # TODO: Add feature
            # self.pass_out()

        # Decrease health if food or water is low
        if self.food <= 0 or self.water <= 0:
            self.take_damage(0.5)  # Taking health damage due to hunger or water
        
        # Decrease food/water at an increased rate if sleep is insufficient
        if self.sleep < 50:
            self.expend_food(max(0, 0.0175))  # Faster depletion of food
            self.expend_water(max(0, 0.02)) # Faster depletion of water
            if self.stamina <= 5:
                self.expend_sleep(1)  # Exhaustion
        
        # Decrease food, water and sleep over time (simulate daily consumption)
        if self.food > 0:
            self.expend_food(0.125)  # Slow depletion of food
        if self.water > 0:
            self.expend_water(0.175) # Faster depletion of water
        if self.sleep > 0:
            self.expend_sleep(0.1) # sleep depletion = 24hrs
        
        # Recover health based on food and water levels
        if self.food > 50 and self.water > 75:
            self.recover_health(1)  # Recover health if food is above 50
        if self.water > 50:
            self.recover_health(0.5)  # Recover health if water is above 50

    def take_damage(self, amount):
        """Reduce health by a certain amount."""
        self.health = max(0, self.health - amount)
        if self.health <= 0:
            self.die()

    def recover_health(self, amount):
        """Recover health up to the maximum health."""
        self.health = min(self.max_health, self.health + amount)

    def expend_stamina(self, amount):
        """Expend stamina for actions (e.g., attacking or moving)."""
        self.stamina = max(0, self.stamina - amount)

    def recover_stamina(self, amount):
        """Recover stamina after resting or eating/drinking."""
        self.stamina = min(self.max_stamina, self.stamina + amount)

    def expend_sleep(self, amount):
        """Expend sleep for action or lack of rest."""
        self.sleep = max(0, self.sleep - amount)

    def recover_sleep(self, amount):
        """Recover sleep after resting."""
        self.sleep = min(self.max_sleep, self.sleep + amount)

    def expend_food(self, amount):
        """Expend food for actions (e.g., walking, fighting, etc.) or lack of nourishment."""
        self.food = max(0, self.food - amount)

    def recover_food(self, amount):
        """Recover food after eating."""
        self.food = min(self.max_food, self.food + amount)

    def expend_water(self, amount):
        """Expend water for actions (e.g., movement, combat, etc.) or dehydration."""
        self.water = max(0, self.water - amount)

    def recover_water(self, amount):
        """Recover water after drinking."""
        self.water = min(self.max_water, self.water + amount)

    def die(self):
        print("Player died")

    def gain_experience(self, amount):
        """Increase experience and level up if necessary."""
        self.experience += amount
        if self.experience >= self.next_level_experience:
            self.level_up()

    def level_up(self):
        """Level up the character and increase stats."""
        self.level += 1
        self.experience -= self.next_level_experience
        self.next_level_experience += 50
        self.max_health += 10
        self.health = self.max_health
        self.max_stamina += 5
        self.stamina = self.max_stamina
        self.max_food += 5
        self.food = self.max_food
        self.max_water += 5
        self.water = self.max_water
        self.max_sleep += 5
        self.sleep = self.max_sleep
        self.view_radius += 2
        self.status_effects.append("Level Up!")
