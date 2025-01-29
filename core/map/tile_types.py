from enum import Enum


class TileType(Enum):
    WALL = "Wall"
    FLOOR = "Floor"
    WATER = "Water"

class Tile:
    def __init__(self, x=None, y=None, color=(255, 255, 255), blocked=False, transparency=0.0, opacity=0.0, name=None, description=None, tile_type=None):
        self.x = x  # Store the x coordinate
        self.y = y  # Store the y coordinate
        self.color = color
        self.name = name
        self.description = description
        self.tile_type = tile_type

        self.blocked = blocked           # Movement
        self.transparency = transparency
        self.opacity = opacity
        self.visible = False
        self.explored = False
        self.light_level = 0.0

        self.items = []  # Items placed on the tile

    def __str__(self):
        return f"{self.name}: {self.description} at ({self.x}, {self.y})"

    def interact(self, item=None):
        """ Default interaction. Can be overridden by subclasses. """
        if item:
            return f"You use {item.name} on the {self.name}."
        return f"You interact with the {self.name}."

    def examine(self):
        """ Default examination. Can be overridden by subclasses. """
        return f"You examine the {self.name}."

    def get_position(self):
        """ Return the (x, y) position of the tile. """
        return self.x, self.y

    def add_item(self, item):
        """Add an item to the tile."""
        self.items.append(item)

    def remove_item(self, item):
        """Remove an item from the tile."""
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def list_items(self):
        """Return a list of items on the tile."""
        if not self.items:
            return "The tile is empty."
        return [item.name for item in self.items]

    

class WaterTile(Tile):
    """
    Represents a water tile on the map with additional properties like:
      - depth: The depth of the water (affects movement/stamina).
      - flow_speed: The speed of water movement.
      - wetness_effect: Effect on entities moving through it.
    """

    def __init__(
        self,
        x=None,
        y=None,
        color=(30, 60, 100),  # Default blue color for water
        depth=1.0,
        flow_speed=0.0,
        name="Water",
        description="A body of water. It looks calm and reflective.",
        blocked=False,
        transparency=0.8,
        opacity=0.2,
        tile_type=TileType.WATER,
    ):
        super().__init__(
            x=x,
            y=y,
            color=color,
            blocked=blocked,
            transparency=transparency,
            opacity=opacity,
            name=name,
            description=description,
            tile_type=tile_type,
        )
        self.depth = depth  # How deep the water is (affects movement penalties)
        self.flow_speed = flow_speed  # Speed of water flow (e.g., currents)
        self.wetness_effect = 0.1 * depth  # Wetness multiplier based on depth

    def interact(self, entity, item=None):
        """
        Interaction with the water tile. Overrides the base class method.
        :param item: Item being used to interact with the tile.
        """
        if item is None and entity.water < entity.max_water:
            entity.recover_water(2)
            entity.message_log.add_message(f"The {entity.name} drinks from the water.")

        if item and item.name == "Bucket":
            return "You scoop some water with the bucket."
        return f"You interact with the {self.name}. The water ripples gently."
    
    def interact(self, entity, item=None):
        """
        Interaction with the water tile. Overrides the base class method.
        :param entity: The entity interacting with the tile.
        :param item: The item being used to interact with the tile.
        """
        if item and item.name == "Bucket":
            return "You scoop some water with the bucket."

        if not item and entity.water < entity.max_water:
            entity.recover_water(2)
            return f"The {entity.name} drinks from the water."

        return f"You interact with the {self.name}. The water ripples gently."

    def add_item(self, item):
        """Add an item to the water."""
        super().add_item(item)
        return f"The {item.name} sinks into the water."

    def examine(self):
        """
        Examine the water tile. Overrides the base class method.
        """
        depth_desc = (
            "shallow" if self.depth <= 1.0 else
            "moderately deep" if self.depth <= 2.5 else
            "very deep"
        )
        flow_desc = (
            "still" if self.flow_speed == 0.0 else
            "slow-moving" if self.flow_speed <= 0.5 else
            "rapid"
        )
        return f"The {self.name} is {depth_desc} and {flow_desc}."

    def affect_entity(self, entity):
        """
        Apply water effects on an entity moving through the tile.
        :param entity: The entity affected by the water (e.g., player, NPC).
        """
        entity.is_wet = True
        if not entity.can_swim:
            entity.stamina -= 5  # Penalty for moving through water without swimming ability
        return "The water slows you down and soaks you."

    def update(self, delta_time: float):
        """
        Update the water tile (e.g., for flow or dynamic effects).
        :param delta_time: Time since the last update.
        """
        # Example: Adjust light level dynamically based on flow
        self.light_level = max(0.0, self.light_level - (self.flow_speed * delta_time))

    def get_position(self):
        return super().get_position()
