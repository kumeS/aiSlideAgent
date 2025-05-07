#!/usr/bin/env python3
"""
Basic test script for the AI Slide Generator
Test 1: Research functionality
"""

import sys
import os
import logging
from pathlib import Path

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_research_basic():
    """Test the basic research functionality"""
    try:
        logger.info("=== Testing Basic Research Functionality ===")
        
        # Import from app_fixed.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from app_fixed import research_command
        from utils.data_store import agent_data_store
        
        # Create a simple ArgumentParser-like object
        class Args:
            def __init__(self):
                self.topic = "量子コンピューティング"
                self.depth = "low"
                self.results = 3
                self.basic = True
                self.json = False
                self.output = None
                self.store = "test_research_results"
                self.store_file = None
                self.next_agent = None
        
        args = Args()
        
        # Run the research command
        logger.info(f"Running research on topic: {args.topic}")
        results = research_command(args)
        
        # Check if results were returned and stored
        if results:
            logger.info("✅ Research returned results")
        else:
            logger.error("❌ Research failed to return results")
            return False
            
        # Check if results were stored in data store
        stored_results = agent_data_store.get(args.store)
        if stored_results:
            logger.info(f"✅ Results stored in data store under key: {args.store}")
            logger.info(f"✅ Retrieved {len(stored_results)} search results")
        else:
            logger.error("❌ Results not found in data store")
            return False
            
        logger.info("✅ Basic research test passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_outline_generation():
    """Test the outline generation functionality"""
    try:
        logger.info("\n=== Testing Outline Generation Functionality ===")
        
        # Import from app_fixed.py
        from app_fixed import outline_command
        from utils.data_store import agent_data_store
        
        # Create a simple ArgumentParser-like object for outline command
        class OutlineArgs:
            def __init__(self):
                self.slides = 3
                self.input = None
                self.store_key = "test_research_results"
                self.output = None
        
        args = OutlineArgs()
        
        # Run the outline command
        logger.info(f"Generating outline from research results (data store key: {args.store_key})")
        outline = outline_command(args)
        
        # Check if outline was generated
        if outline:
            logger.info("✅ Outline was successfully generated")
            logger.info(f"✅ Generated {len(outline)} outline sections")
        else:
            logger.error("❌ Outline generation failed")
            return False
            
        # Check if outline was stored in data store
        stored_outline = agent_data_store.get("outline_result")
        if stored_outline:
            logger.info("✅ Outline stored in data store under key: outline_result")
        else:
            logger.error("❌ Outline not found in data store")
            return False
            
        logger.info("✅ Outline generation test passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success1 = test_research_basic()
    
    if success1:
        success2 = test_outline_generation()
        sys.exit(0 if success1 and success2 else 1)
    else:
        sys.exit(1) 