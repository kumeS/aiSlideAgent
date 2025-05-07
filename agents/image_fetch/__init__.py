"""
Image Fetch Agent Module

This module is responsible for finding and downloading CC0 licensed images for slides.
"""

from .image_fetch import ImageFetchAgent, fetch_image

__all__ = [
    "ImageFetchAgent",
    "fetch_image"
] 