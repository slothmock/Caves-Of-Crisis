import pygame


class Item:
    def __init__(self, name, icon_path, description, stackable=True, max_stack=99, effects=None, rarity="common"):
        """
        Initialize an item.

        Args:
            name (str): Name of the item.
            icon_path (str): Path to the item's icon image.
            description (str): Description of the item.
            stackable (bool): Whether the item can stack in the inventory.
            max_stack (int): Maximum number of items in a stack.
            effects (dict, optional): Effects the item applies when used.
            rarity (str): The rarity of the item.
        """
        self.name = name
        self.icon_path = icon_path
        self.icon = self.load_icon(icon_path)
        self.description = description
        self.stackable = stackable
        self.max_stack = max_stack
        self.effects = effects or {}
        self.rarity = rarity

    def load_icon(self, icon_path):
        """
        Load the item's icon, or return a placeholder if the icon is missing.

        Args:
            icon_path (str): Path to the item's icon image.

        Returns:
            pygame.Surface: The loaded image or a placeholder surface.
        """
        try:
            return pygame.image.load(icon_path).convert_alpha()
        except FileNotFoundError:
            # Return a placeholder surface if the icon is missing
            placeholder = pygame.Surface((32, 32))
            placeholder.fill((200, 200, 200))  # Gray placeholder
            return placeholder

    def use(self, player):
        """
        Apply the item's effects to the player, ensuring stats remain within valid bounds.

        Args:
            player: The player object to apply effects to.

        Returns:
            str: A message describing the result of using the item.
        """
        if not self.effects:
            return f"{self.name} has no effect."

        messages = []
        for effect, value in self.effects.items():
            if hasattr(player, effect):
                # Retrieve current value and max/min bounds
                current_value = getattr(player, effect)
                max_value = getattr(player, f"max_{effect}", None)
                min_value = 0  # Assuming minimum is always 0

                # Apply the effect and clamp the value within bounds
                new_value = current_value + value
                if max_value is not None:
                    new_value = min(max_value, new_value)
                new_value = max(min_value, new_value)

                # Update the player's stat
                setattr(player, effect, new_value)
                messages.append(f"{effect.capitalize()} +{value}")
            else:
                messages.append(f"Effect '{effect}' could not be applied.")

        return f"You used the {self.name}. {' '.join(messages)}"

