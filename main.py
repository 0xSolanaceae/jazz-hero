import sys
import random
import math
import pygame
from pygame.math import Vector2

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jazz Hero")

FPS = 60
NOTE_SPEED = 600
SPAWN_INTERVAL = 1000
COMBO_FADE_TIME = 2000

# Increased hit window makes it easier to register an OK hit.
HIT_WINDOW = 60  

# New timing thresholds (in pixels) for grading hits:
PERFECT_THRESHOLD = 10   # Dead-center
GOOD_THRESHOLD = 25      # Slightly off-center

main_keys = ['a', 's', 'd']

COLORS = {
    'background': (15, 15, 25),
    'track': (30, 30, 40),
    'hit_effect': (255, 200, 100),
    'text': (240, 240, 240),
    'combo': (255, 215, 0)
}

lane_colors = [
    (255, 255, 0),  # Yellow for top lane
    (255, 0, 0),    # Red for middle lane
    (0, 255, 0)     # Green for bottom lane
]

NUM_LANES = 3
LANE_HEIGHT = 60
LANE_SPACING = 80
TRACK_WIDTH = SCREEN_WIDTH - 400
HIT_ZONE_X = 200

track_top = 50
track_bottom = SCREEN_HEIGHT - 50
track_height = track_bottom - track_top

lane_positions = []
for i in range(NUM_LANES):
    lane_center_y = track_top + (i + 0.5) * (track_height / NUM_LANES)
    lane_positions.append(lane_center_y)

# --- Rush Bar Constants and Variables ---
RUSH_MAX = 150  # Increased maximum required for rush mode
rush_meter = 0
in_rush_mode = False

RUSH_GAIN_PER_HIT_NORMAL = 10   # Reduced gain per hit in normal mode
RUSH_GAIN_PER_HIT_RUSH = 3      # Reduced gain during rush mode
RUSH_DECAY_NORMAL = 5           # Drains slowly when not in rush mode (per second)
RUSH_DECAY_RUSH = 20            # Drains fast during rush mode (per second)
RUSH_MULTIPLIER = 2             # Extra multiplier on score during rush mode

# Rush bar UI position and size (now on the left side)
RUSH_BAR_WIDTH = 40
RUSH_BAR_HEIGHT = 300
RUSH_BAR_X = 50
RUSH_BAR_Y = (SCREEN_HEIGHT - RUSH_BAR_HEIGHT) // 2

# Lists for active notes, particles, and hit popups
notes = []
particles = []
hit_popups = []  # New list for our floating popup texts
score = 0
combo = 0
last_combo_time = 0
spawn_time = 0

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

class Note:
    def __init__(self, lane):
        self.lane = lane
        self.pos = Vector2(SCREEN_WIDTH + 50, lane_positions[lane])
        self.color = lane_colors[lane]
        self.active = True

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
                pygame.draw.circle(glow, (*self.color, alpha), (glow_size // 2, glow_size // 2), radius)
            
            mask = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255), (glow_size // 2, glow_size // 2), glow_size // 2)
            glow.blit(mask, (0, 0), None, pygame.BLEND_RGBA_MULT)
            surface.blit(glow, (int(self.pos.x) - glow_size // 2, int(self.pos.y) - glow_size // 2))
            
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), 20)

class HitPopup:
    """Floating text popup for rating hits (e.g., Perfect!, Good!, OK)."""
    def __init__(self, text, position, color):
        self.text = text
        self.pos = Vector2(position)
        self.lifetime = 1.0  # in seconds
        self.max_lifetime = 1.0
        self.font = pygame.font.Font(None, 36)
        self.color = color

    def update(self, dt):
        self.lifetime -= dt
        self.pos.y -= 30 * dt  # move upward

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = int(255 * (self.lifetime / self.max_lifetime))
            text_surface = self.font.render(self.text, True, self.color)
            text_surface.set_alpha(alpha)
            rect = text_surface.get_rect(center=(self.pos.x, self.pos.y))
            surface.blit(text_surface, rect)

def create_particles(position, color):
    for _ in range(20):
        particles.append(Particle(position, color))

def draw_track(surface):
    pygame.draw.rect(surface, COLORS['track'],
                     (150, 50, SCREEN_WIDTH - 150, SCREEN_HEIGHT - 100))
    
    gray_color = (128, 128, 128)
    
    circle_radius = 40
    left_line_x = HIT_ZONE_X - circle_radius
    right_line_x = HIT_ZONE_X + circle_radius

    # Draw lane lines starting from the right edge of the hit zone circles
    for y in lane_positions:
        pygame.draw.line(surface, gray_color, (right_line_x, int(y)), (SCREEN_WIDTH, int(y)), 3)

    line_color = (255, 255, 0)
    
    pygame.draw.line(surface, line_color, (left_line_x, 50), (left_line_x, SCREEN_HEIGHT - 50), 2)
    pygame.draw.line(surface, line_color, (right_line_x, 50), (right_line_x, SCREEN_HEIGHT - 50), 2)
    
    for i, y in enumerate(lane_positions):
        circle_center = (HIT_ZONE_X, int(y))
        pygame.draw.circle(surface, lane_colors[i], circle_center, circle_radius, 5)

def draw_ui(surface):
    score_text = pygame.font.Font(None, 48).render(f"SCORE: {score}", True, COLORS['text'])
    surface.blit(score_text, (20, 20))
    
    if pygame.time.get_ticks() - last_combo_time < COMBO_FADE_TIME:
        alpha = 255 * (1 - (pygame.time.get_ticks() - last_combo_time) / COMBO_FADE_TIME)
        combo_text = pygame.font.Font(None, 72).render(f"{combo}x COMBO!", True, (*COLORS['combo'], int(alpha)))
        combo_pos = combo_text.get_rect(centerx=SCREEN_WIDTH // 2, y=50)
        surface.blit(combo_text, combo_pos)

def draw_rush_bar(surface, rush_value, rush_active):
    # Draw the bar background
    bar_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y, RUSH_BAR_WIDTH, RUSH_BAR_HEIGHT)
    pygame.draw.rect(surface, (50, 50, 50), bar_rect)
    pygame.draw.rect(surface, (200, 200, 200), bar_rect, 3)
    
    # Calculate fill height (from bottom up)
    fill_height = (rush_value / RUSH_MAX) * RUSH_BAR_HEIGHT
    fill_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height, RUSH_BAR_WIDTH, fill_height)
    
    if rush_active:
        # Create a pulsating effect using sine
        pulsate = int((math.sin(pygame.time.get_ticks() / 100) + 1) * 50)  # 0 to 100
        fill_color = (255, min(255, 50 + pulsate), min(255, 50 + pulsate))
    else:
        fill_color = (50, 150, 255)
        
    pygame.draw.rect(surface, fill_color, fill_rect)
    
    # Label above the bar
    font = pygame.font.Font(None, 24)
    label = font.render("RUSH", True, (255, 255, 255))
    label_rect = label.get_rect(center=(RUSH_BAR_X + RUSH_BAR_WIDTH // 2, RUSH_BAR_Y - 10))
    surface.blit(label, label_rect)
    
    # Optionally, display "RUSH MODE" when active
    if rush_active:
        rush_label = pygame.font.Font(None, 36).render("RUSH MODE!", True, (255, 50, 50))
        rush_label_rect = rush_label.get_rect(center=(SCREEN_WIDTH // 2, 100))
        surface.blit(rush_label, rush_label_rect)

def main():
    global score, combo, last_combo_time, spawn_time, rush_meter, in_rush_mode
    clock = pygame.time.Clock()
    running = True
    paused = False  # Pause flag

    while running:
        dt = clock.tick(FPS) / 1000  # dt in seconds
        current_time = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused  # Toggle pause
                elif not paused and event.unicode in main_keys:
                    lane = main_keys.index(event.unicode)
                    hit_count = 0  # To offset popups if multiple hits occur
                    note_hit = False
                    for note in notes:
                        if note.lane == lane and abs(note.pos.x - HIT_ZONE_X) < HIT_WINDOW:
                            error = abs(note.pos.x - HIT_ZONE_X)
                            # Determine rating based on how centered the hit is
                            if error <= PERFECT_THRESHOLD:
                                rating = "Perfect!"
                                grade_multiplier = 1.5
                                popup_color = (0, 255, 0)
                            elif error <= GOOD_THRESHOLD:
                                rating = "Good!"
                                grade_multiplier = 1.0
                                popup_color = (255, 215, 0)
                            else:
                                rating = "OK"
                                grade_multiplier = 0.5
                                popup_color = (255, 255, 255)
                            
                            note.active = False
                            base_points = 100 + combo * 10
                            points = int(base_points * grade_multiplier)
                            if in_rush_mode:
                                points = int(points * RUSH_MULTIPLIER)
                                rush_meter = min(rush_meter + RUSH_GAIN_PER_HIT_RUSH, RUSH_MAX)
                            else:
                                rush_meter = min(rush_meter + RUSH_GAIN_PER_HIT_NORMAL, RUSH_MAX)
                                if rush_meter >= RUSH_MAX:
                                    rush_meter = RUSH_MAX
                                    in_rush_mode = True
                            score += points
                            combo += 1
                            last_combo_time = current_time
                            note_hit = True
                            create_particles((HIT_ZONE_X, note.pos.y), note.color)
                            # Position the hit popup near the lane of the note.
                            # If multiple notes are hit with the same key press, offset them so they don't overlap.
                            popup_x = HIT_ZONE_X + (hit_count - 0.5) * 20
                            popup_y = lane_positions[lane] - 30 - hit_count * 10
                            hit_popups.append(HitPopup(rating, (popup_x, popup_y), popup_color))
                            hit_count += 1
                    if not note_hit:
                        combo = 0

        if not paused:
            if current_time - spawn_time >= SPAWN_INTERVAL:
                chord_count = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
                lanes_to_spawn = random.sample(range(NUM_LANES), chord_count)
                for lane in lanes_to_spawn:
                    notes.append(Note(lane))
                spawn_time = current_time

            # Update rush meter (drain if not hitting)
            if in_rush_mode:
                rush_meter -= RUSH_DECAY_RUSH * dt
                if rush_meter <= 0:
                    rush_meter = 0
                    in_rush_mode = False
            else:
                rush_meter -= RUSH_DECAY_NORMAL * dt
                if rush_meter < 0:
                    rush_meter = 0

            notes[:] = [note for note in notes if note.active]
            for note in notes:
                note.update(dt)
            particles[:] = [p for p in particles if p.lifetime > 0]
            for p in particles:
                p.update()
            # Update hit popups
            hit_popups[:] = [popup for popup in hit_popups if popup.lifetime > 0]
            for popup in hit_popups:
                popup.update(dt)

        screen.fill(COLORS['background'])
        draw_track(screen)
        for note in notes:
            note.draw(screen)
        for p in particles:
            p.draw(screen)
        draw_ui(screen)
        draw_rush_bar(screen, rush_meter, in_rush_mode)
        for popup in hit_popups:
            popup.draw(screen)

        if paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            pause_text = pygame.font.Font(None, 72).render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(pause_text, text_rect)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
