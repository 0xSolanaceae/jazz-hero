import pygame
import sys
import random
from pygame.math import Vector2
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, UI, MENU_BACKGROUND
from utils import draw_gradient_background

def charting_menu(screen):
    """Modern charting menu with glassmorphism effect"""
    charting_running = True
    clock = pygame.time.Clock()
    font = pygame.font.Font(UI["body_font"], 36)
    back_button_rect = pygame.Rect(50, SCREEN_HEIGHT - 100, 200, 60)

    bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    draw_gradient_background(bg_surface, MENU_BACKGROUND[0], MENU_BACKGROUND[1])

    while charting_running:
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(bg_surface, (0, 0))

        # Draw glass panel
        glass_rect = pygame.Rect(
            SCREEN_WIDTH//2 - 300, 100, 600, SCREEN_HEIGHT - 200
        )
        glass_surface = pygame.Surface(glass_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glass_surface, UI["glass_color"], glass_surface.get_rect(), border_radius=20)
        screen.blit(glass_surface, glass_rect.topleft)

        # Draw grid lines
        for y in range(glass_rect.top + 50, glass_rect.bottom, 50):
            pygame.draw.line(screen, (255, 255, 255, 30), (glass_rect.left + 20, y), (glass_rect.right - 20, y))

        # Draw back button
        btn_color = UI["secondary_color"] if back_button_rect.collidepoint(mouse_pos) else UI["accent_color"]
        pygame.draw.rect(screen, btn_color, back_button_rect, border_radius=UI["button_radius"])
        text = font.render("BACK", True, (255, 255, 255))
        text_rect = text.get_rect(center=back_button_rect.center)
        screen.blit(text, text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if back_button_rect.collidepoint(mouse_pos):
                    charting_running = False

        pygame.display.flip()
        clock.tick(FPS)
        
def song_select_menu(screen):
    """Styled mode selection menu with animated background"""
    menu_running = True
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(UI["title_font"], 72)
    button_font = pygame.font.Font(UI["body_font"], 36)
    
    # Pre-render gradient background
    bg_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    draw_gradient_background(bg_surface, MENU_BACKGROUND[0], MENU_BACKGROUND[1])

    # Animated elements
    parallax_layers = [
        {"speed": 0.2, "stars": [Vector2(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(50)]},
        {"speed": 0.5, "stars": [Vector2(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]}
    ]
    particles = []
    particle_timer = 0

    # Button definitions
    buttons = [
        {"rect": pygame.Rect(0, 0, *UI["button_size"]), "text": "Infinite Mode", "action": "infinite"},
        {"rect": pygame.Rect(0, 0, *UI["button_size"]), "text": "Back", "action": "back"}
    ]
    for i, btn in enumerate(buttons):
        btn["rect"].center = (SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 60 + i * 140)

    # Play background music if not already playing
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load('assets/audio/menu_music.mp3')
        pygame.mixer.music.play(-1)  # Loop indefinitely

    while menu_running:
        dt = clock.tick(FPS) * 0.001
        mouse_pos = pygame.mouse.get_pos()
        
        # Animate background
        screen.blit(bg_surface, (0, 0))
        
        # Draw parallax stars
        for layer in parallax_layers:
            for star in layer["stars"]:
                star.x = (star.x + layer["speed"] * dt * 60) % SCREEN_WIDTH
                size = 2 if layer["speed"] == 0.2 else 1
                pygame.draw.circle(screen, (255, 255, 255, 50), star, size)

        # Update particles
        particle_timer += dt
        if particle_timer > 0.1:
            particle_timer = 0
            particles.append({
                "pos": Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 20),
                "vel": Vector2(random.uniform(-0.5, 0.5), random.uniform(-3, -2)),
                "size": random.randint(8, 12),
                "color": random.choice(UI["particle_colors"])
            })
        particles = [p for p in particles if p["pos"].y > -20]
        for p in particles:
            p["pos"] += p["vel"] * dt * 60
            pygame.draw.circle(screen, p["color"], p["pos"], p["size"])

        # Draw glass panel
        glass_rect = pygame.Rect(SCREEN_WIDTH//2 - 300, 100, 600, SCREEN_HEIGHT - 200)
        glass_surface = pygame.Surface(glass_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glass_surface, UI["glass_color"], glass_surface.get_rect(), border_radius=20)
        screen.blit(glass_surface, glass_rect.topleft)

        # Draw title
        title_text = title_font.render("Select Mode", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 150))
        screen.blit(title_text, title_rect)

        # Draw buttons
        for btn in buttons:
            hovered = btn["rect"].collidepoint(mouse_pos)
            color = UI["secondary_color"] if hovered else UI["accent_color"]
            
            # Button shadow
            shadow_surface = pygame.Surface(btn["rect"].size, pygame.SRCALPHA)
            pygame.draw.rect(shadow_surface, (0, 0, 0, 50 if hovered else 30), 
                           shadow_surface.get_rect(), border_radius=UI["button_radius"])
            screen.blit(shadow_surface, (btn["rect"].x - 4, btn["rect"].y + 4))
            
            # Button body
            pygame.draw.rect(screen, color, btn["rect"], border_radius=UI["button_radius"])
            
            # Button text
            text_surf = button_font.render(btn["text"], True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=btn["rect"].center)
            screen.blit(text_surf, text_rect)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn["rect"].collidepoint(event.pos):
                        if btn["action"] == "infinite":
                            return "infinite"
                        elif btn["action"] == "back":
                            return "back"

        pygame.display.flip()

    return "back"

def main_menu(screen):
    """Modern main menu with parallax and animated elements"""
    menu_running = True
    clock = pygame.time.Clock()
    title_font = pygame.font.Font(UI["title_font"], 120)
    button_font = pygame.font.Font(UI["body_font"], 40)
    
    menu_options = [
        {"text": "Play", "action": "play"},
        {"text": "Charting", "action": "charting"},
        {"text": "Exit", "action": "exit"}
    ]

    # Parallax layers
    parallax_layers = [
        {"speed": 0.2, "stars": [Vector2(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(50)]},
        {"speed": 0.5, "stars": [Vector2(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT)) for _ in range(100)]}
    ]

    # Animated background particles
    particles = []
    particle_timer = 0

    # Play background music if not already playing
    if not pygame.mixer.music.get_busy():
        pygame.mixer.music.load('assets/audio/menu_music.mp3')
        pygame.mixer.music.play(-1)  # Loop indefinitely

    while menu_running:
        dt = clock.tick(FPS) * 0.001
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(MENU_BACKGROUND[1])

        # Draw parallax stars
        for layer in parallax_layers:
            for star in layer["stars"]:
                star.x = (star.x + layer["speed"] * dt * 60) % SCREEN_WIDTH
                size = 2 if layer["speed"] == 0.2 else 1
                pygame.draw.circle(screen, (255, 255, 255, 50), star, size)

        # Generate new particles
        particle_timer += dt
        if particle_timer > 0.1:
            particle_timer = 0
            particles.append({
                "pos": Vector2(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 20),
                "vel": Vector2(random.uniform(-0.5, 0.5), random.uniform(-3, -2)),
                "size": random.randint(8, 12),
                "color": random.choice(UI["particle_colors"])
            })

        # Update and draw particles
        particles = [p for p in particles if p["pos"].y > -20]
        for p in particles:
            p["pos"] += p["vel"] * dt * 60
            pygame.draw.circle(screen, p["color"], p["pos"], p["size"])

        # Draw title with gradient
        title_surface = title_font.render("JAZZ HERO", True, (255, 255, 255))
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH//2, 150))
        
        # Create gradient overlay
        gradient = pygame.Surface(title_surface.get_size(), pygame.SRCALPHA)
        for x in range(title_surface.get_width()):
            ratio = x / title_surface.get_width()
            color = (
                int(UI["accent_color"][0] * (1 - ratio) + UI["secondary_color"][0] * ratio),
                int(UI["accent_color"][1] * (1 - ratio) + UI["secondary_color"][1] * ratio),
                int(UI["accent_color"][2] * (1 - ratio) + UI["secondary_color"][2] * ratio),
                255
            )
            pygame.draw.line(gradient, color, (x, 0), (x, title_surface.get_height()))
        title_surface.blit(gradient, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # Add shadow
        shadow = title_font.render("JAZZ HERO", True, UI["text_shadow"])
        screen.blit(shadow, title_rect.move(5, 5))
        screen.blit(title_surface, title_rect)

        # Draw menu buttons
        button_y = SCREEN_HEIGHT//2 - 100
        for idx, option in enumerate(menu_options):
            btn_rect = pygame.Rect(0, 0, *UI["button_size"])
            btn_rect.center = (SCREEN_WIDTH//2, button_y + idx * 120)
            
            # Hover animation
            hover = btn_rect.collidepoint(mouse_pos)
            scale = 1.1 if hover else 1
            scaled_rect = btn_rect.inflate(btn_rect.width * (scale-1), btn_rect.height * (scale-1))
            scaled_rect.center = btn_rect.center
            
            # Draw button
            btn_color = UI["secondary_color"] if hover else UI["accent_color"]
            pygame.draw.rect(screen, btn_color, scaled_rect, border_radius=UI["button_radius"])
            
            # Add text
            text = button_font.render(option["text"], True, (255, 255, 255))
            text_rect = text.get_rect(center=scaled_rect.center)
            screen.blit(text, text_rect)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for idx, option in enumerate(menu_options):
                    btn_rect = pygame.Rect(0, 0, *UI["button_size"])
                    btn_rect.center = (SCREEN_WIDTH//2, button_y + idx * 120)
                    if btn_rect.collidepoint(mouse_pos):
                        if option["action"] == "play":
                            menu_running = False
                            return "play"
                        elif option["action"] == "charting":
                            pygame.mixer.music.stop()  # Stop music when switching to charting menu
                            charting_menu(screen)
                            pygame.mixer.music.load('assets/audio/menu_music.mp3')  # Restart music when returning from charting menu
                            pygame.mixer.music.play(-1)
                        elif option["action"] == "exit":
                            pygame.quit()
                            sys.exit()

        # Draw credits
        credit_font = pygame.font.Font(UI["body_font"], 24)
        credits = credit_font.render("Built by Gio & Miles", True, (200, 200, 200, 150))
        screen.blit(credits, (20, SCREEN_HEIGHT - 40))

        pygame.display.flip()
    
    pygame.mixer.music.stop()  # Stop music when leaving the menu
    return "exit"