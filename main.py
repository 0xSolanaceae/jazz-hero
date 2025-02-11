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
pygame.display.set_caption("Saxophone Hero")

# Game settings
FPS = 60
NOTE_SPEED = 600  # pixels per second
SPAWN_INTERVAL = 1000  # milliseconds
COMBO_FADE_TIME = 2000  # milliseconds
HIT_WINDOW = 45  # pixels

# Key configuration
main_keys = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l']
key_types = ['main', 'between', 'main', 'between', 'main', 'between', 'main', 'between', 'main']

# Visual settings
COLORS = {
    'background': (15, 15, 25),
    'track': (30, 30, 40),
    'main_fret': (180, 180, 200),
    'between_fret': (80, 80, 100),
    'hit_effect': (255, 200, 100),
    'text': (240, 240, 240),
    'combo': (255, 215, 0)
}

# Lane setup
NUM_LANES = 9
LANE_HEIGHT = 60
LANE_SPACING = 10
TRACK_WIDTH = SCREEN_WIDTH - 400
HIT_ZONE_X = 350

# Calculate lane positions
lane_positions = []
for i in range(NUM_LANES):
    y = 100 + i * (LANE_HEIGHT + LANE_SPACING)
    lane_positions.append(y + LANE_HEIGHT//2)

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
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
            surface.blit(s, (self.pos.x - radius, self.pos.y - radius))

# Note class with enhanced visuals
class Note:
    def __init__(self, lane):
        self.lane = lane
        self.note_type = key_types[lane]
        self.pos = Vector2(SCREEN_WIDTH + 50, lane_positions[lane])
        self.color = (random.randint(150, 255), random.randint(100, 200), 100) if self.note_type == 'main' else (100, random.randint(150, 255), 200)
        self.active = True

    def update(self, dt):
        self.pos.x -= NOTE_SPEED * dt
        if self.pos.x < -50:
            self.active = False

    def draw(self, surface):
        if self.active:
            # Glowing core
            pygame.draw.rect(surface, self.color, 
                           (self.pos.x - 15, self.pos.y - 20, 30, 40))
            
            # Trailing glow
            glow = pygame.Surface((60, 80), pygame.SRCALPHA)
            for i in range(10):
                alpha = 255 - i*25
                width = 30 - i*3
                pygame.draw.rect(glow, (*self.color, alpha), 
                               (i*6, 20, width, 40))
            surface.blit(glow, (self.pos.x - 15, self.pos.y - 20))

# Game state
notes = []
particles = []
score = 0
combo = 0
last_combo_time = 0
spawn_time = 0

# Fonts
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)

def create_particles(position):
    for _ in range(20):
        particles.append(Particle(position, COLORS['hit_effect']))

def draw_track(surface):
    # Draw track background
    pygame.draw.rect(surface, COLORS['track'], 
                   (HIT_ZONE_X - 50, 50, TRACK_WIDTH + 100, SCREEN_HEIGHT - 100))
    
    # Draw lane dividers
    for y in lane_positions:
        pygame.draw.line(surface, (50, 50, 60), 
                        (HIT_ZONE_X - 50, y - LANE_HEIGHT//2),
                        (SCREEN_WIDTH, y - LANE_HEIGHT//2), 3)
    
    # Draw fret markers
    for i, y in enumerate(lane_positions):
        if key_types[i] == 'main':
            # 3D fret effect
            fret_color = COLORS['main_fret']
            pygame.draw.rect(surface, fret_color,
                           (HIT_ZONE_X - 40, y - 25, 40, 50))
            pygame.draw.polygon(surface, (220, 220, 230),
                               [(HIT_ZONE_X - 40, y - 25),
                                (HIT_ZONE_X, y - 25),
                                (HIT_ZONE_X - 20, y - 35)])
        else:
            pygame.draw.rect(surface, COLORS['between_fret'],
                           (HIT_ZONE_X - 20, y - 15, 20, 30))

def draw_ui(surface):
    # Score
    score_text = font_medium.render(f"SCORE: {score}", True, COLORS['text'])
    surface.blit(score_text, (20, 20))
    
    # Combo
    if pygame.time.get_ticks() - last_combo_time < COMBO_FADE_TIME:
        alpha = 255 * (1 - (pygame.time.get_ticks() - last_combo_time)/COMBO_FADE_TIME)
        combo_text = font_large.render(f"{combo}x COMBO!", True, (*COLORS['combo'], alpha))
        combo_pos = combo_text.get_rect(centerx=SCREEN_WIDTH//2, y=50)
        surface.blit(combo_text, combo_pos)

def main():
    global score, combo, last_combo_time, spawn_time
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        dt = clock.tick(FPS) / 1000
        current_time = pygame.time.get_ticks()
        
        # Spawn new notes
        if current_time - spawn_time >= SPAWN_INTERVAL:
            notes.append(Note(random.randint(0, NUM_LANES-1)))
            spawn_time = current_time
        
        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.unicode in main_keys:
                    lane = main_keys.index(event.unicode)
                    note_hit = False
                    
                    # Check notes in lane
                    for note in notes:
                        if note.lane == lane and abs(note.pos.x - HIT_ZONE_X) < HIT_WINDOW:
                            note.active = False
                            score += 100 + combo*10
                            combo += 1
                            last_combo_time = current_time
                            note_hit = True
                            create_particles((HIT_ZONE_X, note.pos.y))
                    
                    if note_hit:
                        pass  # Add sound here
                    else:
                        combo = 0
        
        # Update game objects
        notes[:] = [note for note in notes if note.active]
        for note in notes:
            note.update(dt)
        
        particles[:] = [p for p in particles if p.lifetime > 0]
        for p in particles:
            p.update()
        
        # Draw everything
        screen.fill(COLORS['background'])
        draw_track(screen)
        
        # Draw hit zone effect
        pygame.draw.line(screen, COLORS['hit_effect'], 
                        (HIT_ZONE_X, 50), (HIT_ZONE_X, SCREEN_HEIGHT - 50), 3)
        
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