"""
Image Fetch Agent

Finds and downloads CC0 licensed images for slides.
"""

import os
import requests
import logging
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import urllib.parse
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from agents import client, DEFAULT_MODEL

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")

# Constants
ASSETS_DIR = Path(__file__).parent.parent.parent / "static" / "slide_assets"

class ImageSource(BaseModel):
    """Model representing an image source."""
    provider: str
    url: str
    author: Optional[str] = None
    author_url: Optional[str] = None
    license: str = "CC0"

class Image(BaseModel):
    """Model representing an image with metadata."""
    query: str
    url: str
    alt_text: str
    width: int
    height: int
    local_path: Optional[str] = None
    file_size: Optional[int] = None
    source: ImageSource
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate the aspect ratio of the image."""
        return self.width / self.height if self.height > 0 else 0

class ImageFetchAgent:
    """Agent for finding and downloading images for slides."""
    
    def __init__(self, api_key: Optional[str] = None, assets_dir: Optional[Path] = None):
        """Initialize the image fetch agent with API keys and configuration."""
        self.unsplash_api_key = api_key or UNSPLASH_API_KEY
        self.assets_dir = assets_dir or ASSETS_DIR
        
        if not self.unsplash_api_key:
            logger.warning("Unsplash API key not found. Image search capabilities will be limited.")
        
        # Create assets directory if it doesn't exist
        os.makedirs(self.assets_dir, exist_ok=True)
    
    def search_images(self, query: str, count: int = 3) -> List[Image]:
        """
        Search for images matching the query.
        
        Args:
            query: The search query
            count: Number of images to return
            
        Returns:
            List of Image objects
        """
        logger.info(f"Searching for images matching: {query}")
        
        results = []
        
        try:
            # Search Unsplash
            unsplash_results = self._search_unsplash(query, count)
            results.extend(unsplash_results)
            
            # Sort by resolution (highest first)
            results.sort(key=lambda img: img.width * img.height, reverse=True)
            
            return results[:count]
            
        except Exception as e:
            logger.error(f"Error searching for images: {str(e)}")
            return []
    
    def _search_unsplash(self, query: str, count: int = 3) -> List[Image]:
        """Search for images on Unsplash."""
        if not self.unsplash_api_key:
            return []
        
        try:
            # Prepare search parameters
            params = {
                "client_id": self.unsplash_api_key,
                "query": query,
                "per_page": count,
                "orientation": "landscape",  # Prefer landscape for slides
                "content_filter": "high"  # Safe content only
            }
            
            # Make the API request
            response = requests.get("https://api.unsplash.com/search/photos", params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if "results" in data:
                for item in data["results"]:
                    # Get image data
                    image = Image(
                        query=query,
                        url=item["urls"]["regular"],
                        alt_text=item.get("alt_description") or query,
                        width=item["width"],
                        height=item["height"],
                        source=ImageSource(
                            provider="Unsplash",
                            url=item["links"]["html"],
                            author=item["user"]["name"],
                            author_url=item["user"]["links"]["html"],
                            license="Unsplash License"
                        )
                    )
                    results.append(image)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Unsplash: {str(e)}")
            return []
    
    def generate_alt_text(self, image_url: str, context: str) -> str:
        """
        Generate alt text for an image based on the image and context.
        
        Args:
            image_url: URL of the image
            context: The context in which the image will be used
            
        Returns:
            Generated alt text
        """
        try:
            # Call OpenAI API to generate alt text
            prompt = f"""
            Please generate a concise, descriptive alt text for an image that will be used in a slide about:
            {context}
            
            The alt text should be descriptive, concise, and focus on what the image represents in this context.
            Keep it under 15 words.
            """
            
            response = client.chat.completions.create(
                model=DEFAULT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.7
            )
            
            alt_text = response.choices[0].message.content.strip()
            return alt_text
            
        except Exception as e:
            logger.error(f"Error generating alt text: {str(e)}")
            return context
    
    def download_image(self, image: Image) -> Optional[str]:
        """
        Download an image and save it to the assets directory.
        
        Args:
            image: The image to download
            
        Returns:
            Local path to the downloaded image, or None if download failed
        """
        try:
            # Generate a filename based on the query and URL
            url_hash = hashlib.md5(image.url.encode()).hexdigest()[:8]
            safe_query = urllib.parse.quote_plus(image.query.replace(" ", "_").lower())
            filename = f"{safe_query}_{url_hash}.jpg"
            
            # Full path to save the image
            filepath = self.assets_dir / filename
            
            # Download the image
            response = requests.get(image.url, stream=True)
            response.raise_for_status()
            
            # Save the image
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Update the image with the local path and file size
            image.local_path = str(filepath)
            image.file_size = os.path.getsize(filepath)
            
            logger.info(f"Image downloaded and saved to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
    
    def fetch_images_for_slides(self, slide_topics: List[str]) -> Dict[str, Image]:
        """
        Find and download appropriate images for a list of slide topics.
        
        Args:
            slide_topics: List of slide topics to find images for
            
        Returns:
            Dictionary mapping topics to downloaded images
        """
        result = {}
        
        for topic in slide_topics:
            logger.info(f"Finding image for: {topic}")
            
            # Search for images
            images = self.search_images(topic)
            
            if not images:
                logger.warning(f"No images found for topic: {topic}")
                continue
            
            # Select the best image (first result)
            best_image = images[0]
            
            # Generate better alt text
            alt_text = self.generate_alt_text(best_image.url, topic)
            best_image.alt_text = alt_text
            
            # Download the image
            local_path = self.download_image(best_image)
            
            if local_path:
                result[topic] = best_image
        
        return result

def fetch_image(query: str) -> Optional[Image]:
    """
    Helper function to fetch a single image for a query.
    
    Args:
        query: The search query
        
    Returns:
        An Image object with the downloaded image, or None if no image found
    """
    agent = ImageFetchAgent()
    images = agent.search_images(query, count=1)
    
    if not images:
        return None
    
    image = images[0]
    agent.download_image(image)
    
    return image 