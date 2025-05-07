"""
Slide Content Generators

This module contains specialized generators for different slide types.
"""

import logging
from typing import List, Dict, Any, Optional
from ..outline import SlideContent

# Configure logging
logger = logging.getLogger(__name__)

def generate_title_slide(slide: SlideContent) -> str:
    """
    Generate HTML for a title slide using the appropriate template.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the title slide
    """
    return create_direct_title_html(slide)

def create_direct_title_html(slide: SlideContent) -> str:
    """Create HTML for a title slide directly without rendering a template."""
    html = f"""
    <section class="slide title-slide">
        <div class="slide-content">
            <h1>{slide.title}</h1>
            <h2>{slide.content}</h2>
        </div>
    </section>
    """
    return html

def generate_content_slide(slide: SlideContent) -> str:
    """
    Generate HTML for a standard content slide.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the content slide
    """
    return create_direct_content_html(slide)

def create_direct_content_html(slide: SlideContent) -> str:
    """Create HTML for a content slide directly without rendering a template."""
    # Process content for bullet points if needed
    content_html = ""
    
    # Convert content to bullet points if it's a list
    paragraphs = slide.content.split("\n\n")
    
    if len(paragraphs) > 1:
        content_html = "<ul>"
        for paragraph in paragraphs:
            if paragraph.strip():  # Skip empty paragraphs
                content_html += f"<li>{paragraph.strip()}</li>"
        content_html += "</ul>"
    else:
        content_html = f"<p>{slide.content}</p>"
    
    html = f"""
    <section class="slide content-slide">
        <div class="slide-content">
            <h2>{slide.title}</h2>
            <div class="slide-body">
                {content_html}
            </div>
        </div>
    </section>
    """
    return html

def generate_profile_slide(slide: SlideContent) -> str:
    """
    Generate HTML for a profile slide.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the profile slide
    """
    # Process content for profile information
    return create_direct_content_html(slide)  # Use content slide template for now

def generate_career_slide(slide: SlideContent) -> str:
    """
    Generate HTML for a career slide.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the career slide
    """
    # Process content for career information 
    return create_direct_content_html(slide)  # Use content slide template for now

def generate_timeline_slide(slide: SlideContent) -> str:
    """
    Generate HTML for a timeline slide.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the timeline slide
    """
    # Process content for timeline information
    return create_direct_content_html(slide)  # Use content slide template for now

def generate_two_column_slide(slide: SlideContent) -> str:
    """
    Generate HTML for a two-column slide.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the two-column slide
    """
    # Process content for two columns
    return create_direct_content_html(slide)  # Use content slide template for now

def generate_image_slide(slide: SlideContent) -> str:
    """
    Generate HTML for an image slide.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the image slide
    """
    # Create basic image slide
    html = f"""
    <section class="slide image-slide">
        <div class="slide-content">
            <h2>{slide.title}</h2>
            <div class="slide-image">
                <img src="/static/images/placeholder.jpg" alt="{slide.title}">
            </div>
            <p>{slide.content}</p>
        </div>
    </section>
    """
    return html

def generate_quote_slide(slide: SlideContent) -> str:
    """
    Generate HTML for a quote slide.
    
    Args:
        slide: The slide content to generate HTML for
        
    Returns:
        HTML content for the quote slide
    """
    # Create basic quote slide
    html = f"""
    <section class="slide quote-slide">
        <div class="slide-content">
            <blockquote>
                <p>{slide.content}</p>
                <cite>{slide.title}</cite>
            </blockquote>
        </div>
    </section>
    """
    return html

def optimize_image_layout(suggestion: str) -> str:
    """
    Optimize image layout based on AI suggestions.
    
    Args:
        suggestion: Suggestion text from AI
        
    Returns:
        Optimized suggestion
    """
    # This is a placeholder for future image layout optimization
    # This function would interpret AI suggestions for image placement
    # and convert them to actual layout instructions
    
    # For now, just return the original suggestion
    return suggestion

def split_text_to_bullets(paragraphs: List[str], max_chars: int = 90, text_density: str = "balanced") -> List[str]:
    """
    Split text into bullet points based on density preference.
    
    Args:
        paragraphs: List of paragraph strings
        max_chars: Maximum characters per bullet
        text_density: Preference for text density (minimal, balanced, detailed)
        
    Returns:
        List of bullet points
    """
    bullets = []
    
    # Adjust max_chars based on text_density
    if text_density == "minimal":
        # Shorter bullets for minimal text
        adjusted_max = max(40, max_chars - 30)
    elif text_density == "detailed":
        # Longer bullets for detailed text
        adjusted_max = max_chars + 30
    else:
        # Default for "balanced"
        adjusted_max = max_chars
        
    # Process each paragraph
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        # If paragraph is already short enough, use as is
        if len(paragraph) <= adjusted_max:
            bullets.append(paragraph)
            continue
            
        # Check if paragraph has natural breaks (sentences)
        sentences = paragraph.split('. ')
        if len(sentences) > 1:
            # Add each sentence as a bullet
            current_bullet = ""
            for sentence in sentences:
                # Add period back if it was removed by split
                if not sentence.endswith('.'):
                    sentence += '.'
                    
                # If adding this sentence would make the bullet too long,
                # add the current bullet and start a new one
                if len(current_bullet) + len(sentence) > adjusted_max and current_bullet:
                    bullets.append(current_bullet.strip())
                    current_bullet = sentence
                else:
                    if current_bullet:
                        current_bullet += ' ' + sentence
                    else:
                        current_bullet = sentence
                        
            # Add the last bullet if not empty
            if current_bullet:
                bullets.append(current_bullet.strip())
        else:
            # No natural breaks, just truncate
            for i in range(0, len(paragraph), adjusted_max):
                chunk = paragraph[i:i+adjusted_max]
                if i+adjusted_max < len(paragraph):
                    # Find the last space to break at
                    last_space = chunk.rfind(' ')
                    if last_space > adjusted_max * 0.7:  # Only break at space if it's not too early
                        bullets.append(chunk[:last_space])
                        # Start next chunk from the character after the space
                        i = i + last_space + 1 - adjusted_max  # Adjust i for the next iteration
                    else:
                        bullets.append(chunk)
                else:
                    bullets.append(chunk)
    
    return bullets 