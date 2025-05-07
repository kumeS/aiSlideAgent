"""
Template Selector Agent Module

This module is responsible for selecting the most appropriate template 
for a given presentation based on the topic and content.
"""

from .template_selector import TemplateSelectorAgent, select_template_for_presentation
import logging

# Setup logging
logger = logging.getLogger(__name__)

__all__ = ["TemplateSelectorAgent", "select_template_for_presentation"]

# Original function のラッパーを作成
def select_template_for_presentation(topic, slide_deck, style="professional"):
    """
    Select the most appropriate template for a presentation.
    
    Args:
        topic: The presentation topic
        slide_deck: The slide deck content
        style: The intended template style of the presentation
        
    Returns:
        A SlideTheme object containing template information
    """
    from .template_selector import select_template_for_presentation as _original_select
    
    # オリジナルの関数を呼び出す
    theme = _original_select(topic, slide_deck, style)
    
    # テンプレート選択結果の詳細を表示
    print(f"\n🎨 選択されたテンプレート: 「{theme.name}」")
    
    # color_paletteプロパティがない場合は表示しない
    if hasattr(theme, 'color_palette'):
        print(f"  カラーパレット: {theme.color_palette}")
    
    return theme 