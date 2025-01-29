import pygame
from core import logging


class ContextMenu:
    def __init__(self, font, options, screen_width, screen_height, option_height=40, padding=10):
        """Initialize the Context Menu."""
        self.font = font
        self.options = options  # List of options to display in the menu
        self.option_height = option_height  # Height of each option
        self.padding = padding  # Padding around text
        self.width = 200
        self.height = len(options) * self.option_height  # Adjust height based on number of options
        self.x = 0  # X position of the menu
        self.y = 0  # Y position of the menu
        self.active = False  # Whether the context menu is active
        self.hovered_option = None  # Option currently being hovered over
        self.selected_option = None  # Option selected by the player
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.tile = None
        self.item = None

    def show(self, x, y, tile=None, item=None):
        """Show the context menu at the given (x, y) position."""
        self.x = x
        self.y = y
        self.tile = tile  # Store the tile the player clicked on
        self.item = item
        self.active = True
        self.hovered_option = None  # Reset hovered option
        self.selected_option = None  # Reset selected option
        if self.tile:
            logging.logger.debug(f"Context menu shown at ({self.x}, {self.y}) with {self.tile.name} ({self.tile.x}, {self.tile.y})")
            self.options = ["Interact", "Examine"]
        if self.item:
            logging.logger.debug(f"Context menu shown at ({self.x}, {self.y}) with {self.item}")
            self.options = ["Use", "Examine", "Drop"]

        self.height = len(self.options) * self.option_height

    def hide(self):
        """Hide the context menu."""
        self.active = False
        logging.logger.debug("Context menu hidden.")

    def update_hovered_option(self, mouse_pos):
        """Update the currently hovered option based on the mouse position."""
        self.hovered_option = None
        for index, option in enumerate(self.options):
            option_rect = pygame.Rect(self.x, self.y + index * self.option_height, self.width, self.option_height)
            if option_rect.collidepoint(mouse_pos):
                self.hovered_option = option
                break

    def handle_input(self, mouse_pos, mouse_button):
        """Handle mouse input to select a menu option."""
        if not self.active:
            return None

        self.update_hovered_option(mouse_pos)
        if self.hovered_option and mouse_button == pygame.BUTTON_LEFT:
            self.selected_option = self.hovered_option
            logging.logger.debug(f"Option selected: {self.selected_option}")
            self.hide()  # Hide the menu after selecting an option
            return self.selected_option
        return None

    def render(self, screen, mouse_pos):
        """Render the context menu."""
        if not self.active:
            return

        self.update_hovered_option(mouse_pos)

        # Draw the background of the context menu
        pygame.draw.rect(screen, (50, 50, 50), (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, (200, 200, 200), (self.x, self.y, self.width, self.height), 2)  # Border

        # Render the menu options
        for index, option in enumerate(self.options):
            option_rect = pygame.Rect(self.x, self.y + index * self.option_height, self.width, self.option_height)

            # Highlight hovered option
            if self.hovered_option == option:
                pygame.draw.rect(screen, (100, 100, 100), option_rect)  # Highlight background
                pygame.draw.rect(screen, (255, 255, 255), option_rect, 2)  # White border for hovered option

            # Render the option text
            text_color = (255, 255, 255) if self.hovered_option != option else (255, 215, 0)  # Gold for hovered
            option_surface = self.font.render(option, True, text_color)
            screen.blit(option_surface, (self.x + self.padding, self.y + index * self.option_height + self.padding))
