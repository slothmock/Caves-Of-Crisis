import pygame
from core import logging

class MenuOption:
    """
    Represents a single menu option that can be hovered over, clicked, or selected via keyboard.
    """

    def __init__(self, text, y, font, action, screen_width, color=(255, 255, 255), hover_color=(255, 100, 100), font_size=None):
        """
        Initialize a menu option.
        :param text: The text of the menu option.
        :param y: Y-coordinate of the option.
        :param font: Font for rendering the text.
        :param action: Callback function to execute when clicked or selected.
        :param screen_width: The width of the screen (used for centering).
        :param color: Default text color.
        :param hover_color: Text color when hovered.
        :param font_size: Optional font size override (default is `None`).
        """
        self.text = text
        self.y = y
        self.font = pygame.font.Font(None, font_size if font_size else 28)  # Allow dynamic font size if provided
        self.action = action
        self.color = color
        self.hover_color = hover_color
        self.current_color = color  # Store the current color to allow dynamic updates

        # Render the text surface and calculate the rectangle for interaction
        self.rendered_text = self.font.render(self.text, True, self.current_color)
        self.rect = self.rendered_text.get_rect(center=(screen_width // 2, y))  # Center horizontally

    def render(self, screen, mouse_pos):
        """
        Render the menu option, applying hover and focus effects.
        :param screen: The Pygame screen to render to.
        :param mouse_pos: Current mouse position.
        :param is_focused: True if the option is selected via keyboard navigation.
        """
        is_hovered = self.is_hovered(mouse_pos)
        self.current_color = self.hover_color if is_hovered else self.color
        self.rendered_text = self.font.render(self.text, True, self.current_color)
        screen.blit(self.rendered_text, self.rect)

    def is_hovered(self, mouse_pos):
        """
        Check if the mouse is hovering over this menu option.
        :param mouse_pos: Current mouse position.
        :return: True if the mouse is over the option, otherwise False.
        """
        return self.rect.collidepoint(mouse_pos)

    def click(self):
        """
        Execute the assigned action when clicked.
        """
        if self.action:
            result = self.action()
            logging.logger.debug(f"Option '{self.text}' clicked. Action result: {result}")  # Debug feedback
            return result
        else:
            logging.logger.debug(f"Option '{self.text}' clicked but no action was defined.")
            return None  # Return None if no action is defined
