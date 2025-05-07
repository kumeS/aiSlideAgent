#!/usr/bin/env python3
"""
スライド生成の中心機能モジュール
"""

import os
import json
import logging
import time
import datetime
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import re

from utils.data_store import agent_data_store
from utils.logging_setup import setup_logging
from utils.html_utils import create_individual_slide_html, clean_markdown

from agents.slide_writer.slide_template import SlideTemplate

def generate_slides_cli(topic: str, slide_count: int = 5, style: str = "professional", depth: str = "low", output_file: str = None, use_orchestrator: bool = False) -> str:
    """
    Generate slides from the command line interface
    
    Args:
        topic: The presentation topic
        slide_count: Number of slides to generate
        style: Presentation style
        depth: Search depth (low/medium/high)
        output_file: Optional file path to save the HTML
        use_orchestrator: Whether to use the orchestrator agent
        
    Returns:
        HTML content of the generated slides
    """
    # Set up logging for this CLI session
    log_file = setup_logging(topic)
    logger = logging.getLogger(__name__)
    
    # Initialize result storage
    research_results = None
    outline = None
    slide_theme = None
    html_content = None
    
    try:
        # Define line separator for readability
        separator_line = "──────────────────────────────────────────────────"
        print(separator_line)
        
        print(f"📝 生成トピック: {topic}")
        print(f"🔢 スライド数: {slide_count}")
        print(f"🎨 スタイル: {style}")
        print(f"🔍 検索詳細度: {depth}")
        print(separator_line)
        
        # Start timer
        start_time = time.time()
        
        # Step 1: Get research results 
        print("\n🔎 トピックに関する情報を検索中です...")
        
        # Check if we should use orchestration
        if use_orchestrator:
            from agents.orchestrate_slide_generation import orchestrate_slide_generation
            html_content = orchestrate_slide_generation(
                topic=topic,
                slide_count=slide_count,
                style=style,
                depth=depth
            )
        else:
            # Run standard pipeline
            # Search for topic info with appropriate depth
            if depth == "low":
                from agents.research import search_basic
                research_results = search_basic(topic, slide_count)
            else:
                from agents.research import search_deep
                results_count = 10 if depth == "medium" else 15
                research_results = search_deep(topic, results_count)
            
            # Generate outline from research results
            print("\n📑 スライドのアウトラインを生成中です...")
            from agents.outline import generate_outline
            outline = generate_outline(research_results, slide_count)
            
            # Notify user of outline generation completion
            print("\n✅ アウトラインの生成が完了しました:")
            for i, section in enumerate(outline, 1):
                print(f"\n{i}. {section.title}")
                for point in section.points:
                    print(f"   • {point}")
                    
            # Generate template based on topic and outline
            print("\n🎨 プレゼンテーションテンプレートを選択中です...")
            from agents.template_selector import select_template_for_presentation
            slide_theme = select_template_for_presentation(topic, outline, style=style)
            print(f"✅ テンプレートを選択しました: {slide_theme.style}")
            
            # Generate initial slides based on outline and template
            print("\n🖼️ スライドコンテンツを生成中です...")
            from agents.slide_writer import generate_slides
            slides = generate_slides(topic, outline, slide_theme)
            
            # Set up file paths
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c if c.isalnum() else "_" for c in topic)
            safe_topic = safe_topic[:30]  # Limit length for file system
            
            output_dir = Path(f"static/output/{timestamp}_{safe_topic}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy necessary assets
            import shutil
            icons_dir = Path("static/slide_assets/icons")
            if icons_dir.exists():
                output_icons_dir = output_dir / "icons"
                output_icons_dir.mkdir(exist_ok=True)
                for icon_file in icons_dir.glob("*.svg"):
                    shutil.copy(icon_file, output_icons_dir)
            
            # Generate individual slide HTML files
            slide_html_files = []
            for i, slide in enumerate(slides, 1):
                slide_html = create_individual_slide_html(slide, slide_theme, i, len(slides))
                slide_file = output_dir / f"slide{i}.html"
                
                with open(slide_file, "w", encoding="utf-8") as f:
                    f.write(slide_html)
                    
                slide_html_files.append(slide_file)
                
            # Generate the index.html file
            index_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - プレゼンテーション</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Noto Sans JP', sans-serif;
            background-color: #f5f5f5;
            padding: 2rem;
        }}
        .header {{
            background-color: {slide_theme.primary_color};
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }}
        .slide-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        .slide-card {{
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease-in-out;
        }}
        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        }}
        .slide-header {{
            background-color: {slide_theme.secondary_color};
            color: white;
            padding: 1rem;
        }}
        .slide-content {{
            padding: 1rem;
        }}
        .start-button {{
            background-color: {slide_theme.primary_color};
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .start-button:hover {{
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="text-3xl font-bold">{topic}</h1>
        <p class="mt-2 opacity-80">{len(slides)}枚のスライド</p>
        <div class="mt-4">
            <a href="slide1.html" class="start-button">スライドショーを開始</a>
        </div>
    </div>
    
    <div class="slide-grid">
"""
            
            # Add slide cards to the index
            for i, slide in enumerate(slides, 1):
                slide_title = slide.title if hasattr(slide, 'title') and slide.title else f"スライド {i}"
                index_html += f"""
        <a href="slide{i}.html" class="slide-card">
            <div class="slide-header">
                <h2 class="text-lg font-semibold">スライド {i}</h2>
            </div>
            <div class="slide-content">
                <h3 class="font-medium">{slide_title}</h3>
            </div>
        </a>
"""
            
            # Close the HTML file
            index_html += """
    </div>
</body>
</html>
"""
            
            # Write the index.html file
            index_file = output_dir / "index.html"
            with open(index_file, "w", encoding="utf-8") as f:
                f.write(index_html)
                
            # Set up the output paths
            html_path = index_file
            browser_path = html_path.as_uri()
            
            # Use the specified output file if provided
            if output_file:
                # If it's a directory, place index.html there
                output_path = Path(output_file)
                if output_path.is_dir():
                    html_path = output_path / "index.html"
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(index_html)
                # Otherwise assume it's a file path for index.html
                else:
                    html_path = output_path
                    with open(html_path, "w", encoding="utf-8") as f:
                        f.write(index_html)
                        
                browser_path = html_path.as_uri()
                
            print(f"\n✅ スライドの生成が完了しました")
            print(f"📄 HTML ファイル: {html_path}")
            print(f"🌐 ブラウザURL: {browser_path}")
            
            # Open in browser
            print(f"🌐 ブラウザでスライドを開いています...")
            try:
                webbrowser.open(browser_path)
                print(f"✅ ブラウザでスライドを表示しています")
            except Exception as e:
                print(f"❌ ブラウザでの表示に失敗しました: {str(e)}")
                print(f"ℹ️ 手動で次のURLをブラウザに入力してください: {browser_path}")
                
            # Store HTML content for return
            html_content = index_html

        # Calculate and display elapsed time
        elapsed = time.time() - start_time
        minutes, seconds = divmod(elapsed, 60)
        print(f"\n⏱️ 処理時間: {int(minutes)}分 {int(seconds)}秒")
        
        # End with separator line
        print(separator_line)
        
        return html_content
        
    except Exception as e:
        logger.error(f"Error generating slides: {str(e)}", exc_info=True)
        print(f"\n❌ スライド生成中にエラーが発生しました: {str(e)}")
        return None

def generate_slides_from_json(json_file: str, slide_count: int = 5, style: str = "professional", output_file: str = None, open_in_browser: bool = False) -> str:
    """
    Generate slides from a JSON file containing research results
    
    Args:
        json_file: Path to the JSON file with research data
        slide_count: Number of slides to generate
        style: Presentation style
        output_file: Optional file path to save the HTML
        open_in_browser: Whether to open the result in browser
        
    Returns:
        HTML content of the generated slides
    """
    # Set up logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Define line separator for readability
        separator_line = "──────────────────────────────────────────────────"
        print(separator_line)
        
        print(f"📄 JSONファイルから読み込み: {json_file}")
        print(f"🔢 スライド数: {slide_count}")
        print(f"🎨 スタイル: {style}")
        print(separator_line)
        
        # Start timer
        start_time = time.time()
        
        # Load research data from JSON file
        with open(json_file, "r", encoding="utf-8") as f:
            research_data = json.load(f)
        
        print("\n📑 読み込んだデータからアウトラインを生成中です...")
        
        # Extract topic from research data if available
        topic = research_data.get("topic", "プレゼンテーション")
        
        # Check if the research data is already in the expected format
        research_results = research_data
        if "research_result" in research_data:
            research_results = research_data["research_result"]
        
        # Generate outline from research results
        from agents.outline import generate_outline
        outline = generate_outline(research_results, slide_count)
        
        # Notify user of outline generation completion
        print("\n✅ アウトラインの生成が完了しました:")
        for i, section in enumerate(outline, 1):
            print(f"\n{i}. {section.title}")
            for point in section.points:
                print(f"   • {point}")
                
        # Generate template based on topic and outline
        print("\n🎨 プレゼンテーションテンプレートを選択中です...")
        from agents.template_selector import select_template_for_presentation
        slide_theme = select_template_for_presentation(topic, outline, style=style)
        print(f"✅ テンプレートを選択しました: {slide_theme.style}")
        
        # Generate initial slides based on outline and template
        print("\n🖼️ スライドコンテンツを生成中です...")
        from agents.slide_writer import generate_slides
        slides = generate_slides(topic, outline, slide_theme)
        
        # Set up file paths
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)
        safe_topic = safe_topic[:30]  # Limit length for file system
        
        output_dir = Path(f"static/output/{timestamp}_{safe_topic}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy necessary assets
        import shutil
        icons_dir = Path("static/slide_assets/icons")
        if icons_dir.exists():
            output_icons_dir = output_dir / "icons"
            output_icons_dir.mkdir(exist_ok=True)
            for icon_file in icons_dir.glob("*.svg"):
                shutil.copy(icon_file, output_icons_dir)
        
        # Generate individual slide HTML files
        slide_html_files = []
        for i, slide in enumerate(slides, 1):
            slide_html = create_individual_slide_html(slide, slide_theme, i, len(slides))
            slide_file = output_dir / f"slide{i}.html"
            
            with open(slide_file, "w", encoding="utf-8") as f:
                f.write(slide_html)
                
            slide_html_files.append(slide_file)
            
        # Generate the index.html file
        index_html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic} - プレゼンテーション</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        body {{
            font-family: 'Noto Sans JP', sans-serif;
            background-color: #f5f5f5;
            padding: 2rem;
        }}
        .header {{
            background-color: {slide_theme.primary_color};
            color: white;
            padding: 2rem;
            border-radius: 8px;
            margin-bottom: 2rem;
        }}
        .slide-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1.5rem;
        }}
        .slide-card {{
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s ease-in-out;
        }}
        .slide-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        }}
        .slide-header {{
            background-color: {slide_theme.secondary_color};
            color: white;
            padding: 1rem;
        }}
        .slide-content {{
            padding: 1rem;
        }}
        .start-button {{
            background-color: {slide_theme.primary_color};
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            font-weight: 500;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .start-button:hover {{
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 class="text-3xl font-bold">{topic}</h1>
        <p class="mt-2 opacity-80">{len(slides)}枚のスライド</p>
        <div class="mt-4">
            <a href="slide1.html" class="start-button">スライドショーを開始</a>
        </div>
    </div>
    
    <div class="slide-grid">
"""
        
        # Add slide cards to the index
        for i, slide in enumerate(slides, 1):
            slide_title = slide.title if hasattr(slide, 'title') and slide.title else f"スライド {i}"
            index_html += f"""
    <a href="slide{i}.html" class="slide-card">
        <div class="slide-header">
            <h2 class="text-lg font-semibold">スライド {i}</h2>
        </div>
        <div class="slide-content">
            <h3 class="font-medium">{slide_title}</h3>
        </div>
    </a>
"""
        
        # Close the HTML file
        index_html += """
    </div>
</body>
</html>
"""
        
        # Write the index.html file
        index_file = output_dir / "index.html"
        with open(index_file, "w", encoding="utf-8") as f:
            f.write(index_html)
            
        # Set up the output paths
        html_path = index_file
        browser_path = html_path.as_uri()
        
        # Use the specified output file if provided
        if output_file:
            # If it's a directory, place index.html there
            output_path = Path(output_file)
            if output_path.is_dir():
                html_path = output_path / "index.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(index_html)
            # Otherwise assume it's a file path for index.html
            else:
                html_path = output_path
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(index_html)
                    
            browser_path = html_path.as_uri()
            
        print(f"\n✅ スライドの生成が完了しました")
        print(f"📄 HTML ファイル: {html_path}")
        print(f"🌐 ブラウザURL: {browser_path}")
        
        # Open in browser if requested
        if open_in_browser:
            print(f"🌐 ブラウザでスライドを開いています...")
            try:
                webbrowser.open(browser_path)
                print(f"✅ ブラウザでスライドを表示しています")
            except Exception as e:
                print(f"❌ ブラウザでの表示に失敗しました: {str(e)}")
                print(f"ℹ️ 手動で次のURLをブラウザに入力してください: {browser_path}")
                
        # Calculate and display elapsed time
        elapsed = time.time() - start_time
        minutes, seconds = divmod(elapsed, 60)
        print(f"\n⏱️ 処理時間: {int(minutes)}分 {int(seconds)}秒")
        
        # End with separator line
        print(separator_line)
        
        return index_html
        
    except Exception as e:
        logger.error(f"Error generating slides from JSON: {str(e)}", exc_info=True)
        print(f"\n❌ JSONからのスライド生成中にエラーが発生しました: {str(e)}")
        return None 