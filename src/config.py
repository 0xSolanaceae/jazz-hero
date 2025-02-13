# Screen settings
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
FPS = 60

# Note settings
NOTE_SPEED = 600
SPAWN_INTERVAL = 1000
COMBO_FADE_TIME = 2000
HIT_WINDOW = 60  # Increased hit window makes it easier to register an OK hit.

# Timing thresholds (in pixels) for grading hits
PERFECT_THRESHOLD = 10  # Dead-center
GOOD_THRESHOLD = 25     # Slightly off-center

# Main keys
main_keys = ['a', 's', 'd']

UI = {
    "title_font": "assets/fonts/Lato-Bold.ttf",
    "body_font": "assets/fonts/Lato-Regular.ttf",
    "accent_color": (98, 102, 255),
    "secondary_color": (255, 65, 129),
    "glass_color": (255, 255, 255, 50),
    "button_radius": 15,
    "button_size": (320, 80),
    "text_shadow": (30, 30, 30),
    "particle_colors": [
        (98, 102, 255),
        (255, 65, 129),
        (128, 0, 128)
    ]
}

MENU_BACKGROUND = [
    (25, 25, 40),
    (15, 15, 30)
]

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

# Rush Bar Constants and Variables
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