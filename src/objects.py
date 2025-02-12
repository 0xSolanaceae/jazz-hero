import pygame
import random
from pygame.math import Vector2
from config import (
    SCREEN_WIDTH, NOTE_SPEED, 
    lane_positions, lane_colors
)

class Particle:
    def __init__(self, position, color):
        self.pos = Vector2(position)
        self.color = color
        self.velocity = Vector2(random.uniform(-3, 3), random.uniform(-3, 3))
        self.lifetime = 255
        self.size = random.randint(3, 6)

    def update(self):
        self.pos += self.velocity
        self.lifetime -= 8
        self.size = max(self.size - 0.1, 1)

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = min(self.lifetime, 255)
            radius = int(self.size)
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
            surface.blit(s, (self.pos.x - radius, self.pos.y - radius))

class ShortNote:
    def __init__(self, lane):
        self.lane = lane
        self.pos = Vector2(SCREEN_WIDTH + 50, lane_positions[lane])
        self.color = lane_colors[lane]
        self.active = True
        self.hit = False
        self.chord_id = None

    def update(self, dt):
        self.pos.x -= NOTE_SPEED * dt
        if self.pos.x < -50:
            self.active = False

    def draw(self, surface):
        if self.active:
            glow_size = 80
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow.fill((0, 0, 0, 0))
            for i in range(10):
                alpha = max(255 - i * 25, 0)
                radius = 20 + i * 3
                pygame.draw.circle(glow, (*self.color, alpha), (glow_size//2, glow_size//2), radius)
            mask = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255), (glow_size//2, glow_size//2), glow_size//2)
            glow.blit(mask, (0, 0), None, pygame.BLEND_RGBA_MULT)
            surface.blit(glow, (int(self.pos.x)-glow_size//2, int(self.pos.y)-glow_size//2))
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), 20)

class LongNote:
    def __init__(self, lane, length):
        self.lane = lane
        self.length = length
        self.pos = Vector2(SCREEN_WIDTH + 50, lane_positions[lane])
        self.tail_x = self.pos.x + length
        self.color = lane_colors[lane]
        self.active = True
        self.held = False
        self.completed = False
        self.hold_progress = 0.0
        self.start_hold_time = 0
        self.chord_id = None

    def update(self, dt):
        self.pos.x -= NOTE_SPEED * dt
        self.tail_x -= NOTE_SPEED * dt
        if self.tail_x < -50:
            self.active = False

    def draw(self, surface):
        if self.active:
            body_width = self.tail_x - self.pos.x
            pygame.draw.rect(surface, self.color, (self.pos.x, self.pos.y-20, body_width, 40))
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), 20)
            pygame.draw.circle(surface, self.color, (int(self.tail_x), int(self.pos.y)), 20)
            if self.held:
                progress_width = body_width * self.hold_progress
                progress_surface = pygame.Surface((int(progress_width), 40), pygame.SRCALPHA)
                progress_surface.fill((255, 255, 255, 128))
                surface.blit(progress_surface, (self.pos.x, self.pos.y-20))

class HitPopup:
    def __init__(self, text, position, color):
        self.text = text
        self.pos = Vector2(position)
        self.lifetime = 1.0
        self.max_lifetime = 1.0
        self.font = pygame.font.SysFont("Segoe UI", 36)
        self.color = color

    def update(self, dt):
        self.lifetime -= dt
        self.pos.y -= 30 * dt

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            text_surface = self.font.render(self.text, True, self.color)
            text_surface.set_alpha(alpha)
            rect = text_surface.get_rect(center=(self.pos.x, self.pos.y))
            surface.blit(text_surface, rect)