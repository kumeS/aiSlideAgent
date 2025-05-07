"""
Outline Agent

Converts research summaries into structured slide outlines.
"""

import os
import yaml
from typing import Dict, List, Any, Optional, Union
import logging
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json

from agents import client, DEFAULT_MODEL
from agents.research import ResearchResult, SearchResult

# Configure logging - ロギング設定は agents/__init__.py に集約
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SlideContent(BaseModel):
    """Model representing the content of a single slide.

    Flow2 で提案されたトレーサビリティ向上のため、各スライドが参照した検索結果インデックスを `sources` として保持する。"""

    title: str
    content: List[str] = Field(default_factory=list)
    image_suggestion: Optional[str] = None
    notes: Optional[str] = None
    type: str = "content"  # Options: title, content, image, quote, etc.
    sources: Optional[List[str]] = Field(default=None, description="ResearchAgentの結果インデックス (例: ['primary[0]', 'secondary[2]'])")

class SlideDeck(BaseModel):
    """Model representing a complete slide deck outline."""
    topic: str
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    slides: List[SlideContent] = Field(default_factory=list)
    
    def to_yaml(self) -> str:
        """Convert the slide deck to YAML format."""
        return yaml.dump(self.dict(), sort_keys=False, default_flow_style=False)
    
    def to_markdown(self) -> str:
        """Convert the slide deck to Markdown format for easy viewing."""
        md = f"# {self.title}\n\n"
        if self.subtitle:
            md += f"## {self.subtitle}\n\n"
        if self.author:
            md += f"*By: {self.author}*\n\n"
        
        md += "---\n\n"
        
        for i, slide in enumerate(self.slides):
            md += f"### Slide {i+1}: {slide.title}\n\n"
            
            if slide.type == "title":
                md += "*Title Slide*\n\n"
            else:
                md += "*Content Slide*\n\n"
            
            if slide.content:
                for point in slide.content:
                    md += f"- {point}\n"
                md += "\n"
            
            if slide.image_suggestion:
                md += f"*Image Suggestion: {slide.image_suggestion}*\n\n"
            
            if slide.notes:
                md += f"*Notes: {slide.notes}*\n\n"
            
            md += "---\n\n"
        
        return md

class OutlineAgent:
    """Agent for generating slide outlines from research summaries."""
    
    def __init__(self, model: Optional[str] = None):
        """Initialize the outline agent with configuration."""
        self.model = model or DEFAULT_MODEL
    
    def generate_outline(self, research, slide_count=5, topic=None) -> SlideDeck:
        """
        Generate a presentation outline based on research results.
        
        Args:
            research: Research results to base the outline on
            slide_count: Number of slides to generate
            topic: Optional topic name to override research topic
            
        Returns:
            A SlideDeck object containing the outline
        """
        logger.info(f"Generating outline for slides: {slide_count}")
        
        # Extract topic from research results if not provided
        if not topic and isinstance(research, ResearchResult):
            topic = research.topic
        elif not topic:
            # Ensure we have a topic
            topic = "Presentation Topic"
        
        # Use the new slide content generation function
        slide_content = generate_slide_content(research, topic, slide_count)
        
        # Ensure slide_content is properly structured
        if not isinstance(slide_content, dict):
            logger.error(f"Invalid slide content format: {type(slide_content)}")
            # Create a fallback slide deck
            return SlideDeck(
                topic=topic,
                title=topic,
                subtitle="Generated Presentation",
                author="AI Slide Generator",
                slides=[
                    SlideContent(
                        title="Introduction to " + topic,
                        content=["Slide generation encountered an error", "Please try regenerating the outline"],
                        type="title"
                    )
                ]
            )
        
        # Ensure we have a valid title
        title = slide_content.get("title")
        if not title:
            title = topic

        # Convert the slide content to a SlideDeck object
        return SlideDeck(
            topic=topic,
            title=title,
            subtitle=slide_content.get("subtitle"),
            author="AI Slide Generator",
            slides=[SlideContent(**slide) for slide in slide_content.get("slides", [])]
        )
    
    def _expand_slide_deck(self, slide_deck: SlideDeck, additional_count: int, research: ResearchResult) -> None:
        """Add additional slides to a slide deck that has fewer than requested."""
        # Extract the key topics that could be expanded
        topics = []
        for slide in slide_deck.slides:
            if slide.type != "title" and "conclusion" not in slide.title.lower():
                topics.append(slide.title)
        
        # Also consider knowledge gaps
        if research.knowledge_gaps:
            topics.extend(research.knowledge_gaps)
        
        # Generate prompts for additional slides
        for i in range(additional_count):
            if i < len(topics):
                # Expand an existing topic
                topic = topics[i]
                slide = self._generate_additional_slide(topic, research.topic)
                # Insert before the conclusion slide if it exists
                for j, existing_slide in enumerate(slide_deck.slides):
                    if "conclusion" in existing_slide.title.lower() or "summary" in existing_slide.title.lower():
                        slide_deck.slides.insert(j, slide)
                        break
                else:
                    # No conclusion slide found, append to end
                    slide_deck.slides.append(slide)
            else:
                # Create a slide on a general aspect
                slide = self._generate_additional_slide(f"Additional Aspect of {research.topic}", research.topic)
                # Add before the conclusion
                slide_deck.slides.append(slide)
    
    def _generate_additional_slide(self, topic: str, main_topic: str) -> SlideContent:
        """Generate content for an additional slide on a specific topic."""
        try:
            prompt = f"""
            Create content for a new slide about "{topic}" for a presentation on "{main_topic}".
            Include:
            1. A clear, concise title
            2. 3-4 bullet points of key information
            3. An image suggestion
            
            Format as JSON:
            {{
                "title": "Slide Title",
                "content": ["Point 1", "Point 2", "Point 3"],
                "image_suggestion": "Description of ideal image"
            }}
            """
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": topic}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            slide_text = response.choices[0].message.content.strip()
            
            # Extract JSON if it's wrapped in ```json blocks
            if "```json" in slide_text:
                slide_text = slide_text.split("```json", 1)[1]
            if "```" in slide_text:
                slide_text = slide_text.split("```", 1)[0]
            
            slide_data = json.loads(slide_text)
            return SlideContent(
                title=slide_data.get("title", topic),
                content=slide_data.get("content", ["Content being developed"]),
                image_suggestion=slide_data.get("image_suggestion", f"Image related to {topic}"),
                type="content"
            )
            
        except Exception as e:
            logger.error(f"Error generating additional slide: {str(e)}")
            # Fallback slide
            return SlideContent(
                title=topic,
                content=["Key information about this topic", "Additional details to be added"],
                image_suggestion=f"Image related to {topic}",
                type="content"
            )
    
    def _create_fallback_outline(self, research: ResearchResult, slide_count: int) -> SlideDeck:
        """Create a basic outline when the main generation process fails."""
        logger.info("Creating fallback outline")
        
        # Create a minimal slide deck
        slides = []
        
        # Title slide
        slides.append(SlideContent(
            title=research.topic,
            type="title",
            content=["A comprehensive overview"]
        ))
        
        # Introduction
        slides.append(SlideContent(
            title="Introduction",
            type="content",
            content=["Overview of " + research.topic, "Key concepts and importance"]
        ))
        
        # Add slides based on knowledge gaps or primary results
        content_slide_count = slide_count - 3  # Subtract title, intro, and conclusion
        
        if research.knowledge_gaps and len(research.knowledge_gaps) > 0:
            # Use knowledge gaps for slide topics
            for i, gap in enumerate(research.knowledge_gaps[:content_slide_count]):
                slides.append(SlideContent(
                    title=gap,
                    type="content",
                    content=["Key information about this aspect", "Additional details to be developed"],
                    image_suggestion=f"Image related to {gap}"
                ))
        else:
            # Use primary results for slide topics
            for i in range(content_slide_count):
                if i < len(research.primary_results):
                    result = research.primary_results[i]
                    slides.append(SlideContent(
                        title=result.title[:50] + "..." if len(result.title) > 50 else result.title,
                        type="content",
                        content=[result.snippet[:100] + "..." if len(result.snippet) > 100 else result.snippet],
                        image_suggestion=f"Image related to {result.title}"
                    ))
                else:
                    # Generic slides if we don't have enough primary results
                    slides.append(SlideContent(
                        title=f"Aspect {i+1} of {research.topic}",
                        type="content",
                        content=["Information to be developed"]
                    ))
        
        # Conclusion slide
        slides.append(SlideContent(
            title="Conclusion",
            type="content",
            content=["Summary of key points", "Future considerations"]
        ))
        
        # Ensure we have exactly the requested number of slides
        while len(slides) < slide_count:
            slides.insert(-1, SlideContent(
                title=f"Additional Aspect of {research.topic}",
                type="content",
                content=["Information to be developed"]
            ))
        
        # Trim if we have too many slides
        if len(slides) > slide_count:
            slides = slides[:slide_count-1] + [slides[-1]]  # Keep the conclusion
        
        return SlideDeck(
            topic=research.topic,
            title=f"{research.topic}: A Comprehensive Overview",
            subtitle="Generated Presentation",
            author="AI Slide Generator",
            slides=slides
        )

# Convenience function for direct module use
def generate_outline(research_result: Union[ResearchResult, Dict, str], slide_count: int = 10, topic: str = None) -> SlideDeck:
    """
    Generate a slide outline from research results using the OutlineAgent.
    
    Args:
        research_result: The research result to use for generating the outline.
            Can be a ResearchResult object, a dictionary, or a string summary.
        slide_count: The number of slides to generate
        topic: Optional topic override if research_result doesn't contain it
        
    Returns:
        A SlideDeck object containing the complete outline
    """
    agent = OutlineAgent()
    
    # Handle different input types
    if isinstance(research_result, str):
        # If a string is provided, create a minimal ResearchResult
        if not topic:
            # Extract a topic if none provided
            topic = "Presentation Topic"
            try:
                # Try to extract a title from the first line if it looks like a heading
                first_line = research_result.strip().split('\n')[0]
                if first_line.startswith('#'):
                    topic = first_line.lstrip('#').strip()
                elif len(first_line) < 100:  # Short first line might be a title
                    topic = first_line
            except:
                pass
        
        research_obj = ResearchResult(
            topic=topic,
            summary=research_result
        )
        return agent.generate_outline(research_obj, slide_count)
    
    elif isinstance(research_result, dict):
        # Convert dictionary to ResearchResult
        try:
            # If it has the expected fields, create a ResearchResult
            if 'topic' in research_result:
                research_obj = ResearchResult(
                    topic=research_result.get('topic', topic or "Presentation Topic"),
                    summary=research_result.get('summary', ''),
                    primary_results=[SearchResult(**r) if isinstance(r, dict) else r 
                                    for r in research_result.get('primary_results', [])],
                    secondary_results=[SearchResult(**r) if isinstance(r, dict) else r 
                                      for r in research_result.get('secondary_results', [])],
                    knowledge_gaps=research_result.get('knowledge_gaps', [])
                )
            else:
                # Create a minimal ResearchResult with the dictionary as the summary
                research_obj = ResearchResult(
                    topic=topic or "Presentation Topic",
                    summary=json.dumps(research_result)
                )
            
            return agent.generate_outline(research_obj, slide_count)
            
        except Exception as e:
            logger.error(f"Error converting dictionary to ResearchResult: {str(e)}")
            # Create a minimal ResearchResult
            research_obj = ResearchResult(
                topic=topic or "Presentation Topic",
                summary=json.dumps(research_result)
            )
            return agent.generate_outline(research_obj, slide_count)
    
    elif isinstance(research_result, ResearchResult):
        # Use the ResearchResult directly
        return agent.generate_outline(research_result, slide_count)
    
    else:
        # Handle unexpected input type
        logger.error(f"Unexpected input type for generate_outline: {type(research_result)}")
        # Create a minimal ResearchResult
        research_obj = ResearchResult(
            topic=topic or "Presentation Topic",
            summary=str(research_result)
        )
        return agent.generate_outline(research_obj, slide_count)

def generate_slide_content(data, topic=None, slide_count=5) -> SlideContent:
    """Generate slide content from research results"""
    logger.info(f"Generating slide content for topic: {topic}")
    
    # Format research data for the prompt
    research_data = ""
    research_sources = {}  # データソースと参照インデックスのマッピング
    
    if isinstance(data, ResearchResult):
        # Use summary if available, otherwise use snippets from results
        if data.summary and len(data.summary) > 100:
            research_data = data.summary
        
        # トレーサビリティ向上のためのソース情報を追加
        source_info = []
        
        # プライマリソース情報の追加
        for i, result in enumerate(data.primary_results):
            source_id = f"primary[{i}]"
            research_sources[source_id] = {
                "title": result.title,
                "snippet": result.snippet[:150] + "..." if len(result.snippet) > 150 else result.snippet,
                "url": result.url,
                "credibility": result.credibility_score
            }
            source_info.append(f"Source {source_id}: {result.title} - {result.snippet[:150]}...")
            
        # セカンダリソース情報の追加
        for i, result in enumerate(data.secondary_results):
            source_id = f"secondary[{i}]"
            research_sources[source_id] = {
                "title": result.title,
                "snippet": result.snippet[:150] + "..." if len(result.snippet) > 150 else result.snippet,
                "url": result.url,
                "credibility": result.credibility_score
            }
            source_info.append(f"Source {source_id}: {result.title} - {result.snippet[:150]}...")
            
        # リサーチデータと情報ソースを統合
        if source_info:
            research_data += "\n\nAvailable Sources:\n" + "\n".join(source_info)
    elif isinstance(data, dict):
        # Handle dictionary input
        research_data = json.dumps(data)
    elif isinstance(data, str):
        # Handle string input
        research_data = data
    else:
        # Fallback for any other type - convert to string
        research_data = str(data)
    
    prompt = f"""
    Create a structured presentation outline on "{topic}" with exactly {slide_count} slides.
    
    Research information:
    {research_data[:4000]}
    
    The presentation should include:
    - An introductory slide with a clear title
    - Content slides covering key aspects
    - A concluding slide
    
    For each slide, provide:
    1. A clear title (max 1 line)
    2. Optional subtitle (max 1 line)
    3. Content as a list of bullet points (3-5 bullet points per slide)
    4. A relevant image description/suggestion
    5. IMPORTANT: For each slide, include "sources" with a list of source IDs (like "primary[0]", "secondary[1]")
       that the slide's content is based on. This is crucial for traceability.
    
    Your response MUST be in this exact YAML format:
    ```yaml
    title: "Main Presentation Title"
    slides:
      - title: "Slide 1 Title"
        subtitle: "Optional Subtitle" # Optional
        type: "title" # Can be "title", "content", "image", "list", "conclusion"
        content:
          - "Bullet point 1"
          - "Bullet point 2"
          - "Bullet point 3"
        image_suggestion: "Description of image that would fit this slide"
        sources:  # List the sources this slide content is based on
          - "primary[0]"
          - "secondary[2]"
      - title: "Slide 2 Title"
        type: "content"
        content:
          - "Content bullet point 1"
          - "Content bullet point 2"
          - "Content bullet point 3"
        image_suggestion: "Description of image that would fit this slide"
        sources:
          - "primary[1]"
    ```
    
    IMPORTANT: Each bullet point MUST be a simple string, not a nested structure. 
    Do NOT use dictionaries/mappings within the content list - only plain strings 
    are accepted. The content must be exactly {slide_count} slides, no more or less.
    Note that the 'title' field at the top level is REQUIRED and should be the main presentation title.
    CRITICAL: EVERY slide MUST have the 'sources' list indicating which source(s) the content is derived from.
    Use "primary[0]", "primary[1]", etc. for primary source references and "secondary[0]", etc. for secondary sources.
    """
    
    try:
        # Make API request
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert presentation designer who creates well-structured slide outlines. Follow instructions exactly and output valid YAML."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.4
        )
        
        slide_content = response.choices[0].message.content
        logger.debug(f"Generated slide content: {slide_content[:500]}...")
        
        # Extract YAML content
        if "```yaml" in slide_content:
            yaml_content = slide_content.split("```yaml")[1].split("```")[0].strip()
        elif "```" in slide_content:
            yaml_content = slide_content.split("```")[1].strip()
        else:
            yaml_content = slide_content
        
        # Parse YAML and create a SlideContent object
        try:
            # Logging the raw YAML before parsing
            logger.debug(f"Parsing YAML: {yaml_content[:500]}...")
            
            # Parse into Python dict using PyYAML
            import yaml
            slide_data = yaml.safe_load(yaml_content)
            
            # Process dictionary to ensure consistent structure
            processed_data = {"slides": [], "title": ""}
            
            # Extract main title if available
            if "title" in slide_data:
                processed_data["title"] = slide_data["title"]
            elif topic:
                # Use topic as title if not provided in YAML
                processed_data["title"] = f"{topic}"
            else:
                processed_data["title"] = "Presentation"
            
            if "slides" in slide_data and isinstance(slide_data["slides"], list):
                for slide in slide_data["slides"]:
                    if not isinstance(slide, dict):
                        continue
                        
                    processed_slide = {
                        "title": slide.get("title", ""),
                        "subtitle": slide.get("subtitle", ""),
                        "type": slide.get("type", "content"),
                        "content": [],
                        "image_suggestion": slide.get("image_suggestion", ""),
                        "sources": slide.get("sources", None)
                    }
                    
                    # Process content to ensure it's a list of strings
                    content = slide.get("content", [])
                    if isinstance(content, list):
                        for item in content:
                            # Convert any non-string items to strings
                            if isinstance(item, dict):
                                # If it's a dictionary, convert it to a string representation
                                for key, value in item.items():
                                    processed_slide["content"].append(f"{key}: {value}")
                            else:
                                processed_slide["content"].append(str(item))
                    
                    processed_data["slides"].append(processed_slide)
            
            logger.info(f"Successfully parsed slide content with {len(processed_data['slides'])} slides")
            return processed_data
        except Exception as parsing_error:
            logger.error(f"Error parsing outline YAML: {parsing_error}")
            
            # Create a fallback outline
            fallback_slides = []
            default_titles = [
                "Introduction",
                "Key Concepts",
                "Applications",
                "Best Practices",
                "Conclusion"
            ]
            
            # Create title slide
            fallback_slides.append({
                "title": topic or "Presentation",
                "subtitle": "",
                "type": "title",
                "content": ["A comprehensive overview"],
                "image_suggestion": "A professional image related to the topic",
                "sources": None
            })
            
            # Add content slides
            for i in range(1, slide_count):
                idx = min(i, len(default_titles)-1)
                title = default_titles[idx]
                
                if i == 1:
                    content = [
                        f"Overview of {topic or 'the subject'}",
                        "Key concepts and importance"
                    ]
                elif i == slide_count - 1:  # Last slide
                    content = [
                        "Summary of key points",
                        "Future considerations" 
                    ]
                else:
                    # Generate content based on research if available
                    if isinstance(data, ResearchResult) and data.primary_results:
                        result = data.primary_results[min(i-1, len(data.primary_results)-1)]
                        content = [result.snippet[:100] + "..."]
                    else:
                        content = [
                            f"Detailed information about {topic or 'the subject'}, including definitions, examples, and best practices. Learn about the key concepts and applications of {topic or 'the subject'}."
                        ]
                
                fallback_slides.append({
                    "title": title,
                    "subtitle": "",
                    "type": "content",
                    "content": content,
                    "image_suggestion": f"An image illustrating {title.lower()}",
                    "sources": None
                })
            
            logger.info("Creating fallback outline")
            return {"slides": fallback_slides}
    
    except Exception as e:
        logger.error(f"Error generating slide content: {e}")
        
        # Create an emergency fallback
        emergency_slides = []
        
        # Title slide
        emergency_slides.append({
            "title": topic or "Presentation",
            "subtitle": "",
            "type": "title",
            "content": ["Overview"],
            "image_suggestion": "",
            "sources": None
        })
        
        # Add minimal content slides
        for i in range(1, slide_count):
            emergency_slides.append({
                "title": f"Slide {i+1}",
                "subtitle": "",
                "type": "content",
                "content": ["Content unavailable"],
                "image_suggestion": "",
                "sources": None
            })
        
        return {"slides": emergency_slides} 