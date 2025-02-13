import pygame
from objects import Particle
from config import UI

# --------------------------
# Particle Creation Utility
# --------------------------

def create_particles(position, color):
    """Create a burst of particles at a given position."""
    return [Particle(position, color) for _ in range(20)]

# --------------------------
# UI Rendering Utilities
# --------------------------

def draw_button(surface, rect, text, font, base_color, hover_color):
    """Modern neomorphic button design"""
    mouse_pos = pygame.mouse.get_pos()
    is_hovered = rect.collidepoint(mouse_pos)
    
    # Shadow
    shadow_offset = 8 if is_hovered else 5
    shadow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 50 if is_hovered else 30), 
                    shadow_surface.get_rect(), border_radius=UI["button_radius"])
    surface.blit(shadow_surface, (rect.x - shadow_offset/2, rect.y + shadow_offset/2))
    
    # Main button
    color = hover_color if is_hovered else base_color
    pygame.draw.rect(surface, color, rect, border_radius=UI["button_radius"])
    
    # Inner highlight
    highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(highlight, (255, 255, 255, 30), 
                    highlight.get_rect().inflate(-10, -10), 
                    border_radius=UI["button_radius"]-5)
    surface.blit(highlight, rect.topleft)
    
    # Text
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=rect.center)
    surface.blit(text_surface, text_rect)

def draw_gradient_background(surface, top_color, bottom_color):
    """Optimized gradient using rects"""
    gradient_rect = pygame.Rect(0, 0, surface.get_width(), surface.get_height())
    pygame.draw.rect(
        surface,
        top_color,
        gradient_rect
    )
    steps = 100
    for i in range(steps):
        ratio = i / steps
        blended_color = (
            int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio),
            int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio),
            int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        )
        rect = pygame.Rect(0, int(i * surface.get_height() / steps), surface.get_width(), int(surface.get_height() / steps))
        pygame.draw.rect(surface, blended_color, rect)

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