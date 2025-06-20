"""
Configuration loader for Squadcast Slack Sync

This module handles loading configuration from a config.json file
and provides default values for missing configurations.
"""

import os
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "sync_settings": {
        "log_level": "INFO",
        "log_file": "squadcast_slack_sync.log",
        "timeout_seconds": 30
    },
    "slack_settings": {
        "retry_attempts": 3,
        "retry_delay_seconds": 2
    },
    "squadcast_settings": {
        "sync_interval_minutes": 5
    }
}


def load_config() -> Dict[str, Any]:
    """
    Load configuration from a JSON file with fallback to defaults
    
    Returns:
        A dictionary containing the configuration settings
"""
    # Look for config.json in the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    
    config = DEFAULT_CONFIG.copy()
    
    # Try to load config from file
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                loaded_config = json.load(f)
                
            # Update our default config with loaded values
            for section in config:
                if section in loaded_config:
                    config[section].update(loaded_config[section])
                    
            logger.debug(f"Loaded configuration from {config_path}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading config from {config_path}: {e}")
            logger.info("Using default configuration")
    else:
        logger.info(f"Configuration file not found at {config_path}, using defaults")
    
    return config


def get_config_value(section: str, key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value with fallback to default
    
    Args:
        section: The configuration section (e.g., 'sync_settings')
        key: The key within the section
        default: The default value if the key is not found
        
    Returns:
        The configuration value or default
    """
    config = load_config()
    if section in config and key in config[section]:
        return config[section][key]
    return default
