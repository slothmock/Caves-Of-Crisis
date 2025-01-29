import pygame

from core.state_manager import GameStates
from core.ui.menus.controls_menu import HelpGuideMenu
from core.ui.menus.main_menu import MainMenu
from core.ui.menus.pause_menu import PauseMenu


class MenuManager:
    """
    Handles different menus and their navigation/rendering.
    """
    def __init__(self, screen, font, title_font, state_manager):
        """
        Initialize the menu manager.
        :param screen: Pygame screen object.
        :param font: Font for menu options.
        :param title_font: Font for menu titles.
        :param state_manager: Instance of StateManager for managing game states.
        """
        self.screen = screen
        self.font = font
        self.title_font = title_font
        self.state_manager = state_manager

        self.current_menu = None

    def open_main_menu(self):
        """Open the main menu."""
        self.current_menu = MainMenu(self.screen, self.font, self.title_font, self.state_manager, self)

    def open_guide(self):
        """Open the guide"""
        self.current_menu = HelpGuideMenu(self.screen, self.font, self.title_font, self.state_manager, self)

    def open_pause_menu(self):
        """Open the pause menu."""
        self.current_menu = PauseMenu(self.screen, self.font, self.title_font, self.state_manager)

    def quit(self):
        self.current_menu = None
        self.state_manager.pop_state()
        pygame.quit()
        exit()

    def render(self, mouse_pos):
        """Render the current menu."""
        if self.current_menu:
            self.current_menu.render(mouse_pos)

    def handle_input(self, event, mouse_pos):
        """Handle input for the current menu."""
        if self.current_menu:
            return self.current_menu.handle_input(event, mouse_pos)
        return None
    
