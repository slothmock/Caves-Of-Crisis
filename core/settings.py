import json


DEV_MODE = True
FPS = 60

# Default settings
DEFAULT_SETTINGS = {
    "SCREEN_WIDTH": 1280,
    "SCREEN_HEIGHT": 720,
    "TILE_SIZE": 32,
}

# Logging Settings
LOG_FILE = "game.log"

GAME_VERSION = "v0.1" # TODO: Change on git push
AUTHOR_LABEL = "Created By slothmock"

GAME_TITLE = "Caves Of Crisis"
SETTINGS_FILE = "settings.json"

# Load settings from file or return defaults
def load_settings():
    try:
        with open(SETTINGS_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return DEFAULT_SETTINGS

# Save settings to file
def save_settings(settings):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=4)

# Current settings
SETTINGS = load_settings()

# Constants for direct imports in the game
SCREEN_WIDTH: int = SETTINGS["SCREEN_WIDTH"]
SCREEN_HEIGHT: int = SETTINGS["SCREEN_HEIGHT"]
TILE_SIZE: int = SETTINGS["TILE_SIZE"]


# Map Settings
MAP_WIDTH = 250  # Map width in tiles
MAP_HEIGHT = 250  # Map height in tiles
CAVE_FILL_PERCENT = 0.45  # Percentage of walls when generating caves
CAVE_SMOOTHING_ITERATIONS = 5  # Number of smoothing passes for caves

ROOM_COUNT = 20  # Number of rooms to generate
ROOM_MIN_SIZE = 3  # Minimum room size (in tiles)
ROOM_MAX_SIZE = 14  # Maximum room size (in tiles)

# Player Settings
PLAYER_MOVE_INTERVAL = 100  # Time (ms) between player movements
