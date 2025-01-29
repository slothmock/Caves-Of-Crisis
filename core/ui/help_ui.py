import pygame

class HelpUI:
    def __init__(self, font, screen_width, screen_height):
        self.font = font
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active = True
        self.help_text = [
            "Hide All UI: F2",
            "Toggle Help: H",
            "Toggle Character: C",
            "Toggle Log: V",
            "Move: WASD",
            "Context Menu: Right Click",
            "Inventory: Tab",
            "Pick Up Items: G",
            "Rest: R (TBA)",
        ]

    def toggle(self):
        """Toggle the visibility of the help screen."""
        self.active = not self.active

    def render(self, screen):
        """Render the help screen below the character UI."""
        if not self.active:
            return

        # Set position for the help screen (below the character UI)
        y_position = (self.screen_height // 2) - 25  # Adjust this based on character UI height
        x_position = self.screen_width - 260
        padding = 10
        line_height = self.font.get_height() + 5

        # Draw background for the help screen
        pygame.draw.rect(screen, (50, 50, 50), (x_position, y_position, 250, 230))  # Background
        pygame.draw.rect(screen, (200, 200, 200), (x_position, y_position, 250, 230), 3)  # Border

        # Display the help screen text
        for i, line in enumerate(self.help_text):
            help_surface = self.font.render(line, True, (255, 255, 255))
            screen.blit(help_surface, (x_position + padding, y_position + padding + i * line_height))
