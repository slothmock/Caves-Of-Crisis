import random
import pygame

def render_loading_screen(screen, font, stage_label, target_stage_progress, overall_progress, current_progress):
    """
    Render an animated loading screen with continuous updates, smooth progress animation, and immersive messages.
    """
    clock = pygame.time.Clock()
    animation_speed = 0.008  # Smooth animation

    # **Dynamic Messages Based on Progress**
    early_stage_messages = [
        "Mapping uncharted depths...",
        "Carving out passageways...",
        "Winds carve new tunnels...",
        "Echoes whisper in the darkness...",
    ]
    mid_stage_messages = [
        "Reinforcing cave walls...",
        "Shaping underground paths...",
        "Collapsing unstable tunnels...",
        "Taming the wild darkness...",
    ]
    late_stage_messages = [
        "Scattering forgotten relics...",
        "Light struggles to find a way...",
        "Ancient structures take shape...",
        "Finalizing the cavern’s mysteries...",
    ]

    # **Determine message category based on overall progress**
    if overall_progress < 0.3:
        message_pool = early_stage_messages
    elif overall_progress < 0.7:
        message_pool = mid_stage_messages
    else:
        message_pool = late_stage_messages

    last_message = random.choice(message_pool)  # Initial message selection

    while current_progress < target_stage_progress:
        current_progress += animation_speed
        current_progress = min(current_progress, target_stage_progress)  # Clamp value

        screen.fill((0, 0, 0))  # Clear screen

        # **Update stage-specific message dynamically every 5% progress**
        if int(current_progress * 100) % 5 == 0:
            last_message = random.choice(message_pool)

        # **Render Stage-Specific Message (Top Bar)**
        stage_text = f"{last_message} {int(current_progress * 100)}%"
        stage_surface = font.render(stage_text, True, (255, 255, 255))
        stage_rect = stage_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 - 60))
        screen.blit(stage_surface, stage_rect)

        # **Render Stage Progress Bar**
        bar_width, bar_height = 400, 20
        bar_x, bar_y = screen.get_width() // 2 - bar_width // 2, screen.get_height() // 2 - 30
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))  # Background
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, int(bar_width * current_progress), bar_height))  # Green bar

        # **Render Stage Label on Overall Progress Bar (Bottom)**
        overall_text = f"{stage_label} - Overall Progress: {int(overall_progress * 100)}%"
        overall_surface = font.render(overall_text, True, (200, 200, 200))
        overall_rect = overall_surface.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2 + 20))
        screen.blit(overall_surface, overall_rect)

        # **Render Overall Progress Bar**
        overall_bar_y = screen.get_height() // 2 + 50
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, overall_bar_y, bar_width, bar_height))  # Background
        pygame.draw.rect(screen, (255, 165, 0), (bar_x, overall_bar_y, int(bar_width * overall_progress), bar_height))  # Orange bar

        pygame.display.flip()  # Update screen
        clock.tick(60)  # Limit frame rate

    return current_progress


def update_progress(screen, font, stage_label, step_index, step_progress, total_steps, current_progress) -> float:
    """
    Updates the loading screen with continuous progress tracking.

    Args:
        screen (pygame.Surface): The screen to render the loading screen on.
        font (pygame.font.Font): Font for rendering text.
        stage_label (str): Current stage description.
        step_index (int): Step index of the generation process.
        step_progress (float): Progress within the current step (0.0 - 1.0).
        total_steps (int): Total number of steps.
        progress (float): The current progress state.

    Returns:
        float: Updated overall progress.
    """
    overall_progress = (step_index + step_progress) / total_steps
    return render_loading_screen(screen, font, stage_label, step_progress, overall_progress, current_progress)
