"""
Monitoring Agent Implementation

This module provides monitoring and coordination functionality
for the slide generation process, including feedback loops and metrics.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple

from agents import client, DEFAULT_MODEL
from agents.research import ResearchAgent, ResearchResult
from agents.outline import OutlineAgent, SlideDeck
from agents.slide_writer import SlideWriterAgent, SlideTheme, generate_slides
from agents.image_fetch import ImageFetchAgent
from agents.refiner import RefinerAgent

# Configure logging
logger = logging.getLogger(__name__)

class MonitoringAgent:
    """
    MonitoringAgent is responsible for:
    1. Coordinating the research and outline generation process
    2. Monitoring the slide generation and refinement process
    3. Providing feedback and metrics on the generation process
    4. Implementing fallback strategies when components fail
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = True):
        self.model = model
        self.verbose = verbose
        
    def coordinate_research_and_outline(self, topic: str, slide_count: int, depth: str = "medium") -> Tuple[ResearchResult, SlideDeck]:
        """
        Coordinate and monitor the research and outline generation process.
        
        Args:
            topic: The topic to research
            slide_count: Number of slides to generate
            depth: Research depth ("low", "medium", "high")
            
        Returns:
            Tuple of (research_result, slide_deck)
        """
        logger.info(f"Monitoring research and outline for topic: {topic}")
        start_time = time.time()
        
        # Step 1: Execute research with the appropriate depth
        try:
            research_agent = ResearchAgent()
            
            # Check if API is available
            if not research_agent.api_quota_available:
                logger.warning("⚠️ APIクォータ/クレジットバランス不足または接続エラーが検出されました")
                logger.warning("⚠️ オフラインモードで動作しています - 結果の品質が低下する可能性があります")
                
                # Create offline research results using _generate_synthetic_results instead
                from agents.research import SearchResult
                synthetic_results = research_agent._generate_synthetic_results(topic, 10)
                
                # Create ResearchResult
                research_result = ResearchResult(
                    topic=topic,
                    primary_results=synthetic_results,
                    secondary_results=[],
                    summary=f"# {topic}\n\nThis is a synthetic summary about {topic} generated in offline mode."
                )
                
                # Generate outline
                from agents.outline import OutlineAgent
                outline_agent = OutlineAgent()
                outline = outline_agent.generate_outline(research_result, slide_count, topic)
                
                return research_result, outline
            
            # Execute research with regular API access
            research_result = research_agent.search_deep(topic, depth)
            elapsed_research = time.time() - start_time
            logger.info(f"Research completed in {elapsed_research:.2f}s")
            
            # Validate research result
            if not research_result.primary_results or len(research_result.primary_results) < 3:
                logger.warning("⚠️ 検索結果が不十分です（3件未満）")
                
            if not research_result.summary or len(research_result.summary.split()) < 100:
                logger.warning("⚠️ 検索サマリーが不十分です（100単語未満）")
            
            # Step 2: Generate outline based on research
            outline_agent = OutlineAgent()
            outline = outline_agent.generate_outline(research_result, slide_count, topic)
            
            # Validate outline
            if not outline.slides or len(outline.slides) < slide_count * 0.8:
                logger.warning(f"⚠️ 要求されたスライド枚数（{slide_count}）に対して生成されたスライドが不足しています")
                
                # Try to expand outline if too few slides
                additional_needed = max(0, int(slide_count - len(outline.slides)))
                if additional_needed > 0:
                    logger.info(f"📄 アウトラインを {additional_needed} スライド分拡張します")
                    outline_agent._expand_slide_deck(outline, additional_needed, research_result)
            
            # Check for insufficient sources/content
            sources_count = 0
            for result in research_result.primary_results:
                if result.snippet and len(result.snippet) > 50:
                    sources_count += 1
            
            # If we have very few sources, enhance the outline with generated information
            if sources_count <= 1:  # Really minimal info
                logger.info("⚠️ 情報が非常に限られています。AIによるアウトラインの改良を試みます")
                
                from agents import client, DEFAULT_MODEL
                
                # First, have AI generate some basic topic information
                topic_info_prompt = f"""
                The topic is: "{topic}"
                
                Please provide a comprehensive overview of this topic including:
                1. Definition and key concepts
                2. Main applications or use cases
                3. Important historical context or development
                4. Current trends or state-of-the-art
                5. Future prospects or challenges
                
                Format your response as a structured markdown document with clear sections.
                """
                
                response = client.chat.completions.create(
                    model=DEFAULT_MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert in providing comprehensive, factual information on any topic. Provide detailed, balanced information with proper structure."},
                        {"role": "user", "content": topic_info_prompt}
                    ],
                    max_tokens=1500
                )
                
                generated_info = response.choices[0].message.content.strip()
                
                # Add this as a synthetic result
                from agents.research import SearchResult
                synthetic_result = SearchResult(
                    url=f"https://ai-enhanced-info.example.com/{topic.lower().replace(' ', '-')}",
                    title=f"Comprehensive Overview of {topic}",
                    snippet="AI-generated comprehensive overview including definitions, applications, history, trends, and future prospects.",
                    content=generated_info,
                    source_type="ai_enhanced",
                    credibility_score=0.6  # Medium-high credibility for AI-enhanced content
                )
                
                # Add to research results
                research_result.primary_results.append(synthetic_result)
                
                # Update the summary with the new information
                if not research_result.summary or len(research_result.summary) < 200:
                    research_result.summary = f"# Research Summary: {topic}\n\n" + generated_info
                
                # Now regenerate the outline with the enhanced information
                outline = outline_agent.generate_outline(research_result, slide_count, topic)
                logger.info("✅ AIによるアウトラインの改良が完了しました")
            
            return research_result, outline
            
        except Exception as e:
            logger.error(f"❌ リサーチまたはアウトライン生成中にエラーが発生しました: {e}")
            
            try:
                research_agent = ResearchAgent()
                research_result = research_agent.search_deep(topic, depth)
                
                from agents.outline import generate_outline
                outline = generate_outline(research_result, slide_count)
                
                return research_result, outline
            except Exception as fallback_error:
                # フォールバックも失敗した場合の最終手段
                logger.error(f"❌ フォールバック処理にも失敗しました: {fallback_error}")
                
                # 最小限の結果を返す
                from agents.research import SearchResult
                minimal_research = ResearchResult(
                    topic=topic,
                    primary_results=[
                        SearchResult(
                            url=f"https://example.com/{topic.lower().replace(' ', '-')}",
                            title=f"Information about {topic}",
                            snippet=f"Basic information about {topic} would be presented here.",
                            source_type="fallback"
                        )
                    ],
                    summary=f"# {topic}\n\nBasic information about {topic}."
                )
                
                from agents.outline import SlideContent
                minimal_outline = SlideDeck(
                    topic=topic,
                    title=topic,
                    slides=[
                        SlideContent(title=topic, type="title", content=[f"Overview of {topic}"]),
                        SlideContent(title="Introduction", type="content", content=[f"Basic information about {topic}"]),
                        SlideContent(title="Conclusion", type="content", content=["Summary and key points"])
                    ]
                )
                
                return minimal_research, minimal_outline
    
    def coordinate_slides_and_refiner(self, outline: SlideDeck, theme: SlideTheme, 
                                     style: str = "professional") -> Tuple[str, Dict]:
        """
        Coordinate and monitor the slide generation and refinement process.
        
        Args:
            outline: The slide deck outline
            theme: The slide theme to use
            style: Presentation style
            
        Returns:
            Tuple of (html_content, quality_report)
        """
        logger.info(f"Monitoring slide generation and refinement for topic: {outline.topic}")
        start_time = time.time()
        
        # Fetch images for slides
        image_agent = ImageFetchAgent()
        slide_topics = [slide.title for slide in outline.slides if slide.image_suggestion]
        
        if slide_topics:
            logger.info(f"Fetching {len(slide_topics)} images for slides...")
            images_by_topic = image_agent.fetch_images_for_slides(slide_topics)
            
            # Associate images with slides
            for slide in outline.slides:
                if slide.title in images_by_topic:
                    image = images_by_topic[slide.title]
                    slide.image_path = image.local_path
                    slide.alt_text = image.alt_text
        
        # Initial slide generation
        try:
            slide_writer = SlideWriterAgent()
            slide_deck_html = slide_writer.generate_slides(outline, theme)
            html_content = slide_writer.render_full_deck(slide_deck_html)
            
            elapsed_gen = time.time() - start_time
            logger.info(f"Initial slides generated in {elapsed_gen:.2f}s")
            
            # Initial refinement
            refiner = RefinerAgent()
            refined_html, issues = refiner.refine_html(html_content)
            
            # Calculate quality metrics
            citation_coverage = refiner.citation_coverage(refined_html)
            
            # Define iteration thresholds
            max_iterations = 2
            quality_threshold = 0.8  # 80% quality score needed to pass
            
            # Calculate quality score based on issues and coverage
            issue_ratio = min(1.0, len(issues) / 10)  # More than 10 issues = 100% issue ratio
            quality_score = (1 - issue_ratio) * 0.6 + citation_coverage * 0.4  # 60/40 weight
            
            # Refinement iterations if needed
            current_iteration = 1
            iterations_done = 1
            current_html = refined_html
            
            qa_report = {
                "initial_issues": len(issues),
                "citation_coverage": citation_coverage,
                "quality_score": quality_score,
                "iterations": iterations_done,
                "summary": "Initial refinement complete"
            }
            
            # Iterative refinement if quality threshold not met
            while quality_score < quality_threshold and current_iteration < max_iterations:
                logger.info(f"Quality score {quality_score:.2f} below threshold {quality_threshold}, performing iteration {current_iteration+1}")
                
                # Refine again
                current_html, new_issues = refiner.refine_html(current_html)
                
                # Recalculate metrics
                new_citation_coverage = refiner.citation_coverage(current_html)
                new_issue_ratio = min(1.0, len(new_issues) / 10)
                new_quality_score = (1 - new_issue_ratio) * 0.6 + new_citation_coverage * 0.4
                
                logger.info(f"Iteration {current_iteration+1} quality score: {new_quality_score:.2f}")
                
                # Update if improved
                if new_quality_score > quality_score:
                    quality_score = new_quality_score
                    citation_coverage = new_citation_coverage
                    issues = new_issues
                    iterations_done += 1
                
                current_iteration += 1
            
            # Create final QA report
            qa_report = {
                "final_issues": len(issues),
                "citation_coverage": citation_coverage,
                "overall_score": quality_score,
                "iterations": iterations_done,
                "issues_by_type": {},
                "summary": "Refinement process completed successfully"
            }
            
            # Categorize issues by type
            for issue in issues:
                issue_type = issue.get('type', 'unknown')
                if issue_type not in qa_report["issues_by_type"]:
                    qa_report["issues_by_type"][issue_type] = 0
                qa_report["issues_by_type"][issue_type] += 1
            
            # Qualitative summary based on score
            if quality_score >= 0.9:
                qa_report["summary"] = "高品質: 引用カバレッジが高く、アクセシビリティやコンテンツに問題がない"
            elif quality_score >= 0.7:
                qa_report["summary"] = "良好: 一部改善の余地があるが全体的に良好"
            elif quality_score >= 0.5:
                qa_report["summary"] = "普通: いくつかの問題が見られるが使用可能"
            else:
                qa_report["summary"] = "要改善: 複数の問題が見られる"
            
            return current_html, qa_report
            
        except Exception as e:
            logger.error(f"❌ スライド生成または改善中にエラーが発生しました: {e}")
            
            try:
                # Fallback to basic slide generation and refinement
                html_content = generate_slides(outline, theme, style)
                
                refiner = RefinerAgent()
                refined_html, issues = refiner.refine_html(html_content)
                
                # Minimal QA report
                qa_report = {
                    "final_issues": len(issues),
                    "overall_score": 0.5,  # Default middle score
                    "summary": "Basic fallback refinement performed"
                }
                
                return refined_html, qa_report
                
            except Exception as fallback_error:
                logger.error(f"❌ フォールバック処理にも失敗しました: {fallback_error}")
                
                # Create minimal HTML output as last resort
                minimal_html = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{outline.title}</title>
                    <style>
                        body {{ font-family: system-ui, sans-serif; margin: 0; padding: 0; background: #0F172A; color: white; }}
                        .slide {{ min-height: 100vh; padding: 2rem; display: flex; flex-direction: column; justify-content: center; }}
                        h1, h2 {{ margin-bottom: 2rem; }}
                        ul {{ font-size: 1.5rem; }}
                    </style>
                </head>
                <body>
                    <div class="slide">
                        <h1>{outline.title}</h1>
                        <p>Generated presentation</p>
                    </div>
                """
                
                # Add minimal content for each slide
                for slide in outline.slides[:5]:  # Limit to first 5 slides in emergency
                    minimal_html += f"""
                    <div class="slide">
                        <h2>{slide.title}</h2>
                        <ul>
                    """
                    
                    for point in slide.content[:3]:  # Limit to first 3 content points
                        minimal_html += f"<li>{point}</li>\n"
                    
                    minimal_html += """
                        </ul>
                    </div>
                    """
                
                minimal_html += """
                </body>
                </html>
                """
                
                # Minimal QA report for error case
                qa_report = {
                    "final_issues": 0,
                    "overall_score": 0.3,  # Lower score for emergency fallback
                    "summary": "Emergency fallback HTML generated due to failures"
                }
                
                return minimal_html, qa_report

def monitor_research_and_outline(topic: str, slide_count: int, depth: str) -> Tuple[ResearchResult, SlideDeck]:
    """
    Convenience function to monitor the research and outline generation process.
    
    Args:
        topic: The topic to research
        slide_count: Number of slides to generate
        depth: Research depth ("low", "medium", "high")
        
    Returns:
        Tuple of (research_result, slide_deck)
    """
    agent = MonitoringAgent()
    return agent.coordinate_research_and_outline(topic, slide_count, depth)

def monitor_slides_and_refine(outline: SlideDeck, theme: SlideTheme) -> Tuple[str, Dict]:
    """
    Convenience function to monitor the slide generation and refinement process.
    
    Args:
        outline: The slide deck outline
        theme: The slide theme to use
        
    Returns:
        Tuple of (html_content, quality_report)
    """
    agent = MonitoringAgent()
    return agent.coordinate_slides_and_refiner(outline, theme)