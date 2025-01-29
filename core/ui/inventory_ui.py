import pygame
from core import logging


class InventoryUI:
    def __init__(self, screen_width, screen_height, font: pygame.font.Font, bg_color=(50, 50, 50), border_color=(200, 200, 200), inventory=None, context_menu=None):
        """Initialize the Inventory UI."""
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.font = font
        self.bg_color = bg_color
        self.border_color = border_color
        self.inventory = inventory  # Inventory instance
        self.context_menu = context_menu  # Reference to the context menu
        self.width = 250
        self.height = 300
        self.x = self.screen_width - (self.width * 2) - 10
        self.y = 10
        self.active = False
        self.hovered_item = None  # The item stack currently being hovered over
        self.scroll_offset = 0  # Scrolling offset for large inventories
        self.item_height = 25  # Height of each item entry

    def toggle(self):
        self.active = not self.active

    def render(self, screen: pygame.Surface, mouse_pos):
        """Render the inventory UI."""
        if not self.active:
            return

        if not self.inventory:
            logging.logger.debug("No inventory is linked")
            return

        # Draw the background of the inventory window
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, self.border_color, (self.x, self.y, self.width, self.height), 2)  # Border

        # Render the title of the inventory
        total_items = sum(quantity for stacks in self.inventory.items.values() for _, quantity in stacks)
        title_surface = self.font.render(f"Inventory: {total_items}/{self.inventory.max_weight}", True, (255, 255, 255))
        screen.blit(title_surface, (self.x + 10, self.y + 10))

        # Render the items in the inventory
        y_offset = 40  # Start rendering items after the title
        all_stacks = [
            (item, quantity) for stacks in self.inventory.items.values() for item, quantity in stacks
        ]  # Flatten all stacks into a single list
        visible_stacks = all_stacks[self.scroll_offset:self.scroll_offset + self.height // self.item_height]

        self.hovered_item = None  # Reset hovered item
        for index, (item, quantity) in enumerate(visible_stacks):
            item_text = f"{item.name} (x{quantity})"
            item_surface = self.font.render(item_text, True, (255, 255, 255))
            item_rect = pygame.Rect(self.x + 10, self.y + y_offset, self.width - 20, self.item_height)

            # Highlight item on hover
            if item_rect.collidepoint(mouse_pos):
                self.hovered_item = (item, quantity)
                pygame.draw.rect(screen, (100, 100, 100), item_rect)  # Highlight background
            else:
                pygame.draw.rect(screen, self.bg_color, item_rect)  # Default background

            screen.blit(item_surface, (self.x + 10, self.y + y_offset))
            y_offset += self.item_height

        # Show tooltip if hovering over an item and context menu is not open
        if self.hovered_item and not (self.context_menu and self.context_menu.active):
            self.render_tooltip(screen, mouse_pos, *self.hovered_item)

    def render_tooltip(self, screen, mouse_pos, item, quantity):
        """Render a tooltip with item details."""
        RARITY_COLORS = {
            "common": (255, 255, 255),  # White
            "uncommon": (0, 255, 64),  # Green
            "rare": (0, 128, 255),      # Blue
            "epic": (128, 0, 128),      # Purple
            "legendary": (255, 215, 0)  # Gold
        }

        tooltip_width = 200
        line_height = self.font.size("Sample")[1] + 5  # Height of a line + 5px padding
        base_height = 2 * line_height + 15  # Space for name and quantity + padding

        # Calculate the dynamic height based on the number of effects
        effects_lines = [f"{k.capitalize()} +{v}" for k, v in item.effects.items()] if item.effects else []
        tooltip_height = base_height + len(effects_lines) * line_height

        tooltip_x, tooltip_y = mouse_pos

        # Position the tooltip so its top-left corner aligns with the cursor's bottom-right
        tooltip_x = tooltip_x - tooltip_width
        tooltip_y = tooltip_y - tooltip_height

        # Ensure the tooltip stays within screen bounds
        if tooltip_x < 0:
            tooltip_x = 0
        if tooltip_y < 0:
            tooltip_y = 0
        if tooltip_x + tooltip_width > self.screen_width:
            tooltip_x = self.screen_width - tooltip_width
        if tooltip_y + tooltip_height > self.screen_height:
            tooltip_y = self.screen_height - tooltip_height

        # Draw tooltip background
        pygame.draw.rect(screen, (30, 30, 30), (tooltip_x, tooltip_y, tooltip_width, tooltip_height))
        pygame.draw.rect(screen, (200, 200, 200), (tooltip_x, tooltip_y, tooltip_width, tooltip_height), 2)

        # Render item details
        name_surface = self.font.render(f"{item.name} x{quantity}", True, (255, 255, 255))
        rarity_color = RARITY_COLORS.get(item.rarity, (255, 255, 255))  # Default to white
        rarity_surface = self.font.render(item.rarity.capitalize(), True, rarity_color)
        screen.blit(name_surface, (tooltip_x + 10, tooltip_y + 10))
        screen.blit(rarity_surface, (tooltip_x + 10, tooltip_y + 10 + line_height))

        # Render effects
        for i, line in enumerate(effects_lines):
            effects_surface = self.font.render(line, True, (150, 255, 150))
            screen.blit(effects_surface, (tooltip_x + 10, tooltip_y + 10 + 2 * line_height + i * line_height))

    def handle_scroll(self, direction):
        """
        Handle scrolling for the inventory.
        :param direction: -1 to scroll up, 1 to scroll down.
        """
        total_stacks = sum(len(stacks) for stacks in self.inventory.items.values())
        max_offset = max(0, total_stacks - self.height // self.item_height)
        self.scroll_offset = max(0, min(self.scroll_offset + direction, max_offset))

    def get_item_under_cursor(self, mouse_pos):
        """
        Check if an item is under the cursor in the inventory.

        Args:
            mouse_pos (tuple): The current mouse position (x, y).

        Returns:
            tuple: (Item, quantity) if an item is under the cursor, None otherwise.
        """
        # Flatten all stacks into a single list
        all_stacks = [
            (item, quantity) for stacks in self.inventory.items.values() for item, quantity in stacks
        ]

        # Get the visible items based on the scroll offset
        visible_stacks = all_stacks[self.scroll_offset:self.scroll_offset + self.height // self.item_height]

        # Iterate through the visible items and check for cursor collision
        for index, (item, quantity) in enumerate(visible_stacks):
            item_rect = pygame.Rect(
                self.x + 10,  # Padding on the left
                self.y + 40 + index * self.item_height,  # Y offset for the item
                self.width - 20,  # Subtract padding for width
                self.item_height
            )
            if item_rect.collidepoint(mouse_pos):
                return item, quantity  # Return the item and its quantity if found

        return None  # No item under the cursor
