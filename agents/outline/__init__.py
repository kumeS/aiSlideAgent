"""
Outline Agent Module

This module provides functionality to generate structured slide outlines
from research summaries.
"""

from .outline import OutlineAgent, generate_outline as _generate_outline, SlideContent, SlideDeck
import logging

# Setup logging
logger = logging.getLogger(__name__)

__all__ = ["OutlineAgent", "generate_outline", "SlideContent", "SlideDeck"]

def generate_outline(research_results, slide_count=5, topic=None) -> SlideDeck:
    """Generate slide outline based on research results."""
    if topic:
        logger.info(f"Generating outline for topic: {topic} with {slide_count} slides")
    else:
        logger.info(f"Generating outline with {slide_count} slides")
    
    # Call the original generate_outline function from outline.py
    outline = _generate_outline(research_results, slide_count, topic)
    
    # コンソールにスライド構成を表示
    print("\n📝 スライド構成:")
    for i, slide in enumerate(outline.slides):
        print(f"\n🔹 スライド {i+1}: {slide.title}")
        if hasattr(slide, 'subtitle') and slide.subtitle:
            print(f"  サブタイトル: {slide.subtitle}")
        print(f"  コンテンツ:")
        for bullet in slide.content:
            print(f"    • {bullet}")
    
    logger.info(f"✅ {len(outline.slides)} スライドのアウトラインを作成しました")
    return outline 