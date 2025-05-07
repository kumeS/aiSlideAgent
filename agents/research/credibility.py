"""
Credibility Evaluation

This module provides functionality for evaluating the credibility of search results.
"""

import logging
import json
import hashlib
import time
from typing import List, Dict, Any
from urllib.parse import urlparse

from .models import SearchResult
from agents import client

# Configure logging
logger = logging.getLogger(__name__)

def evaluate_credibility(results: List[SearchResult], model: str) -> List[SearchResult]:
    """
    Evaluate the credibility of search results and assign credibility scores.
    Uses both URL-based heuristics and content-based LLM evaluation.
    
    Args:
        results: List of search results to evaluate
        model: LLM model to use for content evaluation
        
    Returns:
        List of search results with credibility scores assigned
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
            
        # ----- Content-based credibility evaluation -----
        # Evaluate results that have content (snippet or content field)
        logger.info("🔍 コンテンツベースの信頼性分析を実行中...")
        
        # Batch process results to reduce API calls
        batch_size = 3  # Number of results to evaluate at once
        batches = [results[i:i + batch_size] for i in range(0, len(results), batch_size)]
        
        # Counter for failed batches
        failed_batch_count = 0
        
        for batch_idx, batch in enumerate(batches):
            # Collect texts from each result in the batch
            batch_texts = []
            
            for result in batch:
                # Use content if available, otherwise use snippet
                content_text = result.content if result.content else result.snippet
                # Check minimum length
                if len(content_text) > 30:  # Only evaluate if there's enough content
                    batch_texts.append({
                        "url": result.url,
                        "title": result.title,
                        "content": content_text[:1000]  # Use first 1000 chars for long content
                    })
            
            # Only make API call if there's content to evaluate
            if batch_texts:
                try:
                    # Log start of processing for first batch
                    if batch_idx == 0:
                        logger.info(f"信頼性評価を開始: 全 {len(batches)} バッチを処理中...")
                        
                    # Use OpenAI API to evaluate content credibility
                    response = client.chat.completions.create(
                        model=model,  # Use the provided model
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
                    
                    # Parse response
                    try:
                        content = response.choices[0].message.content
                        assessment = json.loads(content)
                        
                        # Update scores for each result
                        for item in assessment.get("results", []):
                            url = item.get("url")
                            new_score = item.get("credibility_score")
                            reason = item.get("reason", "")
                            
                            # Find matching result and update
                            for result in batch:
                                if result.url == url and new_score is not None:
                                    # Combine domain-based score (40%) and content-based score (60%)
                                    domain_weight = 0.4
                                    content_weight = 0.6
                                    current_score = result.credibility_score
                                    
                                    # Calculate weighted average
                                    result.credibility_score = (current_score * domain_weight) + (new_score * content_weight)
                                    logger.debug(f"URL: {url} の信頼性スコアを更新: {current_score:.2f} → {result.credibility_score:.2f}, 理由: {reason}")
                        
                        # Batch processed successfully
                        failed_batch_count = 0  # Reset counter on success
                    
                    except json.JSONDecodeError:
                        failed_batch_count += 1
                        logger.debug("信頼性評価の応答をJSONとして解析できませんでした")
                        if failed_batch_count == 1:  # Only show warning on first failure
                            logger.warning("⚠️ 一部の信頼性評価に問題がありました")
                    except Exception as parse_err:
                        failed_batch_count += 1
                        logger.debug(f"信頼性評価の応答解析エラー: {str(parse_err)}")
                        if failed_batch_count == 1:  # Only show warning on first failure
                            logger.warning("⚠️ 一部の信頼性評価に問題がありました")
                
                except Exception as api_err:
                    # Log detailed error in debug log, show minimal info in console
                    logger.debug(f"信頼性評価のAPI呼び出しエラー詳細: {str(api_err)}")
                    failed_batch_count += 1
                    
                    # Only show warning on first failure
                    if failed_batch_count == 1:
                        logger.warning("⚠️ 一部の信頼性評価に問題がありました")
                    
                    # If all batches have failed
                    if failed_batch_count >= len(batches):
                        logger.warning("⚠️ 信頼性評価が完全に失敗しました。基本スコアを使用します")
                        # Apply basic scores (min 0.2, max 0.8)
                        for r in results:
                            if r.credibility_score < 0.2:
                                r.credibility_score = 0.3 + (hash(r.url) % 10) / 20  # Slight randomness based on URL hash
        
        # Completion message (after all batches)
        if len(batches) > 1:
            logger.info("✅ 信頼性評価が完了しました")
        
        # Clip final scores to valid range (0.1-0.9)
        for result in results:
            result.credibility_score = max(0.1, min(0.9, result.credibility_score))
        
        logger.info(f"✅ 信頼性評価完了: URL + コンテンツベースの評価")
        return results
        
    except Exception as e:
        logger.error(f"❌ 信頼性評価エラー: {e}")
        logger.info("❌ 信頼性評価に失敗しました。デフォルト値を使用します")
        
        # Return results with default scores if evaluation fails
        for result in results:
            if not hasattr(result, 'credibility_score') or result.credibility_score == 0:
                result.credibility_score = 0.5
        
        return results

def cluster_results(results: List[SearchResult]) -> List[SearchResult]:
    """
    Cluster results by domain to reduce redundancy.
    
    Args:
        results: List of search results to cluster
        
    Returns:
        Clustered list of search results
    """
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