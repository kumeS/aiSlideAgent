#!/usr/bin/env python3
"""
AI Slide Generator - CLI App

This is the main entry point for the AI Slide Generator application.
It provides a command-line interface for generating and refining presentation slides.
"""

import os
import json
import logging
import time
import datetime
import webbrowser
from pathlib import Path
import sys

# 自作モジュールをインポート
from utils.data_store import agent_data_store
from utils.logging_setup import setup_logging
from utils.cli_utils import parse_args
from utils.slide_generator import generate_slides_cli, generate_slides_from_json
from utils.html_utils import clean_markdown

# For URL content summarization
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_command(args):
    """
    一括生成コマンドの処理
    """
    return generate_slides_cli(
        topic=args.topic,
        slide_count=args.slides,
        style=args.style,
        depth=args.depth,
        output_file=args.output,
        use_orchestrator=args.orchestrator
    )

def research_command(args):
    """
    検索コマンドの処理
    """
    # Set up logging
    log_file = setup_logging(args.topic)
    logger = logging.getLogger(__name__)
    
    try:
        # Start timer
        start_time = time.time()
        
        # Define line separator for readability
        separator_line = "──────────────────────────────────────────────────"
        print(separator_line)
        
        print(f"🔎 検索トピック: {args.topic}")
        print(f"🔍 検索詳細度: {args.depth}")
        print(f"🔢 検索結果数: {args.results}")
        print(separator_line)
        
        # Execute research based on depth
        if args.basic:
            from agents.research import search_basic
            research_results = search_basic(args.topic, args.results)
            
            # Display the results
            print("\n✅ 検索が完了しました:\n")
            
            if args.json:
                # Output as JSON
                print(json.dumps(research_results, ensure_ascii=False, indent=2))
            else:
                # Pretty print the results
                for i, result in enumerate(research_results, 1):
                    print(f"{i}. {result['title']}")
                    print(f"   ソース: {result['source']}")
                    print(f"   {result['summary'][:150]}...\n")
                    
            # Save to file if requested
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump({"topic": args.topic, "research_result": research_results}, f, ensure_ascii=False, indent=2)
                print(f"💾 検索結果をファイルに保存しました: {args.output}")
        else:
            from agents.research import search_deep
            research_result = search_deep(args.topic, args.depth)
            
            # Display the results
            print("\n✅ 検索が完了しました\n")
            
            if args.json:
                # Convert research_result to dictionary for JSON
                research_dict = {
                    "topic": research_result.topic,
                    "summary": research_result.summary,
                    "primary_results": [
                        {
                            "title": r.title,
                            "url": r.url,
                            "snippet": r.snippet
                        } for r in research_result.primary_results
                    ],
                    "secondary_results": [
                        {
                            "title": r.title,
                            "url": r.url,
                            "snippet": r.snippet
                        } for r in research_result.secondary_results
                    ],
                    "knowledge_gaps": research_result.knowledge_gaps
                }
                print(json.dumps(research_dict, ensure_ascii=False, indent=2))
            else:
                # Print summary
                print(f"📋 リサーチサマリー:")
                print(research_result.summary[:500] + "..." if len(research_result.summary) > 500 else research_result.summary)
                print("\n" + "─" * 50 + "\n")
                
                # Print top results
                print("📚 主要な情報源:")
                for i, result in enumerate(research_result.primary_results[:5], 1):
                    print(f"{i}. {result.title}")
                    print(f"   ソース: {result.url}")
                    print(f"   {result.snippet[:150]}...\n")
            
            # Save to file if requested
            if args.output:
                # Convert to serializable format
                research_dict = {
                    "topic": research_result.topic,
                    "summary": research_result.summary,
                    "primary_results": [
                        {
                            "title": r.title,
                            "url": r.url,
                            "snippet": r.snippet
                        } for r in research_result.primary_results
                    ],
                    "secondary_results": [
                        {
                            "title": r.title,
                            "url": r.url,
                            "snippet": r.snippet
                        } for r in research_result.secondary_results
                    ],
                    "knowledge_gaps": research_result.knowledge_gaps
                }
                
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump({"topic": args.topic, "research_result": research_dict}, f, ensure_ascii=False, indent=2)
                print(f"💾 検索結果をファイルに保存しました: {args.output}")
        
        # Store in data store if requested
        if args.store:
            # 検索結果をデータストアに保存
            agent_data_store.set(args.store, research_results if args.basic else research_result)
            print(f"\n🔄 検索結果をデータストアに保存しました (キー: {args.store})")
            
            # デバッグ情報を追加
            print(f"🔍 デバッグ情報 - データストアに保存したキー: {args.store}")
            data_size = len(str(research_results)) if args.basic else len(research_result.summary) + sum(len(r.snippet) for r in research_result.primary_results)
            print(f"🔍 デバッグ情報 - 保存したデータサイズ: 約{data_size} バイト")
            
            # データストアに保存
            if args.store_file:
                agent_data_store.save_to_file(args.store_file)
                print(f"\n💾 データストアをファイルに保存しました: {args.store_file}")
        
        # Calculate and display elapsed time
        elapsed = time.time() - start_time
        minutes, seconds = divmod(elapsed, 60)
        print(f"\n⏱️ 処理時間: {int(minutes)}分 {int(seconds)}秒")
        print(f"\n✅ 処理が完了しました")
        print(f"📄 詳細ログファイル: {log_file}")
        
        return research_results if args.basic else research_result
        
    except Exception as e:
        logger.error(f"Error in research command: {str(e)}", exc_info=True)
        print(f"\n❌ 検索中にエラーが発生しました: {str(e)}")
        return None

def slides_command(args):
    """
    slides コマンドの処理
    """
    if not args.input:
        print("❌ 入力ファイルが指定されていません。JSONファイルを指定してください。")
        print("例: python app.py slides research_results.json")
        return None
        
    return generate_slides_from_json(
        json_file=args.input,
        slide_count=args.slides,
        style=args.style,
        output_file=args.output,
        open_in_browser=args.open
    )

def outline_command(args):
    """
    outline コマンドの処理
    """
    # Set up logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Start timer
        start_time = time.time()
        
        # Define line separator for readability
        separator_line = "──────────────────────────────────────────────────"
        print(separator_line)
        
        print(f"📝 アウトライン生成")
        print(f"🔢 スライド数: {args.slides}")
        print(separator_line)
        
        # Get research data from file or data store
        research_data = None
        
        if args.input:
            print(f"📁 入力ファイル: {args.input}")
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Check if the data is already in the expected format
                if "research_result" in data:
                    research_data = data["research_result"]
                else:
                    research_data = data
        else:
            print(f"🔍 データストアから検索結果を取得中... (キー: {args.store_key})")
            research_data = agent_data_store.get(args.store_key)
            
        if not research_data:
            print(f"❌ データが見つかりません。入力ファイルまたはデータストアキーを確認してください。")
            return None
            
        # Generate outline
        print("\n📑 アウトラインを生成中です...")
        from agents.outline import generate_outline
        outline = generate_outline(research_data, args.slides)
        
        # Display the outline
        print("\n✅ アウトラインの生成が完了しました:")
        for i, section in enumerate(outline, 1):
            print(f"\n{i}. {section.title}")
            for point in section.points:
                print(f"   • {point}")
                
        # Save to file if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                # Convert outline to serializable format
                outline_data = []
                for section in outline:
                    outline_data.append({
                        "title": section.title,
                        "points": section.points
                    })
                    
                json.dump({"outline": outline_data}, f, ensure_ascii=False, indent=2)
            print(f"\n💾 アウトラインをファイルに保存しました: {args.output}")
            
        # Store in data store
        agent_data_store.set("outline_result", outline)
        print("\n🔄 アウトラインをデータストアに保存しました (キー: outline_result)")
        
        # Calculate and display elapsed time
        elapsed = time.time() - start_time
        minutes, seconds = divmod(elapsed, 60)
        print(f"\n⏱️ 処理時間: {int(minutes)}分 {int(seconds)}秒")
        print(f"\n✅ 処理が完了しました")
        print(f"📄 詳細ログファイル: {log_file}")
        
        return outline
        
    except Exception as e:
        logger.error(f"Error in outline command: {str(e)}", exc_info=True)
        print(f"\n❌ アウトライン生成中にエラーが発生しました: {str(e)}")
        return None

def template_command(args):
    """
    template コマンドの処理
    """
    # Set up logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Start timer
        start_time = time.time()
        
        # Define line separator for readability
        separator_line = "──────────────────────────────────────────────────"
        print(separator_line)
        
        print(f"🎨 テンプレート選択")
        print(f"📝 トピック: {args.topic}")
        print(separator_line)
        
        # Get outline data from file or data store
        outline = None
        
        if args.input:
            print(f"📁 入力ファイル: {args.input}")
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if "outline" in data:
                    # Convert to outline objects
                    from collections import namedtuple
                    Section = namedtuple('Section', ['title', 'points'])
                    
                    outline = []
                    for section in data["outline"]:
                        outline.append(Section(title=section["title"], points=section["points"]))
                else:
                    print(f"❌ 入力ファイルにアウトラインデータが見つかりません。")
                    return None
        else:
            print(f"🔍 データストアからアウトラインを取得中... (キー: {args.store_key})")
            outline = agent_data_store.get(args.store_key)
            
        if not outline:
            print(f"❌ アウトラインが見つかりません。入力ファイルまたはデータストアキーを確認してください。")
            return None
            
        # Select template
        print("\n🎨 プレゼンテーションテンプレートを選択中です...")
        from agents.template_selector import select_template_for_presentation
        template = select_template_for_presentation(args.topic, outline)
        
        # Display the template info
        print(f"\n✅ テンプレートの選択が完了しました:")
        print(f"   スタイル: {template.style}")
        print(f"   テーマカラー: {template.primary_color}, {template.secondary_color}")
        print(f"   フォント: {template.font_family}")
        
        # Store in data store
        agent_data_store.set("selected_template", template)
        print("\n🔄 テンプレートをデータストアに保存しました (キー: selected_template)")
        
        # Calculate and display elapsed time
        elapsed = time.time() - start_time
        minutes, seconds = divmod(elapsed, 60)
        print(f"\n⏱️ 処理時間: {int(minutes)}分 {int(seconds)}秒")
        print(f"\n✅ 処理が完了しました")
        print(f"📄 詳細ログファイル: {log_file}")
        
        return template
        
    except Exception as e:
        logger.error(f"Error in template command: {str(e)}", exc_info=True)
        print(f"\n❌ テンプレート選択中にエラーが発生しました: {str(e)}")
        return None

def refine_command(args):
    """
    refine コマンドの処理
    """
    # Set up logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Start timer
        start_time = time.time()
        
        # Define line separator for readability
        separator_line = "──────────────────────────────────────────────────"
        print(separator_line)
        
        print(f"🔍 スライド洗練")
        print(f"📄 入力ファイル: {args.input}")
        print(separator_line)
        
        # Check if input file exists
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"❌ 入力ファイルが見つかりません: {args.input}")
            return None
            
        # Read the input file
        with open(input_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Refine the slides
        print("\n🔍 スライドを洗練中です...")
        from agents.refiner import refine_presentation
        refined_html = refine_presentation(html_content)
        
        # Set up output path
        if args.output:
            output_path = Path(args.output)
        else:
            # Create a refined version in the same directory
            output_path = input_path.parent / f"refined_{input_path.name}"
            
        # Write the refined HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(refined_html)
            
        print(f"\n✅ スライドの洗練が完了しました")
        print(f"📄 洗練されたHTML: {output_path}")
        
        # Open in browser if requested
        browser_path = output_path.as_uri()
        if args.open:
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
        print(f"\n✅ 処理が完了しました")
        print(f"📄 詳細ログファイル: {log_file}")
        
        return refined_html
        
    except Exception as e:
        logger.error(f"Error in refine command: {str(e)}", exc_info=True)
        print(f"\n❌ スライド洗練中にエラーが発生しました: {str(e)}")
        return None

def process_next_agent(args):
    """
    次のエージェントを処理する
    """
    try:
        if args.next_agent == 'outline':
            # アウトライン生成エージェントを実行
            from collections import namedtuple
            OutlineArgs = namedtuple('OutlineArgs', ['input', 'slides', 'store_key', 'output'])
            outline_args = OutlineArgs(
                input=None,
                slides=5,
                store_key=args.store if args.store else "research_result",
                output=args.store_file if args.store_file else None
            )
            return outline_command(outline_args)
            
        elif args.next_agent == 'template':
            # テンプレート選択エージェントを実行
            from collections import namedtuple
            TemplateArgs = namedtuple('TemplateArgs', ['topic', 'input', 'store_key'])
            template_args = TemplateArgs(
                topic=args.topic,
                input=None,
                store_key="outline_result"
            )
            return template_command(template_args)
        
        return None
    except Exception as e:
        logging.getLogger(__name__).error(f"Error processing next agent: {str(e)}")
        print(f"\n❌ 次のエージェント処理中にエラーが発生しました: {str(e)}")
        return None

def main():
    """
    メイン関数
    """
    try:
        # コマンドライン引数を解析
        args = parse_args()
        
        # バージョン表示
        if args.version:
            print("AI Slide Generator v1.0.0")
            return
            
        # コマンドに基づいて処理を振り分け
        if args.command == "generate":
            result = generate_command(args)
        elif args.command == "research":
            result = research_command(args)
            
            # 次のエージェントがある場合は実行
            if args.next_agent:
                process_next_agent(args)
                
        elif args.command == "slides":
            result = slides_command(args)
        elif args.command == "outline":
            result = outline_command(args)
        elif args.command == "template":
            result = template_command(args)
        elif args.command == "refine":
            result = refine_command(args)
        elif args.command == "help" or not args.command:
            # ヘルプを表示して終了
            return
        else:
            print(f"❌ 不明なコマンド: {args.command}")
            return
    except Exception as e:
        logging.getLogger(__name__).error(f"Error in main: {str(e)}")
        print(f"\n❌ プログラム実行中にエラーが発生しました: {str(e)}")
        return

if __name__ == "__main__":
    main()
