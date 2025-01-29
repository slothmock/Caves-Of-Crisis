import pygame

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
        dots = ". " * (int(pygame.time.get_ticks() / 400) % 4)  # Cycle through "", ".", "..", "..."
        animated_label = font.render(label + dots, True, (255, 255, 255))
        screen.blit(animated_label, label_rect)

        pygame.display.flip()  # Update the display
        clock.tick(60)  # Cap the frame rate

    return current_progress