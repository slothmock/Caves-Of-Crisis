from __future__ import annotations
from core.items.item_factory import ItemFactory
from core.items.item_list import ItemList
from core.state_manager import GameStates, StateManager

import random
import threading
import pygame
from typing import Any, Optional

from core.entities.dev_char import Developer
from core.entities.player import Player
from core.camera import Camera
from core.gametime.gametime import InGameTime
from core.logging import logger
from core.message_log.message_log import MessageLog
from core.map.map import Map
from core.map.tile_types import TileType
from core.settings import (
    FPS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    TILE_SIZE,
    GAME_TITLE,
    DEV_MODE,
)
from core.ui import inventory_ui
from core.ui.context_menu import ContextMenu
from core.ui.character_ui import CharacterUI
from core.ui.dev_tools.dev_console import DeveloperConsole
from core.ui.dev_tools.dev_menu import DeveloperMenu
from core.ui.help_ui import HelpUI
from core.ui.inventory_ui import InventoryUI
from core.ui.menus.menu_manager import MenuManager


class Game:
    def __init__(self, screen_width: int = SCREEN_WIDTH, screen_height: int = SCREEN_HEIGHT, tile_size: int = TILE_SIZE):
        """
        Initialize the game, set up essential elements such as screen, clock, and state.
        """
        pygame.init()
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.time_system = InGameTime()
        self.state_manager = StateManager(self)
        self.tile_size = tile_size
        self.show_debug = DEV_MODE
        self.loading = False
        self.loading_thread = None

        # Fonts
        self.mfont = pygame.font.Font(None, 28)
        self.sfont = pygame.font.Font(None, 26)
        self.xlfont = pygame.font.Font(None, 72)

        # Menu Manager
        self.menu_manager = MenuManager(self.screen, self.mfont, self.xlfont, self.state_manager)
        self.menu_manager.open_main_menu()

        # Cursor
        self.cursor_image = self.load_cursor("assets/img/cursor.png")
        pygame.mouse.set_visible(False)

        # Initial Game State
        self.state_manager.push_state(GameStates.MAIN_MENU)

        # Game Elements
        ItemFactory.load_items_from_yaml("core/items/items.yaml")
        self.map: Optional[Map] = None
        self.player: Optional[Player | Developer] = None
        self.entities = []
        self.camera: Optional[Camera] = None
        self.enemies = []
        self.mouse_pos = pygame.mouse.get_pos()

        # UI Elements
        self.message_log: Optional[MessageLog] = None
        self.character_ui: Optional[CharacterUI] = None
        self.inventory_ui: Optional[InventoryUI] = None
        self.dev_menu: Optional[DeveloperMenu] = None
        self.dev_console: Optional[DeveloperConsole] = None
        self.context_menu = ContextMenu(self.mfont, ["Use", "Examine"], SCREEN_WIDTH, SCREEN_HEIGHT)
        self.help_screen = HelpUI(self.sfont, SCREEN_WIDTH, SCREEN_HEIGHT)

        logger.debug("Game initialized.")

    def load_cursor(self, path: str) -> pygame.Surface:
        """Load the custom cursor image, or use a fallback if unavailable."""
        try:
            cursor_image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(cursor_image, (24, 24))
        except FileNotFoundError:
            logger.error("Cursor image not found. Using default white square.")
            cursor_image = pygame.Surface((24, 24))
            cursor_image.fill((255, 255, 255))
            return cursor_image
        
    def update_loading_screen(self):
        pygame.display.flip()
        self.clock.tick(60)  # Cap the frame rate

    def render_loading_screen(screen, font, label: str, target_progress: float, current_progress: float):
        """
        Render the animated loading screen with a progress bar.

        Args:
            screen (pygame.Surface): The screen to render the loading screen on.
            font (pygame.font.Font): Font for rendering text.
            label (str): Text label for the current stage.
            target_progress (float): The target progress value (0.0 to 1.0).
            current_progress (float): The current progress value.
        Returns:
            float: The updated current progress.
        """
        clock = pygame.time.Clock()
        animation_speed = 0.02  # Adjust speed of the progress bar animation

        while current_progress < target_progress:
            current_progress += animation_speed
            current_progress = min(current_progress, target_progress)  # Clamp to target progress

            screen.fill((0, 0, 0))  # Clear the screen

            # Render label
            label_surface = font.render(label, True, (255, 255, 255))
            label_rect = label_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 50))
            screen.blit(label_surface, label_rect)

            # Render progress bar
            bar_width = 300
            bar_height = 20
            bar_x = screen.get_width() // 2 - bar_width // 2
            bar_y = screen.get_height() // 2
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))  # Bar background
            pygame.draw.rect(
                screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * current_progress), bar_height)
            )  # Progress bar

            # Render animation (e.g., dots after the label)
            dots = "." * (int(pygame.time.get_ticks() / 200) % 4)  # Cycle through "", ".", "..", "..."
            animated_label = font.render(label + dots, True, (255, 255, 255))
            screen.blit(animated_label, label_rect)

            pygame.display.flip()  # Update the display
            clock.tick(60)  # Cap the frame rate

        return current_progress

    def init_game_elements(self):
        """Start the map generation process in a background thread."""
        logger.debug("Initializing game elements...")
        self.loading = True
        self.loading_thread = threading.Thread(target=self.generate_map_and_cave, daemon=True)
        self.loading_thread.start()

    def generate_map_and_cave(self):
        """Generate the map and cave with a unified loading screen."""
        self.loading = True  # Enable loading state
        self.current_progress = 0.0  # Track progress for the loading screen

        try:
            # Initialize map and related elements
            self.camera = Camera(SCREEN_WIDTH, SCREEN_HEIGHT, self.tile_size, buffer=2)

            self.message_log = MessageLog(
                x=10, y=SCREEN_HEIGHT - 150, width=SCREEN_WIDTH - 15, height=130, font=self.mfont
            )

            self.map = Map(self.tile_size, width=1000, height=1000)
            self.seed = random.randint(0, 100000)

            # Generate the cave with progress updates
            self.current_progress = self.map.generate_cave(
                screen=self.screen,
                font=self.mfont,
                step_progress=self.current_progress
            )

            player_x, player_y = self.map.find_walkable_tile()
            if not self.map.can_move(player_x, player_y):  # Check if the tile is walkable
                logger.error(f"Spawn point ({player_x}, {player_y}) is blocked! Finding a new position...")
                player_x, player_y = self.map.find_walkable_tile()  # Try again
                
            self.player = Developer(
                x=player_x,
                y=player_y,
                char="@", color=(255, 0, 255),
                tile_size=self.tile_size,
                game_time=self.time_system,
                message_log=self.message_log,
                is_invincible=True,
                unlimited_resources=True,
            ) if DEV_MODE else Player(
                x=player_x,
                y=player_y,
                char="@", color=(255, 20, 147),
                tile_size=self.tile_size,
                game_time=self.time_system,
                message_log=self.message_log,
            )

            self.entities = [self.player]
            self.character_ui = self.setup_character_ui(self.player)
            self.inventory_ui = InventoryUI(
                SCREEN_WIDTH, SCREEN_HEIGHT, font=self.mfont, inventory=self.player.inventory, context_menu=self.context_menu
            )

            self.dev_menu = DeveloperMenu(
                screen_width=SCREEN_WIDTH,
                screen_height=SCREEN_HEIGHT,
                font=self.mfont,
                player=self.player,
                game_map=self.map,
                state_manager=self.state_manager,
                game=self,
            )
            self.dev_console = DeveloperConsole(
                font=self.sfont,
                screen_width=SCREEN_WIDTH,
                screen_height=SCREEN_HEIGHT,
                player=self.player,
                game_map=self.map,
                state_manager=self.state_manager,
                game=self,
            )

            self.message_log.add_message("The adventure begins!")
            self.loading = False



        except Exception as e:
            logger.exception("Error during map generation: %s", e)
        finally:
            self.loading = False  # Disable loading state
            logger.debug("Map and cave generation complete.")

    def setup_character_ui(self, player: Player | Developer) -> Optional[CharacterUI]:
        """Setup the character UI and load an avatar."""
        try:
            char_ui = CharacterUI(screen_width=SCREEN_WIDTH, font=self.sfont)
            char_ui.set_character(character=player)
            char_ui.set_avatar(avatar_path="assets/img/hero_avatars/hero1.png")
            char_ui.load_status_icons()
            return char_ui
        except FileNotFoundError:
            logger.warning("Character avatar not found. Skipping avatar setup.")
            return None
        
    def run(self):
        """Main game loop."""
        logger.debug("Game loop started.")
        while self.state_manager.current_state() != GameStates.QUIT_GAME:
            self.mouse_pos = pygame.mouse.get_pos()
            now = self.clock.tick(FPS)

            if self.loading:
                self.update_loading_screen()
            else:
                self.state_manager.update(now)
                self.screen.fill((0, 0, 0))  # Clear the screen
                self.state_manager.render()
                pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.state_manager.push_state(GameStates.QUIT_GAME)
                else:
                    self.state_manager.handle_events(event, now)

            self.time_system.update()


    def restart(self) -> None:
        """Restart the game by reinitializing elements and resetting the state stack."""
        logger.debug("Restarting game...")
        self.time_system.reset_clock()
        self.entities.clear()
        self.init_game_elements()
        logger.debug("Game restarted.")


    def handle_events(self, event, now: int) -> None:
        """
        Handle events based on the current game state.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()

            active_state = self.state_manager.current_state()

            if active_state == GameStates.MAIN_MENU:
                self.handle_main_menu_events(event)
                return
            elif active_state == GameStates.PAUSED:
                self.handle_paused_events(event)
                return
            elif active_state == GameStates.GAME:
                self.handle_game_events(event, now)
                return
            elif active_state == GameStates.DEV_CONSOLE:
                self.dev_console.handle_input(event)
                return  
            elif active_state == GameStates.DEV_MENU:
                self.dev_menu.handle_input(event)
                return  

    def quit_game(self):
        """Handle quitting the game."""
        self.running = False
        self.time_system = None
        self.camera: Optional[Camera] = None
        self.map: Optional[Map] = None
        self.player: Optional[Player | Developer] = None
        self.enemies = []
        self.entities = []
        logger.debug("Game quit by user.")

    def handle_keydown(self, event: pygame.event.Event):
        """Handle keydown events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F2:
                self.toggle_all_ui()
            elif event.key == pygame.K_h:
                self.help_screen.toggle()
            elif event.key == pygame.K_c:
                self.character_ui.toggle()
            elif event.key == pygame.K_v:
                self.message_log.toggle()
            elif event.key == pygame.K_TAB:
                self.inventory_ui.toggle()
            elif event.key == pygame.K_g:
                tile = self.map.get_tile_at_xy(self.player.x, self.player.y)
                         
                self.player.pick_up_items_from_tile(tile)

            elif event.key == pygame.K_r and not self.player.is_resting:
                ...
                # TODO: Implement resting/sleeping feature
                # self.player.rest()
                
            elif event.key == pygame.K_PAGEUP:
                self.message_log.scroll(-1)
            elif event.key == pygame.K_PAGEDOWN:
                self.message_log.scroll(1)

    def handle_mouse_button(self, event: pygame.event.Event):
        """Handle mouse button events."""
        if event.button == pygame.BUTTON_RIGHT:
            self.handle_right_click(self.mouse_pos)
        elif event.button == pygame.BUTTON_LEFT:
            self.handle_left_click(self.mouse_pos)

    def handle_right_click(self, mouse_pos: tuple) -> None:
        """
        Handle right-click events to show the context menu for tiles or inventory items.
        
        Args:
            mouse_pos (tuple): Tuple of screen coordinates (mouse_x, mouse_y).
        """
        if self.state_manager.current_state() == GameStates.MAIN_MENU:
            return  # No interaction allowed in the main menu

        # Check for inventory item click
        if self.inventory_ui.active:
            # Check if an item is clicked
            item = self.inventory_ui.get_item_under_cursor(mouse_pos)
            if item:
                # Show context menu for the inventory item
                self.context_menu.show(mouse_pos[0], mouse_pos[1], item=item)
                self.message_log.add_message(f"Selected Item: {item[0].name}")
                return

        # Convert screen coordinates to grid coordinates using the camera
        tile_x, tile_y = self.camera.screen_to_grid(mouse_pos[0], mouse_pos[1])

        # Validate tile coordinates
        if 0 <= tile_x < self.map.width and 0 <= tile_y < self.map.height:
            tile = self.map.map_data[tile_y][tile_x]
            self.context_menu.tile = tile

            # Check if the tile is adjacent to the player
            player_x, player_y = self.player.x, self.player.y
            is_adjacent = abs(player_x - tile_x) <= 1 and abs(player_y - tile_y) <= 1

            if tile and not self.inventory_ui.active:
                # Tile is visible or adjacent to the player
                if self.map.visible_map[tile_y][tile_x] or is_adjacent:
                    self.context_menu.show(mouse_pos[0], mouse_pos[1], tile=tile)
                    self.message_log.add_message(f"Selected Tile: {tile.name}")
                # Tile is explored but not currently visible
                elif self.map.explored_map[tile_y][tile_x]:
                    self.message_log.add_message(
                        f"You can't see the {tile.name.lower()} from here, but you vaguely remember the way."
                    )
                # Tile is neither visible nor explored
                else:
                    self.message_log.add_message("You can't see anything here. The darkness feels oppressive.")
                    if not isinstance(self.player, Developer):
                        self.message_log.add_message("-2 Sleep")
                        self.player.expend_sleep(2)
            else:
                self.message_log.add_message("You inventory is open. Close it to interact with tiles.")
        else:
            self.message_log.add_message("Mouse is outside the map bounds.")


    def handle_left_click(self, mouse_pos: tuple):
        """Handle left-click events to select an option in the context menu."""
        selected_option = self.context_menu.handle_input(mouse_pos, pygame.BUTTON_LEFT)
        if selected_option:
            self.handle_context_menu_selection(selected_option)
            self.context_menu.hide()
        else:
            self.context_menu.hide()

    def handle_mouse_wheel(self, event: pygame.event.Event):
        """Handle mouse wheel events."""
        if self.inventory_ui.active:
            self.inventory_ui.handle_scroll(-event.y)
        else:
            self.message_log.scroll(-event.y)

    def handle_main_menu_events(self, event: pygame.event.Event):
        """
        Handle input for the main menu.
        """
        action = self.menu_manager.handle_input(event, self.mouse_pos)

        if action == GameStates.START:
            self.init_game_elements()
            self.state_manager.push_state(GameStates.GAME)
        elif action == GameStates.QUIT_GAME:
            self.quit_game()

    def handle_paused_events(self, event: pygame.event.Event, now: int):
        """
        Handle input when the game is paused.
        """
        action = self.menu_manager.handle_input(event, self.mouse_pos)

        if action == GameStates.RESUME:
            self.state_manager.pop_state()  # Return to the GAME state
        elif action == GameStates.RESTART:
            self.restart()
        elif action == GameStates.QUIT_TO_MAIN_MENU:
            self.state_manager.reset_stack()
            self.state_manager.push_state(GameStates.MAIN_MENU)

    def handle_game_events(self, event: pygame.event.Event, now: int):
        """
        Handle input for the active GAME state.
        """
        if self.loading == True: 
            return

        if event.type == pygame.KEYDOWN:
            # Pause the game
            if event.key == pygame.K_ESCAPE:
                self.state_manager.push_state(GameStates.PAUSED)
                self.menu_manager.open_pause_menu()

            keys = pygame.key.get_pressed()
            self.player.handle_movement_input(keys, now, self.map, self.enemies)
            self.handle_keydown(event)
            if isinstance(self.player, Developer):
                if event.key == pygame.K_F1:
                    self.toggle_debug_mode()
                elif event.key == pygame.K_F12:
                    self.dev_menu.toggle()
                elif event.key == pygame.K_BACKQUOTE:
                    self.dev_console.toggle()


        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_button(event)

        if event.type == pygame.MOUSEWHEEL:
            self.handle_mouse_wheel(event)


    def handle_context_menu_selection(self, selected_option: str) -> None:
        """
        Handle the player's selection in the context menu.
        """
        if selected_option == "Interact":
            ...
        elif selected_option == "Use":
            logger.debug("User selected 'Use'.")
            self.handle_use_option()
        elif selected_option == "Examine":
            logger.debug("User selected 'Examine'.")
            self.handle_examine_option()
        elif selected_option == "Drop":
            logger.debug("User selected 'Drop'.")
            self.handle_drop_option()
        else:
            logger.warning(f"Unhandled context menu option: {selected_option}")

    def handle_use_option(self) -> None:
        """
        Handle 'Use' option - use an item or interact with a tile.
        """
        if self.context_menu.tile:
            if self.context_menu.tile.tile_type == TileType.WATER:
                self.context_menu.tile.interact(self.player)
                self.message_log.add_message("You drink from the water. +2 Water")
            else:
                self.message_log.add_message("Nothing to interact with.")

        elif self.context_menu.item:
            if self.context_menu.item:
                item = self.context_menu.item[0]
                self.message_log.add_message(item.use(self.player))
                self.player.remove_from_inventory(item.name)
            else:
                self.message_log.add_message("You can't use that.")

    def handle_examine_option(self) -> None:
        """Handle 'Examine' option - display info about a tile or item."""
        if self.context_menu.tile:
            # Examine a tile
            self.message_log.add_message(f"{self.context_menu.tile.examine()}")
            self.message_log.add_message(f"{self.context_menu.tile.description}")
        if self.context_menu.item:
            self.message_log.add_message(f"{self.context_menu.item[0].description}")

        return

    def handle_drop_option(self) -> None:
        """Handle dropping an item from the inventory."""
        self.player.drop_item(self.context_menu.item[0].name, self.map.get_tile_at_xy(self.player.x, self.player.y))

    def get_tile_coords_under_cursor(self, mouse_x: int, mouse_y: int) -> tuple:
        """Get the tile at the mouse position, in map coordinates."""
        # Adjust for camera offset (convert screen coordinates to map coordinates)
        adjusted_x = mouse_x + int(self.camera.offset_x)
        adjusted_y = mouse_y + int(self.camera.offset_y)

        # Convert adjusted pixel coordinates to grid coordinates (tile indices)
        tile_x = adjusted_x // self.tile_size
        tile_y = adjusted_y // self.tile_size

        # Ensure the coordinates are within bounds of the map
        if 0 <= tile_x < self.map.width and 0 <= tile_y < self.map.height:
            tile = self.map.get_tile_at_xy(tile_x, tile_y)
            return tile, tile.x, tile.y

        # Return None if out of bounds
        return None, None, None

    def update(self, delta_time: int) -> None:
        """
        Update the game world state, compute FOV, and update visible entities.
        """
        now = pygame.time.get_ticks()
        if self.state_manager.current_state() == GameStates.GAME and self.player and self.map:
            # Update player FOV and stats
            self.time_system.update()
            self.player.compute_fov(self.map)
            self.player.update_stats()
            self.player.update_status_effects()
            # Update visible enemies only
            for enemy in self.enemies:
                if self.camera.in_view(enemy.x, enemy.y) and self.map.visible_map[enemy.y][enemy.x]:
                    enemy.update(self.player, self.entities, self.map, now)

            # Update camera position
            self.camera.update(self.player, self.map.width, self.map.height, SCREEN_HEIGHT - 150, -240)

    def render(self) -> None:
        self.screen.fill((0, 0, 0))

        for state in self.state_manager.state_stack:
            if self.state_manager.current_state() == GameStates.MAIN_MENU:
                self.menu_manager.open_main_menu()
                self.menu_manager.render(self.mouse_pos)
            elif self.state_manager.current_state() == GameStates.PAUSED:
                self.menu_manager.open_pause_menu()
                self.menu_manager.render(self.mouse_pos)
            elif state == GameStates.GAME:
                self.render_game()
            elif state == GameStates.DEV_MENU:
                self.dev_menu.render(self.screen)
            elif state == GameStates.DEV_CONSOLE:
                self.dev_console.render(self.screen)
            
        self.render_debug_info() if self.show_debug else ...

        pygame.display.flip()
        pygame.display.update()

    def render_game(self) -> None:
        """
        Render the game, including the map, entities, and UI components.
        """
        if not self.map:
            self.init_game_elements()
            if self.loading:
                return  # Avoid rendering until map generation is complete

        # Render the map
        self.map.render(screen=self.screen, camera=self.camera)

        # Render all entities within the player's field of view
        for entity in self.entities:
            if self.map.visible_map[entity.y][entity.x] and self.camera.in_view(entity.x, entity.y):
                screen_x, screen_y = self.camera.apply(entity.x * self.tile_size, entity.y * self.tile_size)
                entity.render(self.screen, screen_x, screen_y, self.show_debug)

        # Render the message log
        if self.message_log:
            self.message_log.render(self.screen)

        # Render active UI components

        if self.inventory_ui and self.inventory_ui.active:
            self.inventory_ui.render(self.screen, self.mouse_pos)

        if self.help_screen and self.help_screen.active:
            self.help_screen.render(self.screen)

        if self.character_ui:
            self.character_ui.render(self.screen, self.mouse_pos)

        if self.context_menu.active:
            self.context_menu.render(self.screen, self.mouse_pos)
        # Render game time at the top left
        game_time = self.time_system.get_time_string()
        time_surface = self.mfont.render(f"{game_time}", True, (255, 255, 255))
        self.screen.blit(time_surface, (10, 10))


    def toggle_debug_mode(self):
        self.show_debug = not self.show_debug

    def render_debug_info(self) -> None:
        """
        Render debug information to the screen if debug mode is enabled.
        """
        if not self.show_debug:
            return

        debug_info = [
            f"FPS: {int(self.clock.get_fps())}",
            f"Game State: {self.state_manager.current_state()}",
            f"Camera Offset: ({self.camera.offset_x:.2f}, {self.camera.offset_y:.2f})"
            if self.camera else "Camera not initialized",
        ]

        for i, info in enumerate(debug_info):
            debug_surface = self.mfont.render(info, True, (255, 0, 0), (0, 0, 0))
            self.screen.blit(debug_surface, (10, 30 + i * 20))


    def toggle_all_ui(self) -> None:
        """
        Toggle all UI elements on or off.
        """
        any_ui_active = any(
            ui.active for ui in [
                self.help_screen,
                self.character_ui,
                self.message_log,
                self.inventory_ui
            ]
        )

        new_state = not any_ui_active
        self.help_screen.active = new_state
        self.character_ui.active = new_state
        self.message_log.active = new_state
        self.inventory_ui.active = False  # Inventory is managed separately

    def toggle_dev_menu(self) -> None:
        """
        Toggle the developer menu.
        """
        if self.state_manager.current_state() == GameStates.DEV_MENU:
            self.state_manager.pop_state()
        else:
            self.state_manager.push_state(GameStates.DEV_MENU)

    def toggle_dev_console(self) -> None:
        """
        Toggle the Developer Console on or off.
        """
        if self.dev_console:
            self.dev_console.toggle()
