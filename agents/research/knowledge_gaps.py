"""
Knowledge Gap Analysis

This module provides functionality for identifying knowledge gaps from search results.
"""

import logging
from typing import List

from .models import SearchResult
from agents import client

# Configure logging
logger = logging.getLogger(__name__)

def extract_knowledge_gaps(results: List[SearchResult], topic: str, depth: str, model: str) -> List[str]:
    """
    Identify knowledge gaps from the initial search results.
    
    Args:
        results: List of search results to analyze
        topic: The main research topic
        depth: Search depth level
        model: LLM model to use for analysis
        
    Returns:
        List of identified knowledge gaps
    """
    if not results:
        return [f"Basic information about {topic}"]
    
    logger.info("🔍 情報ギャップを分析中...")
    
    # Combine content for analysis
    combined_text = f"Topic: {topic}\n\n"
    for result in results:
        combined_text += f"Title: {result.title}\nSnippet: {result.snippet}\n\n"
    
    try:
        # Call OpenAI API to identify knowledge gaps
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Identify 3-5 specific knowledge gaps or areas that need deeper research based on the provided information. Focus on technical or detailed aspects that are not well covered."},
                {"role": "user", "content": combined_text}
            ],
            max_tokens=200
        )
        
        # Process the response to extract knowledge gaps
        gaps_text = response.choices[0].message.content.strip()
        
        # Split into individual gaps (assuming each gap is on a new line or numbered)
        gaps = [gap.strip() for gap in gaps_text.split("\n") if gap.strip()]
        
        # Clean up numbering if present
        cleaned_gaps = []
        for gap in gaps:
            # Remove numbering like "1.", "2.", etc.
            if gap[0].isdigit() and gap[1:3] in [". ", ") "]:
                gap = gap[3:].strip()
            cleaned_gaps.append(gap)
        
        logger.info(f"✅ 情報ギャップ分析完了: {len(cleaned_gaps)} 件の追加調査項目を特定")
        return cleaned_gaps
    
    except Exception as e:
        # Log detailed error to file
        logger.error(f"❌ 情報ギャップ分析エラー: {e}")
        # Show concise message in console
        logger.info("❌ 情報ギャップの分析に失敗しました。基本的な項目を使用します")
        return [f"More detailed information about {topic}"] 