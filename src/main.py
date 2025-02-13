import sys
import pygame
from note_logic import NoteLogic
from objects import ShortNote, LongNote, HitPopup
from utils import create_particles, countdown_timer
from menu import main_menu, song_select_menu
from rush_bar import draw_rush_bar
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, NOTE_SPEED, SPAWN_INTERVAL, COMBO_FADE_TIME, HIT_WINDOW,
    PERFECT_THRESHOLD, GOOD_THRESHOLD, main_keys, COLORS, lane_colors, NUM_LANES, HIT_ZONE_X, lane_positions,
    RUSH_MAX, RUSH_GAIN_PER_HIT_NORMAL, RUSH_GAIN_PER_HIT_RUSH,
    RUSH_DECAY_NORMAL, RUSH_DECAY_RUSH, RUSH_MULTIPLIER, UI
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
hit_popups = []
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
    
    note_generator = NoteLogic({
        'SPAWN_INTERVAL': SPAWN_INTERVAL,
        'NUM_LANES': NUM_LANES,
        'NOTE_SPEED': NOTE_SPEED
    })

    countdown_timer(screen, COLORS['background'])
    spawn_time = pygame.time.get_ticks()

    while running:
        dt = clock.tick(FPS) / 1000  # dt in seconds
        current_time = pygame.time.get_ticks()

        # Define the button rects for the pause menu
        play_button_rect = pygame.Rect(0, 0, *UI["button_size"])
        play_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50)
        exit_button_rect = pygame.Rect(0, 0, *UI["button_size"])
        exit_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)

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
                if play_button_rect.collidepoint(event.pos):
                    paused = False
                elif exit_button_rect.collidepoint(event.pos):
                    running = False

        if not paused:
            new_notes = note_generator.generate_notes(current_time, notes)
            notes.extend(new_notes)

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
            pause_text = pygame.font.Font(UI["title_font"], 72).render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 200))
            screen.blit(pause_text, text_rect)

            # Define the button rects for the pause menu
            play_button_rect = pygame.Rect(0, 0, *UI["button_size"])
            play_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)  # Adjusted position
            exit_button_rect = pygame.Rect(0, 0, *UI["button_size"])
            exit_button_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80)  # Adjusted position

            # Draw the Play button
            mouse_pos = pygame.mouse.get_pos()
            play_btn_color = UI["secondary_color"] if play_button_rect.collidepoint(mouse_pos) else UI["accent_color"]
            pygame.draw.rect(screen, play_btn_color, play_button_rect, border_radius=UI["button_radius"])
            play_text = pygame.font.Font(UI["body_font"], 36).render("Play", True, (255, 255, 255))
            play_text_rect = play_text.get_rect(center=play_button_rect.center)
            screen.blit(play_text, play_text_rect)

            # Draw the Exit button
            exit_btn_color = UI["secondary_color"] if exit_button_rect.collidepoint(mouse_pos) else UI["accent_color"]
            pygame.draw.rect(screen, exit_btn_color, exit_button_rect, border_radius=UI["button_radius"])
            exit_text = pygame.font.Font(UI["body_font"], 36).render("Exit", True, (255, 255, 255))
            exit_text_rect = exit_text.get_rect(center=exit_button_rect.center)
            screen.blit(exit_text, exit_text_rect)

        pygame.display.flip()

# --------------------------------------------------
# Main Entry Point
# --------------------------------------------------

def main():
    while True:
        action = main_menu(screen)
        if action == "play":
            mode = song_select_menu(screen)
            if mode == "infinite":
                game()
        elif action == "exit":
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()