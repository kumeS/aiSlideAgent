"""
Research Agent API

This module provides the public API for the research agent.
"""

import logging
import re
from typing import Dict, List, Optional

from .models import ResearchResult, SearchResult
from .search_engine import ResearchAgent

# Configure logging
logger = logging.getLogger(__name__)

def search_deep(topic: str, depth: str = "medium") -> ResearchResult:
    """
    Public API: Perform a deep search on a topic with the default ResearchAgent.
    
    Args:
        topic: The topic to research
        depth: Search depth - "low", "medium", or "high"
        
    Returns:
        ResearchResult containing comprehensive information about the topic
    """
    agent = ResearchAgent()
    return agent.search_deep(topic, depth)

def search_basic(topic: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Perform a basic search on a topic and return simplified results
    
    This function guarantees that exactly `num_results` results will be returned.
    If fewer results are available from the web search, synthetic results will
    be generated to reach the requested number. This ensures consistent behavior
    for downstream functions that expect a specific number of results.
    
    Args:
        topic: The topic to search for
        num_results: Number of results to return (guaranteed)
        
    Returns:
        List of exactly `num_results` simplified search results as dictionaries.
        Each dictionary contains "title", "source", and "summary" keys.
    """
    logger.info(f"🔍 基本検索を実行: {topic} (結果数: {num_results})")
    
    try:
        # Create a research agent
        agent = ResearchAgent()
        
        # Perform a simplified search
        search_results = agent.search_web(topic, num_results=num_results, depth="low")
        
        # Convert to simplified dictionary format and enrich with real titles if needed
        simplified_results = []
        
        for result in search_results:
            # Clean the URL
            url = result.url.strip()
            
            # Remove trailing parentheses and markup that might be part of the URL
            url = re.sub(r'\)$', '', url)
            url = re.sub(r'\]$', '', url)
            
            # If URL contains markdown link format [title](url), extract just the URL
            md_url_match = re.search(r'\((https?://[^\s\)]+)\)', url)
            if md_url_match:
                url = md_url_match.group(1)
                
            # Extract real title if it's in markdown format
            title = result.title.strip()
            markdown_title_pattern = r'\[(.*?)\]'
            markdown_title_match = re.search(markdown_title_pattern, title)
            if markdown_title_match:
                title = markdown_title_match.group(1).strip()
            else:
                # If not in markdown, clean up any other artifacts
                title = re.sub(r'\*\*|\*|[-•]|\bURL:|\bURL\b|\[|\]|\(|\)|`|__', '', title).strip()
            
            # Check if the title is just a domain name
            if title.endswith('.jp') or title.endswith('.com') or title.endswith('.org') or title.endswith('.net'):
                # Try to get a better title from the URL domain parts
                domain_parts = url.split('://')[-1].split('/')[0].split('.')
                if len(domain_parts) >= 2:
                    site_name = domain_parts[-2].capitalize()
                    title = f"{site_name} - {topic}に関する情報"
            
            # Clean up the summary
            summary = result.snippet.strip() if result.snippet else ""
            
            # If summary contains markdown links, clean them
            summary = re.sub(r'\[(.*?)\]\((https?://[^\s\)]+)\)', r'\1 (\2)', summary)
            
            # If summary is just a URL remnant or empty, provide a generic summary
            if not summary or summary.startswith('ook/') or summary.endswith('ai))"') or summary.endswith('ai))'):
                summary = f"{topic}に関する情報 - {title}"
            
            simplified_results.append({
                "title": title,
                "source": url,
                "summary": summary
            })
        
        # Check if we have fewer results than requested and add fallback results if needed
        if len(simplified_results) < num_results:
            logger.info(f"⚠️ 検索結果が不足しています。追加結果を生成します: 要求数 {num_results}, 実際の結果 {len(simplified_results)}")
            # Add placeholder results to reach the requested number
            additional_needed = num_results - len(simplified_results)
            
            for i in range(additional_needed):
                simplified_results.append({
                    "title": f"{topic} - 情報 {len(simplified_results) + 1}",
                    "source": f"https://research.example.org/{topic}/{len(simplified_results) + 1}",
                    "summary": f"{topic}に関する情報です。実際の検索結果が十分ではなかったため、自動生成された補足情報です。"
                })
            logger.info(f"✅ 追加結果を生成しました: 合計 {len(simplified_results)} 件")
        
        logger.info(f"✅ 基本検索が完了しました: {len(simplified_results)} 件の結果")
        return simplified_results
        
    except Exception as e:
        logger.error(f"❌ 基本検索中にエラーが発生しました: {str(e)}")
        # Return a minimal result set to avoid breaking the pipeline
        dummy_results = []
        for i in range(num_results):
            dummy_results.append({
                "title": f"{topic} - 情報 {i+1}",
                "source": "https://example.com",
                "summary": f"{topic}に関する情報です。APIエラーによりオンライン検索ができないため、限定的な情報のみ提供しています。"
            })
        return dummy_results 