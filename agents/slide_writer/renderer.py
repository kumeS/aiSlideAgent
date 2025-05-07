"""
Slide Renderer

This module handles rendering of slides to HTML format and saving presentations.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader

from .models import SlideDeckHTML

# Configure logging
logger = logging.getLogger(__name__)

# Constants
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "static" / "output"

class SlideRenderer:
    """Handles rendering of HTML slides and saving presentations."""
    
    def __init__(self, templates_dir: Optional[Path] = None):
        """Initialize the renderer with template directory."""
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.jinja_env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )
        
        # Create output directory if it doesn't exist
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def get_template_with_fallback(self, primary_template: str, fallback_template: str = "_slide_content.html") -> Any:
        """
        Get a template with fallback if the primary template doesn't exist.
        
        Args:
            primary_template: The name of the template to use
            fallback_template: The name of the fallback template
            
        Returns:
            The template
        """
        try:
            return self.jinja_env.get_template(primary_template)
        except Exception as e:
            logger.warning(f"Template {primary_template} not found, using fallback: {e}")
            try:
                return self.jinja_env.get_template(fallback_template)
            except Exception as fallback_error:
                logger.error(f"Fallback template also not found: {fallback_error}")
                # Return a basic template as last resort
                from jinja2 import Template
                return Template("""
                <section class="slide">
                    <div class="slide-content">
                        <h2>{{ title }}</h2>
                        <div class="slide-body">{{ content|safe }}</div>
                    </div>
                </section>
                """)
    
    def render_full_deck(self, html_deck: SlideDeckHTML, language: str = "ja") -> str:
        """
        Render the complete slide deck as a single HTML document.
        
        Args:
            html_deck: The slide deck to render
            language: The language of the slide deck
            
        Returns:
            Complete HTML document as a string
        """
        logger.info(f"Rendering full slide deck: {html_deck.title}")
        
        # Get the main template for the slide deck
        try:
            template = self.jinja_env.get_template("slide_deck.html")
        except Exception as e:
            logger.error(f"Error loading slide deck template: {e}")
            # Fallback to a basic template
            from jinja2 import Template
            template = Template("""
            <!DOCTYPE html>
            <html lang="{{ language }}">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{{ title }}</title>
                <style>
                    /* Basic slide styles */
                    body {
                        font-family: system-ui, -apple-system, sans-serif;
                        background-color: #111827;
                        color: #F9FAFB;
                        margin: 0;
                        padding: 0;
                    }
                    .slide {
                        min-height: 100vh;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        padding: 2rem;
                        box-sizing: border-box;
                        border-bottom: 1px solid #333;
                    }
                    .slide-content {
                        max-width: 1000px;
                        width: 100%;
                    }
                    h1, h2 {
                        color: #3B82F6;
                    }
                    h1 {
                        font-size: 3rem;
                    }
                    h2 {
                        font-size: 2.5rem;
                    }
                    ul {
                        line-height: 1.6;
                    }
                    /* Add custom CSS variables from theme */
                    {{ css_variables }}
                </style>
            </head>
            <body>
                {{ slides|safe }}
            </body>
            </html>
            """)
        
        # Generate CSS variables from theme
        css_variables = ""
        if hasattr(html_deck, 'theme') and hasattr(html_deck.theme, 'get_css_variables'):
            variables = html_deck.theme.get_css_variables()
            css_variables = ":root {\n"
            for var_name, var_value in variables.items():
                css_variables += f"    {var_name}: {var_value};\n"
            css_variables += "}"
        
        # Combine all slide HTML content
        slides_html = ""
        for slide in html_deck.slides:
            slides_html += slide.html_content + "\n"
        
        # Render the complete template
        return template.render(
            title=html_deck.title,
            subtitle=html_deck.subtitle,
            author=html_deck.author,
            slides=slides_html,
            css_variables=css_variables,
            language=language
        )
    
    def save_presentation(self, html_deck: SlideDeckHTML, output_path: Optional[Path] = None) -> Path:
        """
        Save the presentation to a file.
        
        Args:
            html_deck: The slide deck to save
            output_path: Optional path to save the presentation to
            
        Returns:
            Path to the saved presentation
        """
        # Generate full HTML content
        html_content = self.render_full_deck(html_deck)
        
        # Determine output path
        if output_path is None:
            # Create a URL-friendly filename from the title
            filename = html_deck.title.lower().replace(' ', '_').replace('/', '_').replace('\\', '_')
            output_path = OUTPUT_DIR / f"{filename}.html"
        
        # Ensure the directory exists
        os.makedirs(output_path.parent, exist_ok=True)
        
        # Write the HTML to a file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Presentation saved to {output_path}")
        return output_path

def save_presentation_to_file(html_deck: SlideDeckHTML, output_path: Optional[Path] = None) -> Path:
    """
    Save the presentation to a file. Convenience function for direct use.
    
    Args:
        html_deck: The slide deck to save
        output_path: Optional path to save the presentation to
        
    Returns:
        Path to the saved presentation
    """
    renderer = SlideRenderer()
    return renderer.save_presentation(html_deck, output_path) 