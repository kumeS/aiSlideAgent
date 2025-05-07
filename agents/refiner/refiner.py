"""
RefinerAgent Implementation

This module provides quality assurance and refinement for generated slides,
ensuring WCAG 2.1 AA compliance, proofreading, and overall quality checks.
"""

import logging
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Any

# Use absolute imports
from agents import client, DEFAULT_MODEL

# Import from modules
from .wcag import check_wcag_compliance, check_color_contrast, check_heading_structure, check_keyboard_accessibility
from .content import (
    proofread_text, check_image_accessibility, citation_coverage, 
    check_content_richness, is_japanese_text, use_gpt_proofreading
)

logger = logging.getLogger(__name__)

class RefinerAgent:
    """
    RefinerAgent is responsible for:
    1. Checking WCAG 2.1 AA compliance 
    2. Proofreading text content
    3. Validating image accessibility
    4. Ensuring consistent styling and quality
    """
    
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        
    def refine_html(self, html_content: str, text_density: str = "balanced") -> Tuple[str, List[Dict]]:
        """
        Refine the HTML content of the presentation.
        
        Args:
            html_content: The HTML content to refine
            text_density: Expected text density for content richness check
            
        Returns:
            Tuple containing refined HTML and list of issues found/fixed
        """
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        issues = []
        
        # Check and fix accessibility issues
        wcag_issues = check_wcag_compliance(soup)
        issues.extend(wcag_issues)
        
        # Check and fix text content
        text_issues = proofread_text(soup)
        issues.extend(text_issues)
        
        # Check and fix image accessibility
        image_issues = check_image_accessibility(soup)
        issues.extend(image_issues)
        
        # Check content richness
        content_richness_score, richness_issues = check_content_richness(str(soup), text_density)
        issues.extend(richness_issues)
        
        # Return the refined HTML
        return str(soup), issues
    
    def citation_coverage(self, html_content: str) -> float:
        """
        Calculate the citation coverage for the content.
        
        Args:
            html_content: HTML string to analyze
            
        Returns:
            Citation coverage score (0-1)
        """
        return citation_coverage(html_content)
        
def refine_presentation(html_content: str, text_density: str = "balanced") -> Tuple[str, Dict]:
    """
    Public API: Refine a presentation for quality and accessibility.
    
    Args:
        html_content: HTML content of the presentation
        text_density: Expected text density
        
    Returns:
        Tuple containing refined HTML and a summary of issues/fixes
    """
    logger.info("🔍 Starting presentation refinement")
    
    # Create refiner agent
    agent = RefinerAgent()
    
    # Refine the HTML
    refined_html, issues = agent.refine_html(html_content, text_density)
    
    # Calculate overall quality metrics
    citation_score = agent.citation_coverage(refined_html)
    
    # Count issues by category
    issue_count = {}
    fixed_count = {}
    
    for issue in issues:
        category = issue.get('type', 'other')
        issue_count[category] = issue_count.get(category, 0) + 1
        
        if issue.get('action', '').startswith('fixed') or issue.get('action', '').startswith('added'):
            fixed_count[category] = fixed_count.get(category, 0) + 1
    
    # Create summary
    summary = {
        'total_issues': len(issues),
        'fixed_issues': sum(fixed_count.values()),
        'issue_breakdown': issue_count,
        'fixed_breakdown': fixed_count,
        'citation_score': citation_score
    }
    
    logger.info(f"✅ Refinement complete: {summary['fixed_issues']}/{summary['total_issues']} issues fixed")
    
    return refined_html, summary 