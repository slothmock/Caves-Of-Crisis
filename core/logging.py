import logging
import sys
from core.settings import LOG_FILE, DEV_MODE

# Set the logging level
LOG_LEVEL = logging.DEBUG if DEV_MODE else logging.INFO

# Create a logger
logger = logging.getLogger("GameLogger")
logger.setLevel(LOG_LEVEL)

# Formatter
formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

# Console Handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(LOG_LEVEL)
console_handler.setFormatter(formatter)

# File Handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(LOG_LEVEL)
file_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
