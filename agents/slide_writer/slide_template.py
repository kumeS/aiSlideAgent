"""
Slide Template Module

Handles the generation of individual slide HTML with reusable templates.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from .slide_writer import SlideTheme
from ..outline import SlideContent

# Configure logging
logger = logging.getLogger(__name__)

class SlideTemplate:
    """Class for generating individual slide HTML with reusable templates."""
    
    @staticmethod
    def generate_slide_html(slide: SlideContent, theme: SlideTheme, slide_num: int, total_slides: int) -> str:
        """
        Generate HTML for an individual slide.
        
        Args:
            slide: The slide content
            theme: The slide theme
            slide_num: The slide number
            total_slides: Total number of slides
            
        Returns:
            HTML for the individual slide
        """
        try:
            slide_type = slide.type.lower() if hasattr(slide, 'type') else "content"
            slide_title = slide.title if hasattr(slide, 'title') and slide.title else f"スライド {slide_num}"
            slide_content = slide.content if hasattr(slide, 'content') and slide.content else []
            
            # Apply text density adjustments
            text_density = getattr(theme, "text_density", "balanced")
            max_bullet_points = getattr(theme, "max_bullet_points", 6)
            
            # Adjust content based on text density
            if text_density == "minimal":
                # For minimal, use fewer bullet points with shorter text
                if len(slide_content) > max_bullet_points // 2:
                    slide_content = slide_content[:max_bullet_points // 2]
                # Truncate long bullet points
                slide_content = [_truncate_text(point, 80) for point in slide_content]
            elif text_density == "balanced":
                # For balanced, use moderate number of bullet points
                if len(slide_content) > max_bullet_points:
                    slide_content = slide_content[:max_bullet_points]
                # Moderate truncation
                slide_content = [_truncate_text(point, 120) for point in slide_content]
            elif text_density == "detailed":
                # For detailed, keep more content but still respect maximum
                if len(slide_content) > max_bullet_points + 2:
                    slide_content = slide_content[:max_bullet_points + 2]
                # Allow longer text
                slide_content = [_truncate_text(point, 200) for point in slide_content]
            
            # Add additional theme CSS variables
            css_variables = {
                "--primary-color": theme.primary_color,
                "--secondary-color": theme.secondary_color,
                "--text-color": theme.text_color,
                "--background-color": theme.background_color,
                "--accent-color": getattr(theme, "accent_color", "#F59E0B"),
                "--font-family": theme.font_family,
                "--slide-index": str(slide_num),
                "--total-slides": str(total_slides),
            }
            
            # Add heading font if available
            if hasattr(theme, "heading_font") and theme.heading_font:
                css_variables["--heading-font"] = theme.heading_font
            else:
                css_variables["--heading-font"] = theme.font_family
                
            # Add code font if available
            if hasattr(theme, "code_font") and theme.code_font:
                css_variables["--code-font"] = theme.code_font
            
            # Generate CSS variables string
            css_vars = "\n        ".join([f"{key}: {value};" for key, value in css_variables.items()])
            
            # Choose bullet style based on theme setting or default to circle
            bullet_style = "fa-circle"
            if hasattr(theme, "bullet_style"):
                if theme.bullet_style == "square":
                    bullet_style = "fa-square"
                elif theme.bullet_style == "dash":
                    bullet_style = "fa-minus"
                elif theme.bullet_style == "arrow":
                    bullet_style = "fa-chevron-right"
                    
            # Choose header style based on theme
            header_style_class = "gradient-header"
            if hasattr(theme, "header_style"):
                if theme.header_style == "solid":
                    header_style_class = "solid-header"
                elif theme.header_style == "minimal":
                    header_style_class = "minimal-header"
                elif theme.header_style == "none":
                    header_style_class = "no-header"
            
            # Add class based on text density
            text_density_class = f"text-density-{text_density}"
            
            # Create base HTML structure for an individual slide
            html_head = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スライド {slide_num} - {slide_title}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            {css_vars}
        }}
        
        body {{
            font-family: var(--font-family);
            background-color: var(--background-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            min-height: 100vh;
        }}
        
        /* External navigation bar */
        .external-nav {{
            width: 100%;
            background-color: rgba(0, 0, 0, 0.3);
            padding: 0.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }}
        
        .index-button {{
            background-color: var(--accent-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            transition: opacity 0.2s;
        }}
        
        .index-button:hover {{
            opacity: 0.9;
        }}
        
        /* Hide external nav in slideshow mode */
        body.in-slideshow .external-nav {{
            display: none;
        }}
        
        .slide {{
            width: 90%;
            max-width: 1000px;
            height: auto;
            min-height: 70vh;
            padding: 2rem 3rem;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: flex-start;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
        }}
        
        /* Text density styles - スライドの文字量に応じたスタイル */
        .text-density-minimal .content ul li {{
            margin-bottom: 2rem;
            font-size: 1.4rem;
        }}
        
        .text-density-minimal .subcontent {{
            display: none; /* 最小限モードではサブコンテンツを非表示 */
        }}
        
        .text-density-balanced .content ul li {{
            margin-bottom: 1.2rem;
            font-size: 1.2rem;
        }}
        
        .text-density-detailed .content ul li {{
            margin-bottom: 0.8rem;
            font-size: 1.1rem;
        }}
        
        .text-density-detailed .content ul li.indent-1 {{
            margin-left: 2rem;
            font-size: 1rem;
            opacity: 0.9;
        }}
        
        .text-density-detailed .subcontent {{
            display: block;
        }}

        /* 個別スライドページでは文章量調整ボタンを表示しない */
        .density-controls {{
            display: none;
        }}
        
        h1, h2 {{
            font-family: var(--heading-font, var(--font-family));
            color: var(--primary-color);
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 3.5rem;
            font-weight: 700;
        }}
        
        h2 {{
            font-size: 2.5rem;
            font-weight: 600;
        }}
        
        .title-slide {{
            text-align: center;
            align-items: center;
            justify-content: center;
        }}
        
        .subtitle {{
            font-size: 1.8rem;
            margin-bottom: 2rem;
            opacity: 0.8;
        }}
        
        .title-content {{
            margin: 2rem 0;
        }}
        
        .title-point {{
            font-size: 1.4rem;
            margin: 1rem 0;
        }}
        
        /* Header Styles */
        .gradient-header {{
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            padding: 1.5rem;
            margin: -2rem -3rem 2rem -3rem;
            border-radius: 8px 8px 0 0;
        }}
        
        .gradient-header h2 {{
            color: white;
            margin-bottom: 0;
        }}
        
        .solid-header {{
            background-color: var(--primary-color);
            padding: 1.5rem;
            margin: -2rem -3rem 2rem -3rem;
            border-radius: 8px 8px 0 0;
        }}
        
        .solid-header h2 {{
            color: white;
            margin-bottom: 0;
        }}
        
        .minimal-header {{
            border-bottom: 3px solid var(--primary-color);
            padding-bottom: 1rem;
            margin-bottom: 2rem;
        }}
        
        .no-header {{
            margin-bottom: 2rem;
        }}
        
        /* Content Styles */
        .slide-content {{
            width: 100%;
            flex: 1;
        }}
        
        .bullet-list {{
            list-style: none;
            padding: 0;
            margin: 1rem 0;
            width: 100%;
        }}
        
        .bullet-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 1.5rem;
            font-size: 1.5rem;
        }}
        
        .bullet-icon {{
            color: var(--secondary-color);
            margin-right: 1rem;
            font-size: 0.8em;
            min-width: 1em;
        }}
        
        /* Detailed mode styling */
        .text-density-detailed .bullet-item {{
            margin-bottom: 2rem;
        }}
        
        .bullet-content {{
            flex: 1;
        }}
        
        /* Sub-bullet styling */
        .sub-bullet-list {{
            list-style: none;
            padding-left: 2.5rem;
            margin: 0.5rem 0 0 0;
            width: 100%;
        }}
        
        .sub-bullet-item {{
            display: flex;
            align-items: flex-start;
            margin-bottom: 0.75rem;
            font-size: 1.3rem;
            opacity: 0.9;
        }}
        
        .sub-bullet-icon {{
            color: var(--accent-color);
            margin-right: 0.75rem;
            font-size: 0.7em;
            min-width: 0.8em;
        }}
        
        .slide-footer {{
            margin-top: auto;
            width: 100%;
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            opacity: 0.7;
            padding-top: 2rem;
        }}
        
        /* Image Styles */
        .image-container {{
            width: 100%;
            margin: 2rem auto;
            text-align: center;
        }}
        
        .image-container img {{
            max-width: 100%;
            max-height: 50vh;
            object-fit: contain;
        }}
        
        /* Quote Styles */
        .quote-container {{
            width: 100%;
            margin: 2rem 0;
            padding: 2rem;
            border-left: 5px solid var(--accent-color);
            background-color: rgba(0, 0, 0, 0.05);
        }}
        
        .quote-text {{
            font-size: 1.8rem;
            font-style: italic;
            margin-bottom: 1rem;
        }}
        
        .quote-author {{
            font-size: 1.2rem;
            text-align: right;
        }}
        
        /* Two-column Layout */
        .two-column {{
            display: flex;
            gap: 2rem;
            width: 100%;
        }}
        
        .column {{
            flex: 1;
        }}
        
        /* Responsive Design */
        @media (max-width: 768px) {{
            .slide {{
                padding: 1.5rem;
            }}
            
            h1 {{
                font-size: 2.5rem;
            }}
            
            h2 {{
                font-size: 2rem;
            }}
            
            .bullet-item {{
                font-size: 1.3rem;
            }}
            
            .two-column {{
                flex-direction: column;
                gap: 1rem;
            }}
        }}
    </style>
</head>
<body>"""

            # Add navigation bar
            html_nav = f"""
    <div class="external-nav">
        <a href="index.html" class="index-button">
            <i class="fas fa-home"></i> 目次に戻る
        </a>
        <span class="slide-info">スライド {slide_num}/{total_slides}</span>
    </div>"""
            
            # Combine head and nav
            html = html_head + html_nav
            
            # Add content based on slide type
            if slide_type == "title":
                title_html = f"""
    <div class="slide title-slide {text_density_class}">
        <h1>{slide_title}</h1>"""
                
                if hasattr(slide, 'subtitle') and slide.subtitle:
                    title_html += f"""
        <div class="subtitle">{slide.subtitle}</div>"""
                elif slide_content:
                    title_html += f"""
        <div class="subtitle">{slide_content[0]}</div>"""
                    slide_content = slide_content[1:]
                
                if slide_content:
                    title_html += f"""
        <div class="title-content">"""
                    
                    for point in slide_content:
                        title_html += f"""
            <div class="title-point">{point}</div>"""
                        
                    title_html += """
        </div>"""
                
                title_html += f"""
        <div class="slide-footer">
            <span>スライド {slide_num}/{total_slides}</span>
        </div>
    </div>
</body>
</html>"""
                return html + title_html
            elif slide_type == "image":
                image_html = f"""
    <div class="slide image-slide {text_density_class}">
        <div class="{header_style_class}">
            <h2>{slide_title}</h2>
        </div>
        <div class="slide-content">
            <div class="image-container">
                <img src="{slide.image_url if hasattr(slide, 'image_url') and slide.image_url else ''}" alt="{slide.image_alt if hasattr(slide, 'image_alt') and slide.image_alt else slide_title}">
            </div>
            
            <ul class="bullet-list">"""
                
                for point in slide_content:
                    image_html += f"""
                <li class="bullet-item">
                    <i class="bullet-icon fas {bullet_style}"></i>
                    <div class="bullet-content">
                        <span>{point}</span>
                    </div>
                </li>"""
                    
                image_html += """
            </ul>
        </div>
        <div class="slide-footer">
            <span>スライド {0}/{1}</span>
        </div>
    </div>
</body>
</html>""".format(slide_num, total_slides)
                return html + image_html
            elif slide_type == "quote":
                quote_html = f"""
    <div class="slide quote-slide {text_density_class}">
        <div class="{header_style_class}">
            <h2>{slide_title}</h2>
        </div>
        <div class="slide-content">
            <div class="quote-container">
                <div class="quote-text">{slide.quote if hasattr(slide, 'quote') and slide.quote else slide_content[0] if slide_content else ""}</div>
                <div class="quote-author">{slide.author if hasattr(slide, 'author') and slide.author else slide_content[1] if len(slide_content) > 1 else ""}</div>
            </div>
            
            <ul class="bullet-list">"""
                
                # Add additional points if any (skip the first 2 that are used for quote and author)
                extra_content = slide_content[2:] if len(slide_content) > 2 else []
                for point in extra_content:
                    quote_html += f"""
                <li class="bullet-item">
                    <i class="bullet-icon fas {bullet_style}"></i>
                    <div class="bullet-content">
                        <span>{point}</span>
                    </div>
                </li>"""
                    
                quote_html += """
            </ul>
        </div>
        <div class="slide-footer">
            <span>スライド {0}/{1}</span>
        </div>
    </div>
</body>
</html>""".format(slide_num, total_slides)
                return html + quote_html
            elif slide_type == "two-column":
                column_html = f"""
    <div class="slide two-column-slide {text_density_class}">
        <div class="{header_style_class}">
            <h2>{slide_title}</h2>
        </div>
        <div class="slide-content">
            <div class="two-column">
                <div class="column">
                    <ul class="bullet-list">"""
                
                # First half of bullets go in left column
                left_content = slide_content[:len(slide_content)//2]
                for point in left_content:
                    column_html += f"""
                        <li class="bullet-item">
                            <i class="bullet-icon fas {bullet_style}"></i>
                            <div class="bullet-content">
                                <span>{point}</span>
                            </div>
                        </li>"""
                
                column_html += """
                    </ul>
                </div>
                <div class="column">
                    <ul class="bullet-list">"""
                
                # Second half of bullets go in right column
                right_content = slide_content[len(slide_content)//2:]
                for point in right_content:
                    column_html += f"""
                        <li class="bullet-item">
                            <i class="bullet-icon fas {bullet_style}"></i>
                            <div class="bullet-content">
                                <span>{point}</span>
                            </div>
                        </li>"""
                
                column_html += """
                    </ul>
                </div>
            </div>
        </div>
        <div class="slide-footer">
            <span>スライド {0}/{1}</span>
        </div>
    </div>
</body>
</html>""".format(slide_num, total_slides)
                return html + column_html
            else:  # Default: if not a recognized type, use content slide
                content_html = f"""
    <div class="slide content-slide {text_density_class}">
        <div class="{header_style_class}">
            <h2>{slide_title}</h2>
        </div>
        <div class="slide-content">
            <ul class="bullet-list">"""
            
            for point in slide_content:
                # Handle sub-bullets in detailed mode (indicated by indentation with spaces or tabs)
                if text_density == "detailed" and (point.startswith("  •") or point.startswith("\t•")):
                    # This is a sub-bullet point
                    point = point.lstrip(" \t•").strip()
                    content_html += f"""
                <li class="sub-bullet-item">
                    <i class="sub-bullet-icon fas fa-circle"></i>
                    <div class="bullet-content">
                        <span>{point}</span>
                    </div>
                </li>"""
                else:
                    # Handle multi-level bullet points for detailed view
                    if text_density == "detailed" and "• " in point[1:]:
                        # Split into main point and sub-points
                        parts = point.split("• ")
                        main_point = parts[0].strip()
                        
                        content_html += f"""
                <li class="bullet-item">
                    <i class="bullet-icon fas {bullet_style}"></i>
                    <div class="bullet-content">
                        <span>{main_point}</span>
                        <ul class="sub-bullet-list">"""
                        
                        for i, sub_point in enumerate(parts[1:]):
                            if sub_point.strip():
                                content_html += f"""
                            <li class="sub-bullet-item">
                                <i class="sub-bullet-icon fas fa-circle"></i>
                                <span>{sub_point.strip()}</span>
                            </li>"""
                        
                        content_html += """
                        </ul>
                    </div>
                </li>"""
                    else:
                        # Regular bullet point
                        content_html += f"""
                <li class="bullet-item">
                    <i class="bullet-icon fas {bullet_style}"></i>
                    <div class="bullet-content">
                        <span>{point}</span>
                    </div>
                </li>"""
            
            content_html += """
            </ul>
        </div>
        <div class="slide-footer">
            <span>スライド {0}/{1}</span>
        </div>
    </div>
</body>
</html>""".format(slide_num, total_slides)
            
            return html + content_html
        except Exception as e:
            logger.error(f"Error generating individual slide HTML: {str(e)}")
            # Return a fallback slide with error message
            return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スライド {slide_num} - エラー</title>
    <style>
        body {{ font-family: sans-serif; background-color: #f5f5f5; color: #333; padding: 2rem; }}
        .slide {{ max-width: 800px; margin: 0 auto; background: white; padding: 2rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h2 {{ color: #e53e3e; }}
        .back-link {{ display: inline-block; margin-top: 1rem; color: #3182ce; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="slide">
        <h2>スライド生成エラー</h2>
        <p>スライド {slide_num} の生成中にエラーが発生しました：</p>
        <pre>{str(e)}</pre>
        <p><a href="index.html" class="back-link"><i class="fas fa-home"></i> 目次に戻る</a></p>
    </div>
</body>
</html>"""

    @staticmethod
    def create_slideshow_html(slide_files, topic, theme, slides_dir):
        """
        Create an index HTML file that provides navigation to individual slides.
        
        Args:
            slide_files: List of slide file paths
            topic: The presentation topic
            theme: The slide theme
            slides_dir: Directory containing the slides
            
        Returns:
            HTML for the index/slideshow page
        """
        # Validate input parameters
        if not slide_files:
            logger.error("No slide files provided")
            slide_files = []
            
        # CSS variables from theme
        css_variables = {
            "--primary-color": theme.primary_color,
            "--secondary-color": theme.secondary_color,
            "--text-color": theme.text_color,
            "--background-color": theme.background_color,
            "--accent-color": getattr(theme, "accent_color", "#F59E0B"),
        }
        
        # Generate CSS variables string
        css_vars = "\n        ".join([f"{key}: {value};" for key, value in css_variables.items()])
        
        # Start building the HTML
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - スライドショー</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            {css_vars}
        }}
        
        body {{
            font-family: var(--font-family, 'Noto Sans JP', 'Montserrat', sans-serif);
            background-color: var(--background-color);
            color: var(--text-color);
            margin: 0;
            padding: 3rem;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1 {{
            color: var(--primary-color);
            font-size: 3rem;
            margin-bottom: 2rem;
            text-align: center;
        }}
        
        .slide-list {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 2rem;
            margin: 3rem 0;
        }}
        
        .slide-card {{
            background-color: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            overflow: hidden;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
        }}
        
        .slide-card a {{
            display: block;
            padding: 2rem;
            color: var(--text-color);
            text-decoration: none;
        }}
        
        .slide-number {{
            display: block;
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
            color: var(--secondary-color);
        }}
        
        .slide-title {{
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }}
        
        .controls {{
            display: flex;
            justify-content: center;
            margin-top: 3rem;
        }}
        
        .start-button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 1rem 2rem;
            font-size: 1.2rem;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }}
        
        .start-button:hover {{
            background-color: var(--secondary-color);
        }}
        
        .iframe-mode {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 100;
        }}
        
        .iframe-mode iframe {{
            width: 100%;
            height: 100%;
            border: none;
        }}
        
        .iframe-controls {{
            position: fixed;
            bottom: 1rem;
            left: 0;
            right: 0;
            display: flex;
            justify-content: center;
            gap: 1rem;
            z-index: 101;
        }}
        
        .iframe-button {{
            background-color: var(--primary-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            cursor: pointer;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{topic}</h1>
        
        <div class="slide-list">
"""
        
        # Get the actual slide files
        valid_slide_files = []
        for slide_file in slide_files:
            if os.path.exists(slide_file) and os.path.isfile(slide_file):
                valid_slide_files.append(slide_file)
                
        # If no valid slide files, create a fallback
        if not valid_slide_files:
            logger.warning("No valid slide files found, creating fallback")
            fallback_path = os.path.join(slides_dir, "slide_01.html")
            with open(fallback_path, 'w', encoding='utf-8') as f:
                f.write(f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スライド 1</title>
    <style>
        body {{ font-family: 'Noto Sans JP', sans-serif; background-color: #111827; color: #F9FAFB; margin: 0; padding: 2rem; }}
        .slide {{ display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 90vh; }}
        h2 {{ color: #3B82F6; }}
    </style>
</head>
<body>
    <div class="slide">
        <h2>{topic}</h2>
        <p>スライドを生成できませんでした。</p>
    </div>
</body>
</html>""")
            valid_slide_files = [fallback_path]
            
        # Extract titles from slides
        import re
        for i, slide_file in enumerate(valid_slide_files, 1):
            slide_filename = os.path.basename(slide_file)
            try:
                # Get slide title from HTML
                with open(slide_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Try to extract title
                slide_title = f"スライド {i}"  # Default title
                title_match = re.search(r'<title>スライド \d+ - (.+?)</title>', content)
                if title_match:
                    slide_title = title_match.group(1)
                else:
                    # Try h1 or h2 tags
                    h1_match = re.search(r'<h1>(.+?)</h1>', content)
                    h2_match = re.search(r'<h2>(.+?)</h2>', content)
                    if h1_match:
                        slide_title = h1_match.group(1)
                    elif h2_match:
                        slide_title = h2_match.group(1)
                
                html += f"""            <div class="slide-card">
                <a href="{slide_filename}">
                    <span class="slide-number">スライド {i}</span>
                    <div class="slide-title">{slide_title}</div>
                </a>
            </div>
"""
            except Exception as e:
                logger.error(f"Error processing slide file {slide_file}: {str(e)}")
                html += f"""            <div class="slide-card">
                <a href="{slide_filename}">
                    <span class="slide-number">スライド {i}</span>
                    <div class="slide-title">スライド {i}</div>
                </a>
            </div>
"""
            
        # Complete the HTML
        html += """        </div>
        
        <div class="controls">
            <button id="start-presentation" class="start-button">
                <i class="fas fa-play-circle"></i> プレゼンテーションを開始
            </button>
        </div>
    </div>
    
    <div id="iframe-mode" class="iframe-mode">
        <iframe id="slide-iframe" src=""></iframe>
        <div class="iframe-controls">
            <div class="density-controls">
                <button class="density-button" data-density="minimal" title="少ないテキスト・簡潔なポイント">
                    <i class="fas fa-compress-alt"></i> 最小限
                </button>
                <button class="density-button active" data-density="balanced" title="バランスの取れた内容量">
                    <i class="fas fa-balance-scale"></i> バランス
                </button>
                <button class="density-button" data-density="detailed" title="詳細な内容・補足情報を豊富に含む">
                    <i class="fas fa-expand-alt"></i> 詳細
                </button>
            </div>
            <button id="prev-slide" class="iframe-button"><i class="fas fa-arrow-left"></i> 前へ</button>
            <button id="exit-presentation" class="iframe-button"><i class="fas fa-times"></i> 終了</button>
            <button id="next-slide" class="iframe-button">次へ <i class="fas fa-arrow-right"></i></button>
        </div>
    </div>
    
    <script>
        // Slideshow functionality
        document.addEventListener('DOMContentLoaded', function() {
            const slides = [
"""
        
        # Add slides to JS array
        for i, slide_file in enumerate(valid_slide_files):
            slide_filename = os.path.basename(slide_file)
            html += f"""                "{slide_filename}"{'' if i == len(valid_slide_files) - 1 else ','}
"""
            
        # Add text density controls JavaScript
        html += """            ];
            
            // Text density settings
            const textDensitySettings = {
                minimal: {
                    name: "最小限",
                    description: "少ないテキスト・簡潔なポイント",
                    icon: "fa-compress-alt"
                },
                balanced: {
                    name: "バランス",
                    description: "バランスの取れた内容量",
                    icon: "fa-balance-scale"
                },
                detailed: {
                    name: "詳細",
                    description: "詳細な内容・補足情報を豊富に含む",
                    icon: "fa-expand-alt"
                }
            };
            
            let currentSlideIndex = 0;
            let currentTextDensity = "balanced"; // Default
            const iframeMode = document.getElementById('iframe-mode');
            const slideIframe = document.getElementById('slide-iframe');
            const startButton = document.getElementById('start-presentation');
            const exitButton = document.getElementById('exit-presentation');
            const prevButton = document.getElementById('prev-slide');
            const nextButton = document.getElementById('next-slide');
            const densityButtons = document.querySelectorAll('.density-button');
            
            // Try to load previous setting
            try {
                const savedDensity = localStorage.getItem('preferredTextDensity');
                if (savedDensity && textDensitySettings[savedDensity]) {
                    currentTextDensity = savedDensity;
                    // Update UI to match saved density
                    densityButtons.forEach(button => {
                        const buttonDensity = button.getAttribute('data-density');
                        button.classList.toggle('active', buttonDensity === currentTextDensity);
                    });
                }
            } catch (e) {
                console.warn("Could not load saved preference:", e);
            }
            
            // Start presentation
            startButton.addEventListener('click', function() {
                iframeMode.style.display = 'block';
                document.body.style.overflow = 'hidden';
                loadSlide(0);
            });
            
            // Exit presentation
            exitButton.addEventListener('click', function() {
                iframeMode.style.display = 'none';
                document.body.style.overflow = 'auto';
            });
            
            // Navigate to previous slide
            prevButton.addEventListener('click', function() {
                if (currentSlideIndex > 0) {
                    loadSlide(currentSlideIndex - 1);
                }
            });
            
            // Navigate to next slide
            nextButton.addEventListener('click', function() {
                if (currentSlideIndex < slides.length - 1) {
                    loadSlide(currentSlideIndex + 1);
                }
            });
            
            // Setup text density buttons
            densityButtons.forEach(button => {
                button.addEventListener('click', function() {
                    const density = this.getAttribute('data-density');
                    applyTextDensity(density);
                    
                    // Update active state
                    densityButtons.forEach(btn => {
                        btn.classList.toggle('active', btn === this);
                    });
                });
            });
            
            // Load slide by index
            function loadSlide(index) {
                if (index >= 0 && index < slides.length) {
                    currentSlideIndex = index;
                    slideIframe.src = slides[index];
                    
                    // Update button states
                    prevButton.disabled = (index === 0);
                    nextButton.disabled = (index === slides.length - 1);
                    
                    // Apply text density settings to the iframe
                    slideIframe.onload = function() {
                        try {
                            // iframeの中のドキュメントを取得
                            const doc = slideIframe.contentDocument || slideIframe.contentWindow.document;
                            // スライドショーモード用のクラスを追加
                            doc.body.classList.add('in-slideshow');
                            // 文章量の設定を適用
                            applyTextDensity(currentTextDensity);
                        } catch (e) {
                            console.error("Failed to apply settings to iframe:", e);
                        }
                    };
                }
            }
            
            // Function to apply text density to the current slide
            function applyTextDensity(density) {
                try {
                    const doc = slideIframe.contentDocument || slideIframe.contentWindow.document;
                    const slide = doc.querySelector('.slide');
                    
                    if (slide) {
                        // Remove existing density classes
                        slide.classList.remove('text-density-minimal', 'text-density-balanced', 'text-density-detailed');
                        // Add new density class
                        slide.classList.add('text-density-' + density);
                        
                        // Store current density
                        currentTextDensity = density;
                        
                        // Store preference if possible
                        try {
                            localStorage.setItem('preferredTextDensity', density);
                        } catch (e) {
                            console.warn("Could not save preference:", e);
                        }
                        
                        console.log("Applied text density:", density);
                    } else {
                        console.warn("No slide element found in iframe");
                    }
                } catch (e) {
                    console.error("Error applying text density:", e);
                }
            }
            
            // Keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (iframeMode.style.display === 'block') {
                    if (e.key === 'ArrowLeft') {
                        if (currentSlideIndex > 0) {
                            loadSlide(currentSlideIndex - 1);
                        }
                    } else if (e.key === 'ArrowRight') {
                        if (currentSlideIndex < slides.length - 1) {
                            loadSlide(currentSlideIndex + 1);
                        }
                    } else if (e.key === 'Escape') {
                        iframeMode.style.display = 'none';
                        document.body.style.overflow = 'auto';
                    }
                }
            });
        });
    </script>
"""
        
        # Add CSS for the density controls
        html += """
    <style>
        /* Density Control Buttons */
        .density-controls {
            display: flex;
            margin-right: 1rem;
        }
        
        .density-button {
            background-color: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 0.4rem 0.8rem;
            margin: 0 0.2rem;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.2s;
            display: flex;
            align-items: center;
        }
        
        .density-button i {
            margin-right: 0.4rem;
        }
        
        .density-button:hover {
            background-color: rgba(255, 255, 255, 0.3);
        }
        
        .density-button.active {
            background-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5);
        }
    </style>
</body>
</html>"""
        
        return html 

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