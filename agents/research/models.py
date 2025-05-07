"""
Research Data Models

This module defines the data models used by the research agent.
"""

import hashlib
from typing import List, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field

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