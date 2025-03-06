from dataclasses import dataclass, field
from typing import Dict, Any
import json
import os

@dataclass
class UsdViewerConfig:
    # Performance settings
    lazy_loading: bool = True  # Load tree items only when needed
    auto_expand_tree: bool = False  # Don't auto-expand everything by default
    cache_prim_info: bool = True  # Cache prim info for performance
    max_expanded_depth: int = 2  # Only auto-expand to this depth
    
    # UI settings
    tree_background_alternating: bool = True
    use_dark_theme: bool = False
    window_width: int = 1200
    window_height: int = 800
    
    # Advanced settings
    max_items_per_batch: int = 100  # For batch loading operations
    custom_settings: Dict[str, Any] = field(default_factory=dict)

# Global configuration instance
config = UsdViewerConfig()

def load_config_from_file(file_path):
    """Load configuration from a JSON file"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Update configuration with loaded values
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                    elif key == 'custom_settings':
                        config.custom_settings.update(value)
                        
            return True
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
    return False

def save_config_to_file(file_path):
    """Save current configuration to a JSON file"""
    try:
        data = {
            'lazy_loading': config.lazy_loading,
            'auto_expand_tree': config.auto_expand_tree,
            'cache_prim_info': config.cache_prim_info,
            'max_expanded_depth': config.max_expanded_depth,
            'tree_background_alternating': config.tree_background_alternating,
            'use_dark_theme': config.use_dark_theme,
            'window_width': config.window_width,
            'window_height': config.window_height,
            'max_items_per_batch': config.max_items_per_batch,
            'custom_settings': config.custom_settings
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        return True
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
    return False

def reset_to_defaults():
    """Reset configuration to defaults"""
    global config
    config = UsdViewerConfig()

# Return the config directory in the user's home directory
def get_config_dir():
    home = os.path.expanduser("~")
    return os.path.join(home, ".usd_prim_editor")

# Default config file path
def get_default_config_path():
    return os.path.join(get_config_dir(), "config.json")

# Try to load configuration from default location on import
load_config_from_file(get_default_config_path())
