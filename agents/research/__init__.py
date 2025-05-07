"""
Research Agent Module

This module provides functionality for deep web research on topics
using multi-layer search and source credibility validation.
"""

# Import main classes and functions for public API
from .models import SearchResult, ResearchResult
from .search_engine import ResearchAgent
from .api import search_deep, search_basic

# Public API surface
__all__ = ["ResearchAgent", "ResearchResult", "SearchResult", "search_deep", "search_basic"] 