import pygame

from core.settings import TILE_SIZE

class Entity:
    def __init__(self, x, y, char, color, tile_size=TILE_SIZE):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.tile_size = tile_size

    def render(self, screen, screen_x, screen_y):
        """Render the entity at the specified screen position."""
        rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
        pygame.draw.rect(screen, self.color, rect)
        font = pygame.font.Font(None, 32)
        text = font.render(self.char, True, (0, 0, 0))
        screen.blit(text, rect.topleft)

    def check_collision(self, other_entities):
        """
        Check if this entity collides with any other entity.
        :param other_entities: List of other entities to check collision against.
        :return: The entity it collides with, or None if no collision.
        """
        for entity in other_entities:
            if self != entity and self.x == entity.x and self.y == entity.y:
                return entity
        return None
