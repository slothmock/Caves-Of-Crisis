import pygame
from core.ui.menus.menu_option import MenuOption
from core.state_manager import GameStates


class HelpGuideMenu:
    """
    Help and controls menu for the game.
    """
    def __init__(self, screen, font, title_font, state_manager, menu_manager):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.state_manager = state_manager
        self.menu_manager = menu_manager

        screen_width = screen.get_width()
        self.options = [
            MenuOption("Cave Guide (TBA)", 300, self.font, self.dummy_action, screen_width),
            MenuOption("Back to Main Menu", 400, self.font, self.back_to_main_menu, screen_width),
        ]

    def render(self, mouse_pos):
        """Render the help guide menu."""
        self.screen.fill((0, 0, 0))  # Green background

        # Render title
        title_surface = self.title_font.render("Help & Controls", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        [option.render(self.screen, mouse_pos) for option in self.options]


    def handle_input(self, event, mouse_pos):
        """Handle input for navigating and interacting with the menu."""
        for option in self.options:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if option.is_hovered(mouse_pos):
                    return option.click()

    def dummy_action(self):
        """Placeholder action for menu options."""
        print("Help content displayed.")

    def back_to_main_menu(self):
        """Return to the main menu."""
        self.menu_manager.open_main_menu()
