#!/usr/bin/env python3
"""
スライドのHTML生成に関する機能モジュール
"""

def create_individual_slide_html(slide, theme, slide_num, total_slides):
    """
    Create HTML for an individual slide.
    
    Args:
        slide: The slide content
        theme: The slide theme
        slide_num: The slide number
        total_slides: Total number of slides
        
    Returns:
        HTML for the individual slide
    """
    try:
        slide_type = slide.type.lower() if hasattr(slide, 'type') else "content"
        slide_title = slide.title if hasattr(slide, 'title') and slide.title else f"スライド {slide_num}"
        slide_content = slide.content if hasattr(slide, 'content') and slide.content else []
        
        # Add additional theme CSS variables
        css_variables = {
            "--primary-color": theme.primary_color,
            "--secondary-color": theme.secondary_color,
            "--text-color": theme.text_color,
            "--background-color": theme.background_color,
            "--accent-color": getattr(theme, "accent_color", "#F59E0B"),
            "--font-family": theme.font_family,
            "--slide-index": str(slide_num),
            "--total-slides": str(total_slides),
        }
        
        # Add heading font if available
        if hasattr(theme, "heading_font") and theme.heading_font:
            css_variables["--heading-font"] = theme.heading_font
        else:
            css_variables["--heading-font"] = theme.font_family
            
        # Add code font if available
        if hasattr(theme, "code_font") and theme.code_font:
            css_variables["--code-font"] = theme.code_font
        
        # Generate CSS variables string
        css_vars = "\n        ".join([f"{key}: {value};" for key, value in css_variables.items()])
        
        # Choose bullet style based on theme setting or default to circle
        bullet_style = "fa-circle"
        if hasattr(theme, "bullet_style"):
            if theme.bullet_style == "square":
                bullet_style = "fa-square"
            elif theme.bullet_style == "dash":
                bullet_style = "fa-minus"
            elif theme.bullet_style == "arrow":
                bullet_style = "fa-chevron-right"
                
        # Choose header style based on theme
        header_style_class = "gradient-header"
        if hasattr(theme, "header_style"):
            if theme.header_style == "solid":
                header_style_class = "solid-header"
            elif theme.header_style == "minimal":
                header_style_class = "minimal-header"
            elif theme.header_style == "none":
                header_style_class = "no-header"
        
        # Create base HTML structure for an individual slide
        html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>スライド {slide_num} - {slide_title}</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;500;700&family=Montserrat:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            {css_vars}
        }}
        
        body {{
            font-family: var(--font-family);
            background-color: var(--background-color);
            color: var(--text-color);
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
            min-height: 100vh;
        }}
        
        /* External navigation bar */
        .external-nav {{
            width: 100%;
            background-color: rgba(0, 0, 0, 0.3);
            padding: 0.5rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }}
        
        .index-button {{
            background-color: var(--accent-color);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            text-decoration: none;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.9rem;
            transition: opacity 0.2s;
        }}
        
        .index-button:hover {{
            opacity: 0.9;
        }}
        
        /* Hide external nav in slideshow mode */
        body.in-slideshow .external-nav {{
            display: none;
        }}
        
        .slide {{
            width: 90%;
            max-width: 1000px;
            height: auto;
            min-height: 70vh;
            padding: 2rem 3rem;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: flex-start;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            position: relative;
            overflow: hidden;
            margin-bottom: 2rem;
        }}
        
        /* Text density styles */
        .text-density-minimal .content ul li {{
            margin-bottom: 2rem;
            font-size: 1.4rem;
        }}
        
        .text-density-balanced .content ul li {{
            margin-bottom: 1.2rem;
            font-size: 1.2rem;
        }}
        
        .text-density-detailed .content ul li {{
            margin-bottom: 0.8rem;
            font-size: 1.1rem;
        }}
        
        h1, h2 {{
            font-family: var(--heading-font, var(--font-family));
            color: var(--primary-color);
            margin-bottom: 2rem;
        }}
        
        h1 {{
            font-size: 3.5rem;
            font-weight: 700;
        }}
        
        h2 {{
            font-size: 2.5rem;
            font-weight: 600;
        }}
        
        .title-slide {{
            text-align: center;
            align-items: center;
            justify-content: center;
        }}
        
        .subtitle {{
            font-size: 1.8rem;
            margin-bottom: 2rem;
            opacity: 0.8;
        }}
        
        /* Header Styles */
        .gradient-header {{
            background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
            padding: 1.5rem;
            margin: -2rem -3rem 2rem -3rem;
            border-radius: 8px 8px 0 0;
        }}
        
        .gradient-header h2 {{
            color: white;
            margin-bottom: 0;
        }}
        
        .solid-header {{
            background-color: var(--primary-color);
            padding: 1.5rem;
            margin: -2rem -3rem 2rem -3rem;
            border-radius: 8px 8px 0 0;
        }}
        
        .solid-header h2 {{
            color: white;
            margin-bottom: 0;
        }}
        
        .minimal-header {{
            padding: 1.5rem;
            margin: -2rem -3rem 2rem -3rem;
            border-bottom: 3px solid var(--primary-color);
        }}
        
        .minimal-header h2 {{
            margin-bottom: 0;
        }}
        
        .no-header {{
            padding: 0;
            margin: 0 0 2rem 0;
        }}
        
        /* Content Styles */
        .content {{
            width: 100%;
            flex-grow: 1;
        }}
        
        .content ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        .content ul li {{
            position: relative;
            padding-left: 1.5rem;
            margin-bottom: 1rem;
            line-height: 1.5;
        }}
        
        .content ul li::before {{
            font-family: "Font Awesome 5 Free";
            font-weight: 900;
            content: "\\f111";  /* Default: circle */
            position: absolute;
            left: 0;
            color: var(--primary-color);
        }}
        
        /* Use the selected bullet style */
        .content ul li::before {{
            content: "\\f111";  /* Default: circle */
        }}
        
        .bullet-square .content ul li::before {{
            content: "\\f0c8";  /* Square */
        }}
        
        .bullet-dash .content ul li::before {{
            content: "\\f2d0";  /* Minus */
        }}
        
        .bullet-arrow .content ul li::before {{
            content: "\\f054";  /* Chevron right */
        }}
        
        /* Code styling */
        code {{
            font-family: var(--code-font, monospace);
            background-color: rgba(0,0,0,0.1);
            padding: 0.2rem 0.4rem;
            border-radius: 4px;
        }}
        
        pre {{
            background-color: rgba(0,0,0,0.1);
            padding: 1rem;
            border-radius: 4px;
            overflow-x: auto;
            width: 100%;
        }}
        
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        
        /* Images */
        .slide-image {{
            max-width: 100%;
            max-height: 300px;
            margin: 1rem 0;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            object-fit: contain;
        }}
        
        /* Slide number */
        .slide-number {{
            position: absolute;
            bottom: 1rem;
            right: 2rem;
            font-size: 0.9rem;
            opacity: 0.7;
        }}
        
        /* Media Queries */
        @media (max-width: 768px) {{
            .slide {{
                padding: 1.5rem 2rem;
            }}
            
            h1 {{
                font-size: 2.5rem;
            }}
            
            h2 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="external-nav">
        <a href="index.html" class="index-button"><i class="fas fa-th-large"></i> すべてのスライド</a>
        <div class="nav-info">スライド {slide_num}/{total_slides}</div>
    </div>

    <div class="slide {f'bullet-{bullet_style.replace("fa-", "")}' if bullet_style != 'fa-circle' else ''}">
"""
        
        # Add slide number
        html += f'<div class="slide-number">{slide_num}/{total_slides}</div>\n'
        
        # Add content based on slide type
        if slide_type == "title":
            # Title slide
            html += f"""    <div class="title-slide">
        <h1>{slide_title}</h1>
"""
            
            # Add subtitle if available
            if hasattr(slide, 'subtitle') and slide.subtitle:
                html += f'        <div class="subtitle">{slide.subtitle}</div>\n'
                
            # Add presenter name if available
            if hasattr(slide, 'presenter') and slide.presenter:
                html += f'        <div class="presenter">{slide.presenter}</div>\n'
                
            html += '    </div>\n'
            
        else:
            # Default content slide
            # Add header with title
            html += f"""    <div class="{header_style_class}">
        <h2>{slide_title}</h2>
    </div>
    
    <div class="content text-density-{'balanced' if not hasattr(theme, 'text_density') else theme.text_density}">
"""
            
            # Add content based on the format (list of bullets or HTML)
            if isinstance(slide_content, list):
                html += '        <ul>\n'
                for point in slide_content:
                    html += f'            <li>{point}</li>\n'
                html += '        </ul>\n'
            else:
                # Assume direct HTML content
                html += f'        {slide_content}\n'
                
            # Add image if available
            if hasattr(slide, 'image') and slide.image:
                html += f'        <img src="{slide.image}" alt="{slide_title}" class="slide-image">\n'
                
            html += '    </div>\n'
            
        # Close the slide div
        html += '</div>\n'
        
        # Add navigation links for prev/next
        if slide_num > 1:
            prev_link = f'slide{slide_num-1}.html'
            html += f'<div class="navigation">\n'
            html += f'    <a href="{prev_link}" class="nav-link prev-link">前へ</a>\n'
        else:
            html += f'<div class="navigation">\n'
            html += f'    <span class="nav-link disabled">前へ</span>\n'
            
        if slide_num < total_slides:
            next_link = f'slide{slide_num+1}.html'
            html += f'    <a href="{next_link}" class="nav-link next-link">次へ</a>\n'
        else:
            html += f'    <span class="nav-link disabled">次へ</span>\n'
            
        html += '</div>\n'
        
        # Close body and html tags
        html += """
<script>
    // Keyboard navigation
    document.addEventListener('keydown', function(event) {
        if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') {
            const prevLink = document.querySelector('.prev-link');
            if (prevLink && prevLink.href) {
                window.location.href = prevLink.href;
            }
        } else if (event.key === 'ArrowRight' || event.key === 'ArrowDown' || event.key === ' ') {
            const nextLink = document.querySelector('.next-link');
            if (nextLink && nextLink.href) {
                window.location.href = nextLink.href;
            }
        } else if (event.key === 'Escape') {
            window.location.href = 'index.html';
        }
    });
</script>
</body>
</html>
"""
        return html
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error creating HTML for slide {slide_num}: {str(e)}")
        return f"<div>Error creating slide {slide_num}: {str(e)}</div>"

def clean_markdown(text):
    """マークダウン形式のテキストをHTMLに適した形式に変換する"""
    if not text:
        return ""
    
    # コードブロックの変換
    text = re.sub(r'```(\w+)?\n(.*?)\n```', r'<pre><code>\2</code></pre>', text, flags=re.DOTALL)
    
    # インラインコードの変換
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    
    # 強調（ボールド）の変換
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__([^_]+)__', r'<strong>\1</strong>', text)
    
    # 強調（イタリック）の変換
    text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'_([^_]+)_', r'<em>\1</em>', text)
    
    # リンクの変換
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
    
    # 引用の変換
    text = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', text, flags=re.MULTILINE)
    
    # リストの変換 - 処理が複雑なのでシンプルな置換のみ
    text = re.sub(r'^- (.+)$', r'• \1', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\. (.+)$', r'• \1', text, flags=re.MULTILINE)
    
    # 段落の変換 - 複数の改行を段落として扱う
    text = re.sub(r'\n\n+', r'<br><br>', text)
    
    return text

import re  # 正規表現モジュールを追加 