"""
Research Summarization

This module provides functionality for generating comprehensive summaries of research results.
"""

import logging
from typing import List, Dict, Any, Optional

from .models import ResearchResult, SearchResult
from agents import client

# Configure logging
logger = logging.getLogger(__name__)

def generate_summary(research: ResearchResult, model: str) -> str:
    """
    Generate a comprehensive summary of the research findings.
    
    Args:
        research: The research result to summarize
        model: LLM model to use for summarization
        
    Returns:
        Comprehensive summary of the research
    """
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
            model=model,  # Use the provided model
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
            model=model,  # Use the provided model
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