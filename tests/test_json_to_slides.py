"""
Test script for generating slides from JSON input.

This script tests the ability to generate presentation slides directly from
a JSON file containing research results, specifically quantum_research.json.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import pytest
from unittest.mock import patch, MagicMock

# Import the agent modules
from agents import generate_outline, generate_slides
from agents.template_selector import select_template_for_presentation
from agents.research import ResearchResult
from agents.slide_writer import SlideTheme

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_json_to_slides():
    """Test generating slides from a JSON file."""
    logger.info("Testing slide generation from JSON input (quantum_research.json)")
    
    # Load the quantum_research.json file
    json_path = Path(__file__).parent.parent / "quantum_research.json"
    assert json_path.exists(), f"JSON file not found at {json_path}"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        research_data = json.load(f)
    
    # Generate an outline from the research data
    logger.info("Generating outline from JSON data")
    slide_count = 5
    outline = generate_outline(research_data, slide_count)
    
    # Select a template
    logger.info("Selecting template")
    template = select_template_for_presentation(research_data["topic"], outline)
    
    # Generate slides
    logger.info("Generating slides")
    slides_html = generate_slides(outline, theme=template)
    
    # Validate the output
    assert slides_html, "Generated HTML should not be empty"
    assert len(slides_html) > 1000, "Generated HTML should be substantial"
    assert "<html" in slides_html.lower(), "Output should be HTML"
    assert research_data["topic"] in slides_html, "HTML should contain the topic"
    
    # Save the HTML output for manual inspection
    output_dir = Path(__file__).parent.parent / "static" / "output"
    output_dir.mkdir(exist_ok=True, parents=True)
    output_path = output_dir / "test_quantum_slides.html"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(slides_html)
    
    logger.info(f"Saved output to {output_path}")
    logger.info("JSON to slides test completed successfully")
    
    return slides_html

def test_json_to_slides_mocked():
    """Test generating slides from a JSON file with mocked API calls."""
    logger.info("Testing slide generation from JSON with mocked API")
    
    # Load the quantum_research.json file
    json_path = Path(__file__).parent.parent / "quantum_research.json"
    assert json_path.exists(), f"JSON file not found at {json_path}"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        research_data = json.load(f)
    
    # Mock the API calls
    with patch('agents.client.chat.completions.create') as mock_create:
        # Mock response for outline generation
        mock_create.return_value = MagicMock(
            choices=[MagicMock(
                message=MagicMock(
                    content='{"title": "量子コンピューティング入門", "subtitle": "原理と応用", "slides": [{"title": "量子コンピューティングとは", "content": ["量子力学の原理を利用した次世代計算技術", "キュービットを使用し、重ね合わせと量子もつれにより並列計算が可能", "従来のコンピュータでは難しい問題を効率的に解決"], "type": "title"}, {"title": "キュービットと量子力学", "content": ["キュービットは量子ビットで0と1の重ね合わせ状態をとる", "量子もつれにより複数のキュービット間に強い相関関係が生まれる", "観測すると状態が確定する（波動関数の収縮）"], "type": "content"}, {"title": "量子アルゴリズム", "content": ["ショアのアルゴリズム：素因数分解を効率的に行う", "グローバーのアルゴリズム：データベース検索を高速化", "量子シミュレーション：複雑な量子系をシミュレーション"], "type": "content"}, {"title": "量子コンピューティングの応用", "content": ["材料科学：新素材の特性予測と開発", "薬物設計：分子相互作用のシミュレーション", "金融：リスク分析と最適化問題の解決", "機械学習：大規模データ処理の効率化"], "type": "content"}, {"title": "現状と課題", "content": ["エラー訂正：量子状態は非常に壊れやすい", "スケーラビリティ：多数のキュービットを制御する技術", "実用化に向けた継続的な研究開発の必要性"], "type": "content"}]}'
                )
            )]
        )
        
        # Generate an outline from the research data
        logger.info("Generating outline from JSON data (mocked)")
        slide_count = 5
        outline = generate_outline(research_data, slide_count)
        
        # Select a template
        template = SlideTheme(
            name="Quantum",
            primary_color="#3B82F6",
            secondary_color="#10B981",
            text_color="#F9FAFB",
            background_color="#111827",
        )
        
        # Mock the slide generation
        with patch('agents.slide_writer.SlideWriterAgent.render_full_deck') as mock_render:
            mock_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>量子コンピューティング</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .slide { margin-bottom: 20px; }
                </style>
            </head>
            <body>
                <div class="slide">
                    <h1>量子コンピューティング入門</h1>
                    <h2>原理と応用</h2>
                </div>
                <div class="slide">
                    <h2>量子コンピューティングとは</h2>
                    <ul>
                        <li>量子力学の原理を利用した次世代計算技術</li>
                        <li>キュービットを使用し、重ね合わせと量子もつれにより並列計算が可能</li>
                    </ul>
                </div>
            </body>
            </html>
            """
            mock_render.return_value = mock_html
            
            # Generate slides
            logger.info("Generating slides (mocked)")
            slides_html = generate_slides(outline, theme=template)
            
            # Validate the output
            assert mock_html in slides_html, "HTML should match mocked output"
    
    logger.info("Mocked JSON to slides test completed successfully")
    return slides_html

def main():
    """Run tests."""
    logger.info("Starting tests for JSON to slides generation")
    
    try:
        # Default to running mocked tests
        use_network = os.environ.get("USE_NETWORK_TESTS", "").lower() == "true"
        
        if use_network:
            slides_html = test_json_to_slides()
        else:
            slides_html = test_json_to_slides_mocked()
        
        logger.info("All tests completed successfully")
        
        # Check if html has expected content
        if "量子コンピューティング" in slides_html:
            logger.info("✅ HTML contains the expected topic")
        
        return 0
    
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run tests
    import sys
    sys.exit(main()) 