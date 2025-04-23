# cabbage/__init__.py

# Expose the main processing function and config loader at the package level
from .main_processor import process_query, load_config, DEFAULT_CONFIG

# Define what gets imported with 'from cabbage import *' (optional but good practice)
__all__ = ['process_query', 'load_config', 'DEFAULT_CONFIG']

# You could add version information here later
# __version__ = "0.1.0"