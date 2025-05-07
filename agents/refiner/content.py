"""
Content Quality Checking

This module provides functionality for proofreading and content quality assessment.
"""

import re
import logging
import math
from typing import Dict, List, Tuple, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse

from agents import client

# Configure logging
logger = logging.getLogger(__name__)

def proofread_text(soup: BeautifulSoup) -> List[Dict]:
    """
    Proofread text content in the HTML.
    
    Args:
        soup: BeautifulSoup object representing the HTML
        
    Returns:
        List of issues found and fixed
    """
    issues = []
    
    # Get all text-containing elements
    text_elements = []
    
    # Heading elements
    headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    text_elements.extend(headings)
    
    # Paragraph elements
    paragraphs = soup.find_all('p')
    text_elements.extend(paragraphs)
    
    # List items
    list_items = soup.find_all('li')
    text_elements.extend(list_items)
    
    # Other text-containing elements
    other_text = soup.find_all(['div', 'span', 'blockquote', 'figcaption'])
    for element in other_text:
        # Only include if it has direct text content (not just child elements with text)
        if element.string and element.string.strip():
            text_elements.append(element)
    
    # Proofread each element with significant text
    for element in text_elements:
        text = element.get_text().strip()
        
        # Only proofread if there's enough text to warrant it
        if len(text) > 10:
            # Check if the text is primarily Japanese
            is_japanese = is_japanese_text(text)
            
            # Perform proofreading with OpenAI API
            try:
                corrected_text = use_gpt_proofreading(text, is_japanese)
                
                # If text was corrected, update the element
                if corrected_text and corrected_text != text:
                    # Replace the text while preserving child elements (like spans, links, etc.)
                    # This is complex - just update the direct text nodes
                    for child in element.contents:
                        if isinstance(child, str) and child.strip():
                            # Only replace text nodes with non-whitespace
                            element.contents[element.contents.index(child)] = corrected_text
                            issues.append({
                                'type': 'proofread',
                                'element': element.name,
                                'original': text,
                                'corrected': corrected_text,
                                'action': 'text_corrected'
                            })
                            break
                    
                    # If no text nodes were replaced, it might be the element itself
                    if not any(issue for issue in issues if issue['original'] == text):
                        element.string = corrected_text
                        issues.append({
                            'type': 'proofread',
                            'element': element.name,
                            'original': text,
                            'corrected': corrected_text,
                            'action': 'text_corrected'
                        })
            except Exception as e:
                logger.error(f"Proofreading error: {e}")
    
    return issues

def is_japanese_text(text: str) -> bool:
    """
    Determine if the text is primarily Japanese.
    
    Args:
        text: Text to analyze
        
    Returns:
        True if the text is primarily Japanese
    """
    # Check for Japanese characters: Hiragana, Katakana, or Kanji
    hiragana_pattern = re.compile(r'[\u3040-\u309F]')
    katakana_pattern = re.compile(r'[\u30A0-\u30FF]')
    kanji_pattern = re.compile(r'[\u4E00-\u9FFF]')
    
    # Count characters in each script
    jp_chars = len(hiragana_pattern.findall(text)) + len(katakana_pattern.findall(text)) + len(kanji_pattern.findall(text))
    
    # If more than 20% of characters are Japanese, consider it Japanese text
    return jp_chars > len(text) * 0.2

def use_gpt_proofreading(text: str, is_japanese: bool = False) -> str:
    """
    Use GPT to proofread and correct text.
    
    Args:
        text: Text to proofread
        is_japanese: Whether the text is primarily in Japanese
        
    Returns:
        Corrected text
    """
    try:
        # Adjust the system prompt based on language
        if is_japanese:
            system_prompt = """
            あなたは日本語の校正者です。以下のテキストを校正してください。
            - 誤字脱字を修正
            - 文法ミスを修正
            - 句読点の使用を確認
            - 表現を自然な日本語に
            修正したテキストのみを返してください。大きな変更は避け、意味を保持してください。
            """
        else:
            system_prompt = """
            You are a professional proofreader. Correct the following text:
            - Fix spelling errors
            - Fix grammar mistakes
            - Check punctuation usage
            - Make expressions natural
            Only return the corrected text, without explanations. Avoid major changes and preserve meaning.
            """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a cheaper model for proofreading
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            max_tokens=max(len(text) * 2, 100),  # Ensure enough tokens for response
            temperature=0.2  # Low temperature for more conservative corrections
        )
        
        corrected_text = response.choices[0].message.content.strip()
        return corrected_text if corrected_text else text
    
    except Exception as e:
        logger.error(f"GPT proofreading error: {e}")
        return text  # Return original text if proofreading fails
    
def check_image_accessibility(soup: BeautifulSoup) -> List[Dict]:
    """
    Check image accessibility and fix issues.
    
    Args:
        soup: BeautifulSoup object representing the HTML
        
    Returns:
        List of image accessibility issues found and fixed
    """
    issues = []
    
    # Check all image elements
    images = soup.find_all('img')
    for img in images:
        # Check for alt text
        if not img.has_attr('alt') or not img['alt']:
            # Generate alt text based on context
            alt_text = generate_alt_text(img)
            img['alt'] = alt_text
            
            issues.append({
                'type': 'image_accessibility',
                'issue': 'missing_alt',
                'element': 'img',
                'action': f'added alt text: "{alt_text}"'
            })
        
        # Check for ARIA labels when needed
        if img.has_attr('role') and img['role'] == 'button' and not img.has_attr('aria-label'):
            # If it's a button, ensure it has an ARIA label
            aria_label = img['alt'] if img.has_attr('alt') else f"Image button {len(issues)}"
            img['aria-label'] = aria_label
            
            issues.append({
                'type': 'image_accessibility',
                'issue': 'missing_aria_label',
                'element': 'img',
                'action': f'added aria-label: "{aria_label}"'
            })
    
    # Check for image maps
    image_maps = soup.find_all('map')
    for map_element in image_maps:
        # Check areas for alt text
        areas = map_element.find_all('area')
        for area in areas:
            if not area.has_attr('alt') or not area['alt']:
                # Generate basic alt text based on href
                if area.has_attr('href'):
                    parsed_url = urlparse(area['href'])
                    path = parsed_url.path
                    alt_text = path.split('/')[-1].replace('-', ' ').replace('_', ' ')
                else:
                    alt_text = f"Image map area {len(issues)}"
                
                area['alt'] = alt_text
                
                issues.append({
                    'type': 'image_accessibility',
                    'issue': 'missing_map_alt',
                    'element': 'area',
                    'action': f'added alt text: "{alt_text}"'
                })
    
    # Check for SVGs without accessible text
    svgs = soup.find_all('svg')
    for svg in svgs:
        # Check if SVG has title or desc
        has_title = svg.find('title') is not None
        has_desc = svg.find('desc') is not None
        
        if not has_title and not has_desc:
            # Add title based on context
            title_text = "SVG graphic"
            if svg.parent and svg.parent.name in ['button', 'a']:
                # Try to infer purpose from parent
                if svg.parent.string:
                    title_text = svg.parent.string.strip()
                elif svg.parent.has_attr('aria-label'):
                    title_text = svg.parent['aria-label']
            
            # Create and insert a title element
            title = soup.new_tag('title')
            title.string = title_text
            svg.insert(0, title)
            
            # Add role="img" and aria-labelledby
            svg['role'] = 'img'
            svg['aria-labelledby'] = 'svg-title'
            title['id'] = 'svg-title'
            
            issues.append({
                'type': 'image_accessibility',
                'issue': 'svg_missing_title',
                'element': 'svg',
                'action': f'added title: "{title_text}"'
            })
    
    return issues

def generate_alt_text(image_tag) -> str:
    """
    Generate alternative text for an image based on context.
    
    Args:
        image_tag: The image element
        
    Returns:
        Generated alt text
    """
    # Try to infer alt text from various sources
    
    # 1. Check for image filename
    if image_tag.has_attr('src'):
        src = image_tag['src']
        filename = src.split('/')[-1].split('?')[0]  # Get last part of path, remove query params
        if filename and filename not in ['image.jpg', 'img.png', 'picture.jpg']:
            # Clean up filename
            alt_text = (filename
                .replace('.jpg', '')
                .replace('.png', '')
                .replace('.gif', '')
                .replace('-', ' ')
                .replace('_', ' ')
                .title()  # Capitalize first letter of each word
            )
            return alt_text
    
    # 2. Check for nearby text (captions, figcaptions)
    parent = image_tag.parent
    
    # Check if in figure with figcaption
    if parent.name == 'figure':
        figcaption = parent.find('figcaption')
        if figcaption and figcaption.string:
            return figcaption.string.strip()
    
    # 3. Check for title attribute
    if image_tag.has_attr('title'):
        return image_tag['title']
    
    # 4. Check for aria-label
    if image_tag.has_attr('aria-label'):
        return image_tag['aria-label']
    
    # 5. Look at parent or sibling headings
    heading = parent.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    if heading and heading.string:
        return f"Image related to {heading.string.strip()}"
    
    # 6. Provide a generic but contextual description
    if parent.name == 'a' and parent.has_attr('href'):
        return "Clickable image link"
    elif parent.name == 'button':
        return "Button image"
    
    # 7. Fallback to a generic description
    return "Presentation image"

def citation_coverage(html_content: str) -> float:
    """
    Calculate the citation coverage for the content.
    
    Args:
        html_content: HTML string to analyze
        
    Returns:
        Citation coverage score (0-1)
    """
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract citations and content
    citations = soup.find_all(['cite', 'blockquote', 'a[href]'])
    content = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
    
    if not content:
        return 0.0  # No content to cite
    
    # Calculate raw citation density
    raw_score = len(citations) / len(content)
    
    # Normalize to 0-1 range (assuming 0.5 citations per content element is optimal)
    normalized_score = min(1.0, raw_score / 0.5)
    
    return normalized_score

def check_content_richness(html_content: str, text_density: str = "balanced") -> Tuple[float, List[Dict]]:
    """
    Analyze content richness and identify areas for improvement.
    
    Args:
        html_content: HTML string to analyze
        text_density: Expected text density
        
    Returns:
        Tuple of (richness score, list of issues)
    """
    issues = []
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Content elements to analyze
    content_elements = soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote'])
    
    if not content_elements:
        issues.append({
            'type': 'content_richness',
            'issue': 'no_content',
            'severity': 'high',
            'suggestion': 'Add meaningful content to the slide.'
        })
        return 0.0, issues
    
    # Metrics to analyze
    total_word_count = 0
    total_sentences = 0
    total_paragraphs = len(soup.find_all('p'))
    total_bullets = len(soup.find_all('li'))
    total_headings = len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
    
    # Process text in all elements
    all_text = ""
    for element in content_elements:
        text = element.get_text().strip()
        all_text += text + " "
        
        if text:
            # Count words
            words = re.findall(r'\b\w+\b', text)
            total_word_count += len(words)
            
            # Count sentences
            sentences = re.split(r'[.!?。]+', text)
            total_sentences += len([s for s in sentences if s.strip()])
    
    # Adjust expected density based on setting
    if text_density == "minimal":
        min_words = 20
        optimal_words = 50
        max_words = 100
    elif text_density == "detailed":
        min_words = 100
        optimal_words = 200
        max_words = 400
    else:  # balanced
        min_words = 50
        optimal_words = 120
        max_words = 250
    
    # Check overall word count
    if total_word_count < min_words:
        issues.append({
            'type': 'content_richness',
            'issue': 'low_word_count',
            'severity': 'medium',
            'details': f'Content has only {total_word_count} words (minimum recommended: {min_words}).',
            'suggestion': 'Add more detailed information to enhance the content.'
        })
    elif total_word_count > max_words:
        issues.append({
            'type': 'content_richness',
            'issue': 'excessive_word_count',
            'severity': 'low',
            'details': f'Content has {total_word_count} words (maximum recommended: {max_words}).',
            'suggestion': 'Consider splitting into multiple slides or simplifying to avoid overwhelming the audience.'
        })
    
    # Check content structure
    if total_paragraphs == 0 and total_bullets == 0:
        issues.append({
            'type': 'content_richness',
            'issue': 'poor_structure',
            'severity': 'medium',
            'suggestion': 'Use paragraphs or bullet points to structure the content.'
        })
    
    # Check content specificity
    specificity_score = evaluate_content_specificity(all_text)
    if specificity_score < 0.3:
        issues.append({
            'type': 'content_richness',
            'issue': 'general_content',
            'severity': 'medium',
            'suggestion': 'Include more specific examples, data, or detailed explanations.'
        })
    
    # Calculate overall richness score (0-1)
    # Consider: word count, sentence quality, structure, specificity
    word_count_score = min(1.0, total_word_count / optimal_words) if total_word_count <= optimal_words else 1.0 - min(1.0, (total_word_count - optimal_words) / (max_words - optimal_words) * 0.5)
    
    # Structure score based on presence of headings, paragraphs, and bullets
    structure_elements = total_paragraphs + total_bullets + total_headings
    structure_score = min(1.0, structure_elements / 5.0)  # Assume 5 structural elements is optimal
    
    # Combine scores with different weights
    richness_score = (
        0.4 * word_count_score +
        0.3 * structure_score +
        0.3 * specificity_score
    )
    
    # Clamp to 0-1 range
    richness_score = max(0.0, min(1.0, richness_score))
    
    # Add measurement info to issues for reporting
    issues.append({
        'type': 'content_richness',
        'issue': 'measurement',
        'severity': 'info',
        'details': {
            'word_count': total_word_count,
            'paragraphs': total_paragraphs,
            'bullets': total_bullets,
            'headings': total_headings,
            'richness_score': richness_score
        }
    })
    
    return richness_score, issues

def evaluate_content_specificity(text: str) -> float:
    """
    Evaluate how specific vs. general the content is.
    
    Args:
        text: Text content to evaluate
        
    Returns:
        Specificity score (0-1)
    """
    # Check for specific indicators
    has_numbers = bool(re.search(r'\d+(\.\d+)?', text))
    has_dates = bool(re.search(r'\b(19|20)\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b', text))
    has_proper_nouns = bool(re.search(r'\b[A-Z][a-z]+\b', text))
    has_technical_terms = bool(re.search(r'\b[A-Za-z]+(ization|ology|istics|ification|ibility)\b', text))
    
    # Look for specific quantity words
    quantity_words = ['percent', '%', 'ratio', 'rate', 'average', 'median', 'kg', 'mb', 'gb', 'TB']
    has_quantities = any(word in text.lower() for word in quantity_words)
    
    # Look for specific reference indicators
    reference_words = ['according to', 'research shows', 'study', 'demonstrated', 'evidence', 'found that']
    has_references = any(phrase in text.lower() for phrase in reference_words)
    
    # Count the number of specific indicators present
    specificity_indicators = [has_numbers, has_dates, has_proper_nouns, 
                             has_technical_terms, has_quantities, has_references]
    
    specificity_count = sum(1 for indicator in specificity_indicators if indicator)
    
    # Calculate score based on number of indicators
    # More indicators = higher score
    specificity_score = min(1.0, specificity_count / 4.0)  # 4 indicators for full score
    
    return specificity_score 