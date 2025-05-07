"""
Slide Models

This module defines the data models for slide content representation.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class HTMLSlide(BaseModel):
    """Model representing a generated HTML slide."""
    id: str
    html_content: str
    slide_type: str = "content"
    image_path: Optional[str] = None

class SlideDeckHTML(BaseModel):
    """Model representing a complete HTML slide deck."""
    topic: str
    title: str
    subtitle: Optional[str] = None
    author: Optional[str] = None
    slides: List[HTMLSlide] = Field(default_factory=list)
    theme: Optional[dict] = Field(default_factory=dict)
    
    def to_json(self) -> str:
        """Convert the slide deck to JSON format."""
        import json
        return json.dumps(self.dict(), indent=2) 