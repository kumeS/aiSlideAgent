"""
Slide Writer Agent

Generates HTML/CSS slides using Jinja2 templates and the provided slide deck outline.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import re

from agents import client, DEFAULT_MODEL
from ..outline import SlideDeck, SlideContent

# Import from split modules
from .models import HTMLSlide, SlideDeckHTML
from .themes import SlideTheme
from .generators import (
    generate_title_slide, generate_content_slide, generate_profile_slide,
    generate_career_slide, generate_timeline_slide, generate_two_column_slide,
    generate_image_slide, generate_quote_slide, optimize_image_layout,
    split_text_to_bullets
)
from .renderer import SlideRenderer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Helper function to truncate text with ellipsis
def _truncate_text(text: str, max_length: int) -> str:
    """Truncate text to a maximum length and add ellipsis if needed."""
    if len(text) <= max_length:
        return text
    # Try to truncate at a space or punctuation
    truncate_point = max_length
    while truncate_point > max_length - 20 and truncate_point > 0:
        if text[truncate_point] in " .,;:!?":
            break
        truncate_point -= 1
    if truncate_point <= max_length - 20:
        truncate_point = max_length  # Fallback to hard truncation
    return text[:truncate_point] + "..."

class SlideWriterAgent:
    """Agent for generating HTML/CSS slides from slide deck outlines."""
    
    def __init__(self, model: Optional[str] = None, templates_dir: Optional[Path] = None):
        """Initialize the slide writer agent with configuration."""
        self.model = model or DEFAULT_MODEL
        self.renderer = SlideRenderer(templates_dir)
    
    def generate_slides(self, slide_deck: SlideDeck, theme: Optional[SlideTheme] = None) -> SlideDeckHTML:
        """
        Generate HTML/CSS slides from a slide deck outline.
        
        Args:
            slide_deck: The slide deck outline to generate slides from
            theme: Optional theme configuration
            
        Returns:
            A SlideDeckHTML object containing the complete slide deck
        """
        logger.info(f"Generating slides for topic: {slide_deck.topic}")
        
        # Use provided theme or default
        if theme is None:
            theme = SlideTheme(name="Default")
        
        # Initialize the HTML slide deck
        html_deck = SlideDeckHTML(
            topic=slide_deck.topic,
            title=slide_deck.title,
            subtitle=slide_deck.subtitle,
            author=slide_deck.author or "AI Slide Generator",
            theme=theme.dict()
        )
        
        # Get text density setting from theme
        text_density = theme.text_density if hasattr(theme, "text_density") else "balanced"
        
        # Generate HTML for each slide
        for i, slide in enumerate(slide_deck.slides):
            slide_id = f"slide-{i+1}"
            slide_type = slide.type.lower() if hasattr(slide, "type") and slide.type else "content"
            
            # Select generator based on slide type
            html_content = ""
            image_path = None
            
            # Check slide type and generate appropriate HTML
            if i == 0 or slide_type == "title":
                html_content = generate_title_slide(slide)
                slide_type = "title"
            
            elif slide_type == "content" or slide_type == "standard":
                html_content = generate_content_slide(slide)
                slide_type = "content"
            
            elif slide_type == "profile":
                html_content = generate_profile_slide(slide)
                
            elif slide_type == "career":
                html_content = generate_career_slide(slide)
                
            elif slide_type == "timeline":
                html_content = generate_timeline_slide(slide)
                
            elif slide_type == "two_column" or slide_type == "two-column":
                html_content = generate_two_column_slide(slide)
                
            elif slide_type == "image":
                html_content = generate_image_slide(slide)
                
            elif slide_type == "quote":
                html_content = generate_quote_slide(slide)
                
            else:
                # Default to content slide for unknown types
                html_content = generate_content_slide(slide)
                slide_type = "content"
            
            # Add the slide to the deck
            html_slide = HTMLSlide(
                id=slide_id,
                html_content=html_content,
                slide_type=slide_type,
                image_path=image_path
            )
            html_deck.slides.append(html_slide)
        
        return html_deck
    
    def render_full_deck(self, html_deck: SlideDeckHTML, language: str = "ja") -> str:
        """
        Render the complete slide deck as a single HTML document.
        
        Args:
            html_deck: The slide deck to render
            language: The language of the slide deck
            
        Returns:
            Complete HTML document as a string
        """
        return self.renderer.render_full_deck(html_deck, language)
    
    def save_presentation(self, html_deck: SlideDeckHTML, output_path: Optional[Path] = None) -> Path:
        """
        Save the presentation to a file.
        
        Args:
            html_deck: The slide deck to save
            output_path: Optional path to save the presentation to
            
        Returns:
            Path to the saved presentation
        """
        return self.renderer.save_presentation(html_deck, output_path)

def generate_slides(slide_deck: SlideDeck, theme: Optional[SlideTheme] = None, style: str = "professional", language: str = "ja") -> str:
    """
    Public API: Generate HTML slides from a slide deck outline.
    
    Args:
        slide_deck: The slide deck outline to generate slides from
        theme: Optional theme configuration
        style: Style to use if no theme is provided
        language: Language of the slide deck
        
    Returns:
        HTML content of the generated slides
    """
    logger.info(f"Generating slides with style: {style}")
    
    # Create a slide writer agent
    agent = SlideWriterAgent()
    
    # If no theme provided, create one based on style
    if theme is None:
        # Load theme from registry if available
        if style in ["professional", "academic", "creative", "minimal"]:
            theme_from_registry = SlideTheme.load_from_registry(style)
            if theme_from_registry:
                theme = theme_from_registry
            else:
                # Create a basic theme based on style
                if style == "professional":
                    theme = SlideTheme(
                        name="Professional",
                        primary_color="#3B82F6",  # Blue
                        secondary_color="#10B981",  # Green
                        text_density="balanced"
                    )
                elif style == "academic":
                    theme = SlideTheme(
                        name="Academic",
                        primary_color="#4F46E5",  # Indigo
                        secondary_color="#0EA5E9",  # Sky Blue
                        text_density="detailed"
                    )
                elif style == "creative":
                    theme = SlideTheme(
                        name="Creative",
                        primary_color="#EC4899",  # Pink
                        secondary_color="#F59E0B",  # Amber
                        text_density="minimal"
                    )
                elif style == "minimal":
                    theme = SlideTheme(
                        name="Minimal",
                        primary_color="#4B5563",  # Gray
                        secondary_color="#6B7280",  # Light Gray
                        text_density="minimal"
                    )
        else:
            # Default theme
            theme = SlideTheme(name="Default")
    
    # Generate slides
    html_deck = agent.generate_slides(slide_deck, theme)
    
    # Render full HTML document
    return agent.render_full_deck(html_deck, language)

def save_presentation_with_assets(slide_deck: SlideDeck, output_dir: Optional[Path] = None, 
                                 theme: Optional[SlideTheme] = None, style: str = "professional", 
                                 language: str = "ja") -> Path:
    """
    Generate and save a presentation with all necessary assets.
    
    Args:
        slide_deck: The slide deck outline to generate slides from
        output_dir: Directory to save the presentation in
        theme: Optional theme configuration
        style: Style to use if no theme is provided
        language: Language of the slide deck
        
    Returns:
        Path to the saved presentation
    """
    logger.info(f"Generating and saving presentation with style: {style}")
    
    # Create a slide writer agent
    agent = SlideWriterAgent()
    
    # If no theme provided, create one based on style
    if theme is None:
        # Create a basic theme based on style
        if style == "professional":
            theme = SlideTheme(
                name="Professional",
                primary_color="#3B82F6",  # Blue
                secondary_color="#10B981",  # Green
                text_density="balanced"
            )
        elif style == "academic":
            theme = SlideTheme(
                name="Academic",
                primary_color="#4F46E5",  # Indigo
                secondary_color="#0EA5E9",  # Sky Blue
                text_density="detailed"
            )
        elif style == "creative":
            theme = SlideTheme(
                name="Creative",
                primary_color="#EC4899",  # Pink
                secondary_color="#F59E0B",  # Amber
                text_density="minimal"
            )
        elif style == "minimal":
            theme = SlideTheme(
                name="Minimal",
                primary_color="#4B5563",  # Gray
                secondary_color="#6B7280",  # Light Gray
                text_density="minimal"
            )
        else:
            theme = SlideTheme(name="Default")
    
    # Generate slides
    html_deck = agent.generate_slides(slide_deck, theme)
    
    # Save the presentation
    from pathlib import Path
    if output_dir:
        # Create a URL-friendly filename from the title
        filename = slide_deck.title.lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
        output_path = Path(output_dir) / f"{filename}.html"
    else:
        output_path = None
    
    return agent.save_presentation(html_deck, output_path) 