"""
Fallback Search Mechanisms

This module provides fallback search mechanisms when online search APIs are unavailable.
"""

import logging
import hashlib
import random
import re
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

import json
from .models import SearchResult

# Configure logging
logger = logging.getLogger(__name__)

def generate_synthetic_results(query: str, count: int = 5) -> List[SearchResult]:
    """
    Generate synthetic search results when real search fails.
    
    Args:
        query: The search query
        count: Number of results to generate
        
    Returns:
        List of synthetic SearchResult objects
    """
    logger.info(f"🧠 生成モードでコンテンツを作成します: {query} (件数: {count})")
    
    # Clean the query for domain creation
    clean_query = re.sub(r'[^a-zA-Z0-9]', '', query.lower()) 
    if not clean_query:
        clean_query = "research"
    
    # Categories for synthetic resources
    categories = [
        {"type": "educational", "domains": ["example.edu", "academy.example.com", "knowledge.example.edu", "institute.example.org"]},
        {"type": "research", "domains": ["research.example.org", "science.example.net", "datasci.example.info", "lab.example.co.jp"]},
        {"type": "community", "domains": ["community.example.com", "forum.example.org", "wiki.example.info", "discussion.example.net"]}
    ]
    
    # Create templates for different types of resources
    templates = {
        "basics": f"{query}の基礎 - 教育リソース",
        "advanced": f"上級{query}技術 - 教育リソース",
        "applications": f"{query}の応用 - 教育リソース",
        "algorithms": f"{query}アルゴリズム - 教育リソース",
        "implementations": f"{query}の実装 - 教育リソース",
        "case_studies": f"{query}ケーススタディ - 教育リソース",
        "future": f"{query}の未来展望 - 教育リソース",
        "frameworks": f"{query}フレームワーク - 教育リソース",
        "tutorials": f"{query}チュートリアル - 教育リソース",
        "best_practices": f"{query}のベストプラクティス - 教育リソース",
    }
    
    # Create templates for snippets based on resource type
    snippet_templates = {
        "basics": f"{query}は{query}の基本概念と原理を解説しています。初心者向けの導入から始まり、{query}の歴史、基本理論、主要な構成要素について説明しています。...",
        "advanced": f"上級者向けの{query}技術について詳細に説明しています。最新の研究成果、高度なテクニック、専門的な応用例を含みます。...",
        "applications": f"{query}の実際の応用例と産業での活用方法を紹介しています。さまざまな分野での実用例や成功事例が含まれています。...",
        "algorithms": f"{query}アルゴリズムは複数あり、それぞれ特性や用途が異なります。代表的なアルゴリズムの仕組みや実装方法について解説しています。...",
        "implementations": f"{query}の実装方法について詳しく解説しています。コード例やベストプラクティス、一般的な課題と解決策が含まれています。...",
        "case_studies": f"{query}の実際の活用事例を詳細に分析しています。成功例と失敗例の両方から学ぶべき教訓が示されています。...",
        "future": f"{query}の今後の発展方向や将来性について考察しています。最新の研究トレンドや期待される技術革新についても触れています。...",
        "frameworks": f"{query}のための主要なフレームワークとツールを比較解説しています。それぞれの特徴や適した使用シーンが分析されています。...",
        "tutorials": f"{query}を実践的に学ぶためのステップバイステップガイドです。初心者から上級者までのレベル別チュートリアルが含まれています。...",
        "best_practices": f"{query}を効果的に活用するためのベストプラクティスとガイドラインをまとめています。一般的な落とし穴や避けるべき誤りも解説されています。..."
    }
    
    results = []
    used_templates = []
    
    # Generate specified number of results
    for i in range(count):
        # Select a category
        category = random.choice(categories)
        domain = random.choice(category["domains"])
        
        # Select a template (avoid repeating if possible)
        available_templates = [k for k in templates.keys() if k not in used_templates]
        if not available_templates:
            available_templates = list(templates.keys())
        
        template_key = random.choice(available_templates)
        used_templates.append(template_key)
        if len(used_templates) > len(templates) // 2:
            used_templates.pop(0)  # Remove oldest to allow some repeats
            
        title = templates[template_key]
        
        # Create a URL using the domain
        path = f"{clean_query}/{i+1}"
        url = f"https://{domain}/{path}"
        
        # Create a snippet using the appropriate template
        snippet = snippet_templates[template_key]
        
        # Create and add the result
        result = SearchResult(
            url=url,
            title=title,
            snippet=snippet,
            source_type="synthetic"
        )
        results.append(result)
    
    logger.info(f"✅ 合成結果の生成が完了しました: {len(results)} 件")
    return results

def generate_offline_results(query: str, count: int = 5) -> List[SearchResult]:
    """
    Generate comprehensive results without using OpenAI API when quota is exceeded.
    
    Args:
        query: The search query
        count: Number of results to generate
        
    Returns:
        List of SearchResult objects
    """
    logger.info(f"🔌 オフラインモードでコンテンツを生成します: {query}")
    
    # Just use the synthetic generator with a notice prefixed
    results = generate_synthetic_results(query, count)
    
    # Add a notice to each result
    for result in results:
        result.snippet = f"[オフラインモードで生成] " + result.snippet
        
    return results

def search_with_serpapi(query: str, api_key: str, num_results: int = 5) -> List[SearchResult]:
    """
    Search using SerpAPI as an alternative provider.
    
    Args:
        query: Search query
        api_key: SerpAPI key
        num_results: Number of results to return
        
    Returns:
        List of SearchResult objects
    """
    logger.info(f"🔍 SerpAPIで検索中: {query}")
    
    try:
        import requests
        
        # Prepare the request to SerpAPI
        params = {
            "engine": "google",
            "q": query,
            "api_key": api_key,
            "num": num_results,
            "hl": "ja"  # Japanese language results
        }
        
        response = requests.get(
            "https://serpapi.com/search", 
            params=params,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.error(f"❌ SerpAPI エラー: ステータスコード {response.status_code}")
            return []
        
        data = response.json()
        
        # Extract organic results
        if "organic_results" not in data:
            logger.error("❌ SerpAPI: 検索結果が見つかりません")
            return []
        
        results = []
        for item in data["organic_results"][:num_results]:
            url = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            
            if not snippet and "rich_snippet" in item:
                # Try to get more details from rich snippet
                rich = item["rich_snippet"]
                if "top" in rich and "detected_extensions" in rich["top"]:
                    snippet = rich["top"]["detected_extensions"].get("description", "")
            
            result = SearchResult(
                url=url,
                title=title,
                snippet=snippet or f"{query}に関する情報",
                source_type="serpapi"
            )
            results.append(result)
        
        logger.info(f"✅ SerpAPI検索完了: {len(results)} 件の結果")
        return results
        
    except Exception as e:
        logger.error(f"❌ SerpAPI検索エラー: {str(e)}")
        return [] 