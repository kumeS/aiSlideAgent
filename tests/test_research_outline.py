"""
Test script for Research and Outline agents.

This script tests the deep search and outline generation capabilities
using the topic "Quantum Dots" as specified in the requirements.
"""

import os
import logging
from dotenv import load_dotenv
import pytest
from unittest.mock import patch, MagicMock

# Import the agent modules - conftest.pyで既にPYTHONPATHは設定済み
from agents import ResearchAgent, OutlineAgent
from agents.research import SearchResult, ResearchResult

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@pytest.mark.network
def test_research_agent():
    """Test the ResearchAgent with the topic 'Quantum Dots'."""
    logger.info("Testing ResearchAgent with topic 'Quantum Dots'")
    
    # Initialize the research agent
    research_agent = ResearchAgent()
    
    # Perform deep search on the topic
    research_result = research_agent.search_deep("Quantum Dots", depth=2)
    
    # Validate the research results
    assert research_result.topic == "Quantum Dots", "Topic should be set correctly"
    assert len(research_result.primary_results) > 0, "Should have primary results"
    
    if research_result.secondary_results:
        logger.info(f"Found {len(research_result.secondary_results)} secondary results")
    
    if research_result.knowledge_gaps:
        logger.info(f"Identified {len(research_result.knowledge_gaps)} knowledge gaps")
        for i, gap in enumerate(research_result.knowledge_gaps):
            logger.info(f"  {i+1}. {gap}")
    
    logger.info(f"Research summary length: {len(research_result.summary.split())}")
    logger.info("Research test completed successfully")
    
    return research_result

def test_research_agent_mocked():
    """テスト用にHTTPリクエストをモックしたバージョン"""
    logger.info("Testing ResearchAgent with mocked OpenAI API")
    
    with patch('agents.client.chat.completions.create') as mock_create:
        mock_create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Mocked response about Quantum Dots"))]
        )
        
        # Initialize the research agent
        research_agent = ResearchAgent()
        
        # Mock the _generate_synthetic_results method to return predefined results
        with patch.object(research_agent, '_generate_synthetic_results') as mock_generate:
            mock_results = [
                SearchResult(
                    url="https://example.com/quantum-dots-1",
                    title="Introduction to Quantum Dots",
                    snippet="Quantum dots are semiconductor particles a few nanometers in size.",
                    source_type="web",
                    credibility_score=0.9
                ),
                SearchResult(
                    url="https://example.com/quantum-dots-2",
                    title="Applications of Quantum Dots",
                    snippet="Quantum dots are used in display technology and solar cells.",
                    source_type="web",
                    credibility_score=0.8
                )
            ]
            mock_generate.return_value = mock_results
            
            # Perform search
            research_result = research_agent.search_deep("Quantum Dots", depth="low")
            
            # Validate the research results
            assert research_result.topic == "Quantum Dots", "Topic should be set correctly"
            assert len(research_result.primary_results) > 0, "Should have primary results"
    
    logger.info("Mocked research test completed successfully")
    return research_result

@pytest.mark.network
def test_outline_agent(research_result, slide_count=10):
    """Test the OutlineAgent with the research results."""
    logger.info(f"Testing OutlineAgent with {slide_count} slides")
    
    # Initialize the outline agent
    outline_agent = OutlineAgent()
    
    # Generate an outline from the research
    slide_deck = outline_agent.generate_outline(research_result, slide_count)
    
    # Validate the slide deck
    assert slide_deck.topic == research_result.topic, "Topic should match"
    assert len(slide_deck.slides) == slide_count, f"Should have exactly {slide_count} slides"
    
    # Log the outline for review
    logger.info(f"Generated slide deck: {slide_deck.title}")
    logger.info(f"Number of slides: {len(slide_deck.slides)}")
    
    # Print the outline in markdown format for easy viewing
    print("\n" + "="*50)
    print(f"SLIDE DECK OUTLINE: {slide_deck.title}")
    print("="*50)
    print(slide_deck.to_markdown())
    
    logger.info("Outline test completed successfully")
    
    return slide_deck

def test_outline_agent_mocked():
    """Mock version of the outline agent test"""
    logger.info("Testing OutlineAgent with mocked data")
    
    # First get a mocked research result
    research_result = test_research_agent_mocked()
    
    with patch('agents.client.chat.completions.create') as mock_create:
        # Mock response for outline generation
        mock_create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='{"title": "Quantum Dots: Nanoscale Wonders", "subtitle": "Applications and Properties", "slides": [{"title": "Introduction to Quantum Dots", "content": ["Nanoscale semiconductor particles", "Size-dependent properties", "Discovery and development"]}]}'
                )
            )]
        )
        
        # Test with a smaller slide count for speed
        slide_deck = test_outline_agent(research_result, slide_count=3)
        
        # Basic validations
        assert slide_deck.topic == "Quantum Dots"
        assert len(slide_deck.slides) > 0
    
    logger.info("Mocked outline test completed successfully")
    return slide_deck

def main():
    """Run both tests in sequence."""
    logger.info("Starting tests for research and outline agents")
    
    try:
        # Default to running mocked tests
        use_network = os.environ.get("USE_NETWORK_TESTS", "").lower() == "true"
        
        if use_network:
            # Run the network-dependent tests
            research_result = test_research_agent()
            slide_deck_5 = test_outline_agent(research_result, 5)
        else:
            # Run the mocked tests
            research_result = test_research_agent_mocked()
            slide_deck_5 = test_outline_agent_mocked()
        
        logger.info("All tests completed successfully")
        return 0
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Exit with the appropriate code
    sys.exit(main()) 