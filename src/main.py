import sys
import random
import math
import pygame
from pygame.math import Vector2
from objects import Particle, ShortNote, LongNote, HitPopup
from utils import create_particles, draw_gradient_background, draw_button, countdown_timer
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, NOTE_SPEED, SPAWN_INTERVAL, COMBO_FADE_TIME, HIT_WINDOW,
    PERFECT_THRESHOLD, GOOD_THRESHOLD, main_keys, COLORS, lane_colors, NUM_LANES, HIT_ZONE_X, lane_positions,
    RUSH_MAX, RUSH_GAIN_PER_HIT_NORMAL, RUSH_GAIN_PER_HIT_RUSH,
    RUSH_DECAY_NORMAL, RUSH_DECAY_RUSH, RUSH_MULTIPLIER, RUSH_BAR_WIDTH, RUSH_BAR_HEIGHT,
    RUSH_BAR_X, RUSH_BAR_Y
)

pygame.init()
pygame.mixer.init()

icon = pygame.image.load('assets/icon.png')
pygame.display.set_icon(icon)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Jazz Hero")

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

    surface.blit(fill_surface, (RUSH_BAR_X, RUSH_BAR_Y + RUSH_BAR_HEIGHT - fill_height))

    pygame.draw.rect(surface, (255, 255, 255, 50), fill_rect, width=2, border_radius=5)

    if rush_active and fill_height > 0:
        rush_shine(fill_height, surface)
    label_font = pygame.font.SysFont("Segoe UI", 24, bold=True)
    label = label_font.render("RUSH", True, (255, 255, 255))
    label_rect = label.get_rect(center=(RUSH_BAR_X + RUSH_BAR_WIDTH // 2, RUSH_BAR_Y - 20))
    surface.blit(label, label_rect)

    # Display "RUSH MODE!" at the top of the screen when active
    if rush_active:
        rush_label = pygame.font.SysFont("Segoe UI", 28, bold=True).render("RUSH MODE!", True, (255, 50, 50))
        rush_label_rect = rush_label.get_rect(center=(SCREEN_WIDTH // 2, 50))
        surface.blit(rush_label, rush_label_rect)

def rush_shine(fill_height, surface):
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

# --------------------------------------------------
# Game Loop (Called after the Menu)
# --------------------------------------------------

def game():
    global score, combo, last_combo_time, spawn_time, rush_meter, in_rush_mode, chord_counter
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
    chord_counter = 0

    countdown_timer(screen, COLORS['background'])
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
                elif not paused:
                    if event.unicode in main_keys:
                        lane = main_keys.index(event.unicode)
                        note_hit = False
                        # First, check for short notes in this lane
                        for note in notes:
                            if isinstance(note, ShortNote) and note.lane == lane and not note.hit and abs(note.pos.x - HIT_ZONE_X) < HIT_WINDOW:
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

                                note.hit = True
                                particles.extend(create_particles((HIT_ZONE_X, note.pos.y), note.color))
                                hit_popups.append(HitPopup(rating, (HIT_ZONE_X, note.pos.y - 30), popup_color))
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

                                # Handle chord logic for short notes
                                if note.chord_id is not None:
                                    chord_notes = [n for n in notes if n.chord_id == note.chord_id]
                                    if all(n.hit for n in chord_notes):
                                        for n in chord_notes:
                                            n.active = False
                                        combo += 1
                                        last_combo_time = current_time
                                else:
                                    note.active = False
                                    combo += 1
                                    last_combo_time = current_time
                                note_hit = True
                                break  # Process only one note per keypress
                        # If no short note was hit, check for long notes in this lane
                        if not note_hit:
                            for note in notes:
                                if isinstance(note, LongNote) and note.lane == lane and not note.held and not note.completed and abs(note.pos.x - HIT_ZONE_X) < HIT_WINDOW:
                                    note.held = True
                                    note.start_hold_time = pygame.time.get_ticks()
                                    particles.extend(create_particles((HIT_ZONE_X, note.pos.y), note.color))
                                    hit_popups.append(HitPopup("Hold!", (HIT_ZONE_X, note.pos.y - 30), (255, 255, 255)))
                                    note_hit = True
                                    break
            elif event.type == pygame.KEYUP:
                if event.unicode in main_keys:
                    lane = main_keys.index(event.unicode)
                    # Check if a long note is being held in this lane
                    for note in notes:
                        if isinstance(note, LongNote) and note.lane == lane and note.held and not note.completed:
                            elapsed = pygame.time.get_ticks() - note.start_hold_time
                            max_duration = note.length / NOTE_SPEED * 1000  # Convert to ms
                            progress = min(elapsed / max_duration, 1.0)
                            base_points = 200  # Base points for long notes
                            points = int(base_points * progress)
                            if in_rush_mode:
                                points = int(points * RUSH_MULTIPLIER)
                                rush_meter = min(rush_meter + RUSH_GAIN_PER_HIT_RUSH, RUSH_MAX)
                            else:
                                rush_meter = min(rush_meter + RUSH_GAIN_PER_HIT_NORMAL, RUSH_MAX)
                                if rush_meter >= RUSH_MAX:
                                    rush_meter = RUSH_MAX
                                    in_rush_mode = True
                            score += points
                            if progress == 1.0:
                                rating = "Perfect!"
                                popup_color = (0, 255, 0)
                            elif progress >= 0.8:
                                rating = "Good!"
                                popup_color = (255, 215, 0)
                            else:
                                rating = "OK"
                                popup_color = (255, 255, 255)
                            particles.extend(create_particles((HIT_ZONE_X, note.pos.y), note.color))
                            hit_popups.append(HitPopup(rating, (HIT_ZONE_X, note.pos.y - 30), popup_color))
                            combo += 1
                            last_combo_time = pygame.time.get_ticks()
                            note.held = False
                            note.active = False
                            break
            elif paused and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if exit_button_rect.collidepoint(event.pos):
                    running = False

        if not paused:
            # Spawn new notes if enough time has passed
            if current_time - spawn_time >= SPAWN_INTERVAL:
                # 30% chance to spawn a long note, else spawn a chord of short notes
                if random.random() < 0.1:
                    lane = random.randint(0, NUM_LANES - 1)
                    length = NOTE_SPEED * 0.8  # Long note lasts 1.5 seconds
                    new_note = LongNote(lane, length)
                    notes.append(new_note)
                else:
                    chord_count = random.choices([1, 2, 3], weights=[60, 30, 10], k=1)[0]
                    chord_counter += 1
                    this_chord_id = chord_counter  # All notes in this spawn share the same chord_id
                    lanes_to_spawn = random.sample(range(NUM_LANES), chord_count)
                    for lane in lanes_to_spawn:
                        new_note = ShortNote(lane)
                        new_note.chord_id = this_chord_id
                        notes.append(new_note)
                spawn_time = current_time

            # Rush mode decay logic
            if in_rush_mode:
                rush_meter -= RUSH_DECAY_RUSH * dt
                if rush_meter <= 0:
                    rush_meter = 0
                    in_rush_mode = False
            else:
                rush_meter -= RUSH_DECAY_NORMAL * dt
                rush_meter = max(rush_meter, 0)
            # Update notes
            notes[:] = [note for note in notes if note.active]
            for note in notes:
                note.update(dt)
                if isinstance(note, ShortNote):
                    if note.pos.x < HIT_ZONE_X - HIT_WINDOW and not note.hit:
                        if note.chord_id is not None:
                            chord_notes = [n for n in notes if n.chord_id == note.chord_id]
                            for n in chord_notes:
                                n.active = False
                        combo = 0
                elif isinstance(note, LongNote):
                    if note.held and not note.completed:
                        elapsed = pygame.time.get_ticks() - note.start_hold_time
                        max_duration = note.length / NOTE_SPEED * 1000
                        note.hold_progress = min(elapsed / max_duration, 1.0)
                        if note.tail_x < HIT_ZONE_X - HIT_WINDOW:
                            # Automatically complete long note if tail passes hit zone
                            note.completed = True
                            note.active = False
                            base_points = 200
                            points = base_points
                            if in_rush_mode:
                                points = int(points * RUSH_MULTIPLIER)
                                rush_meter = min(rush_meter + RUSH_GAIN_PER_HIT_RUSH, RUSH_MAX)
                            else:
                                rush_meter = min(rush_meter + RUSH_GAIN_PER_HIT_NORMAL, RUSH_MAX)
                                if rush_meter >= RUSH_MAX:
                                    rush_meter = RUSH_MAX
                                    in_rush_mode = True
                            score += points
                            particles.extend(create_particles((HIT_ZONE_X, note.pos.y), note.color))
                            hit_popups.append(HitPopup("Perfect!", (HIT_ZONE_X, note.pos.y - 30), (0, 255, 0)))
                            combo += 1
                            last_combo_time = current_time

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
    """Modern main menu with animated background, drop-shadow title, and interactive buttons."""
    menu_running = True
    menu_options = ["Play", "Charting", "Exit"]
    title = "Jazz Hero"
    # Choose modern, clean fonts
    title_font = pygame.font.SysFont("Segoe UI", 100, bold=True)
    button_font = pygame.font.SysFont("Segoe UI", 40, bold=True)
    credits_font = pygame.font.SysFont("Segoe UI", 24)
    clock = pygame.time.Clock()

    # Set up button geometry
    button_width = 300
    button_height = 60
    button_spacing = 80
    buttons = []
    start_y = SCREEN_HEIGHT // 2
    for i, option in enumerate(menu_options):
        rect = pygame.Rect(0, 0, button_width, button_height)
        rect.center = (SCREEN_WIDTH // 2, start_y + i * button_spacing)
        buttons.append((option, rect))

    # List for background particles (for a subtle dynamic effect)
    menu_particles = []
    particle_spawn_timer = 0
    particle_spawn_interval = 100  # spawn a particle every 100ms

    while menu_running:
        clock.tick(FPS)
        current_time = pygame.time.get_ticks()

        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                for option, rect in buttons:
                    if rect.collidepoint(mouse_pos):
                        if option == "Play":
                            menu_running = False  # Exit the menu to start the game
                        elif option == "Charting":
                            charting_menu()
                        elif option == "Exit":
                            pygame.quit()
                            sys.exit()

        # Spawn new background particles periodically
        if current_time - particle_spawn_timer > particle_spawn_interval:
            particle_spawn_timer = current_time
            # Create a particle that starts just below the screen
            pos = Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT - 50)
            p = Particle(pos, (255, 255, 255))
            # Slow, upward drift with a slight horizontal variation
            p.velocity = Vector2(random.uniform(-0.5, 0.5), -random.uniform(0.5, 1.5))
            p.lifetime = 300  # adjust lifetime as needed
            p.size = random.randint(2, 4)
            menu_particles.append(p)

        # Update background particles and remove faded ones
        for p in menu_particles[:]:
            p.update()
            if p.lifetime <= 0:
                menu_particles.remove(p)

        # Draw a lighter gradient background
        draw_gradient_background(screen, (100, 100, 150), (150, 100, 180))

        # Draw background particles
        for p in menu_particles:
            p.draw(screen)

        # Draw the title with a drop shadow for extra depth
        shadow_offset = Vector2(4, 4)
        shadow_surface = title_font.render(title, True, (0, 0, 0))
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + shadow_offset.x,
                                                       SCREEN_HEIGHT // 4 + shadow_offset.y))
        screen.blit(shadow_surface, shadow_rect)
        title_surface = title_font.render(title, True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        screen.blit(title_surface, title_rect)

        # Draw each button with hover effects
        mouse_pos = pygame.mouse.get_pos()
        for option, rect in buttons:
            hovered = rect.collidepoint(mouse_pos)
            draw_button(screen, rect, option, button_font,
                        base_color=(50, 50, 80),
                        hover_color=(80, 80, 120),
                        text_color=(255, 255, 255),
                        is_hovered=hovered)

        # Draw credits at the bottom
        credits_text = credits_font.render("Built by Gio & Miles", True, (200, 200, 200))
        credits_rect = credits_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        screen.blit(credits_text, credits_rect)

        pygame.display.flip()

# --------------------------------------------------
# Main Entry Point
# --------------------------------------------------

def main():
    while True:
        main_menu()
        game()

if __name__ == "__main__":
    main()