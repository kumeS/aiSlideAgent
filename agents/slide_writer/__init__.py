"""
Slide Writer Agent Module

Handles the generation of slide HTML content from slide deck outlines.
"""

# Import from new modules
from .models import HTMLSlide, SlideDeckHTML
from .themes import SlideTheme
from .generators import (
    generate_title_slide, generate_content_slide, generate_profile_slide,
    generate_career_slide, generate_timeline_slide, generate_two_column_slide,
    generate_image_slide, generate_quote_slide, split_text_to_bullets
)
from .renderer import SlideRenderer, save_presentation_to_file
from .slide_writer import SlideWriterAgent, generate_slides, save_presentation_with_assets

from .template_registry import template_registry, TemplateRegistry
from .slide_template import SlideTemplate
import logging

# Setup logging
logger = logging.getLogger(__name__)

__all__ = [
    # Main classes
    "SlideWriterAgent", 
    "SlideTheme", 
    "HTMLSlide", 
    "SlideDeckHTML", 
    "SlideRenderer",
    
    # Template-related
    "template_registry",
    "TemplateRegistry",
    "SlideTemplate",
    
    # Public API functions
    "generate_slides",
    "save_presentation_to_file",
    "save_presentation_with_assets",
    
    # Generator functions
    "generate_title_slide",
    "generate_content_slide",
    "generate_profile_slide",
    "generate_career_slide",
    "generate_timeline_slide",
    "generate_two_column_slide",
    "generate_image_slide",
    "generate_quote_slide"
]

# Original function のラッパーを作成
def generate_slides(outline, theme=None, style="professional"):
    """
    Generate HTML slides from an outline.
    
    Args:
        outline: The slide deck outline
        theme: Optional SlideTheme object
        style: Style of the presentation if theme not provided
        
    Returns:
        HTML content of the generated slides
    """
    from .slide_writer import generate_slides as _original_generate_slides
    
    print("\n🖥️ スライド生成プロセス:")
    print("  ステップ1: アウトラインから各スライドの内容を確認")
    print("  ステップ2: テンプレートを選択")
    print(f"  ステップ3: スライド毎にテンプレートを適用")
    print("  ステップ4: 全スライドをひとつのHTML文書に統合")
    
    # 各スライドのテンプレート適用を表示
    print("\n📊 テンプレート適用プロセス:")
    for i, slide in enumerate(outline.slides):
        slide_type = slide.type if hasattr(slide, 'type') else "標準"
        print(f"  スライド {i+1}: '{slide.title}' - {slide_type}タイプのテンプレートを適用")
    
    # オリジナルの関数を呼び出す
    html_content = _original_generate_slides(outline, theme, style)
    
    print(f"\n✅ 全 {len(outline.slides)} スライドを単一のHTML文書に統合しました")
    
    return html_content 