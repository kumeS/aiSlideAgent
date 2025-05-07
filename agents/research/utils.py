"""
Research Utilities

This module provides common utility functions for the research agent.
"""

import logging
import re
from typing import Optional, List, Dict, Any
import os

# Configure logging
logger = logging.getLogger(__name__)

def check_api_quota() -> bool:
    """
    Check if we have available API quota by making a minimal API call.
    
    Returns:
        True if API quota is available, False otherwise
    """
    try:
        from agents import client
        
        # Try with the cheapest model first
        ultra_cheap_model = "gpt-3.5-turbo-0125"  # Always use the cheapest model for testing
        
        # Make a minimal API call with minimal tokens to check if we have quota
        response = client.chat.completions.create(
            model=ultra_cheap_model,
            messages=[
                {"role": "system", "content": "Test."},
                {"role": "user", "content": "Hi"}
            ],
            max_tokens=1
        )
        logger.info("✅ API接続テスト成功: OpenAI APIが利用可能です")
        return True
    except Exception as e:
        error_message = str(e)
        if "insufficient_quota" in error_message:
            logger.warning("⚠️ OpenAI APIのクォータが不足しています。代替の検索手法を使用します。")
            return False
        elif "billing" in error_message.lower():
            logger.warning("⚠️ OpenAI APIの支払い関連の問題が発生しています。代替の検索手法を使用します。")
            return False
        elif "credit balance" in error_message.lower() or "credit_balance" in error_message.lower():
            logger.warning("⚠️ OpenAI APIのクレジットバランスが不足しています。代替の検索手法を使用します。")
            return False
        else:
            # Other errors might be temporary, so we'll try to use the API anyway
            logger.warning(f"⚠️ API接続テスト中にエラーが発生しましたが、検索は試行します: {e}")
            return True

def get_appropriate_model(api_quota_available: bool, fallback_model: str, search_model: str, 
                         main_model: str, task_importance: str = "medium") -> str:
    """
    Get the appropriate model based on task importance and available budget.
    
    Args:
        api_quota_available: Whether API quota is available
        fallback_model: Model to use when quota is not available
        search_model: Model to use for search tasks
        main_model: Model to use for critical tasks
        task_importance: "high", "medium", or "low" indicating task criticality
        
    Returns:
        Model name to use for this task
    """
    # If API quota is not available, always use the fallback model
    if not api_quota_available:
        return fallback_model
    
    # Map task importance to models
    if task_importance == "high":
        # For critical tasks (outline generation, final summaries)
        return main_model
    elif task_importance == "medium":
        # For important but not critical tasks (search, credibility)
        return search_model
    else:
        # For less critical tasks (gap analysis, clustering)
        return fallback_model

def clean_url(url: str) -> str:
    """
    Clean a URL to ensure it is properly formatted.
    
    Args:
        url: URL to clean
        
    Returns:
        Cleaned URL
    """
    # Remove leading/trailing whitespace
    url = url.strip()
    
    # Ensure URL has a scheme
    if not re.match(r'^https?://', url):
        url = 'https://' + url
    
    return url

def extract_markdown_link_parts(text: str) -> Dict[str, str]:
    """
    Extract title and URL from a markdown-formatted link.
    
    Args:
        text: Text potentially containing a markdown link [title](url)
        
    Returns:
        Dictionary with 'title' and 'url' keys
    """
    # Check for [title](url) pattern
    md_link_pattern = r'\[(.*?)\]\((https?://[^\s\)]+)\)'
    match = re.search(md_link_pattern, text)
    
    if match:
        return {
            'title': match.group(1).strip(),
            'url': match.group(2).strip()
        }
    
    return {
        'title': text.strip(),
        'url': ''
    } 