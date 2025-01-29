from tkinter import NO
import pygame
from core import logging
from core.state_manager import GameStates

class DeveloperMenu:
    """
    Developer Menu for executing debug actions during the game.
    """
    def __init__(self, screen_width, screen_height, font, player, game_map, state_manager, game):
        """
        Initialize the Developer Menu.
        """
        self.active = False
        self.font = font
        self.player = player
        self.game_map = game_map
        self.state_manager = state_manager
        self.game = game
        self.menu_width = 600
        self.menu_height = 400
        self.x = (screen_width - self.menu_width) // 2
        self.y = (screen_height - self.menu_height) // 2
        self.bg_color = (50, 50, 50)
        self.border_color = (200, 200, 200)
        self.options = [
            {"name": "Time Scale", "params": ["<seconds>"]},
            {"name": "Godmode", "params": None},
            {"name": "Fill Resources", "params": None},
            {"name": "Set Resource", "params": ["<resource>", "<value>"]},
            {"name": "Apply Effect", "params": ["<effect>", "<severity>", "<duration>"]},
            {"name": "Clear Effects", "params": None},
            {"name": "Teleport", "params": ["<x>", "<y>"]},
            {"name": "Grant Item", "params": ["<item>", "<quantity>"]},
            {"name": "Reveal Map", "params": None},
        ]
        self.selected_option = 0
        self.current_input = []  # Stores inputs for multi-part commands
        self.input_stage = 0     # Tracks the current parameter being entered

    def toggle(self):
        """
        Toggle the developer menu on/off, updating the game state and UI visibility.
        """
        self.active = not self.active
        if self.active:
            self.state_manager.push_state(GameStates.DEV_MENU)
            self.hide_game_ui()
        else:
            self.state_manager.pop_state()
            self.restore_game_ui()

    def hide_game_ui(self):
        """
        Save current UI states and hide all game UI elements.
        """
        self.saved_ui_states = {
            "help_screen": self.game.help_screen.active,
            "character_ui": self.game.character_ui.active,
            "message_log": self.game.message_log.active,
            "inventory_ui": self.game.inventory_ui.active,
        }
        self.game.help_screen.active = False
        self.game.character_ui.active = False
        self.game.message_log.active = False
        self.game.inventory_ui.active = False

    def restore_game_ui(self):
        """
        Restore previously saved UI states.
        """
        if hasattr(self, "saved_ui_states"):
            self.game.help_screen.active = self.saved_ui_states.get("help_screen", False)
            self.game.character_ui.active = self.saved_ui_states.get("character_ui", False)
            self.game.message_log.active = self.saved_ui_states.get("message_log", False)
            self.game.inventory_ui.active = self.saved_ui_states.get("inventory_ui", False)

    def render(self, screen: pygame.surface.Surface) -> None:
        """
        Render the developer menu.
        """
        if not self.active:
            return

        # Draw background and border
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.menu_width, self.menu_height))
        pygame.draw.rect(screen, self.border_color, (self.x, self.y, self.menu_width, self.menu_height), 3)

        # Render title
        title = self.font.render("Developer Menu", True, (255, 255, 255))
        screen.blit(title, (self.x + 10, self.y + 10))

        # Render options
        for index, option in enumerate(self.options):
            color = (255, 255, 255) if index == self.selected_option else (150, 150, 150)
            option_name = option["name"]
            params = " ".join(option["params"]) if option["params"] else ""
            full_text = f"{option_name} {params}"
            option_surface = self.font.render(full_text, True, color)
            screen.blit(option_surface, (self.x + 20, self.y + 50 + index * 30))

        # Render current input for multi-part command
        input_text = " ".join(self.current_input)
        input_surface = self.font.render(f"Input: {input_text}", True, (200, 200, 200))
        screen.blit(input_surface, (self.x + 20, self.y + self.menu_height - 30))

    def handle_input(self, event, now):
        """
        Handle input for navigating and selecting options.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_F12:
                self.toggle()
            elif event.key == pygame.K_UP:
                self.selected_option = (self.selected_option - 1) % len(self.options)
            elif event.key == pygame.K_DOWN:
                self.selected_option = (self.selected_option + 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                self.execute_option()
                self.toggle()
            elif event.key == pygame.K_BACKSPACE:
                if self.current_input:
                    self.current_input.pop()
            elif event.unicode and self.current_input is not None:
                self.current_input.append(event.unicode)

    def execute_option(self):
        """
        Execute the currently selected menu option.
        """
        option = self.options[self.selected_option]
        name = option["name"]

        # Handle commands with no parameters
        if option["params"] is None:
            if name == "Godmode":
                self.player.toggle_invincibility()
            elif name == "Fill Resources":
                self.player.fill_resources()
            elif name == "Reveal Map":
                self.player.reveal_map(self.game_map)
            elif name == "Clear Effects":
                self.player.clear_effects()

        # Handle commands with parameters
        else:
            # Join current input into a single string and split into arguments
            full_input = "".join(self.current_input).strip()
            args = full_input.split(" ")


            # Ensure sufficient arguments are provided for the command
            if len(args) >= len(option["params"]):
                if name == "Set Resource":
                    resource, value = args[0], int(args[1])
                    self.player.set_resource(resource, value)
                elif name == "Teleport":
                    x, y = int(args[0]), int(args[1])
                    self.player.teleport(x, y)
                elif name == "Apply Effect":
                    effect, severity, duration, duration_unit = args[0], args[1], int(args[2]), args[3]
                    self.player.apply_effect_dev(effect, severity, duration, duration_unit)
                elif name == "Grant Item":
                    item_name, quantity = args[0], int(args[1])
                    self.player.grant_item(item_name, quantity)
                elif name == "Time Scale":
                    seconds = args[0]
                    if len(seconds) < 1:
                        return
                    self.player.timefactor(seconds)
                
                logging.logger.debug(f"Executed {name} with input: {self.current_input}")
                
                # Reset input after execution
                self.current_input = []
                self.toggle()


    def handle_teleport(self):
        """
        Example teleportation logic for debugging.
        """
        try:
            x = int(input("Enter X coordinate: "))
            y = int(input("Enter Y coordinate: "))
            self.player.teleport(x, y)
            logging.logger.debug(f"Teleported to ({x}, {y}).")
        except ValueError:
            logging.logger.debug("Invalid coordinates.")

    def handle_grant_item(self):
        """
        Grant an item dynamically through developer input.
        """
        item_name = input("Enter item name: ")
        try:
            quantity = int(input("Enter quantity: "))
            self.player.grant_item(item_name, quantity)
            logging.logger.debug(f"Granted {quantity} x {item_name}.")
        except ValueError:
            logging.logger.debug("Invalid quantity.")

    def handle_time_scale(self):
        value = input("Enter # of seconds (default: 5): ")
