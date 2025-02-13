import pygame
import math
from config import RUSH_MAX, RUSH_BAR_WIDTH, RUSH_BAR_HEIGHT, RUSH_BAR_X, RUSH_BAR_Y, SCREEN_WIDTH

def draw_rush_bar(surface, rush_value, rush_active):
    bar_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y, RUSH_BAR_WIDTH, RUSH_BAR_HEIGHT)
    pygame.draw.rect(surface, (30, 30, 30), bar_rect, border_radius=10)
    pygame.draw.rect(surface, (80, 80, 80), bar_rect, width=3, border_radius=10)

    fill_height = int((rush_value / RUSH_MAX) * RUSH_BAR_HEIGHT)
    fill_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height, RUSH_BAR_WIDTH, fill_height)

    fill_surface = pygame.Surface((RUSH_BAR_WIDTH, fill_height), pygame.SRCALPHA)
    for y in range(fill_height):
        if rush_active:
            pulsate = (math.sin((pygame.time.get_ticks() / 100) + (y / RUSH_BAR_HEIGHT) * math.pi) + 1) / 2
            r, g, b = 255, int(100 + pulsate * 155), int(100 + pulsate * 155)
        else:
            ratio = y / fill_height
            r, g, b = 50, int(200 - 50 * ratio), int(255 - 100 * ratio)
        pygame.draw.line(fill_surface, (r, g, b), (0, y), (RUSH_BAR_WIDTH, y))

    surface.blit(fill_surface, (RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height))
    pygame.draw.rect(surface, (255, 255, 255, 50), fill_rect, width=2, border_radius=5)

    if rush_active and fill_height > 0:
        rush_shine(fill_height, surface)

    # Modern label with shadow
    label_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
    label = label_font.render("RUSH", True, (255, 255, 255))
    label_shadow = label_font.render("RUSH", True, (0, 0, 0))
    label_rect = label.get_rect(center=(RUSH_BAR_X + RUSH_BAR_WIDTH // 2, RUSH_BAR_Y - 20))
    surface.blit(label_shadow, label_rect.move(2, 2))
    surface.blit(label, label_rect)

    if rush_active:
        rush_label = pygame.font.SysFont("Segoe UI", 28, bold=True).render("RUSH MODE!", True, (255, 50, 50))
        rush_label_shadow = pygame.font.SysFont("Segoe UI", 28, bold=True).render("RUSH MODE!", True, (0, 0, 0))
        rush_label_rect = rush_label.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(rush_label_shadow, rush_label_rect.move(2, 2))
        surface.blit(rush_label, rush_label_rect)

def rush_shine(fill_height, surface):
    shine_height = 10
    shine_offset = (pygame.time.get_ticks() // 5) % (fill_height + shine_height) - shine_height
    shine_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height + shine_offset, RUSH_BAR_WIDTH, shine_height)
    shine_surface = pygame.Surface((RUSH_BAR_WIDTH, shine_height), pygame.SRCALPHA)
    for y in range(shine_height):
        alpha = max(0, 150 - abs(y - shine_height // 2) * 30)
        pygame.draw.line(shine_surface, (255, 255, 255, alpha), (0, y), (RUSH_BAR_WIDTH, y))
    surface.blit(shine_surface, shine_rect.topleft)