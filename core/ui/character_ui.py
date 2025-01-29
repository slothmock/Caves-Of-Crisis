import pygame

from core import logging
from core.status_effects.status_effects import StatusSeverity


class CharacterUI:
    """
    Class to render the character UI at the top-right corner of the screen, including an avatar box.
    Dynamically fetches data from a linked BaseCharacter instance.
    """

    def __init__(self, screen_width, font, bg_color=(50, 50, 50), border_color=(200, 200, 200)):
        """
        Initialize the Character UI.
        :param screen_width: The width of the game screen.
        :param font: Pygame font for rendering text.
        :param bg_color: Background color of the UI.
        :param border_color: Border color of the UI.
        """
        self.x = screen_width - 260
        self.y = 10
        self.width = 250
        self.height = 320
        self.font = font
        self.bg_color = bg_color
        self.border_color = border_color
        self.character = None  # BaseCharacter instance to fetch data from
        self.active = True

        # Avatar settings
        self.avatar = None
        self.avatar_box = pygame.Rect(self.x + 10, self.y + 10, 64, 64)  # 64x64 box for the avatar

        # Status Icons
        self.status_icons = {}

    def set_character(self, character):
        """
        Link a BaseCharacter instance to fetch stats dynamically.
        :param character: A BaseCharacter object (Player, Enemy, etc.).
        """
        self.character = character

    def set_avatar(self, avatar_path):
        """
        Set the avatar image from a file path.
        :param avatar_path: Path to the avatar image file.
        """
        try:
            self.avatar = pygame.image.load(avatar_path)
            self.avatar = pygame.transform.scale(self.avatar, (64, 64))
        except pygame.error:
            logging.logger.error(f"Error loading avatar image: {avatar_path}")
            self.avatar = None

    def load_status_icons(self):
        """Load status effect icons into memory."""
        try:
            self.status_icons = {
                "Dev": pygame.image.load("assets/img/status_icons/dev.png"),
                "Hunger": pygame.image.load("assets/img/status_icons/food.png"),
                "Thirst": pygame.image.load("assets/img/status_icons/water.png"),
                "Stamina": pygame.image.load("assets/img/status_icons/stamina.png"),
                "Sleep": pygame.image.load("assets/img/status_icons/sleep.png"),
                "Wet": pygame.image.load("assets/img/status_icons/wet.png"),
            }
        except pygame.error as e:
            logging.logger.error(f"Error loading status icons: {e}")

    def toggle(self):
        self.active = not self.active

    def render(self, screen, mouse_pos):
        """
        Render the character UI.
        :param screen: The Pygame screen to render to.
        """
        if not self.active:
            return
        if not self.character:
            return  # Do nothing if no character is linked

        # Draw the background
        pygame.draw.rect(screen, self.bg_color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(screen, self.border_color, (self.x, self.y, self.width, self.height), 3)  # Border

        # Render the avatar box
        self.render_avatar(screen)

        # Render character name and level
        name_surface = self.font.render(f"{self.character.name} (Lvl {self.character.level})", True, (255, 255, 255))
        screen.blit(name_surface, (self.x + 80, self.y + 10))  # Positioned next to the avatar

        # Render character xp and next level xp
        xp_surface = self.font.render(f"{self.character.experience}/{self.character.next_level_experience} EXP", True, (255, 255, 255))
        screen.blit(xp_surface, (self.x + 80, self.y + 30))  # Positioned next to the avatar

        # Render health bar
        self.render_bar(
            screen,
            int(self.character.health),
            self.character.max_health,
            self.x + 10,
            self.y + 100,
            230,
            20,
            (200, 50, 50),
            "Health",
        )

        # Render food bar
        self.render_bar(
            screen,
            int(self.character.food),
            self.character.max_food,
            self.x + 10,
            self.y + 145,
            230,
            20,
            (50, 200, 50),
            "Food",
        )

        # Render water bar
        self.render_bar(
            screen,
            int(self.character.water),
            self.character.max_water,
            self.x + 10,
            self.y + 190,
            230,
            20,
            (50, 100, 255),
            "Water",
        )

        # Render stamina bar
        self.render_bar(
            screen,
            int(self.character.stamina),
            self.character.max_stamina,
            self.x + 10,
            self.y + 235,
            230,
            20,
            (240, 205, 60),
            "Stamina",
        )

        # Render sleep bar
        self.render_bar(
            screen,
            int(self.character.sleep),
            self.character.max_sleep,
            self.x + 10,
            self.y + 280,
            230,
            20,
            (150, 150, 255),
            "Sleep",
        )

        # Render status effect icons
        self.render_status_icons(screen, mouse_pos)

    def render_avatar(self, screen):
        """
        Render the avatar image or a placeholder box if no image is provided.
        :param screen: The Pygame screen to render to.
        """
        if self.avatar:
            screen.blit(self.avatar, (self.avatar_box.x, self.avatar_box.y))
        else:
            # Draw a placeholder box
            pygame.draw.rect(screen, (100, 100, 100), self.avatar_box)
            pygame.draw.rect(screen, (255, 255, 255), self.avatar_box, 2)
            placeholder_text = self.font.render("No Avatar", True, (255, 255, 255))
            text_rect = placeholder_text.get_rect(center=self.avatar_box.center)
            screen.blit(placeholder_text, text_rect)

    def render_status_icons(self, screen, mouse_pos):
        """
        Render status effect icons below the stats, with tooltips on hover.
        
        Args:
            screen (pygame.Surface): The Pygame screen to render to.
            mouse_pos (tuple): The current position of the mouse (x, y).
        """
        if not self.character or not self.character.status_effects:
            return
        

        icon_size = 32
        y_offset = self.y  # Start position for icon box
        padding = 2  # Padding around icons
        icon_x = self.x - icon_size + padding
        icon_size_with_padding = icon_size - padding * 2

        for effect_name, effect_data in self.character.status_effects.effects.items():
            # Retrieve the icon for the effect
            icon = self.status_icons.get(effect_name.capitalize())
            time_remaining = self.character.status_effects.get_time_remaining(effect_name)

            if not icon:
                logging.logger.warning(f"Icon not found for {effect_name}")
                continue

            # Scale and draw the icon
            icon = pygame.transform.scale(icon, (icon_size_with_padding, icon_size_with_padding))
            icon_rect = pygame.Rect(self.x - icon_size, y_offset, icon_size, icon_size)

            pygame.draw.rect(screen, (50, 50, 50), icon_rect)  # Background
            pygame.draw.rect(screen, effect_data["severity"].color, icon_rect, 3)  # Border
            screen.blit(icon, (icon_x, y_offset + 3))

            # Move to the next icon position
            y_offset += icon_size + padding

            # Check if the mouse is hovering over the icon
            if time_remaining is not None and time_remaining > 0:
                description = f"{effect_data.get('description', 'No details available.')} Time Remaining: {time_remaining}"
            else:
                description = f"{effect_data.get('description', 'No details available.')}"

            if icon_rect.collidepoint(mouse_pos):
                self.render_tooltip(
                    screen=screen,
                    mouse_pos=mouse_pos,
                    title=effect_name,
                    description=description,
                )


    def render_tooltip(self, screen, mouse_pos, title, description):
        """
        Render a tooltip for a status effect.
        :param screen: The Pygame screen to render to.
        :param mouse_pos: The current position of the mouse (tuple of x, y).
        :param title: The title of the status effect.
        :param description: The description of the status effect.
        """
        # Fonts for title and description
        title_font = pygame.font.Font(None, 22)
        desc_font = pygame.font.Font(None, 18)

        title_surface = title_font.render(title, True, (255, 255, 255))
        desc_surface = desc_font.render(description, True, (200, 200, 200))

        # Tooltip dimensions
        padding = 5
        tooltip_width = max(title_surface.get_width(), desc_surface.get_width()) + padding * 2
        tooltip_height = title_surface.get_height() + desc_surface.get_height() + padding * 3
        tooltip_x = min(mouse_pos[0] + 10, self.x + self.width - tooltip_width)
        tooltip_y = max(mouse_pos[1] - tooltip_height - 10, self.y)

        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)

        # Render background and border
        pygame.draw.rect(screen, (50, 50, 50), tooltip_rect)
        pygame.draw.rect(screen, (200, 200, 200), tooltip_rect, 2)

        # Render title and description
        screen.blit(title_surface, (tooltip_x + padding, tooltip_y + padding))
        screen.blit(desc_surface, (tooltip_x + padding, tooltip_y + padding + title_surface.get_height()))


    def render_bar(self, screen, current, maximum, x, y, width, height, color, label):
        """
        Render a status bar (health, stamina, food, water, sleep).
        :param screen: The Pygame screen to render to.
        :param current: Current value of the stat.
        :param maximum: Maximum value of the stat.
        :param x: X-coordinate of the bar.
        :param y: Y-coordinate of the bar.
        :param width: Width of the bar.
        :param height: Height of the bar.
        :param color: Color of the bar.
        :param label: Label for the bar (e.g., "HP").
        """
        # Calculate bar width
        try:
            fill_width = int((current / maximum) * width)
        except ZeroDivisionError:
            fill_width = 0
        pygame.draw.rect(screen, color, (x, y, fill_width, height))  # Filled bar
        pygame.draw.rect(screen, (255, 255, 255), (x, y, width, height), 2)  # Outline

        # Render the label
        label_surface = self.font.render(f"{label}: {current}/{maximum}", True, (255, 255, 255))
        screen.blit(label_surface, (x, y - 20))  # Positioned above the bar