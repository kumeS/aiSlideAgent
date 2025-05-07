"""
AI Slide Generator Agents Package

This package contains the agent implementations for the AI Slide Generator.
Each agent is responsible for a specific part of the slide generation process.
"""
import os
import logging
from dotenv import load_dotenv
import openai
from openai import OpenAI

# OpenAIのHTTP関連のロガーのレベルをDEBUGに設定してコンソールに表示されないようにする
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("openai.http_client").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Load environment variables from .env file
load_dotenv()

# Get API keys and configuration from environment
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file or environment.")
    
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Initialize the OpenAI client with global settings
client = OpenAI(api_key=openai_api_key)

# Set default model to use
DEFAULT_MODEL = openai_model

# Import main agent modules for easy access
from .outline import OutlineAgent, generate_outline
from .research import ResearchAgent, search_deep
from .slide_writer import SlideWriterAgent, SlideTheme, generate_slides
from .template_selector import TemplateSelectorAgent, select_template_for_presentation
from .image_fetch import ImageFetchAgent, fetch_image
from .refiner import RefinerAgent, refine_presentation
from .monitoring import MonitoringAgent, monitor_research_and_outline, monitor_slides_and_refine
from .monitoring import OrchestratorAgent, orchestrate_slide_generation

# Check OpenAI API key validity and log diagnostics
def check_openai_key_validity():
    """Check if the OpenAI API key is valid and log diagnostic information."""
    import logging
    import os
    
    logger = logging.getLogger(__name__)
    
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.warning("⚠️ OPENAI_API_KEY is not set in environment variables or .env file")
        return False
        
    if api_key.startswith("sk-") and len(api_key) > 20:
        logger.debug("✅ OPENAI_API_KEY format appears valid")
        return True
    else:
        logger.warning("⚠️ OPENAI_API_KEY format appears invalid. Should start with 'sk-' and be longer")
        return False

# Run the check at import time
key_validity = check_openai_key_validity()

__all__ = [
    "client",
    "DEFAULT_MODEL",
    "ResearchAgent",
    "search_deep",
    "OutlineAgent",
    "generate_outline",
    "SlideWriterAgent",
    "SlideTheme",
    "generate_slides",
    "ImageFetchAgent",
    "fetch_image",
    "RefinerAgent",
    "refine_presentation",
    "TemplateSelectorAgent",
    "select_template_for_presentation",
    "MonitoringAgent",
    "monitor_research_and_outline",
    "monitor_slides_and_refine",
    "OrchestratorAgent",
    "orchestrate_slide_generation",
] 