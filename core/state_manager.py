from enum import Enum
import pygame

class GameStates(Enum):
    MAIN_MENU = "main_menu"
    PAUSED = "paused"
    GAME = "game"
    START = "start"
    RESUME = "resume"
    RESTART = "restart"
    QUIT_TO_MAIN_MENU = "quit_to_main_menu"
    QUIT_GAME = "quit"
    DEV_MENU = "dev_menu"
    DEV_CONSOLE = "dev_console"

class StateManager:
    """
    Manages game states and delegates control based on the active state.
    """

    def __init__(self, game):
        """
        Initialize the StateManager.
        :param game: Reference to the main Game instance.
        """
        self.game = game
        self.state_stack = []

    def push_state(self, state):
        """Push a new state onto the stack."""
        self.state_stack.append(state)

    def pop_state(self):
        """Pop the current state from the stack."""
        if self.state_stack:
            self.state_stack.pop()

    def reset_stack(self):
        self.state_stack = []
        self.push_state(GameStates.MAIN_MENU)

    def current_state(self):
        """Return the current active state."""
        return self.state_stack[-1] if self.state_stack else None

    def handle_events(self, event, now):
        """
        Handle events based on the current state.
        """
        current_state = self.current_state()
        if current_state == GameStates.MAIN_MENU:
            self.game.menu_manager.handle_input(event, self.game.mouse_pos)
        elif current_state == GameStates.PAUSED:
            self.game.handle_paused_events(event, now)
        elif current_state == GameStates.GAME:
            self.game.handle_game_events(event, now)
        elif current_state == GameStates.DEV_MENU:
            self.game.dev_menu.handle_input(event, now)
        elif current_state == GameStates.DEV_CONSOLE:
            self.game.dev_console.handle_input(event)

    def update(self, delta_time):
        """
        Update game logic based on the current state.
        """
        current_state = self.current_state()
        if current_state == GameStates.GAME:
            self.game.update(delta_time)

    def render(self):
        """
        Render the current game state.
        """

        current_state = self.current_state()
        if current_state == GameStates.MAIN_MENU:
            self.game.menu_manager.render(self.game.mouse_pos)
        elif current_state == GameStates.QUIT_TO_MAIN_MENU:
            self.game.menu_manager.render(self.game.mouse_pos)
        elif current_state == GameStates.PAUSED:
            self.game.menu_manager.render(self.game.mouse_pos)
        elif current_state == GameStates.GAME:
            self.game.render_game()
        elif current_state == GameStates.DEV_MENU:
            self.game.render_game()
            self.game.dev_menu.render(self.game.screen)
        elif current_state == GameStates.DEV_CONSOLE:
            self.game.render_game()
            self.game.dev_console.render(self.game.screen)

        self.game.screen.blit(self.game.cursor_image, self.game.mouse_pos)