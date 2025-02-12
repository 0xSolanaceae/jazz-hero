import pygame
import sys
import random
from pygame.math import Vector2
from config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS, FPS
from utils import draw_gradient_background, draw_button
from objects import Particle

def charting_menu(screen):
    """Placeholder charting menu. Press ESC to return to the main menu."""
    charting_running = True
    charting_font = pygame.font.SysFont("Segoe UI", 50)
    clock = pygame.time.Clock()
    
    while charting_running:
        screen.fill(COLORS['background'])
        charting_text = charting_font.render("Charting Mode Placeholder - Press ESC to return", True, COLORS['text'])
        charting_rect = charting_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(charting_text, charting_rect)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    charting_running = False
        
        pygame.display.flip()
        clock.tick(FPS)

def main_menu(screen):
    """Modern main menu with animated background, drop-shadow title, and interactive buttons."""
    menu_running = True
    menu_options = ["Play", "Charting", "Exit"]
    title = "Jazz Hero"
    title_font = pygame.font.SysFont("Segoe UI", 100, bold=True)
    button_font = pygame.font.SysFont("Segoe UI", 40, bold=True)
    credits_font = pygame.font.SysFont("Segoe UI", 24)
    clock = pygame.time.Clock()

    button_width = 300
    button_height = 60
    button_spacing = 80
    buttons = []
    start_y = SCREEN_HEIGHT // 2
    for i, option in enumerate(menu_options):
        rect = pygame.Rect(0, 0, button_width, button_height)
        rect.center = (SCREEN_WIDTH // 2, start_y + i * button_spacing)
        buttons.append((option, rect))

    menu_particles = []
    particle_spawn_timer = 0
    particle_spawn_interval = 100  # ms

    while menu_running:
        clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for option, rect in buttons:
                    if rect.collidepoint(mouse_pos):
                        if option == "Play":
                            menu_running = False
                        elif option == "Charting":
                            charting_menu(screen)
                        elif option == "Exit":
                            pygame.quit()
                            sys.exit()

        if current_time - particle_spawn_timer > particle_spawn_interval:
            particle_spawn_timer = current_time
            pos = Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT - 50)
            p = Particle(pos, (255, 255, 255))
            p.velocity = Vector2(random.uniform(-0.5, 0.5), -random.uniform(0.5, 1.5))
            p.lifetime = 300
            p.size = random.randint(2, 4)
            menu_particles.append(p)

        menu_particles = [p for p in menu_particles if p.lifetime > 0]
        for p in menu_particles:
            p.update()

        draw_gradient_background(screen, (100, 100, 150), (150, 100, 180))

        for p in menu_particles:
            p.draw(screen)

        shadow_offset = Vector2(4, 4)
        shadow_surface = title_font.render(title, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH//2 + shadow_offset.x, SCREEN_HEIGHT//4 + shadow_offset.y))
        screen.blit(shadow_surface, shadow_rect)
        title_surface = title_font.render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//4))
        screen.blit(title_surface, title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for option, rect in buttons:
            hovered = rect.collidepoint(mouse_pos)
            draw_button(screen, rect, option, button_font,
                        base_color=(50, 50, 80),
                        hover_color=(80, 80, 120),
                        text_color=(255, 255, 255),
                        is_hovered=hovered)

        credits_text = credits_font.render("Built by Gio & Miles", True, (200, 200, 200))
        credits_rect = credits_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT-30))
        screen.blit(credits_text, credits_rect)

        pygame.display.flip()