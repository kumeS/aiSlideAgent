"""
Refiner Agent Module

Provides quality assurance and refinement for generated slides,
ensuring WCAG 2.1 AA compliance, proofreading, and content quality.
"""

from .refiner import RefinerAgent, refine_presentation
from .wcag import (
    check_wcag_compliance, check_color_contrast, 
    check_heading_structure, check_keyboard_accessibility
)
from .content import (
    proofread_text, check_image_accessibility, citation_coverage,
    check_content_richness, is_japanese_text
)

import logging

# Setup logging
logger = logging.getLogger(__name__)

__all__ = [
    # Main classes
    "RefinerAgent",
    
    # Public API functions
    "refine_presentation",
    
    # WCAG accessibility functions
    "check_wcag_compliance",
    "check_color_contrast",
    "check_heading_structure",
    "check_keyboard_accessibility",
    
    # Content quality functions
    "proofread_text",
    "check_image_accessibility",
    "citation_coverage",
    "check_content_richness"
] 