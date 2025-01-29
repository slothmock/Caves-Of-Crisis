import pygame


class Menu:
    def __init__(self, screen, title, options, font, title_font, title_color=(255, 255, 255), option_color=(200, 200, 200), selected_color=(255, 0, 0)):
        """
        Base class for menus.
        :param screen: The Pygame screen to render the menu.
        :param title: The title of the menu.
        :param options: A list of strings representing menu options.
        :param font: The font for the menu options.
        :param title_font: The font for the title.
        :param title_color: The color of the title.
        :param option_color: The default color of the options.
        :param selected_color: The color of the selected option.
        """
        self.screen = screen
        self.title = title
        self.options = options
        self.font = font
        self.title_font = title_font
        self.title_color = title_color
        self.option_color = option_color
        self.selected_color = selected_color
        self.selected_index = 0

    def render(self, mouse_pos):
        """Render the menu."""
        self.screen.fill((0, 0, 0))  # Clear the screen with black

        # Render the title
        title_surface = self.title_font.render(self.title, True, self.title_color)
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Render the options
        for index, option in enumerate(self.options):
            color = self.selected_color if index == self.selected_index else self.option_color
            option_surface = self.font.render(option, True, color)
            option_rect = option_surface.get_rect(center=(self.screen.get_width() // 2, 200 + index * 50))
            self.screen.blit(option_surface, option_rect)

    def navigate(self, direction):
        """Navigate through menu options."""
        self.selected_index = (self.selected_index + direction) % len(self.options)

    def select(self):
        """Return the currently selected option."""
        return self.selected_index
