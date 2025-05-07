"""
Slide Theme Management

This module handles slide themes, their storage and retrieval.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Constants
THEME_REGISTRY_PATH = Path(__file__).parent.parent.parent / "static" / "slide_assets" / "theme_registry.json"

class SlideTheme(BaseModel):
    """Model representing a slide theme with enhanced customization options."""
    name: str
    # Core colors
    primary_color: str = "#3B82F6"  # Blue
    secondary_color: str = "#10B981"  # Green
    accent_color: str = "#F59E0B"  # Amber
    text_color: str = "#F9FAFB"  # Light gray
    background_color: str = "#111827"  # Dark blue/gray
    
    # Typography
    font_family: str = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"
    heading_font: Optional[str] = None  # If different from main font
    code_font: str = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
    
    # Content options
    text_density: str = "balanced"  # Options: 'minimal', 'balanced', 'detailed'
    max_bullet_points: int = 6  # Maximum number of bullet points per slide
    
    # Layout options
    slide_ratio: str = "16:9"  # Default aspect ratio
    header_style: str = "gradient"  # Options: 'gradient', 'solid', 'minimal', 'none'
    bullet_style: str = "circle"  # Options: 'circle', 'square', 'dash', 'arrow', 'none'
    
    # Animation
    transitions: str = "slide"  # Options: 'none', 'fade', 'slide', 'convex', 'concave', 'zoom'
    transition_speed: str = "default"  # Options: 'slow', 'default', 'fast'
    
    # Metadata
    description: Optional[str] = None
    author: Optional[str] = None
    version: str = "1.0"
    template_key: Optional[str] = None  # For theme registry lookup
    tags: List[str] = Field(default_factory=list)
    
    def get_css_variables(self) -> Dict[str, str]:
        """Convert theme to CSS variables."""
        variables = {
            "--primary-color": self.primary_color,
            "--secondary-color": self.secondary_color,
            "--accent-color": self.accent_color,
            "--text-color": self.text_color,
            "--background-color": self.background_color,
            "--font-family": self.font_family,
            "--code-font": self.code_font,
            "--slide-ratio": self.slide_ratio,
            "--bullet-style": self.bullet_style,
            "--header-style": self.header_style,
            "--transition": self.transitions,
            "--transition-speed": self.transition_speed,
            "--text-density": self.text_density,
            "--max-bullet-points": str(self.max_bullet_points),
        }
        
        # Add heading font if specified
        if self.heading_font:
            variables["--heading-font"] = self.heading_font
        else:
            variables["--heading-font"] = self.font_family
            
        return variables
    
    def to_json(self) -> str:
        """Convert theme to JSON for storage."""
        return json.dumps(self.dict(), indent=2)
    
    @classmethod
    def from_json(cls, json_data: Union[str, dict]) -> 'SlideTheme':
        """Create a theme from JSON data."""
        if isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        return cls(**data)
    
    def save_to_registry(self, key: Optional[str] = None):
        """Save this theme to the theme registry for reuse."""
        # Use the provided key or generate from name
        registry_key = key or self.template_key or self._generate_key()
        self.template_key = registry_key
        
        # Load existing registry or create new
        registry = {}
        if THEME_REGISTRY_PATH.exists():
            try:
                with open(THEME_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
            except Exception as e:
                logger.error(f"Error loading theme registry: {e}")
        
        # Add or update theme
        registry[registry_key] = self.dict()
        
        # Save registry
        os.makedirs(THEME_REGISTRY_PATH.parent, exist_ok=True)
        with open(THEME_REGISTRY_PATH, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
        
        logger.info(f"Theme '{self.name}' saved to registry with key '{registry_key}'")
        return registry_key
    
    @classmethod
    def load_from_registry(cls, key: str) -> Optional['SlideTheme']:
        """Load a theme from the registry by key."""
        if not THEME_REGISTRY_PATH.exists():
            logger.warning("Theme registry does not exist")
            return None
        
        try:
            with open(THEME_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            if key in registry:
                return cls.from_json(registry[key])
            else:
                logger.warning(f"Theme key '{key}' not found in registry")
                return None
        except Exception as e:
            logger.error(f"Error loading theme from registry: {e}")
            return None
    
    @classmethod
    def get_available_themes(cls) -> Dict[str, str]:
        """Get a dictionary of available themes in the registry."""
        if not THEME_REGISTRY_PATH.exists():
            logger.warning("Theme registry does not exist")
            return {}
        
        try:
            with open(THEME_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                registry = json.load(f)
            
            # Return dict of key: name pairs
            return {key: data.get('name', key) for key, data in registry.items()}
        except Exception as e:
            logger.error(f"Error loading themes from registry: {e}")
            return {}
    
    def _generate_key(self) -> str:
        """Generate a registry key from the theme name."""
        base_key = self.name.lower().replace(' ', '_')
        return f"{base_key}_v{self.version.replace('.', '_')}" 