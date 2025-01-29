import pygame
from core.state_manager import GameStates
from core.ui.menus.menu_option import MenuOption


class PauseMenu:
    """
    Pause menu for the game.
    """
    def __init__(self, screen, font, title_font, state_manager):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.state_manager = state_manager

        screen_width = screen.get_width()
        self.options = [
            MenuOption("Resume", 200, self.font, self.resume_game, screen_width),
            MenuOption("Restart", 250, self.font, self.restart_game, screen_width),
            MenuOption("Quit to Main Menu", 300, self.font, self.main_menu, screen_width),
        ]
        self.selected_index = 0

    def render(self, mouse_pos):
        """Render the pause menu."""
        self.screen.fill((0, 0, 0))  # Black background

        # Render title
        title_surface = self.title_font.render("Paused", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        self.screen.blit(title_surface, title_rect)

        # Render menu options
        for option in self.options:
            option.render(self.screen, mouse_pos)

    def handle_input(self, event, mouse_pos):
        """Handle input for the pause menu."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state_manager.pop_state()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for option in self.options:
                if option.is_hovered(mouse_pos):
                    return option.click()

    def navigate(self, direction):
        """Navigate through menu options."""
        self.selected_index = (self.selected_index + direction) % len(self.options)

    def handle_selection(self):
        """Handle selection of the current option."""
        self.options[self.selected_index].click()

    def resume_game(self):
        """Resume the game."""
        self.state_manager.pop_state()

    def restart_game(self):
        """Restart the game."""
        self.state_manager.reset_stack()
        self.state_manager.game.restart()
        self.state_manager.push_state(GameStates.GAME)

    def main_menu(self):
        """Return to the main menu."""
        self.state_manager.reset_stack()  # Clear all active states
        self.state_manager.push_state(GameStates.MAIN_MENU)  # Transition to MAIN_MENU
        self.state_manager.game.menu_manager.open_main_menu()  # Open the main menu in MenuManager
