"""
Search Engine Module

This module provides the core search functionality for the research agent.
"""

import os
import json
import logging
import re
import time
import random
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv

from .models import SearchResult, ResearchResult
from .utils import check_api_quota, get_appropriate_model, clean_url
from .fallback import generate_synthetic_results, generate_offline_results, search_with_serpapi
from .credibility import evaluate_credibility, cluster_results
from .knowledge_gaps import extract_knowledge_gaps
from .summarization import generate_summary

from agents import client, DEFAULT_MODEL

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

class ResearchAgent:
    """Agent for performing multi-layer web research on topics."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the research agent with API keys and configuration."""
        self.serp_api_key = api_key or SERP_API_KEY
        self.model = model or DEFAULT_MODEL
        self.max_retries = 3
        self.fallback_mode = False
        
        # Use a less expensive model for search to avoid quota issues
        self.search_model = os.getenv("OPENAI_SEARCH_MODEL", "gpt-3.5-turbo-0125")
        
        # Alternative model for fallbacks
        self.fallback_model = os.getenv("OPENAI_FALLBACK_MODEL", "gpt-3.5-turbo-0125")
        
        # Check if models are available by testing API (without making a full search)
        self.api_quota_available = check_api_quota()
    
    def _get_appropriate_model(self, task_importance: str = "medium") -> str:
        """
        Get the appropriate model based on task importance and available budget.
        
        Args:
            task_importance: "high", "medium", or "low" indicating task criticality
            
        Returns:
            Model name to use for this task
        """
        return get_appropriate_model(
            self.api_quota_available, 
            self.fallback_model, 
            self.search_model, 
            self.model, 
            task_importance
        )
    
    def search_web(self, query: str, num_results: int = 10, depth: str = "medium") -> List[SearchResult]:
        """
        Perform a web search and return structured results.
        Primarily uses OpenAI's search-enabled models.
        
        Args:
            query: The search query
            num_results: Number of results to return
            depth: Search depth - "low", "medium", or "high"
        """
        # Check if we have API quota
        if not self.api_quota_available:
            logger.warning("⚠️ APIクォータ不足のため、代替検索方法を試行します")
            
            # First try using an alternative search provider if available
            alternative_results = self._search_with_alternative_provider(query, num_results)
            if alternative_results:
                logger.info(f"✅ 代替検索プロバイダーから {len(alternative_results)} 件の結果を取得")
                return alternative_results
            
            # If alternative search also fails, fall back to offline generation
            logger.warning("⚠️ 代替検索も失敗しました。オフライン生成に切り替えます")
            return generate_offline_results(query, num_results)
            
        # If we have quota, try OpenAI search
        return self._search_with_openai(query, num_results, depth)
    
    def _search_with_alternative_provider(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Use alternative search providers when OpenAI API is unavailable."""
        logger.info(f"🔍 代替検索プロバイダーで検索中: {query}")
        
        try:
            # Try SerpAPI if key is available
            if self.serp_api_key:
                return search_with_serpapi(query, self.serp_api_key, num_results)
            
            # Add additional alternative search providers here
            # For example, you could implement:
            # - DuckDuckGo API (free)
            # - Bing API
            # - Custom web scraping solution
            
            # If no alternative providers are available
            logger.warning("⚠️ 代替検索プロバイダーが設定されていません")
            return []
        
        except Exception as e:
            logger.error(f"❌ 代替検索エラー: {e}")
            return []
    
    def _search_with_openai(self, query: str, num_results: int = 10, depth: str = "medium") -> List[SearchResult]:
        """
        Use OpenAI's search-enabled model to perform web searches.
        
        This method guarantees that exactly `num_results` results will be returned.
        If fewer results are available from the web search, synthetic results 
        will be added to reach the requested number. This ensures that downstream
        components always receive the expected number of results.
        
        Args:
            query: The search query
            num_results: Number of results to return (guaranteed)
            depth: Search depth - "low", "medium", or "high"
            
        Returns:
            List of exactly `num_results` SearchResult objects, potentially including
            synthetic results if real search results are insufficient.
        """
        logger.info(f"🔍 検索中: {query} (深さ: {depth})")
        
        try:
            # 型安全性の確保: depth が文字列でない場合は文字列に変換
            if not isinstance(depth, str):
                logger.warning(f"⚠️ 検索深度パラメータが文字列ではありません。文字列に変換します: {depth} → 'medium'")
                depth = "medium"  # デフォルト値に設定
                
            # Map depth string to search_context_size
            search_depth = {
                "low": "low",
                "medium": "medium",
                "high": "high",
                # Add support for alternative values that might be passed
                "small": "low",
                "large": "high",
                "shallow": "low",
                "deep": "high"
            }.get(depth.lower(), "medium")
            
            # Log the actual search depth being used
            if depth.lower() != search_depth:
                logger.info(f"🔍 検索深度のマッピング: '{depth}' → '{search_depth}'")
            
            # 検索対応モデルを使用する
            # 検索可能なモデルだけを明示的に指定
            search_capable_models = ["gpt-4o-search-preview", "gpt-4o", "gpt-4-turbo", "gpt-4-turbo-2024-04-09"]
            
            # 可能な限り、検索対応モデルを使用
            search_model = None
            
            # まず環境変数で明示的に指定されているモデルを確認
            for model_name in search_capable_models:
                if os.getenv(f"OPENAI_USE_{model_name.replace('-', '_').upper()}", "false").lower() == "true":
                    search_model = model_name
                    logger.info(f"🔍 環境変数で指定された検索対応モデル「{search_model}」を使用")
                    break
            
            # 環境変数で指定がなければ、デフォルトで検索対応モデルを使用
            if not search_model:
                # 検索対応モデルを優先的に使用
                search_model = "gpt-4o-search-preview"  # 検索対応モデルを直接指定
                logger.info(f"🔍 検索対応モデル「{search_model}」を使用")
            
            # 検索対応モデルが利用不可と明示的に指定されている場合は代替方法にフォールバック
            if os.getenv("OPENAI_DISABLE_SEARCH", "false").lower() == "true":
                logger.warning(f"⚠️ 検索機能が無効化されています。代替方法を使用します。")
                return generate_synthetic_results(query, num_results)
            
            # Construct a prompt that will return structured search results
            system_prompt = """
            You are a search engine assistant that helps find and summarize information from the web.
            Search the web for the query, and return results in this EXACT format for each result:

            ---
            Title: [ACTUAL PAGE TITLE, not just domain name]
            URL: [FULL URL]
            Summary: [2-3 sentence summary of the actual page content, not just meta description]
            ---

            Provide real page titles - not just domain names. 
            Summaries should be informative and based on actual content.
            Do not use markdown formatting in your response.
            """
            
            # Retry with slight variations if needed
            max_search_retries = 2
            search_retry_count = 0
            response = None
            
            while search_retry_count <= max_search_retries and response is None:
                try:
                    # Make the API request with web search enabled
                    query_to_use = query
                    
                    # On retry, add more context to help the search
                    if search_retry_count == 1:
                        query_to_use = f"detailed information about {query}"
                    elif search_retry_count == 2:
                        query_to_use = f"{query} guide tutorial information"
                    
                    response = client.chat.completions.create(
                        model=search_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Search for: {query_to_use}"}
                        ],
                        max_tokens=1500,
                        web_search_options={
                            "search_context_size": search_depth,  # Use the mapped depth
                            "user_location": {
                                "type": "approximate",
                                "approximate": {
                                    "country": "JP",  # Default to Japan
                                },
                            },
                        }
                    )
                except Exception as search_error:
                    search_retry_count += 1
                    # Format error message to be more user-friendly
                    error_str = str(search_error)
                    
                    # Extract and simplify common error messages
                    if "invalid_value" in error_str and "web_search_options.search_context_size" in error_str:
                        simplified_error = "検索深度パラメータが無効です。有効な値: 'low', 'medium', 'high'"
                    elif "not supported with this model" in error_str and "Web search" in error_str:
                        simplified_error = f"モデル '{search_model}' はウェブ検索に対応していません。別のモデルを試します。"
                    elif "insufficient_quota" in error_str or "billing" in error_str.lower():
                        simplified_error = "APIクォータ不足: クレジットを確認してください。代替検索を試行します。"
                    elif "Rate limit" in error_str:
                        simplified_error = "レートリミット制限: 短時間に多くのリクエストが行われました。しばらく待ってから再試行します。"
                    elif "auth" in error_str.lower() and "error" in error_str.lower():
                        simplified_error = "認証エラー: APIキーを確認してください。"
                    else:
                        # Keep original error but limit verbosity
                        shortened_error = error_str[:100] + "..." if len(error_str) > 100 else error_str
                        simplified_error = f"検索エラー: {shortened_error}"
                    
                    logger.warning(f"検索試行 {search_retry_count}: {simplified_error}")
                    
                    if search_retry_count > max_search_retries:
                        # すべての検索が失敗した場合はエラーをログに記録
                        logger.error(f"検索失敗: 3回試行しましたが成功しませんでした。エラー詳細: {error_str}")
                        logger.info("代替情報生成に切り替えます")
                        raise  # Re-raise if we've exhausted our retries
                    time.sleep(2)  # Brief pause before retrying
            
            if response is None:
                raise Exception("All search attempts failed")
            
            # Extract search results from the response
            content = response.choices[0].message.content.strip()
            
            # Log the raw response for debugging
            logger.debug(f"Raw search response: {content[:1000]}...")
            
            # Parse the results using the clean format we specified
            search_results = []
            result_blocks = content.split("---")
            
            for block in result_blocks:
                if not block.strip():
                    continue
                    
                title_match = re.search(r'Title:\s*(.*?)(?:\n|$)', block, re.IGNORECASE)
                url_match = re.search(r'URL:\s*(https?://\S+)(?:\n|$)', block, re.IGNORECASE)
                summary_match = re.search(r'Summary:\s*([\s\S]*?)(?=\n\s*$|\Z)', block, re.IGNORECASE)
                
                if title_match and url_match:
                    title = title_match.group(1).strip()
                    url = url_match.group(1).strip()
                    
                    # Clean up the URL - remove trailing parentheses and markup
                    url = re.sub(r'\)$', '', url)
                    url = re.sub(r'\]$', '', url)
                    
                    # If URL contains markdown link format [title](url), extract just the URL
                    md_url_match = re.search(r'\((https?://[^\s\)]+)\)', url)
                    if md_url_match:
                        url = md_url_match.group(1)
                    
                    # Clean up the title - remove markdown formatting
                    title = re.sub(r'\*\*|\*|__|\[|\]|\(|\)|`', '', title)
                    
                    summary = summary_match.group(1).strip() if summary_match else "No summary available"
                    
                    search_result = SearchResult(
                        url=url,
                        title=title,
                        snippet=summary,
                        source_type="ai_search"
                    )
                    search_results.append(search_result)
            
            # If no results from blocks, try older patterns
            if not search_results:
                # Try to match Title, URL, Summary pattern
                title_url_summary_pattern = r'(?:^|\n)(?:\d+\.\s*)?Title:\s*(.*?)(?:\n|\r\n)URL:\s*(https?://\S+)(?:\n|\r\n)Summary:\s*((?:.|\n)*?)(?=(?:^|\n)(?:\d+\.\s*)?Title:|$)'
                matches = re.findall(title_url_summary_pattern, content, re.MULTILINE | re.DOTALL)
                
                if matches:
                    for match in matches:
                        if len(match) >= 3:
                            title = match[0].strip()
                            url = match[1].strip()
                            summary = match[2].strip()
                            
                            search_result = SearchResult(
                                url=url,
                                title=title,
                                snippet=summary,
                                source_type="ai_search"
                            )
                            search_results.append(search_result)
            
            # If still no results, try JSON pattern
            if not search_results:
                json_pattern = r'\{[^{}]*"title"[^{}]*"url"[^{}]*"snippet"[^{}]*\}'
                json_objects = re.findall(json_pattern, content, re.DOTALL)
                
                if json_objects:
                    for json_str in json_objects:
                        try:
                            cleaned_json = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', json_str)
                            cleaned_json = cleaned_json.replace("'", '"')
                            result_data = json.loads(cleaned_json)
                            
                            if "title" in result_data and "url" in result_data and "snippet" in result_data:
                                search_result = SearchResult(
                                    url=result_data["url"],
                                    title=result_data["title"],
                                    snippet=result_data["snippet"],
                                    source_type="ai_search"
                                )
                                search_results.append(search_result)
                        except Exception as e:
                            logger.warning(f"Failed to parse JSON object: {e}")
            
            # If still no results, try numbered list pattern
            if not search_results:
                result_pattern = r'(?:\d+[\.\)]\s*|•\s*|\*\s*)(.*?)\n\s*(?:URL|Link):\s*(https?://\S+)\s*(?:\n|$).*?(?:Snippet|Summary|Description):\s*(.*?)(?:\n\s*(?:\d+[\.\)]|•|\*)|$)'
                matches = re.findall(result_pattern, content, re.DOTALL)
                
                for match in matches:
                    if len(match) >= 3:
                        title = match[0].strip()
                        url = match[1].strip()
                        snippet = match[2].strip()
                        
                        search_result = SearchResult(
                            url=url,
                            title=title,
                            snippet=snippet,
                            source_type="ai_search"
                        )
                        search_results.append(search_result)
            
            # If still no results, extract URLs
            if not search_results:
                url_pattern = r'((?:https?://)[^\s\)]+)'
                urls = re.findall(url_pattern, content)
                
                for url in urls:
                    # Find context around this URL
                    url_pos = content.find(url)
                    context_start = max(0, content.rfind('\n', 0, url_pos))
                    context_end = content.find('\n', url_pos + len(url))
                    if context_end == -1:
                        context_end = len(content)
                    
                    context = content[context_start:context_end].strip()
                    
                    # Extract title - assume it's at the beginning of the context
                    title_end = min(100, len(context))
                    title = context[:title_end].strip()
                    if len(title) > 50:
                        title = title[:50] + "..."
                    
                    # Use remaining context as snippet
                    snippet = context[len(title):].strip()
                    if not snippet:
                        snippet = f"Information about {query}"
                    
                    search_result = SearchResult(
                        url=url,
                        title=title,
                        snippet=snippet,
                        source_type="ai_search"
                    )
                    search_results.append(search_result)
            
            # If we still have no results, generate synthetic results
            if not search_results:
                logger.warning(f"⚠️ ウェブ検索結果が見つかりませんでした。合成結果を生成します。")
                synthetic_results = generate_synthetic_results(query, num_results)
                logger.info(f"✅ 合成結果を生成しました: {len(synthetic_results)} 件")
                return synthetic_results
            
            if search_results:
                logger.info(f"✅ 検索完了: {len(search_results)} 件の結果を取得")
            else:
                logger.warning(f"⚠️ 検索結果なし: 検索は正常に実行されましたが、結果が見つかりませんでした")
            
            # Check if we have fewer results than requested
            if len(search_results) < num_results:
                logger.info(f"⚠️ 要求された結果数 ({num_results}) より少ない結果 ({len(search_results)}) しか取得できませんでした。")
                # Add synthetic results to reach the requested number
                additional_needed = num_results - len(search_results)
                if additional_needed > 0:
                    logger.info(f"追加結果を生成します: {additional_needed} 件")
                    synthetic_results = generate_synthetic_results(query, additional_needed)
                    search_results.extend(synthetic_results)
                    logger.info(f"✅ 合計: {len(search_results)} 件の結果")
            
            # Limit results to requested number
            return search_results[:num_results]
            
        except Exception as e:
            # Check if it's a quota error
            error_message = str(e)
            if ("insufficient_quota" in error_message or 
                "billing" in error_message.lower() or 
                "credit balance" in error_message.lower() or 
                "credit_balance" in error_message.lower()):
                logger.error(f"❌ APIクォータ/クレジットエラー: {e}")
                # Update the API quota status for future calls
                self.api_quota_available = False
                logger.info("❌ APIクォータ/クレジット不足のため、処理を中止します")
                raise Exception("APIクォータ/クレジット不足のため検索できません。APIキーを確認してもう一度お試しください。")
            else:
                # For other errors, simply report the error and stop
                logger.error(f"❌ 検索エラー: {e}")
                logger.info("❌ 検索に失敗しました。処理を中止します")
                raise Exception(f"検索に失敗しました: {error_message[:200]}")
    
    def search_deep(self, topic: str, depth: str = "medium", primary_results_count: int = 30) -> ResearchResult:
        """
        Perform a multi-layer search on a topic.
        
        Args:
            topic: The main topic to research
            depth: Search depth - "low", "medium", or "high"
            primary_results_count: Number of initial search results to retrieve
            
        Returns:
            ResearchResult containing all search findings and summary
        """
        logger.info(f"🚀 トピック「{topic}」の調査を開始 (深さ: {depth})")
        
        # Initialize research result
        research_result = ResearchResult(topic=topic)
        
        # Set secondary search depth based on primary depth
        secondary_search_depth = depth
        
        # Set the count of secondary searches based on depth
        # For 'low' depth, we'll search until we find 3 valid results instead of a fixed number
        required_sources = {
            "low": 3,     # Find at least 3 sources for low depth
            "medium": 3,  # Default number
            "high": 5     # More secondary searches
        }.get(depth, 3)
        
        secondary_search_count = required_sources  # Default behavior for medium/high
        
        # Set number of layers based on depth
        layers = {
            "low": 1,     # Only primary search
            "medium": 2,  # Primary + some secondary
            "high": 2     # Primary + extensive secondary
        }.get(depth, 2)
        
        # Try alternative search queries if the topic contains non-English characters
        search_queries = [topic]
        
        # Add translated queries if needed
        if any(ord(c) > 127 for c in topic):
            try:
                # Generate alternative search queries using AI
                response = client.chat.completions.create(
                    model=self._get_appropriate_model(depth),
                    messages=[
                        {"role": "system", "content": "You are a multilingual translation assistant. Convert the given query into English if it's not already in English, preserving the original meaning."},
                        {"role": "user", "content": f"Translate if needed: {topic}"}
                    ],
                    max_tokens=100
                )
                
                translated = response.choices[0].message.content.strip()
                if translated.lower() != topic.lower():
                    search_queries.append(translated)
                    logger.info(f"🔤 検索クエリを追加: {translated}")
                    
                    # Also add more specific variants
                    search_queries.append(f"{translated} guide")
                    search_queries.append(f"{translated} tutorial")
                
            except Exception as e:
                # 翻訳に失敗しても、処理を停止せずに代替クエリを生成
                logger.warning(f"⚠️ 検索クエリ変換エラー: {str(e)}")
                # よくあるトピックの場合は、手動で翻訳を試みる
                if "量子" in topic:
                    search_queries.append("Quantum computing")
                    search_queries.append("Quantum physics")
                    logger.info("🔤 代替翻訳クエリを追加: Quantum computing")
                elif "人工知能" in topic or "AI" in topic.upper():
                    search_queries.append("Artificial Intelligence")
                    search_queries.append("AI technology")
                    logger.info("🔤 代替翻訳クエリを追加: Artificial Intelligence")
                elif "機械学習" in topic:
                    search_queries.append("Machine Learning")
                    search_queries.append("ML algorithms")
                    logger.info("🔤 代替翻訳クエリを追加: Machine Learning")
                # その他の一般的なトピック
                else:
                    # 英語のキーワードを追加
                    search_queries.append("guide tutorial")
                    search_queries.append("introduction overview")
                    logger.info("🔤 一般的な英語キーワードを追加しました")
        
        # First layer: Primary search - try multiple queries until we get results
        all_primary_results = []
        
        for query in search_queries:
            logger.info(f"🔎 検索クエリを実行: {query}")
            primary_results = self.search_web(query, num_results=primary_results_count, depth=depth)
            
            if primary_results:
                all_primary_results.extend(primary_results)
                
                # For "low" depth, check if we have enough unique sources
                if depth == "low":
                    # Count unique domains in our results
                    unique_domains = set()
                    for result in all_primary_results:
                        try:
                            from urllib.parse import urlparse
                            domain = urlparse(result.url).netloc
                            unique_domains.add(domain)
                        except:
                            # If URL parsing fails, count the whole URL
                            unique_domains.add(result.url)
                    
                    if len(unique_domains) >= required_sources:
                        logger.info(f"✅ '{depth}' 深度で必要な {required_sources} 件のソースを確保")
                        break
                # For other depths, use the original logic
                elif len(all_primary_results) >= primary_results_count // 2:
                    logger.info("✅ 十分な検索結果を取得")
                    break  # We have enough results, stop trying more queries
        
        # Deduplicate results
        seen_urls = set()
        unique_primary_results = []
        for result in all_primary_results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_primary_results.append(result)
        
        # Evaluate credibility of primary results
        primary_results = evaluate_credibility(unique_primary_results, self._get_appropriate_model("low"))
        
        # Cluster to reduce redundancy
        primary_results = cluster_results(primary_results)
        research_result.primary_results = primary_results
        
        if layers >= 2 and primary_results:
            # Extract knowledge gaps for secondary searches
            logger.info("🔬 追加調査項目を特定中...")
            knowledge_gaps = extract_knowledge_gaps(
                primary_results, 
                topic, 
                depth, 
                self._get_appropriate_model(depth)
            )
            research_result.knowledge_gaps = knowledge_gaps
            
            # Second layer: Search for each knowledge gap
            logger.info("🔍 詳細情報の検索を開始...")
            secondary_results = []
            
            # Use only a subset of knowledge gaps based on depth
            for gap in knowledge_gaps[:secondary_search_count]:
                # Create a more specific search query
                for base_query in search_queries[:1]:  # Use only the first query as base to limit requests
                    specific_query = f"{base_query} {gap}"
                    logger.info(f"🔎 詳細検索: {specific_query}")
                gap_results = self.search_web(specific_query, num_results=5, depth=secondary_search_depth)
                
                # Evaluate and add to secondary results
                if gap_results:
                    gap_results = evaluate_credibility(gap_results, self._get_appropriate_model("low"))
                    secondary_results.extend(gap_results)
                    logger.info(f"✅ 詳細情報を取得: {len(gap_results)} 件")
                    break  # If we got results, don't try other base queries
            
            # Cluster secondary results
            if secondary_results:
                secondary_results = cluster_results(secondary_results)
                research_result.secondary_results = secondary_results
        
        # If we still have no results (primary or secondary), generate basic knowledge
        if not research_result.primary_results and not research_result.secondary_results:
            logger.warning("⚠️ 検索結果がありません。基本情報を生成します")
            synthetic_results = generate_synthetic_results(topic, 5)
            research_result.primary_results = synthetic_results
            
            # Also generate some knowledge gaps
            research_result.knowledge_gaps = [
                f"Fundamentals of {topic}",
                f"Applications of {topic}",
                f"Best practices for {topic}",
                f"Future developments in {topic}"
            ]
        
        # Ensure knowledge_gaps doesn't exceed reasonable size to prevent truncation
        if research_result.knowledge_gaps and len(research_result.knowledge_gaps) > 0:
            # Check each knowledge gap for length and truncate if too long
            for i in range(len(research_result.knowledge_gaps)):
                if len(research_result.knowledge_gaps[i]) > 500:
                    logger.warning(f"⚠️ 知識ギャップ項目が長すぎます。切り詰めます: {research_result.knowledge_gaps[i][:50]}...")
                    research_result.knowledge_gaps[i] = research_result.knowledge_gaps[i][:500] + "..."
            
            # Limit total number of knowledge gaps
            if len(research_result.knowledge_gaps) > 10:
                logger.warning(f"⚠️ 知識ギャップが多すぎます。上位10件に限定します")
                research_result.knowledge_gaps = research_result.knowledge_gaps[:10]
        
        # Generate a comprehensive summary
        logger.info("📝 調査結果のサマリーを作成中...")
        research_result.summary = generate_summary(research_result, self.model)
        
        logger.info("✅ トピック調査完了")
        return research_result 