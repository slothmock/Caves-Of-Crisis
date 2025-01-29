import pygame

from core import logging
from core.settings import AUTHOR_LABEL, GAME_TITLE, SCREEN_HEIGHT, GAME_VERSION, SCREEN_WIDTH
from core.state_manager import GameStates, StateManager
from core.ui.menus.menu_option import MenuOption


class MainMenu:
    """
    Main menu for the game.
    """
    def __init__(self, screen, font, title_font, state_manager:StateManager, menu_manager):
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.state_manager = state_manager
        self.menu_manager = menu_manager

        screen_width = screen.get_width()
        self.options = [
            MenuOption("Start a new adventure", 250, self.font, self.start_game, screen_width),
            MenuOption("Help & Controls", 300, self.font, self.open_guide, screen_width),
            MenuOption("Quit Game", 350, self.font, self.quit_game, screen_width),
        ]

    def render(self, mouse_pos):
        """Render the main menu."""
        self.screen.fill((0, 0, 0))  # Black background

        # Render title
        title_surface = self.title_font.render(GAME_TITLE, True, (255, 85, 85))
        title_rect = title_surface.get_rect(center=(self.screen.get_width() // 2, 100))
        version_surface = self.font.render(f"{GAME_VERSION}", True, (200, 200, 200))
        author_surface = self.font.render(f"{AUTHOR_LABEL}", True, (200, 200, 200))

        self.screen.blit(title_surface, title_rect)
        self.screen.blit(version_surface, (10, SCREEN_HEIGHT - 30))
        self.screen.blit(author_surface, (SCREEN_WIDTH - 215, SCREEN_HEIGHT - 30))

        # Render menu options
        [option.render(self.screen, mouse_pos) for option in self.options]

    def handle_input(self, event, mouse_pos):
        """Handle input for navigating and interacting with the menu."""
        for option in self.options:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if option.is_hovered(mouse_pos):
                    return option.click()

    def start_game(self):
        """Start the game."""
        if self.state_manager.game.map is not None:
            self.state_manager.game.init_game_elements()
        self.state_manager.push_state(GameStates.GAME)
        return GameStates.GAME

    def open_guide(self):
        """Open the help & controls menu."""
        if self.menu_manager:
            self.menu_manager.curent_menu = None
            self.menu_manager.open_guide()

    def quit_game(self):
        """Quit the game."""
        if self.menu_manager:
            self.menu_manager.quit()
