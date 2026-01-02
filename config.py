"""
Bot Configuration Settings
Created: 2026-01-02 10:21:08 UTC
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================================
# BOT CREDENTIALS
# ============================================================================

# Discord Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')

# Bot Command Prefix
BOT_PREFIX = os.getenv('BOT_PREFIX', '!')

# ============================================================================
# BOT SETTINGS
# ============================================================================

# Bot name and version
BOT_NAME = 'Musicbot'
BOT_VERSION = '1.0.0'

# Bot activity/status
BOT_STATUS = 'music tracks | !help'
BOT_ACTIVITY = 'music'

# ============================================================================
# MUSIC SETTINGS
# ============================================================================

# Music platform configurations
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '')

# Music playback settings
DEFAULT_VOLUME = 0.5  # Default volume level (0.0 to 1.0)
MAX_QUEUE_SIZE = 1000  # Maximum number of songs in queue
MAX_PLAYLIST_SIZE = 500  # Maximum songs in a playlist

# ============================================================================
# LOGGING SETTINGS
# ============================================================================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = 'musicbot.log'
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ============================================================================
# DATABASE SETTINGS
# ============================================================================

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///musicbot.db')
DATABASE_ECHO = False  # Set to True for SQL query logging

# ============================================================================
# PERMISSIONS & ROLES
# ============================================================================

# Role-based access control
ADMIN_ROLE = 'Admin'
MOD_ROLE = 'Moderator'

# Permissions
ALLOW_DJ_REQUESTS = True
REQUIRE_DJ_ROLE = False
DJ_ROLE = 'DJ'

# ============================================================================
# FEATURES
# ============================================================================

# Feature flags
ENABLE_RECOMMENDATIONS = True
ENABLE_LYRICS = True
ENABLE_PLAYLIST_SUPPORT = True
ENABLE_SEARCH_FILTERS = True
ENABLE_AUDIO_EFFECTS = False

# ============================================================================
# RATE LIMITING
# ============================================================================

# Rate limiting configuration
RATE_LIMIT_ENABLED = True
RATE_LIMIT_PER_USER = 5  # Commands per minute
RATE_LIMIT_COOLDOWN = 60  # Cooldown in seconds

# ============================================================================
# TIMEOUT & RECONNECTION
# ============================================================================

# Connection settings
CONNECTION_TIMEOUT = 30  # seconds
RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY = 5  # seconds

# Auto-disconnect settings
AUTO_DISCONNECT_IDLE_TIME = 300  # 5 minutes in seconds
AUTO_DISCONNECT_EMPTY_CHANNEL = True

# ============================================================================
# CACHE SETTINGS
# ============================================================================

# Caching configuration
ENABLE_CACHE = True
CACHE_TTL = 3600  # Time to live in seconds (1 hour)
MAX_CACHE_SIZE = 100  # Maximum cached items

# ============================================================================
# ERROR HANDLING
# ============================================================================

# Error handling settings
SHOW_ERROR_DETAILS = os.getenv('SHOW_ERROR_DETAILS', 'False') == 'True'
ERROR_RESPONSE_TIMEOUT = 30  # seconds
ENABLE_ERROR_TRACKING = True

# ============================================================================
# SECURITY
# ============================================================================

# Security settings
ENABLE_COMMAND_VALIDATION = True
MAX_MESSAGE_LENGTH = 4000  # Discord message character limit
SAFE_MODE = False  # Disable certain commands in safe mode

# ============================================================================
# ADDITIONAL SETTINGS
# ============================================================================

# Default language
DEFAULT_LANGUAGE = 'en'

# Timezone
TIMEZONE = 'UTC'

# Debug mode
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ============================================================================
# EXPORT CONFIG
# ============================================================================

CONFIG = {
    'bot_token': BOT_TOKEN,
    'bot_prefix': BOT_PREFIX,
    'bot_name': BOT_NAME,
    'bot_version': BOT_VERSION,
    'default_volume': DEFAULT_VOLUME,
    'max_queue_size': MAX_QUEUE_SIZE,
    'debug': DEBUG,
}
