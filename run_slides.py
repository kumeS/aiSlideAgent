#!/usr/bin/env python3
"""
JSONファイルからスライドを生成する独立したスクリプト
SVGアイコンをサポート
"""
import os
import sys
import json
import logging
import argparse
import webbrowser
from pathlib import Path

# Import required modules
from agents.outline import generate_outline
from agents.template_selector import select_template_for_presentation
from agents.slide_writer.slide_template import SlideTemplate

# Set up output directory
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# SVGアイコンのパスとスライドタイプの対応を定義
ICON_MAPPING = {
    "title": "quantum.svg",  # タイトルスライド用
    "content": "algorithm.svg",  # 一般コンテンツスライド用
    "concept": "quantum.svg",  # 概念説明スライド用
    "algorithm": "algorithm.svg",  # アルゴリズム説明スライド用
    "application": "application.svg",  # 応用例スライド用
    "security": "security.svg",  # セキュリティスライド用
    "future": "future.svg",  # 未来展望スライド用
    "conclusion": "future.svg",  # 結論スライド用
}

def get_icon_content(icon_name):
    """SVGアイコンの内容を取得"""
    icon_path = os.path.join("static", "slide_assets", "icons", icon_name)
    try:
        if os.path.exists(icon_path):
            with open(icon_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            print(f"Warning: Icon file {icon_path} not found")
            return ""
    except Exception as e:
        print(f"Error reading icon file: {str(e)}")
        return ""

def enhance_slide_with_icon(slide, slide_html):
    """スライドにSVGアイコンを追加"""
    # スライドタイプに対応するアイコンを取得
    slide_type = slide.type.lower() if hasattr(slide, 'type') else "content"
    
    # スライドタイトルからキーワードを検出して適切なアイコンを選ぶ
    icon_name = ICON_MAPPING.get(slide_type, "quantum.svg")
    
    # キーワードベースでアイコンを選択するロジック
    slide_title = slide.title.lower() if hasattr(slide, 'title') else ""
    if "アルゴリズム" in slide_title or "algorithm" in slide_title:
        icon_name = ICON_MAPPING["algorithm"]
    elif "応用" in slide_title or "application" in slide_title:
        icon_name = ICON_MAPPING["application"]
    elif "セキュリティ" in slide_title or "security" in slide_title:
        icon_name = ICON_MAPPING["security"]
    elif "未来" in slide_title or "展望" in slide_title or "future" in slide_title:
        icon_name = ICON_MAPPING["future"]
    
    # SVGアイコンの内容を取得
    icon_content = get_icon_content(icon_name)
    if not icon_content:
        return slide_html
    
    # アイコンのサイズとスタイルを適用
    icon_styled = icon_content.replace('<svg ', '<svg class="slide-icon" ')
    
    # スライドHTMLにアイコンを挿入（ヘッダーの後ろ）
    icon_div = f"""<div class="icon-container">
    {icon_styled}
</div>"""
    
    # ヘッダー部分を特定して直後にアイコンを挿入
    if '<div class="header' in slide_html:
        slide_html = slide_html.replace('</div><!-- End of header -->', '</div><!-- End of header -->\n' + icon_div)
    else:
        # ヘッダーが見つからない場合は本文の前に挿入
        slide_html = slide_html.replace('<div class="content">', icon_div + '\n<div class="content">')
    
    # アイコン用のCSSスタイルを追加
    icon_css = """
        .icon-container {
            position: absolute;
            top: 20px;
            right: 20px;
            width: 48px;
            height: 48px;
            opacity: 0.7;
        }
        
        .slide-icon {
            width: 48px;
            height: 48px;
            color: var(--accent-color, var(--primary-color));
        }
        
        /* テキスト密度に応じてアイコンを調整 */
        .text-density-minimal .icon-container {
            opacity: 0.9;
            transform: scale(1.2);
        }
        
        .text-density-detailed .icon-container {
            opacity: 0.6;
            transform: scale(0.9);
        }
    """
    
    # CSSの終了タグの直前にスタイルを追加
    slide_html = slide_html.replace('</style>', icon_css + '\n</style>')
    
    return slide_html

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate slides from a JSON file')
    parser.add_argument('json_file', help='Path to the JSON file with research data')
    parser.add_argument('--slides', '-s', type=int, default=5, help='Number of slides to generate (default: 5)')
    parser.add_argument('--style', type=str, default='professional', 
                        choices=['professional', 'modern', 'minimal', 'business'],
                        help='Presentation style (default: professional)')
    parser.add_argument('--open', '-b', action='store_true', 
                        help='Open the generated slides in a browser')
    parser.add_argument('--icons', '-i', action='store_true', default=True,
                        help='Include SVG icons in slides (default: True)')
    parser.add_argument('--text-density', '-t', choices=['minimal', 'balanced', 'detailed'], 
                        default='balanced', help='Text density level (minimal, balanced, detailed)')
    
    args = parser.parse_args()
    
    # Load the JSON file
    print(f"Loading research data from: {args.json_file}")
    try:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            research_data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        return 1
    
    # Display basic info
    topic = research_data.get("topic", "Unknown Topic")
    print(f"Topic: {topic}")
    print(f"Style: {args.style}")
    print(f"Slides: {args.slides}")
    print(f"Icons: {'Enabled' if args.icons else 'Disabled'}")
    print(f"Text Density: {args.text_density}")
    
    # Step 1: Generate outline from research data
    print("\nGenerating outline from JSON data...")
    outline = generate_outline(research_data, args.slides, topic)
    print(f"Created outline with {len(outline.slides)} slides")
    
    # Step 2: Select appropriate template
    print("\nSelecting appropriate template...")
    slide_theme = select_template_for_presentation(topic, outline, args.style)
    print(f"Selected template: {slide_theme.name}")
    
    # Set text density on the theme
    slide_theme.text_density = args.text_density
    
    # Step 3: Create individual slide HTML files
    print("\nCreating individual slide HTML files...")
    
    # Create output directory for individual slides
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:30]
    slides_dir = os.path.join(OUTPUT_DIR, f"{timestamp}_{safe_topic}")
    os.makedirs(slides_dir, exist_ok=True)
    
    # List to store individual slide paths
    slide_files = []
    
    # Generate each slide as a separate HTML file
    for i, slide in enumerate(outline.slides):
        slide_num = i + 1
        print(f"\nGenerating slide {slide_num}/{len(outline.slides)}: {slide.title}")
        print(f"  Type: {slide.type}")
        print(f"  Content:")
        for bullet in slide.content:
            print(f"    • {bullet}")
            
        # Generate individual slide HTML
        slide_html = SlideTemplate.generate_slide_html(slide, slide_theme, slide_num, len(outline.slides))
        
        # Add SVG icon if enabled - これは個別スライドに適用
        if args.icons:
            slide_html = enhance_slide_with_icon(slide, slide_html)
        
        # Save individual slide to file
        slide_filename = f"slide_{slide_num:02d}.html"
        slide_path = os.path.join(slides_dir, slide_filename)
        with open(slide_path, 'w', encoding='utf-8') as f:
            f.write(slide_html)
            
        slide_files.append(slide_path)
        print(f"Slide {slide_num} generated and saved: {slide_filename}")
    
    # Create the main slideshow HTML that combines all individual slides
    print("\nCombining individual slides into slideshow...")
    
    # テキスト密度設定をスライドテーマに追加して、スライドショーHTMLの生成に反映させる
    slide_theme.text_density = args.text_density
    
    # スライドショーHTML生成（文章量調整ボタンはこの関数内で追加される）
    slideshow_html = SlideTemplate.create_slideshow_html(slide_files, topic, slide_theme, slides_dir)
    
    # Define the output path for the combined slideshow
    output_path = os.path.join(slides_dir, "index.html")
        
    # Save the slideshow HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(slideshow_html)
        
    print(f"\nSlideshow generation complete: {output_path}")
    
    # Open in browser if requested
    if args.open:
        print(f"Opening slideshow in browser...")
        try:
            file_path = Path(os.path.abspath(output_path))
            file_uri = file_path.as_uri()
            webbrowser.open(file_uri)
            print(f"✅ Browser opened successfully")
        except Exception as e:
            print(f"❌ Failed to open browser: {str(e)}")
            print(f"ℹ️ Manually open this URL in your browser: {file_path.as_uri()}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 