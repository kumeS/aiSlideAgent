#!/usr/bin/env python3
"""
コマンドライン解析ユーティリティモジュール
"""

import argparse
import logging
import os

def parse_args():
    """コマンドライン引数をパースして返す"""
    parser = argparse.ArgumentParser(
        description="AI Slide Generator - AI技術を使用して高品質なプレゼンテーションスライドを自動生成",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
例:
  # 基本的なスライド生成
  python app.py generate "量子コンピューティング" --slides 5
  
  # 詳細検索を使用したスライド生成
  python app.py research "量子コンピューティング" --depth high --results 10
  
  # JSON形式の研究結果を元にスライド生成
  python app.py slides quantum_research.json --slides 8 --style modern
        """
    )
    
    # サブコマンドの設定
    subparsers = parser.add_subparsers(dest="command", help="実行するコマンド")
    
    # 'generate' コマンド - 一括処理でスライド生成
    generate_parser = subparsers.add_parser("generate", help="トピックからスライドを一括生成")
    generate_parser.add_argument("topic", help="プレゼンテーションのトピック")
    generate_parser.add_argument("--slides", type=int, default=5, help="生成するスライド数 (デフォルト: 5)")
    generate_parser.add_argument("--style", default="professional", 
                                choices=["default", "modern", "professional", "business", "minimal"], 
                                help="プレゼンテーションのスタイル (デフォルト: professional)")
    generate_parser.add_argument("--depth", default="low", 
                                choices=["low", "medium", "high"], 
                                help="検索の詳細度 (low=基本, medium=標準, high=詳細)")
    generate_parser.add_argument("--output", help="スライドのHTMLを保存するファイルパス (指定しない場合は自動生成)")
    generate_parser.add_argument("--orchestrator", action="store_true", help="オーケストレーターエージェントを使用")
    generate_parser.add_argument("--open", action="store_true", help="生成後にブラウザでスライドを開く")
    
    # 'research' コマンド - 検索のみを実行
    research_parser = subparsers.add_parser("research", help="トピックの検索を実行")
    research_parser.add_argument("topic", help="検索するトピック")
    research_parser.add_argument("--depth", default="low", 
                                choices=["low", "medium", "high"], 
                                help="検索の詳細度 (low=基本, medium=標準, high=詳細)")
    research_parser.add_argument("--results", type=int, default=5, help="取得する検索結果の数 (デフォルト: 5)")
    research_parser.add_argument("--output", help="検索結果をJSON形式で保存するファイルパス")
    research_parser.add_argument("--basic", action="store_true", help="基本的な検索のみを使用 (詳細検索を無効化)")
    research_parser.add_argument("--json", action="store_true", help="結果をJSON形式で出力")
    research_parser.add_argument("--store", help="データストアに検索結果を保存するためのキー")
    research_parser.add_argument("--store-file", help="検索結果を含むデータストアをJSONファイルに保存")
    research_parser.add_argument("--next-agent", choices=["outline", "template", "slides", "refine"], 
                                help="検索完了後に実行する次のエージェント")
    
    # 'outline' コマンド - アウトライン生成
    outline_parser = subparsers.add_parser("outline", help="検索結果からプレゼンテーションのアウトラインを生成")
    outline_parser.add_argument("--input", help="検索結果が含まれるJSONファイル")
    outline_parser.add_argument("--slides", type=int, default=5, help="生成するスライド数 (デフォルト: 5)")
    outline_parser.add_argument("--store-key", default="research_result", 
                                help="検索結果が保存されているデータストアキー (デフォルト: research_result)")
    outline_parser.add_argument("--output", help="アウトラインをJSON形式で保存するファイルパス")
    outline_parser.add_argument("--json", action="store_true", help="結果をJSON形式で出力")
    
    # 'slides' コマンド - 検索結果またはJSONからスライド生成
    slides_parser = subparsers.add_parser("slides", help="検索結果またはJSONファイルからスライドを生成")
    slides_parser.add_argument("input", nargs="?", help="検索結果またはアウトラインが含まれるJSONファイル")
    slides_parser.add_argument("--slides", type=int, default=5, help="生成するスライド数 (デフォルト: 5)")
    slides_parser.add_argument("--style", default="professional", 
                              choices=["default", "modern", "professional", "business", "minimal"], 
                              help="プレゼンテーションのスタイル (デフォルト: professional)")
    slides_parser.add_argument("--output", help="スライドのHTMLを保存するファイルパス (指定しない場合は自動生成)")
    slides_parser.add_argument("--open", action="store_true", help="生成後にブラウザでスライドを開く")
    
    # 'template' コマンド - テンプレート選択
    template_parser = subparsers.add_parser("template", help="アウトラインに基づいてテンプレートを選択")
    template_parser.add_argument("--topic", required=True, help="プレゼンテーションのトピック")
    template_parser.add_argument("--input", help="アウトラインが含まれるJSONファイル")
    template_parser.add_argument("--store-key", default="outline_result", 
                                help="アウトラインが保存されているデータストアキー (デフォルト: outline_result)")
    template_parser.add_argument("--json", action="store_true", help="結果をJSON形式で出力")
    
    # 'refine' コマンド - スライド洗練
    refine_parser = subparsers.add_parser("refine", help="生成されたスライドを洗練")
    refine_parser.add_argument("--input", required=True, help="スライドのHTMLファイル")
    refine_parser.add_argument("--output", help="洗練されたスライドのHTMLを保存するファイルパス")
    refine_parser.add_argument("--open", action="store_true", help="生成後にブラウザでスライドを開く")
    
    # 'help' コマンド - 使い方の表示
    help_parser = subparsers.add_parser("help", help="使い方の表示")
    
    # グローバルオプション
    parser.add_argument("--debug", action="store_true", help="デバッグログを有効化")
    parser.add_argument("--quiet", action="store_true", help="コンソール出力を最小化")
    parser.add_argument("--version", action="store_true", help="バージョン情報を表示して終了")
    
    args = parser.parse_args()
    
    # コマンドが指定されていない場合、helpを表示
    if not args.command and not args.version:
        parser.print_help()
        exit(0)
    
    # ログレベルの設定
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.quiet:
        logging.basicConfig(level=logging.WARNING)
    else:
        logging.basicConfig(level=logging.INFO)
    
    return args 