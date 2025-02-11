import sys
import random
import pygame
from pygame.math import Vector2

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jazz Hero")

# Game settings
FPS = 60
NOTE_SPEED = 600  # pixels per second
SPAWN_INTERVAL = 1000  # milliseconds
COMBO_FADE_TIME = 2000  # milliseconds
HIT_WINDOW = 45  # pixels

# Key configuration (only 3 lanes now)
main_keys = ['a', 's', 'd']

# Visual settings
COLORS = {
    'background': (15, 15, 25),
    'track': (30, 30, 40),
    'hit_effect': (255, 200, 100),
    'text': (240, 240, 240),
    'combo': (255, 215, 0)
}

# Fixed colors for each lane (top, middle, bottom)
lane_colors = [
    (255, 255, 0),  # Yellow for top lane
    (255, 0, 0),    # Red for middle lane
    (0, 255, 0)     # Green for bottom lane
]

# Lane setup for 3 lanes
NUM_LANES = 3
LANE_HEIGHT = 60
LANE_SPACING = 80
TRACK_WIDTH = SCREEN_WIDTH - 400
HIT_ZONE_X = 200

# Calculate lane positions (center of each lane)
track_top = 50
track_bottom = SCREEN_HEIGHT - 50
track_height = track_bottom - track_top

lane_positions = []
for i in range(NUM_LANES):
    lane_center_y = track_top + (i + 0.5) * (track_height / NUM_LANES)
    lane_positions.append(lane_center_y)


# Particle system
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

# Note class with fixed colors based on lane
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
            # Draw trailing glow as concentric circles on a temporary surface
            glow_size = 80
            glow = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow.fill((0, 0, 0, 0))
            for i in range(10):
                alpha = max(255 - i * 25, 0)
                radius = 20 + i * 3
                pygame.draw.circle(glow, (*self.color, alpha), (glow_size // 2, glow_size // 2), radius)
            
            # Create a circular mask so that the glow remains circular
            mask = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255), (glow_size // 2, glow_size // 2), glow_size // 2)
            glow.blit(mask, (0, 0), None, pygame.BLEND_RGBA_MULT)
            surface.blit(glow, (int(self.pos.x) - glow_size // 2, int(self.pos.y) - glow_size // 2))
            
            # Draw the core (filled) circular note on top
            pygame.draw.circle(surface, self.color, (int(self.pos.x), int(self.pos.y)), 20)

# Game state variables
notes = []
particles = []
score = 0
combo = 0
last_combo_time = 0
spawn_time = 0

def create_particles(position, color):
    # Create particles with the provided color
    for _ in range(20):
        particles.append(Particle(position, color))

def draw_track(surface):
    # Draw track background starting at 150 so that it reaches SCREEN_WIDTH
    pygame.draw.rect(surface, COLORS['track'],
                     (150, 50, SCREEN_WIDTH - 150, SCREEN_HEIGHT - 100))
    
    gray_color = (128, 128, 128)
    
    # First, draw horizontal lane lines for each lane
    for y in lane_positions:
        pygame.draw.line(surface, gray_color, (HIT_ZONE_X, int(y)), (SCREEN_WIDTH, int(y)), 3)
    
    # Then, draw the vertical hit zone (yellow) line
    pygame.draw.line(surface, COLORS['hit_effect'],
                     (HIT_ZONE_X, 50), (HIT_ZONE_X, SCREEN_HEIGHT - 50), 3)
    
    # Finally, draw the circles so they appear on top of the lines
    circle_offset = 0  # How far left of HIT_ZONE_X the circles will be drawn
    circle_radius = 40
    for i, y in enumerate(lane_positions):
        circle_center = (HIT_ZONE_X - circle_offset, int(y))
        pygame.draw.circle(surface, lane_colors[i], circle_center, circle_radius, 5)

def draw_ui(surface):
    # Score display
    score_text = pygame.font.Font(None, 48).render(f"SCORE: {score}", True, COLORS['text'])
    surface.blit(score_text, (20, 20))
    
    # Combo display (fades out over COMBO_FADE_TIME)
    if pygame.time.get_ticks() - last_combo_time < COMBO_FADE_TIME:
        alpha = 255 * (1 - (pygame.time.get_ticks() - last_combo_time) / COMBO_FADE_TIME)
        combo_text = pygame.font.Font(None, 72).render(f"{combo}x COMBO!", True, (*COLORS['combo'], int(alpha)))
        combo_pos = combo_text.get_rect(centerx=SCREEN_WIDTH // 2, y=50)
        surface.blit(combo_text, combo_pos)

def main():
    global score, combo, last_combo_time, spawn_time
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(FPS) / 1000
        current_time = pygame.time.get_ticks()
        
        # Spawn new notes periodically.
        # Now, we can spawn a chord (multiple notes) at one time.
        if current_time - spawn_time >= SPAWN_INTERVAL:
            # Choose a random number of notes to spawn (between 1 and the total number of lanes)
            chord_count = random.randint(1, NUM_LANES)
            # Select unique lanes randomly.
            lanes_to_spawn = random.sample(range(NUM_LANES), chord_count)
            for lane in lanes_to_spawn:
                notes.append(Note(lane))
            spawn_time = current_time
        
        # Handle events and key presses
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.unicode in main_keys:
                    lane = main_keys.index(event.unicode)
                    note_hit = False
                    
                    # Check for a note in the corresponding lane within the hit window
                    for note in notes:
                        if note.lane == lane and abs(note.pos.x - HIT_ZONE_X) < HIT_WINDOW:
                            note.active = False
                            score += 100 + combo * 10
                            combo += 1
                            last_combo_time = current_time
                            note_hit = True
                            create_particles((HIT_ZONE_X, note.pos.y), note.color)
                    
                    if not note_hit:
                        combo = 0
        
        # Update notes and particles
        notes[:] = [note for note in notes if note.active]
        for note in notes:
            note.update(dt)
        
        particles[:] = [p for p in particles if p.lifetime > 0]
        for p in particles:
            p.update()
        
        # Draw everything
        screen.fill(COLORS['background'])
        draw_track(screen)
        
        for note in notes:
            note.draw(screen)
        
        for p in particles:
            p.draw(screen)
        
        draw_ui(screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
