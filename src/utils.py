import pygame
from objects import Particle

# --------------------------
# Particle Creation Utility
# --------------------------

def create_particles(position, color):
    """Create a burst of particles at a given position."""
    return [Particle(position, color) for _ in range(20)]

# --------------------------
# UI Rendering Utilities
# --------------------------

def draw_gradient_background(surface, top_color, bottom_color):
    """Draw a vertical gradient background."""
    height = surface.get_height()
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        pygame.draw.line(surface, (r, g, b), (0, y), (surface.get_width(), y))

def draw_button(surface, rect, text, font, base_color, hover_color, text_color, is_hovered):
    """Draw an interactive button with hover effects."""
    color = hover_color if is_hovered else base_color
    pygame.draw.rect(surface, color, rect, border_radius=12)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2, border_radius=12)
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

# --------------------------
# Game Flow Utilities
# --------------------------

def countdown_timer(screen, background_color, font_color=(255, 255, 255), go_color=(0, 255, 0)):
    """Display a 3-second countdown with GO! animation."""
    countdown_seconds = 3
    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()
    font_large = pygame.font.SysFont("Segoe UI", 150, bold=True)
    
    while True:
        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000
        if elapsed >= countdown_seconds:
            break

        # Handle quit events during countdown
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Render countdown numbers
        countdown_value = countdown_seconds - int(elapsed)
        screen.fill(background_color)
        countdown_text = font_large.render(str(countdown_value), True, font_color)
        text_rect = countdown_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
        screen.blit(countdown_text, text_rect)
        pygame.display.flip()
        clock.tick(60)

    # Show GO! message
    screen.fill(background_color)
    go_text = font_large.render("GO!", True, go_color)
    go_rect = go_text.get_rect(center=(screen.get_width()//2, screen.get_height()//2))
    screen.blit(go_text, go_rect)
    pygame.display.flip()
    pygame.time.delay(500)