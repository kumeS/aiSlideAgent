"""
Slide Template Registry

Handles registration, storage, and retrieval of slide templates.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from .slide_writer import SlideTheme

# Configure logging
logger = logging.getLogger(__name__)

# Constants
THEME_REGISTRY_PATH = Path(__file__).parent.parent.parent / "static" / "slide_assets" / "theme_registry.json"

class TemplateRegistry:
    """Registry for slide templates to allow reuse and customization."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(TemplateRegistry, cls).__new__(cls)
            cls._instance._registry = {}
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the template registry."""
        if not self._initialized:
            # Create the registry directory if it doesn't exist
            registry_dir = THEME_REGISTRY_PATH.parent
            os.makedirs(registry_dir, exist_ok=True)
            
            # Load existing registry if available
            self._load_registry()
            
            # Add default templates if not already present
            self._add_default_templates()
            
            self._initialized = True
    
    def _load_registry(self) -> None:
        """Load the registry from disk."""
        if THEME_REGISTRY_PATH.exists():
            try:
                with open(THEME_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    self._registry = json.load(f)
                logger.debug(f"Loaded {len(self._registry)} templates from registry")
            except Exception as e:
                logger.error(f"Error loading theme registry: {e}")
                self._registry = {}
        else:
            logger.debug("Theme registry does not exist, creating new registry")
            self._registry = {}
    
    def _save_registry(self) -> None:
        """Save the registry to disk."""
        try:
            with open(THEME_REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._registry, f, indent=2)
            logger.debug(f"Saved {len(self._registry)} templates to registry")
        except Exception as e:
            logger.error(f"Error saving theme registry: {e}")
    
    def _add_default_templates(self) -> None:
        """Add default templates to the registry."""
        default_templates = {
            "modern": {
                "name": "Modern",
                "primary_color": "#3498db",
                "secondary_color": "#2ecc71",
                "text_color": "#F9FAFB",
                "background_color": "#111827",
                "accent_color": "#F59E0B",
                "header_style": "gradient",
                "bullet_style": "circle",
                "transitions": "slide",
                "text_density": "balanced",
                "max_bullet_points": 6,
                "description": "A modern, clean design with gradient headers and circular bullets",
                "version": "1.0",
                "tags": ["modern", "gradient", "clean"]
            },
            "minimal": {
                "name": "Minimal",
                "primary_color": "#333333",
                "secondary_color": "#666666",
                "text_color": "#111827",
                "background_color": "#F9FAFB",
                "accent_color": "#10B981",
                "header_style": "minimal",
                "bullet_style": "dash",
                "transitions": "fade",
                "text_density": "minimal",
                "max_bullet_points": 4,
                "description": "A minimalist design with subtle headers and clean typography",
                "version": "1.0",
                "tags": ["minimal", "clean", "light"]
            },
            "professional": {
                "name": "Professional",
                "primary_color": "#3B82F6",
                "secondary_color": "#10B981",
                "text_color": "#F9FAFB",
                "background_color": "#111827",
                "accent_color": "#F59E0B",
                "header_style": "solid",
                "bullet_style": "square",
                "transitions": "slide",
                "text_density": "balanced",
                "max_bullet_points": 6,
                "description": "A professional design suitable for business presentations",
                "version": "1.0",
                "tags": ["business", "professional", "corporate"]
            },
            "creative": {
                "name": "Creative",
                "primary_color": "#8B5CF6",
                "secondary_color": "#EC4899",
                "text_color": "#F9FAFB",
                "background_color": "#18181B",
                "accent_color": "#F59E0B",
                "header_style": "gradient",
                "bullet_style": "arrow",
                "transitions": "zoom",
                "text_density": "minimal",
                "max_bullet_points": 5,
                "description": "A creative, colorful design for impactful presentations",
                "version": "1.0",
                "tags": ["creative", "colorful", "impact"]
            },
            "business": {
                "name": "Business",
                "primary_color": "#1E40AF",
                "secondary_color": "#047857",
                "text_color": "#F9FAFB",
                "background_color": "#0F172A",
                "accent_color": "#D97706",
                "header_style": "solid",
                "bullet_style": "circle",
                "transitions": "slide",
                "text_density": "detailed",
                "max_bullet_points": 8,
                "description": "A business-oriented design for corporate presentations",
                "version": "1.0",
                "tags": ["business", "corporate", "formal"]
            },
            "academic": {
                "name": "Academic",
                "primary_color": "#4F46E5",
                "secondary_color": "#7C3AED",
                "text_color": "#F9FAFB",
                "background_color": "#1E293B",
                "accent_color": "#F59E0B",
                "header_style": "solid",
                "bullet_style": "square",
                "transitions": "fade",
                "text_density": "detailed",
                "max_bullet_points": 10,
                "description": "An academic design for educational and research presentations",
                "version": "1.0",
                "tags": ["academic", "education", "research"]
            }
        }
        
        # Add default templates to registry if they don't exist
        for key, template_data in default_templates.items():
            if key not in self._registry:
                logger.debug(f"Adding default template: {key}")
                self._registry[key] = template_data
        
        # Save registry if any templates were added
        if len(self._registry) >= len(default_templates):
            self._save_registry()
    
    def register_template(self, key: str, theme: SlideTheme) -> None:
        """
        Register a new theme template or update an existing one.
        
        Args:
            key: The key to use for the template
            theme: The SlideTheme object to register
        """
        self._registry[key] = theme.dict()
        self._save_registry()
        logger.debug(f"Registered template: {key}")
    
    def get_template(self, key: str) -> Optional[SlideTheme]:
        """
        Get a template by key.
        
        Args:
            key: The key of the template to retrieve
            
        Returns:
            SlideTheme object or None if key not found
        """
        if key in self._registry:
            return SlideTheme.parse_obj(self._registry[key])
        else:
            logger.warning(f"Template key not found: {key}")
            return None
    
    def list_templates(self) -> Dict[str, str]:
        """
        Get a list of available templates.
        
        Returns:
            Dictionary mapping template keys to template names
        """
        return {key: data.get("name", key) for key, data in self._registry.items()}
    
    def remove_template(self, key: str) -> bool:
        """
        Remove a template from the registry.
        
        Args:
            key: The key of the template to remove
            
        Returns:
            True if template was removed, False otherwise
        """
        if key in self._registry:
            del self._registry[key]
            self._save_registry()
            logger.debug(f"Removed template: {key}")
            return True
        else:
            logger.warning(f"Cannot remove template, key not found: {key}")
            return False

# Create singleton instance
template_registry = TemplateRegistry() 