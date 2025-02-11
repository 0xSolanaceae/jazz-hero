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
RUSH_MAX = 300  # Increased maximum required for rush mode
rush_meter = 0
in_rush_mode = False

RUSH_GAIN_PER_HIT_NORMAL = 10   # Reduced gain per hit in normal mode
RUSH_GAIN_PER_HIT_RUSH = 0      # Reduced gain during rush mode
RUSH_DECAY_NORMAL = 5           # Drains slowly when not in rush mode (per second)
RUSH_DECAY_RUSH = 25            # Drains fast during rush mode (per second)
RUSH_MULTIPLIER = 2             # Extra multiplier on score during rush mode

# Rush bar UI position and size (now on the left side)
RUSH_BAR_WIDTH = 40
RUSH_BAR_HEIGHT = 300
RUSH_BAR_X = 50
RUSH_BAR_Y = (SCREEN_HEIGHT - RUSH_BAR_HEIGHT) // 2

# Lists for active notes, particles, and hit popups
notes = []
particles = []
hit_popups = []  # Floating popup texts for hits
score = 0
combo = 0
last_combo_time = 0
spawn_time = 0
chord_counter = 0

# --------------------------------------------------
# Particle, Note, and HitPopup Classes
# --------------------------------------------------

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
        self.hit = False       # Has this note been hit?
        self.chord_id = None   # Which chord group does this note belong to?

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
        self.font = pygame.font.SysFont("Segoe UI", 36)
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

# --------------------------------------------------
# Drawing Functions
# --------------------------------------------------

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
    ui_font = pygame.font.SysFont("Segoe UI", 36)
    score_text = ui_font.render(f"SCORE: {score}", True, COLORS['text'])
    surface.blit(score_text, (20, 0))
    
    if pygame.time.get_ticks() - last_combo_time < COMBO_FADE_TIME:
        alpha = 255 * (1 - (pygame.time.get_ticks() - last_combo_time) / COMBO_FADE_TIME)
        combo_text = pygame.font.SysFont("Segoe UI", 48).render(f"{combo}x COMBO!", True, (*COLORS['combo'], int(alpha)))
        combo_pos = combo_text.get_rect(centerx=SCREEN_WIDTH // 2, y=50)
        surface.blit(combo_text, combo_pos)

def draw_rush_bar(surface, rush_value, rush_active):
    # Background bar (with rounded corners)
    bar_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y, RUSH_BAR_WIDTH, RUSH_BAR_HEIGHT)
    pygame.draw.rect(surface, (30, 30, 30), bar_rect, border_radius=10)
    pygame.draw.rect(surface, (80, 80, 80), bar_rect, width=3, border_radius=10)

    # Calculate the fill height (fill from the bottom up)
    fill_height = int((rush_value / RUSH_MAX) * RUSH_BAR_HEIGHT)
    fill_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height, RUSH_BAR_WIDTH, fill_height)

    # Create a gradient fill surface for the rush bar
    fill_surface = pygame.Surface((RUSH_BAR_WIDTH, fill_height), pygame.SRCALPHA)
    for y in range(fill_height):
        if rush_active:
            # Pulsating gradient: vary brightness using a sine function
            pulsate = (math.sin((pygame.time.get_ticks() / 100) + (y / RUSH_BAR_HEIGHT) * math.pi) + 1) / 2
            r = 255
            g = int(100 + pulsate * 155)
            b = int(100 + pulsate * 155)
        else:
            # Static gradient from light to dark blue
            ratio = y / fill_height
            r = 50
            g = int(200 - 50 * ratio)
            b = int(255 - 100 * ratio)
        pygame.draw.line(fill_surface, (r, g, b), (0, y), (RUSH_BAR_WIDTH, y))
    
    # Blit the gradient fill onto the main surface
    surface.blit(fill_surface, (RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height))
    
    # Optional: Draw a subtle inner border on the fill
    pygame.draw.rect(surface, (255, 255, 255, 50), fill_rect, width=2, border_radius=5)

    # Add an animated shine effect when in rush mode
    if rush_active and fill_height > 0:
        shine_height = 10
        # The shine moves upward continuously over the fill area
        shine_offset = (pygame.time.get_ticks() // 5) % (fill_height + shine_height) - shine_height
        shine_rect = pygame.Rect(RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height + shine_offset, RUSH_BAR_WIDTH, shine_height)
        shine_surface = pygame.Surface((RUSH_BAR_WIDTH, shine_height), pygame.SRCALPHA)
        for y in range(shine_height):
            # Create a soft white line with fading alpha at the edges
            alpha = max(0, 150 - abs(y - shine_height // 2) * 30)
            pygame.draw.line(shine_surface, (255, 255, 255, alpha), (0, y), (RUSH_BAR_WIDTH, y))
        surface.blit(shine_surface, shine_rect.topleft)
    
    # Label above the bar
    label_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
    label = label_font.render("RUSH", True, (255, 255, 255))
    label_rect = label.get_rect(center=(RUSH_BAR_X + RUSH_BAR_WIDTH // 2, RUSH_BAR_Y - 20))
    surface.blit(label, label_rect)

    # Display "RUSH MODE!" at the top of the screen when active
    if rush_active:
        rush_label = pygame.font.SysFont("Segoe UI", 28, bold=True).render("RUSH MODE!", True, (255, 50, 50))
        rush_label_rect = rush_label.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(rush_label, rush_label_rect)

# --------------------------------------------------
# Countdown before Game Starts
# --------------------------------------------------

def countdown_timer():
    """Display a 3, 2, 1 countdown before the game starts."""
    countdown_seconds = 3
    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()
    font_large = pygame.font.SysFont("Segoe UI", 150, bold=True)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        elapsed = (pygame.time.get_ticks() - start_ticks) / 1000  # seconds elapsed
        if elapsed >= countdown_seconds:
            break

        countdown_value = countdown_seconds - int(elapsed)
        screen.fill(COLORS['background'])
        countdown_text = font_large.render(str(countdown_value), True, (255, 255, 255))
        text_rect = countdown_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(countdown_text, text_rect)
        
        pygame.display.flip()
        clock.tick(FPS)
    
    screen.fill(COLORS['background'])
    go_text = font_large.render("GO!", True, (0, 255, 0))
    go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(go_text, go_rect)
    pygame.display.flip()
    pygame.time.delay(500)

# --------------------------------------------------
# Game Loop (Called after the Menu)
# --------------------------------------------------

def game():
    global score, combo, last_combo_time, spawn_time, rush_meter, in_rush_mode
    clock = pygame.time.Clock()
    running = True
    paused = False  # Pause flag

    # Reset game variables
    score = 0
    combo = 0
    spawn_time = pygame.time.get_ticks()
    notes.clear()
    particles.clear()
    hit_popups.clear()
    rush_meter = 0
    in_rush_mode = False

    countdown_timer()
    spawn_time = pygame.time.get_ticks()

    while running:
        dt = clock.tick(FPS) / 1000  # dt in seconds
        current_time = pygame.time.get_ticks()

        # Define the exit button rect for the pause menu
        exit_button_rect = pygame.Rect(0, 0, 200, 60)
        exit_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
                elif not paused and event.unicode in main_keys:
                    lane = main_keys.index(event.unicode)
                    note_hit = False
                    for note in notes:
                        # Only consider notes in this lane that haven’t been hit already
                        if note.lane == lane and not note.hit and abs(note.pos.x - HIT_ZONE_X) < HIT_WINDOW:
                            error = abs(note.pos.x - HIT_ZONE_X)
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
                            
                            # Mark this note as hit and show effects/popups immediately
                            note.hit = True
                            create_particles((HIT_ZONE_X, note.pos.y), note.color)
                            hit_popups.append(HitPopup(rating, (HIT_ZONE_X, note.pos.y - 30), popup_color))
                            # Add score (using current combo) immediately
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
                            note_hit = True

                            # Now check if this note is part of a chord.
                            # If it is, only add combo once all notes in the chord have been hit.
                            if note.chord_id is not None:
                                # Get all notes sharing the same chord_id (even those already hit)
                                chord_notes = [n for n in notes if n.chord_id == note.chord_id]
                                if all(n.hit for n in chord_notes):
                                    # All notes in this chord have been hit:
                                    for n in chord_notes:
                                        n.active = False  # Remove them so they’re no longer drawn/updated.
                                    combo += 1
                                    last_combo_time = current_time
                            else:
                                # (For safety—should not happen since every note now has a chord_id.)
                                note.active = False
                                combo += 1
                                last_combo_time = current_time
                            break  # Process only one note per keypress
                    if not note_hit:
                        combo = 0
            # Handle mouse click for exit button in pause menu
            elif paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if exit_button_rect.collidepoint(event.pos):
                    running = False

        if not paused:
            if current_time - spawn_time >= SPAWN_INTERVAL:
                # Determine how many notes to spawn simultaneously (a chord)
                chord_count = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
                global chord_counter
                chord_counter += 1
                this_chord_id = chord_counter  # All notes in this spawn share the same chord_id
                lanes_to_spawn = random.sample(range(NUM_LANES), chord_count)
                for lane in lanes_to_spawn:
                    new_note = Note(lane)
                    new_note.chord_id = this_chord_id
                    notes.append(new_note)
                spawn_time = current_time

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
                if note.pos.x < HIT_ZONE_X - HIT_WINDOW and not note.hit:
                    # If part of a chord, mark all notes in that chord as inactive.
                    if note.chord_id is not None:
                        chord_notes = [n for n in notes if n.chord_id == note.chord_id]
                        for n in chord_notes:
                            n.active = False
                    combo = 0
            particles[:] = [p for p in particles if p.lifetime > 0]
            for p in particles:
                p.update()
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
            # Draw a semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            screen.blit(overlay, (0, 0))
            pause_text = pygame.font.SysFont("Segoe UI", 72).render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
            screen.blit(pause_text, text_rect)

            # Draw the Exit button
            mouse_pos = pygame.mouse.get_pos()
            if exit_button_rect.collidepoint(mouse_pos):
                button_color = (255, 70, 70)
            else:
                button_color = (200, 50, 50)
            pygame.draw.rect(screen, button_color, exit_button_rect)
            exit_text = pygame.font.SysFont("Segoe UI", 36).render("Exit", True, (255, 255, 255))
            exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
            screen.blit(exit_text, exit_text_rect)

        pygame.display.flip()

# --------------------------------------------------
# Menu Functions
# --------------------------------------------------

def charting_menu():
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

def main_menu():
    """Display a modern looking main menu with clickable buttons for Play, Charting, or Exit."""
    menu_running = True
    menu_options = ["Play", "Charting", "Exit"]
    title = "Jazz Hero"
    title_font = pygame.font.SysFont("Segoe UI", 120, bold=True)
    menu_font = pygame.font.SysFont("Segoe UI", 50)
    credits_font = pygame.font.SysFont("Segoe UI", 30)
    clock = pygame.time.Clock()

    while menu_running:
        screen.fill(COLORS['background'])
        
        # Draw game title
        title_text = title_font.render(title, True, COLORS['text'])
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_text, title_rect)
        
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
        
        # Render menu options as clickable buttons
        for idx, option in enumerate(menu_options):
            option_y = SCREEN_HEIGHT // 2 + idx * 60
            option_text = menu_font.render(option, True, COLORS['text'])
            option_rect = option_text.get_rect(center=(SCREEN_WIDTH // 2, option_y))
            
            # Highlight if mouse is hovering over the button
            if option_rect.collidepoint(mouse_pos):
                option_text = menu_font.render(option, True, (255, 215, 0))
                if mouse_clicked:
                    if option == "Play":
                        menu_running = False  # Start game
                    elif option == "Charting":
                        charting_menu()
                    elif option == "Exit":
                        pygame.quit()
                        sys.exit()
            screen.blit(option_text, option_rect)
        
        # Draw credits at the bottom
        credits_text = credits_font.render("Built by Us", True, COLORS['text'])
        credits_rect = credits_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(credits_text, credits_rect)
        
        pygame.display.flip()
        clock.tick(FPS)

# --------------------------------------------------
# Main Entry Point
# --------------------------------------------------

def main():
    while True:
        main_menu()  # Show main menu first
        game()       # Start the game after "Play" is selected

if __name__ == "__main__":
    main()
