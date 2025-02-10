import sys
import random
import pygame
from pygame.math import Vector2

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Saxophone Hero")

# Game settings
FPS = 60
NOTE_SPEED = 400  # pixels per second
SPAWN_INTERVAL = 800  # milliseconds
COMBO_FADE_TIME = 2000  # milliseconds

# Saxophone key configuration (9 keys: 5 main, 4 in-between)
main_keys = ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l']
key_types = ['main', 'between', 'main', 'between', 'main', 'between', 'main', 'between', 'main']

# Visual settings
COLORS = {
    'background': (23, 32, 42),
    'main_key': (180, 180, 180),
    'between_key': (100, 100, 100),
    'text': (255, 255, 255),
    'combo': (255, 215, 0)
}

# Key geometry (alternating main and between keys)
key_widths = [120 if t == 'main' else 60 for t in key_types]
total_width = sum(key_widths)
start_x = (SCREEN_WIDTH - total_width) // 2

# Calculate key positions
key_positions = []
current_x = start_x
for width in key_widths:
    key_positions.append(current_x + width//2)
    current_x += width

# Hit zone setup
HIT_ZONE_HEIGHT = 100
hit_zone_y = SCREEN_HEIGHT - HIT_ZONE_HEIGHT - 50

# Particle system
class Particle:
    def __init__(self, position, color):
        self.pos = Vector2(position)
        self.color = color
        self.velocity = Vector2(random.uniform(-3, 3), random.uniform(-5, 0))
        self.lifetime = 255
        self.size = random.randint(3, 6)

    def update(self):
        self.pos += self.velocity
        self.lifetime -= 8
        self.size += 0.5

    def draw(self, surface):
        if self.lifetime > 0:
            alpha = min(self.lifetime, 255)
            radius = int(self.size)
            s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (radius, radius), radius)
            surface.blit(s, (self.pos.x - radius, self.pos.y - radius))

# Note class with saxophone-specific visuals
class Note:
    def __init__(self, key_index):
        self.key_index = key_index
        self.note_type = key_types[key_index]
        x_pos = key_positions[key_index]
        self.pos = Vector2(x_pos, -50)
        self.color = (random.randint(100, 255), random.randint(100, 255), 50) if self.note_type == 'main' else (50, random.randint(100, 255), random.randint(100, 255))
        self.active = True

    def update(self, dt):
        self.pos.y += NOTE_SPEED * dt
        if self.pos.y > SCREEN_HEIGHT + 50:
            self.active = False

    def draw(self, surface):
        if self.active:
            # Main body with gradient
            gradient = pygame.Surface((40, 40), pygame.SRCALPHA)
            for i in range(4):
                alpha = 255 - i*60
                radius = 20 - i*5
                pygame.draw.circle(gradient, (*self.color, alpha), (20, 20), radius)
            surface.blit(gradient, (int(self.pos.x)-20, int(self.pos.y)-20))

            # Trail effect
            trail_length = 40
            trail = pygame.Surface((trail_length, 40), pygame.SRCALPHA)
            for i in range(trail_length//5):
                alpha = max(255 - i*50, 0)
                pygame.draw.circle(trail, (*self.color, alpha), 
                                    (trail_length - i*5, 20), 15 - i*3)
            surface.blit(trail, (int(self.pos.x)-trail_length, int(self.pos.y)-20))

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
font_small = pygame.font.Font(None, 32)

def create_particles(position, color):
    for _ in range(20):
        particles.append(Particle(position, color))

def draw_saxophone_body(surface):
    # Draw main body tube
    body_width = total_width + 100
    tube_rect = pygame.Rect(start_x - 50, hit_zone_y - 100, body_width, 200)
    pygame.draw.ellipse(surface, (50, 50, 60), tube_rect)
    
    # Draw key mechanics
    for i, (pos, width) in enumerate(zip(key_positions, key_widths)):
        key_color = COLORS['main_key'] if key_types[i] == 'main' else COLORS['between_key']
        key_height = 40 if key_types[i] == 'main' else 25
        
        # Key base
        pygame.draw.rect(surface, key_color, 
                        (pos - width//2, hit_zone_y - 30, width, key_height))
        
        # Key mechanism
        pygame.draw.line(surface, (80, 80, 90),
                        (pos, hit_zone_y - 30), 
                        (pos, hit_zone_y - 100), 3)

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
        
        # Spawn new notes (prefer main keys)
        if current_time - spawn_time >= SPAWN_INTERVAL:
            if random.random() < 0.7:  # 70% chance for main key
                notes.append(Note(random.choice([i for i, t in enumerate(key_types) if t == 'main'])))
            else:
                notes.append(Note(random.choice([i for i, t in enumerate(key_types) if t == 'between'])))
            spawn_time = current_time
        
        # Handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.unicode in main_keys:
                    key_index = main_keys.index(event.unicode)
                    note_hit = False
                    
                    # Check notes in hit zone
                    for note in notes:
                        if note.key_index == key_index and hit_zone_y < note.pos.y < SCREEN_HEIGHT:
                            distance = abs(note.pos.y - (hit_zone_y + HIT_ZONE_HEIGHT//2))
                            if distance < 40:
                                note.active = False
                                score += 100 + combo*10
                                combo += 1
                                last_combo_time = current_time
                                note_hit = True
                                create_particles((note.pos.x, hit_zone_y + HIT_ZONE_HEIGHT//2), note.color)
                    
                    if note_hit:
                        pass
                        #pygame.mixer.Sound.play(pygame.mixer.Sound('sax_hit.wav'))
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
        draw_saxophone_body(screen)
        
        # Draw hit zone
        pygame.draw.rect(screen, (60, 70, 80), 
                        (start_x - 50, hit_zone_y - 20, total_width + 100, HIT_ZONE_HEIGHT + 40))
        
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