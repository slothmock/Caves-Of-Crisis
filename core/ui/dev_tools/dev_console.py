from __future__ import annotations

import pygame
from typing import List, Dict

from core.state_manager import GameStates



class DeveloperConsole:
    """
    Developer Console for executing debug commands during the game.
    """

    def __init__(
        self,
        font: pygame.font.Font,
        screen_width: int,
        screen_height: int,
        player,
        game_map,
        state_manager,
        game,
    ) -> None:
        """
        Initialize the Developer Console.
        """
        self.active: bool = False
        self.font: pygame.font.Font = font
        self.input_text: str = ""  # Current input
        self.log: List[str] = []  # Log of commands/results
        self.max_log_length: int = 10
        self.width: int = screen_width - 20
        self.height: int = 190
        self.x: int = 10
        self.y: int = screen_height - self.height
        self.player = player
        self.game_map = game_map
        self.state_manager = state_manager
        self.game = game

        # Command auto-complete setup
        self.commands: Dict[str, List[str]] = {
            "timefactor": ["<multiplier>"],
            "teleport": ["<x>", "<y>"],
            "grant": ["<item>", "<quantity>"],
            "reveal": [],
            "fillresources": [],
            "setresource": ["<resource>", "<value>"],
            "setmaxresource": ["<resource>", "<value>"],
            "applyeffect": ["<effect>", "<severity>", "<duration (in-game minutes)>"],
            "effectsclear": [],
            "godmode": [],
            "invincible": [],
        }
        self.matched_commands: List[str] = []
        self.selected_index: int = 0

    def toggle(self) -> None:
        """
        Toggle the console on/off, updating the game state and UI visibility.
        """
        self.active = not self.active
        if self.active:
            self.state_manager.push_state(GameStates.DEV_CONSOLE)
            self.hide_game_ui()
        else:
            self.state_manager.pop_state()
            self.restore_game_ui()

    def hide_game_ui(self) -> None:
        """
        Save current UI states and hide all game UI elements.
        """
        self.saved_ui_states: Dict[str, bool] = {
            "help_screen": self.game.help_screen.active,
            "character_ui": self.game.character_ui.active,
            "message_log": self.game.message_log.active,
            "inventory_ui": self.game.inventory_ui.active,
        }

        # Hide all UI elements
        self.game.help_screen.active = False
        self.game.character_ui.active = False
        self.game.message_log.active = False
        self.game.inventory_ui.active = False

    def restore_game_ui(self) -> None:
        """
        Restore previously saved UI states.
        """
        if hasattr(self, "saved_ui_states"):
            self.game.help_screen.active = self.saved_ui_states.get("help_screen", False)
            self.game.character_ui.active = self.saved_ui_states.get("character_ui", False)
            self.game.message_log.active = self.saved_ui_states.get("message_log", False)
            self.game.inventory_ui.active = self.saved_ui_states.get("inventory_ui", False)

    def handle_input(self, event: pygame.event.Event) -> None:
        """
        Handle text input and commands.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.toggle()
            elif event.key == pygame.K_RETURN:  # Execute command
                self.execute_command(self.input_text)
                self.input_text = ""  # Clear input after execution
                self.matched_commands = []  # Clear suggestions
            elif event.key == pygame.K_BACKSPACE:  # Remove last character
                self.input_text = self.input_text[:-1]
                self.update_matched_commands()
            elif event.key == pygame.K_TAB:  # Auto-complete command
                if self.matched_commands:
                    self.input_text = self.matched_commands[self.selected_index]
                    self.matched_commands = []  # Clear suggestions after auto-complete
            elif event.key == pygame.K_UP:  # Navigate suggestions
                if self.matched_commands:
                    self.selected_index = (self.selected_index - 1) % len(self.matched_commands)
            elif event.key == pygame.K_DOWN:  # Navigate suggestions
                if self.matched_commands:
                    self.selected_index = (self.selected_index + 1) % len(self.matched_commands)
            else:
                self.input_text += event.unicode  # Add typed character
                self.update_matched_commands()

    def update_matched_commands(self) -> None:
        """
        Update the list of commands that match the current input.
        """
        input_chars: List[str] = self.input_text.split()
        if not input_chars:
            self.matched_commands = list(self.commands.keys())
        else:
            # Match the first part of the command
            first_part: str = input_chars[0]
            if len(input_chars) == 1:
                self.matched_commands = [
                    cmd for cmd in self.commands if cmd.startswith(first_part)
                ]
            else:
                command: str = input_chars[0]
                if command in self.commands:
                    args = self.commands[command]
                    current_arg_index = len(input_chars) - 2
                    if current_arg_index < len(args):
                        current_arg = input_chars[-1]
                        self.matched_commands = [
                            arg for arg in args if arg.startswith(current_arg)
                        ]
                    else:
                        self.matched_commands = []

        self.selected_index = 0  # Reset selection to the first suggestion

    def execute_command(self, command: str) -> None:
        """
        Parse and execute a command.
        """
        try:
            if command.startswith("teleport"):
                _, x, y = command.split()
                self.player.teleport(int(x), int(y))
                self.log.append(f"[DevTools] Teleported to ({x}, {y}).")
            elif command.startswith("grant"):
                _, item_name, quantity = command.split()
                self.player.grant_item(item_name, int(quantity))
                self.log.append(f"[DevTools] Granted {quantity} x {item_name}.")
            elif command == "reveal":
                self.player.reveal_map(self.game_map)
                self.log.append("[DevTools] Map revealed.")
            elif command == "fillresources":
                self.player.fill_resources()
                self.log.append("[DevTools] Resources filled.")
            elif command.startswith("setresource"):
                _, resource, amount = command.split()
                self.player.set_resource(resource, int(amount))
                self.log.append(f"[DevTools] {resource} set to {amount}.")
            elif command.startswith("setmaxresource"):
                _, resource, amount = command.split()
                self.player.set_resource_max(resource, int(amount))
                self.log.append(f"[DevTools] {resource} set to {amount}.")
            elif command.startswith("applyeffect"):
                _, effect, severity, duration = command.split()
                self.player.apply_effect_dev(effect.capitalize(), severity.upper(), int(duration))
                self.log.append(f"[DevTools] {effect} effect applied for {duration} in-game minutes.")
            elif command == "effectsclear":
                self.player.clear_effects()
                self.log.append("[DevTools] Cleared all effects.")
            elif command in {"godmode", "invincible"}:
                self.player.toggle_invincibility()
                self.log.append("[DevTools] Toggled invincibility/godmode.")
            elif command in {"clear", "cls"}:
                self.log.clear()
                self.log.append("[DevTools] Dev Console cleared.")
            else:
                self.log.append(f"Unknown command: {command}")
        except Exception as e:
            self.log.append(f"Error: {e}")

        # Truncate log if necessary
        if len(self.log) > self.max_log_length:
            self.log.pop(0)

    def render(self, screen):
        """
        Render the console and its content.
        """
        if not self.active:
            return

        # Draw the console background
        console_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(screen, (50, 50, 50), console_rect)  # Background
        pygame.draw.rect(screen, (200, 200, 200), console_rect, 2)  # Border

        # Render the input box
        input_box = pygame.Rect(self.x + 5, self.y + self.height - 30, self.width - 10, 25)
        pygame.draw.rect(screen, (0, 0, 0), input_box)  # Input box background
        pygame.draw.rect(screen, (255, 255, 255), input_box, 2)  # Input box border

        # Render input text
        input_surface = self.font.render(self.input_text, True, (255, 255, 255))
        screen.blit(input_surface, (self.x + 10, self.y + self.height - 26))

        # Render the log
        for i, message in enumerate(reversed(self.log[-self.max_log_length:])):
            message_surface = self.font.render(message, True, (255, 255, 255))
            screen.blit(message_surface, (self.x + 10, self.y + 10 + i * 20))

        # Render command suggestions if available
        if self.matched_commands:
            suggestion_box_height = len(self.matched_commands) * 20 + 5
            suggestion_box = pygame.Rect(
                self.x + 5,
                self.y + self.height - 30 - suggestion_box_height,
                self.width - 10,
                suggestion_box_height,
            )
            pygame.draw.rect(screen, (30, 30, 30), suggestion_box)  # Background
            pygame.draw.rect(screen, (255, 255, 255), suggestion_box, 2)  # Border

            for i, suggestion in enumerate(self.matched_commands):
                # Determine color and label for the highlighted suggestion
                color = (255, 255, 0) if i == self.selected_index else (255, 255, 255)
                label = " [TAB] to accept" if i == self.selected_index else ""

                # Retrieve the parameters for the suggestion (if any)
                if suggestion in self.commands:
                    parameters = " ".join(self.commands[suggestion])  # Join parameters into a single string
                else:
                    parameters = ""

                # Combine suggestion, parameters, and label
                full_suggestion = f"{suggestion} {parameters}{label}"

                # Render the suggestion with parameters
                suggestion_surface = self.font.render(full_suggestion, True, color)
                screen.blit(
                    suggestion_surface,
                    (
                        self.x + 10,
                        self.y + self.height - 30 - suggestion_box_height + 5 + i * 20,
                    ),
                )
