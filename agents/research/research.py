"""
Research Agent

Implements multi-layer web search and content analysis for comprehensive topic research.
"""

import os
import json
import requests
from typing import Dict, List, Any, Optional, Tuple
import hashlib
from urllib.parse import urlparse
from pydantic import BaseModel, Field
import logging
from dotenv import load_dotenv
import time
import random
import re

from agents import client, DEFAULT_MODEL

# Configure logging - ロギング設定は agents/__init__.py に集約
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SERP_API_KEY = os.getenv("SERP_API_KEY")

class SearchResult(BaseModel):
    """Model representing a search result with metadata."""
    url: str
    title: str
    snippet: str
    content: Optional[str] = None
    source_type: str = Field(default="web")
    credibility_score: float = Field(default=0.0)
    domain: str = ""
    url_hash: str = ""
    
    def __init__(self, **data):
        super().__init__(**data)
        # Extract domain from URL
        parsed_url = urlparse(self.url)
        self.domain = parsed_url.netloc
        # Create URL hash for clustering
        self.url_hash = hashlib.md5(self.url.encode()).hexdigest()

class ResearchResult(BaseModel):
    """Model representing the complete research results.

    Flow2 で提案された DataModel v2 に基づき、検索結果の生データを保持して後続エージェントで直接引用できるよう、
    `raw_chunks` と `embeddings` フィールドを追加する。"""

    topic: str
    primary_results: List[SearchResult] = Field(default_factory=list)
    secondary_results: List[SearchResult] = Field(default_factory=list)
    summary: str = ""
    knowledge_gaps: List[str] = Field(default_factory=list)
    # --- Flow2 additions ---
    raw_chunks: List[str] = Field(default_factory=list, description="トークン制限回避のために分割された検索結果の抜粋")
    embeddings: Optional[List[float]] = Field(default=None, description="検索結果サマリーのベクトル表現 (オプション)")

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
        self.api_quota_available = self._check_api_quota()
        
        # Comment out this forced fallback setting to allow API usage when available
        # self.fallback_mode = True
    
    def _check_api_quota(self) -> bool:
        """Check if we have available API quota by making a minimal API call."""
        try:
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
    
    def _get_appropriate_model(self, task_importance: str = "medium") -> str:
        """
        Get the appropriate model based on task importance and available budget.
        
        Args:
            task_importance: "high", "medium", or "low" indicating task criticality
            
        Returns:
            Model name to use for this task
        """
        # If API quota is not available, always use the fallback model
        if not self.api_quota_available:
            return self.fallback_model
        
        # Map task importance to models
        if task_importance == "high":
            # For critical tasks (outline generation, final summaries)
            return self.model
        elif task_importance == "medium":
            # For important but not critical tasks (search, credibility)
            return self.search_model
        else:
            # For less critical tasks (gap analysis, clustering)
            return self.fallback_model
    
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
            return self._generate_offline_results(query, num_results)
            
        # If we have quota, try OpenAI search
        return self._search_with_openai(query, num_results, depth)
    
    def _generate_offline_results(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Generate comprehensive results without using OpenAI API when quota is exceeded."""
        logger.info(f"⚠️ APIクォータなしでの処理ができません。処理を中止します")
        raise Exception("APIクォータが不足しています。APIキーを確認してもう一度お試しください。")
    
    def _search_with_openai(self, query: str, num_results: int = 10, depth: str = "medium") -> List[SearchResult]:
        """Use OpenAI's search-enabled model to perform web searches."""
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
                return self._generate_synthetic_results(query, num_results)
            
            # 重複したログメッセージをコメントアウトして削除
            # logger.info(f"🔍 検索対応モデル「{search_model}」を使用")
            
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
                synthetic_results = self._generate_synthetic_results(query, num_results)
                logger.info(f"✅ 合成結果を生成しました: {len(synthetic_results)} 件")
                return synthetic_results
            
            if search_results:
                logger.info(f"✅ 検索完了: {len(search_results)} 件の結果を取得")
            else:
                logger.warning(f"⚠️ 検索結果なし: 検索は正常に実行されましたが、結果が見つかりませんでした")
            
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
    
    def _generate_synthetic_results(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Generate synthetic search results when real search fails.
        
        Args:
            query: The search query
            num_results: Number of synthetic results to generate
            
        Returns:
            List of synthetic SearchResult objects
        """
        logger.info(f"🤖 クエリ「{query}」に対する合成結果を生成中...")
        
        # 英語のクエリを想定したトピック抽出
        topic = query.lower()
        if "quantum" in topic or "量子" in topic:
            domain_content = {
                "量子コンピューティング基礎": "量子コンピュータは量子力学の原理を利用した次世代コンピュータです。従来のビット（0か1）ではなく、キュービットを使用し、重ね合わせと量子もつれにより並列計算が可能になります。量子アルゴリズムとしてショアのアルゴリズムやグローバーのアルゴリズムが有名です。",
                "量子コンピュータの実用化": "IBMやGoogleなどの企業が量子コンピュータの実用化に向けて研究を進めています。現在は数十〜数百キュービットの実験的なマシンが開発されていますが、エラー訂正や量子ゲートの精度向上が課題です。",
                "量子暗号": "量子鍵配送（QKD）は盗聴を検知できる安全な通信方式として注目されています。量子状態の観測により状態が変化する性質を利用し、理論上は完全に安全な暗号を実現できます。",
                "量子アルゴリズム": "量子アルゴリズムは従来のコンピュータより効率的に解ける問題があります。素因数分解（ショアのアルゴリズム）、探索問題（グローバーのアルゴリズム）、量子シミュレーションなどが代表的です。",
                "量子コンピューティングの応用": "量子コンピュータは材料科学、薬物設計、金融モデリング、機械学習、最適化問題などの分野で革新的な進歩をもたらす可能性があります。特に複雑な量子系のシミュレーションは古典コンピュータでは困難です。"
            }
        elif "ai" in topic or "machine learning" in topic or "人工知能" in topic or "機械学習" in topic:
            domain_content = {
                "人工知能の基礎": "人工知能（AI）は、人間の知能を模倣し、学習、推論、自己修正能力を持つシステムです。機械学習とディープラーニングはAIの主要な手法であり、データからパターンを学習して予測や判断を行います。",
                "機械学習アルゴリズム": "教師あり学習、教師なし学習、強化学習が機械学習の主要なパラダイムです。回帰分析、決定木、サポートベクターマシン、ニューラルネットワークなどの手法があります。",
                "深層学習の発展": "深層学習はニューラルネットワークの層を深くした手法で、画像認識、自然言語処理、音声認識などで革命的な成果を上げています。CNNやRNN、Transformerなどのアーキテクチャが代表的です。",
                "AIの倫理と社会的影響": "AIの発展に伴い、プライバシー、バイアス、自動化による雇用変化、意思決定の透明性などの課題が生じています。責任あるAI開発と利用のためのガイドラインや規制が議論されています。",
                "AIの応用分野": "医療診断、自動運転車、推薦システム、自然言語処理、ロボット工学など、AIは多様な分野で革新をもたらしています。特にGPTのような大規模言語モデルは様々な課題に対応できる汎用性を示しています。"
            }
        else:
            # その他のトピックに対する一般的な合成コンテンツ
            domain_content = {
                f"{query}の概要": f"{query}は現代の技術や研究において重要なトピックです。基本的な概念から応用まで幅広い知識体系があります。",
                f"{query}の歴史": f"{query}の分野は長い歴史を持ち、時代とともに発展してきました。初期の概念から現在の最先端研究まで様々な進化を遂げています。",
                f"{query}の応用": f"{query}は科学、技術、社会など多くの分野で応用されています。実用的な例としては様々なケーススタディがあります。",
                f"{query}の将来展望": f"{query}の分野は今後さらなる発展が期待されています。新しい技術や方法論により、現在の課題が解決される可能性があります。",
                f"{query}における課題": f"{query}に関する研究や応用には、いくつかの重要な課題が存在します。これらの課題解決が今後の進展の鍵となります。"
            }
        
        # 合成結果の生成
        synthetic_results = []
        domains = ["research.example.org", "academy.example.com", "science.example.net", 
                   "knowledge.example.edu", "institute.example.org"]
        
        items = list(domain_content.items())
        # 要求された結果数に応じてコンテンツを調整（少なくとも1つは返す）
        for i in range(min(num_results, len(items))):
            topic_key, content = items[i]
            domain = domains[i % len(domains)]
            
            result = SearchResult(
                url=f"https://{domain}/{query.replace(' ', '-').lower()}/{i+1}",
                title=f"{topic_key} - 教育リソース",
                snippet=content[:150] + "...",
                content=content,
                source_type="synthetic",
                credibility_score=0.7
            )
            # domainとurl_hashを設定
            result.domain = domain
            result.url_hash = hashlib.md5(result.url.encode()).hexdigest()
            
            synthetic_results.append(result)
        
        return synthetic_results
    
    def evaluate_credibility(self, results: List[SearchResult]) -> List[SearchResult]:
        """
        Evaluate the credibility of search results and assign credibility scores.
        Uses both URL-based heuristics and content-based LLM evaluation.
        """
        logger.info("🧐 情報の信頼性を評価中...")
        
        try:
            # Simple baseline credibility evaluation based on source type
            for result in results:
                # Start with a baseline score based on source type
                if result.source_type == "web":
                    result.credibility_score = 0.5  # ベースラインを中立的な0.5に変更
                elif result.source_type == "ai_search":
                    result.credibility_score = 0.5
                elif result.source_type == "offline_synthetic":
                    result.credibility_score = 0.4
                elif result.source_type == "synthetic":
                    result.credibility_score = 0.3
                else:
                    result.credibility_score = 0.3
                
                # Extract domain from URL for further analysis
                try:
                    url_obj = urlparse(result.url)
                    result.domain = url_obj.netloc
                except:
                    result.domain = ""
                
                # Adjust scores based on domain characteristics
                if result.domain:
                    # Academic and government sources tend to be more reliable
                    if ".edu" in result.domain or ".gov" in result.domain:
                        result.credibility_score += 0.15
                    # .org can be somewhat more credible, but not always
                    elif ".org" in result.domain:
                        result.credibility_score += 0.1
                    # Known reference sites
                    elif any(ref in result.domain for ref in ["wikipedia.org", "britannica.com", "scholarpedia.org"]):
                        result.credibility_score += 0.1
                    # News sources
                    elif any(news in result.domain for news in ["bbc", "nytimes", "reuters", "apnews", "theguardian"]):
                        result.credibility_score += 0.1
                    
                    # Blogs and less formal sources may be less reliable
                    if "blog." in result.domain or "blogs." in result.domain:
                        result.credibility_score -= 0.05
                    
                    # Social media tends to be less reliable for factual information
                    if any(social in result.domain for social in ["facebook", "twitter", "reddit", "instagram", "tiktok"]):
                        result.credibility_score -= 0.1
                    
                    # Create a URL hash for tracking
                    result.url_hash = hashlib.md5(result.url.encode()).hexdigest()
                
            # ----- 新機能: コンテンツベースの信頼性評価 -----
            # コンテンツが利用可能な結果（スニペットまたはコンテンツがある場合）に対してLLM評価を実行
            logger.info("🔍 コンテンツベースの信頼性分析を実行中...")
            
            # バッチ処理のために結果をグループ化（APIコールを減らすため）
            batch_size = 3  # 一度に評価する結果の数
            batches = [results[i:i + batch_size] for i in range(0, len(results), batch_size)]
            
            # 全バッチの処理が失敗した場合のカウンター
            failed_batch_count = 0
            
            for batch_idx, batch in enumerate(batches):
                # バッチ内の各結果のテキストを集約
                batch_texts = []
                
                for result in batch:
                    # コンテンツがある場合はそれを使用、なければスニペットを使用
                    content_text = result.content if result.content else result.snippet
                    # 最低限の長さがあるか確認
                    if len(content_text) > 30:  # 最低30文字以上のコンテンツがある場合のみ評価
                        batch_texts.append({
                            "url": result.url,
                            "title": result.title,
                            "content": content_text[:1000]  # 長すぎる場合は最初の1000文字だけ使用
                        })
                
                # 評価するコンテンツがある場合のみAPI呼び出し
                if batch_texts:
                    try:
                        # 最初のバッチ処理開始時にログを表示
                        if batch_idx == 0:
                            logger.info(f"信頼性評価を開始: 全 {len(batches)} バッチを処理中...")
                            
                        # OpenAI APIを使用してコンテンツの信頼性を評価
                        response = client.chat.completions.create(
                            model=self._get_appropriate_model("low"),  # 低リソースモデルで十分
                            messages=[
                                {"role": "system", "content": """
                                あなたは情報の信頼性を評価する専門家です。提供されたコンテンツについて以下の基準で評価してください:
                                
                                1. 事実確認可能性: 情報が検証可能な事実に基づいているか
                                2. 客観性: 偏見や主観的意見が含まれていないか
                                3. 専門性: 専門的な知識や情報が含まれているか
                                4. 最新性: 情報が最新かどうか (日付や時間的文脈から判断)
                                5. 一貫性: 内容に矛盾がないか
                                
                                各URLのコンテンツに対して、0.0〜1.0の信頼性スコアを生成してください。
                                0.0は「まったく信頼できない」、1.0は「非常に信頼できる」を意味します。
                                
                                必ず次のJSON形式で出力してください:
                                {
                                  "results": [
                                    {"url": "URL1", "credibility_score": 0.X, "reason": "簡潔な理由"},
                                    {"url": "URL2", "credibility_score": 0.Y, "reason": "簡潔な理由"}
                                  ]
                                }
                                """},
                                {"role": "user", "content": f"以下のコンテンツの信頼性をJSON形式で評価してください: {json.dumps(batch_texts, ensure_ascii=False)}"}
                            ],
                            response_format={"type": "json_object"},
                            temperature=0.2,
                            max_tokens=800
                        )
                        
                        # レスポンスを解析
                        try:
                            content = response.choices[0].message.content
                            assessment = json.loads(content)
                            
                            # 各結果のスコアを更新
                            for item in assessment.get("results", []):
                                url = item.get("url")
                                new_score = item.get("credibility_score")
                                reason = item.get("reason", "")
                                
                                # 対応する結果を見つけて更新
                                for result in batch:
                                    if result.url == url and new_score is not None:
                                        # ドメインベースのスコアとコンテンツベースのスコアを組み合わせる
                                        # ドメインベースを40%、コンテンツベースを60%の重みで統合
                                        domain_weight = 0.4
                                        content_weight = 0.6
                                        current_score = result.credibility_score
                                        
                                        # 重み付き平均で新しいスコアを計算
                                        result.credibility_score = (current_score * domain_weight) + (new_score * content_weight)
                                        logger.debug(f"URL: {url} の信頼性スコアを更新: {current_score:.2f} → {result.credibility_score:.2f}, 理由: {reason}")
                            
                            # バッチが正常に処理された
                            failed_batch_count = 0  # 成功したらカウンターをリセット
                        
                        except json.JSONDecodeError:
                            failed_batch_count += 1
                            logger.debug("信頼性評価の応答をJSONとして解析できませんでした")
                            if failed_batch_count == 1:  # 最初の失敗時のみ警告を表示
                                logger.warning("⚠️ 一部の信頼性評価に問題がありました")
                        except Exception as parse_err:
                            failed_batch_count += 1
                            logger.debug(f"信頼性評価の応答解析エラー: {str(parse_err)}")
                            if failed_batch_count == 1:  # 最初の失敗時のみ警告を表示
                                logger.warning("⚠️ 一部の信頼性評価に問題がありました")
                    
                    except Exception as api_err:
                        # 詳細なエラーをデバッグログに記録し、コンソールには最小限の情報を表示
                        logger.debug(f"信頼性評価のAPI呼び出しエラー詳細: {str(api_err)}")
                        failed_batch_count += 1
                        
                        # 最初の失敗時のみ警告を表示
                        if failed_batch_count == 1:
                            logger.warning("⚠️ 一部の信頼性評価に問題がありました")
                        
                        # 全てのバッチが失敗した場合
                        if failed_batch_count >= len(batches):
                            logger.warning("⚠️ 信頼性評価が完全に失敗しました。基本スコアを使用します")
                            # 基本スコアを適用（最低0.2、最大0.8）
                            for r in results:
                                if r.credibility_score < 0.2:
                                    r.credibility_score = 0.3 + (hash(r.url) % 10) / 20  # URLハッシュに基づくわずかなランダム性
            
            # 最終完了メッセージ（すべてのバッチ処理後）
            if len(batches) > 1:
                logger.info("✅ 信頼性評価が完了しました")
            
            # 最終的なスコアをクリップして有効な範囲（0.1〜0.9）に収める
            for result in results:
                result.credibility_score = max(0.1, min(0.9, result.credibility_score))
            
            logger.info(f"✅ 信頼性評価完了: URL + コンテンツベースの評価")
            return results
            
        except Exception as e:
            logger.error(f"❌ 信頼性評価エラー: {e}")
            logger.info("❌ 信頼性評価に失敗しました。デフォルト値を使用します")
            
            # Just return results with default scores if evaluation fails
            for result in results:
                if not hasattr(result, 'credibility_score') or result.credibility_score == 0:
                    result.credibility_score = 0.5
            
            return results
    
    def cluster_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Cluster results by domain to reduce redundancy."""
        logger.info("📊 検索結果をグループ化中...")
        domain_map = {}
        clustered_results = []
        
        for result in results:
            if result.domain not in domain_map:
                domain_map[result.domain] = []
            domain_map[result.domain].append(result)
        
        # Take the highest credibility result from each domain
        for domain, domain_results in domain_map.items():
            best_result = max(domain_results, key=lambda x: x.credibility_score)
            clustered_results.append(best_result)
        
        # Sort by credibility score
        clustered_results.sort(key=lambda x: x.credibility_score, reverse=True)
        logger.info(f"✅ グループ化完了: {len(clustered_results)} 件の結果")
        return clustered_results
    
    def extract_knowledge_gaps(self, results: List[SearchResult], topic: str, depth: str = "medium") -> List[str]:
        """Identify knowledge gaps from the initial search results."""
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
                model=self._get_appropriate_model(depth),
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
            # 詳細なエラーはログファイルに記録
            logger.error(f"❌ 情報ギャップ分析エラー: {e}")
            # コンソールには簡潔なメッセージのみ表示
            logger.info("❌ 情報ギャップの分析に失敗しました。基本的な項目を使用します")
            return [f"More detailed information about {topic}"]
    
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
        primary_results = self.evaluate_credibility(unique_primary_results)
        
        # Cluster to reduce redundancy
        primary_results = self.cluster_results(primary_results)
        research_result.primary_results = primary_results
        
        if layers >= 2 and primary_results:
            # Extract knowledge gaps for secondary searches
            logger.info("🔬 追加調査項目を特定中...")
            knowledge_gaps = self.extract_knowledge_gaps(primary_results, topic, depth)
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
                    gap_results = self.evaluate_credibility(gap_results)
                    secondary_results.extend(gap_results)
                    logger.info(f"✅ 詳細情報を取得: {len(gap_results)} 件")
                    break  # If we got results, don't try other base queries
            
            # Cluster secondary results
            if secondary_results:
                secondary_results = self.cluster_results(secondary_results)
                research_result.secondary_results = secondary_results
        
        # If we still have no results (primary or secondary), generate basic knowledge
        if not research_result.primary_results and not research_result.secondary_results:
            logger.warning("⚠️ 検索結果がありません。基本情報を生成します")
            synthetic_results = self._generate_synthetic_results(topic, 5)
            research_result.primary_results = synthetic_results
            
            # Also generate some knowledge gaps
            research_result.knowledge_gaps = [
                f"Fundamentals of {topic}",
                f"Applications of {topic}",
                f"Best practices for {topic}",
                f"Future developments in {topic}"
            ]
        
        # Generate a comprehensive summary
        logger.info("📝 調査結果のサマリーを作成中...")
        research_result.summary = self.generate_summary(research_result)
        
        logger.info("✅ トピック調査完了")
        return research_result
    
    def generate_summary(self, research: ResearchResult) -> str:
        """Generate a comprehensive summary of the research findings."""
        logger.info("📊 情報を要約中...")
        
        # Check if we already have a good summary
        if research.summary and len(research.summary.split()) > 200:
            logger.info("✅ 既存のサマリーを使用します")
            # コンソールに既存のサマリーを表示
            print("\n📋 リサーチサマリー:")
            print(research.summary[:500] + "..." if len(research.summary) > 500 else research.summary)
            return research.summary
        
        # Strategy 1: Use OpenAI API to generate a summary from the search results
        summary = None
        try:
            # Collect all relevant snippets and titles for context
            research_context = []
            
            # Start with higher credibility primary results
            for result in sorted(research.primary_results, key=lambda x: x.credibility_score, reverse=True):
                research_context.append(f"Title: {result.title}")
                research_context.append(f"Snippet: {result.snippet}")
                if result.content:
                    truncated = (result.content[:500] + "...") if len(result.content) > 500 else result.content
                    research_context.append(f"Content: {truncated}")
                research_context.append("---")
            
            # Add some secondary results if needed
            if len(research_context) < 1000 and research.secondary_results:
                for result in sorted(research.secondary_results, key=lambda x: x.credibility_score, reverse=True)[:5]:
                    research_context.append(f"Title: {result.title}")
                    research_context.append(f"Snippet: {result.snippet}")
                    research_context.append("---")
            
            prompt = f"""
            Create a comprehensive summary about "{research.topic}" based on the following research findings:
            
            {"\n".join(research_context[:3500])}
            
            Your summary should:
            1. Present key concepts, facts and insights in a well-structured way
            2. Organize information logically with headings and subheadings
            3. Be educational and informative, suitable for a presentation slide deck
            4. Include the most important points from multiple sources
            5. Use markdown format with ## for headings and ### for subheadings
            
            Aim for a comprehensive summary of 500-800 words.
            """
            
            # Using a more robust model for summary generation
            response = client.chat.completions.create(
                model=self.model,  # Use the most capable model available
                messages=[
                    {"role": "system", "content": "You are an expert researcher who creates comprehensive summaries from multiple sources."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.3  # Low temperature for more factual output
            )
            
            summary = response.choices[0].message.content.strip()
            
            if summary and len(summary.split()) > 50:
                logger.info("✅ サマリー作成完了")
                print("\n📋 リサーチサマリー:")
                print(summary[:500] + "..." if len(summary) > 500 else summary)
                return summary
            else:
                logger.warning("⚠️ 生成されたサマリーが短すぎます")
                
        except Exception as e:
            logger.error(f"❌ サマリー生成エラー (戦略 1): {e}")
        
        # Strategy 2: Alternative approach with a simpler prompt
        try:
            # Using a more straightforward prompt
            alternative_prompt = f"""
            Topic: {research.topic}
            
            Please create a detailed educational summary on this topic using the following information:
            
            {research.primary_results[0].snippet if research.primary_results else ""}
            {research.primary_results[1].snippet if len(research.primary_results) > 1 else ""}
            {research.primary_results[2].snippet if len(research.primary_results) > 2 else ""}
            
            Format your response as a structured markdown document with:
            - ## Main headings
            - ### Subheadings
            - Paragraphs with clear explanations
            - Important concepts highlighted
            
            The summary should be comprehensive enough for a presentation.
            """
            
            response = client.chat.completions.create(
                model=self.search_model,  # Try with the search model if main model failed
                messages=[
                    {"role": "system", "content": "You are a knowledgeable educator creating clear and structured topic summaries."},
                    {"role": "user", "content": alternative_prompt}
                ],
                max_tokens=1500
            )
            
            summary = response.choices[0].message.content.strip()
            
            if summary and len(summary.split()) > 50:
                logger.info("✅ 代替サマリー作成完了 (戦略 2)")
                print("\n📋 リサーチサマリー:")
                print(summary[:500] + "..." if len(summary) > 500 else summary)
                return summary
                
        except Exception as e:
            logger.error(f"❌ サマリー生成エラー (戦略 2): {e}")
        
        # Emergency fallback - generate a basic summary using titles and snippets
        try:
            # Generate a basic summary using the available information
            
            # Collect titles from primary results
            titles = [result.title for result in research.primary_results]
            unique_titles = list(set(titles))
            
            # Create a basic markdown structure
            basic_summary = f"# {research.topic}\n\n"
            
            # Add a basic definition if available
            if research.primary_results:
                basic_summary += f"## Definition\n{research.primary_results[0].snippet}\n\n"
            
            # Add key concepts based on titles
            basic_summary += "## Key Concepts\n\n"
            
            # Extract key topics from titles
            topics = set()
            for title in unique_titles[:5]:  # Use up to 5 titles
                words = title.split()
                if len(words) > 2:
                    topics.add(" ".join(words[:3]))  # Use first 3 words of each title
            
            # Add each topic as a subheading
            for i, topic in enumerate(list(topics)[:3]):  # Use up to 3 topics
                basic_summary += f"### {i+1}. {topic}\n"
                
                # Find a relevant snippet
                for result in research.primary_results:
                    if any(word.lower() in result.snippet.lower() for word in topic.split()):
                        basic_summary += f"{result.snippet}\n\n"
                        break
                else:
                    # If no relevant snippet found, use a generic placeholder
                    basic_summary += f"Information about {topic} and its applications.\n\n"
            
            # Add a conclusion
            basic_summary += f"## Summary\n{research.topic} encompasses various important concepts and applications as outlined above."
            
            logger.info("✅ 基本情報を使用したサマリー作成完了")
            print("\n📋 リサーチサマリー:")
            print(basic_summary[:500] + "..." if len(basic_summary) > 500 else basic_summary)
            return basic_summary
            
        except Exception as e:
            logger.error(f"❌ 緊急サマリー生成エラー: {e}")
            
            # Ultimate fallback - just concatenate titles and snippets
            fallback = f"# {research.topic}\n\n"
            fallback += "## Overview\n"
            if research.primary_results:
                for i, result in enumerate(research.primary_results[:3]):
                    fallback += f"- {result.title}: {result.snippet}\n"
            else:
                fallback += f"Information about {research.topic}."
            
            return fallback

    def _search_with_alternative_provider(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Use alternative search providers when OpenAI API is unavailable."""
        logger.info(f"🔍 代替検索プロバイダーで検索中: {query}")
        
        try:
            # Try SerpAPI if key is available
            if self.serp_api_key:
                return self._search_with_serpapi(query, num_results)
            
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
        
    def _search_with_serpapi(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """Perform search using SerpAPI."""
        try:
            import requests
            
            # Set up SerpAPI request
            params = {
                "engine": "google",
                "q": query,
                "api_key": self.serp_api_key,
                "num": num_results
            }
            
            # Make request to SerpAPI
            response = requests.get(
                "https://serpapi.com/search", 
                params=params
            )
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                results = []
                
                # Extract organic results
                if "organic_results" in data:
                    for result in data["organic_results"][:num_results]:
                        search_result = SearchResult(
                            url=result.get("link", ""),
                            title=result.get("title", ""),
                            snippet=result.get("snippet", ""),
                            source_type="serpapi"
                        )
                        results.append(search_result)
                
                if results:
                    logger.info(f"✅ SerpAPIから {len(results)} 件の結果を取得")
                    return results
            
            logger.warning(f"⚠️ SerpAPI検索が結果を返しませんでした (ステータスコード: {response.status_code})")
            return []
            
        except Exception as e:
            logger.error(f"❌ SerpAPI検索エラー: {e}")
            return []

# Convenience function for direct module use
def search_deep(topic: str, depth: str = "medium") -> ResearchResult:
    """
    Public API: Perform a deep search on a topic with the default ResearchAgent.
    
    Args:
        topic: The topic to research
        depth: Search depth - "low", "medium", or "high"
    """
    agent = ResearchAgent()
    return agent.search_deep(topic, depth)

def search_basic(topic: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    Perform a basic search on a topic and return simplified results
    
    Args:
        topic: The topic to search for
        num_results: Number of results to return
        
    Returns:
        List of simplified search results as dictionaries
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
            
            # Extract real title if it's in markdown format
            title = result.title.strip()
            markdown_title_pattern = r'\[(.*?)\]'
            markdown_title_match = re.search(markdown_title_pattern, title)
            if markdown_title_match:
                title = markdown_title_match.group(1).strip()
            else:
                # If not in markdown, clean up any other artifacts
                title = re.sub(r'\*\*|\*|[-•]|\bURL:|\bURL\b', '', title).strip()
            
            # Check if the title is just a domain name
            if title.endswith('.jp') or title.endswith('.com') or title.endswith('.org') or title.endswith('.net'):
                # Try to get a better title from the URL domain parts
                domain_parts = url.split('://')[-1].split('/')[0].split('.')
                if len(domain_parts) >= 2:
                    site_name = domain_parts[-2].capitalize()
                    title = f"{site_name} - {topic}に関する情報"
            
            # Clean up the summary
            summary = result.snippet.strip() if result.snippet else ""
            
            # If summary is just a URL remnant or empty, provide a generic summary
            if not summary or summary.startswith('ook/') or summary.endswith('ai))"') or summary.endswith('ai))'):
                summary = f"{topic}に関する情報 - {title}"
            
            simplified_results.append({
                "title": title,
                "source": url,
                "summary": summary
            })
        
        logger.info(f"✅ 基本検索が完了しました: {len(simplified_results)} 件の結果")
        return simplified_results
        
    except Exception as e:
        logger.error(f"❌ 基本検索中にエラーが発生しました: {str(e)}")
        # Return a minimal result set to avoid breaking the pipeline
        dummy_results = []
        for i in range(min(num_results, 3)):
            dummy_results.append({
                "title": f"{topic} - 情報 {i+1}",
                "source": "https://example.com",
                "summary": f"{topic}に関する情報です。APIエラーによりオンライン検索ができないため、限定的な情報のみ提供しています。"
            })
        return dummy_results 