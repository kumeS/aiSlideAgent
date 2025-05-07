"""
Template Selector Agent

プレゼンテーション内容を分析し、最適なテンプレートを選択するエージェント
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field
import re

from agents import client, DEFAULT_MODEL
from agents.outline import SlideDeck, SlideContent
from agents.slide_writer import SlideTheme

# Configure logging - ロギング設定は agents/__init__.py に集約
logger = logging.getLogger(__name__)

# Constants
TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

class TemplateMetadata(BaseModel):
    """テンプレートのメタデータモデル"""
    name: str
    description: str
    keywords: List[str] = Field(default_factory=list)
    suitable_for: List[str] = Field(default_factory=list)
    preview_image: Optional[str] = None
    
class TemplateSelectionResult(BaseModel):
    """テンプレート選択結果モデル"""
    template_name: str
    rationale: str
    customization: Dict[str, Any] = Field(default_factory=dict)
    theme_recommendations: Dict[str, Any] = Field(default_factory=dict)

class TemplateSelectorAgent:
    """プレゼンテーション内容を分析し、最適なテンプレートを選択するエージェント"""
    
    def __init__(self, model: Optional[str] = None, templates_dir: Optional[Path] = None):
        """
        Initialize the template selector agent with configuration.
        
        Args:
            model: OpenAI model to use for content analysis
            templates_dir: Directory containing the templates
        """
        self.model = model or DEFAULT_MODEL
        self.templates_dir = templates_dir or TEMPLATES_DIR
        self.available_templates = self._scan_templates()
        
    def _scan_templates(self) -> Dict[str, TemplateMetadata]:
        """利用可能なテンプレートをスキャンしてメタデータを読み込む"""
        templates = {}
        themes_dir = self.templates_dir / "themes"
        
        if not themes_dir.exists():
            logger.warning(f"テーマディレクトリが見つかりません: {themes_dir}")
            # 基本テンプレート情報をハードコード
            templates = {
                "professional": TemplateMetadata(
                    name="Professional",
                    description="ビジネス向けのプロフェッショナルなデザイン。会議や企業プレゼンテーションに最適。",
                    keywords=["ビジネス", "フォーマル", "企業", "会議"],
                    suitable_for=["business", "corporate", "meeting", "proposal"]
                ),
                "minimal": TemplateMetadata(
                    name="Minimal",
                    description="シンプルで洗練されたミニマルなデザイン。文字が主体で内容を重視したいプレゼンに最適。",
                    keywords=["シンプル", "ミニマル", "クリーン", "テキスト重視"],
                    suitable_for=["academic", "report", "documentation"]
                ),
                "modern": TemplateMetadata(
                    name="Modern",
                    description="現代的なデザインで視覚的なインパクトを重視。様々なレイアウトオプションを備えています。",
                    keywords=["モダン", "スタイリッシュ", "視覚的", "多機能"],
                    suitable_for=["marketing", "product", "creative", "overview"]
                ),
                "business": TemplateMetadata(
                    name="Business",
                    description="ビジネス情報を構造化して表示。プロフィールや時系列データの表示に強みがあります。",
                    keywords=["ビジネス", "プロフィール", "タイムライン", "情報整理"],
                    suitable_for=["profile", "timeline", "organization", "structure"]
                )
            }
            return templates
        
        # テーマディレクトリ内のHTMLファイル（テンプレート）をスキャン
        for template_file in themes_dir.glob("*.html"):
            template_name = template_file.stem
            
            # メタデータファイルが存在すればそこから読み込む
            metadata_file = themes_dir / f"{template_name}.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata = json.load(f)
                    templates[template_name] = TemplateMetadata(**metadata)
                except Exception as e:
                    logger.warning(f"メタデータファイルの読み込みに失敗: {e}")
                    # 基本情報のみ設定
                    templates[template_name] = TemplateMetadata(
                        name=template_name.capitalize(),
                        description=f"{template_name.capitalize()} template"
                    )
            else:
                # メタデータファイルがない場合はHTMLからキーワードを抽出
                try:
                    with open(template_file, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    
                    # ファイル名から基本的な名前を設定
                    formatted_name = template_name.replace("-", " ").replace("_", " ").capitalize()
                    
                    # HTMLコメントからキーワードを抽出
                    keywords = []
                    description = formatted_name
                    
                    # キーワードやデスクリプションをコメントから抽出
                    comment_regex = r"<!--\s*(.*?)\s*-->"
                    comments = re.findall(comment_regex, html_content)
                    for comment in comments:
                        if "keywords:" in comment.lower():
                            kw_text = comment.lower().split("keywords:")[1].strip()
                            keywords = [k.strip() for k in kw_text.split(",")]
                        if "description:" in comment.lower():
                            description = comment.split("description:")[1].strip()
                    
                    templates[template_name] = TemplateMetadata(
                        name=formatted_name,
                        description=description,
                        keywords=keywords
                    )
                except Exception as e:
                    logger.warning(f"テンプレートファイルの読み込みに失敗: {e}")
                    # エラー時は基本情報のみ設定
                    templates[template_name] = TemplateMetadata(
                        name=template_name.capitalize(),
                        description=f"{template_name.capitalize()} template"
                    )
        
        # 既存テンプレートがない場合はデフォルトのテンプレート情報を返す
        if not templates:
            templates = {
                "professional": TemplateMetadata(
                    name="Professional",
                    description="ビジネス向けのプロフェッショナルなデザイン",
                    keywords=["ビジネス", "フォーマル", "企業"]
                ),
                "minimal": TemplateMetadata(
                    name="Minimal",
                    description="シンプルで洗練されたミニマルなデザイン",
                    keywords=["シンプル", "ミニマル", "クリーン"]
                ),
                "modern": TemplateMetadata(
                    name="Modern",
                    description="現代的なデザインで視覚的にインパクトのある構成",
                    keywords=["モダン", "スタイリッシュ", "視覚的"]
                )
            }
            
        logger.debug(f"利用可能なテンプレート: {', '.join(templates.keys())}")
        return templates
    
    def analyze_content(self, topic: str, slide_deck: SlideDeck) -> str:
        """スライド内容を分析してサマリーを作成"""
        # スライドタイプ、キーワード、画像の有無などを抽出
        content_types = [slide.type for slide in slide_deck.slides]
        titles = [slide.title for slide in slide_deck.slides]
        
        # 重要キーワードを抽出
        all_content = ' '.join([' '.join(slide.content) for slide in slide_deck.slides])
        
        # 文字数制限（最大1000文字）
        truncated_content = all_content[:1000] + ("..." if len(all_content) > 1000 else "")
        
        prompt = f"""
        次のプレゼンテーション内容を分析し、5行以内で要約してください。
        トピック: {topic}
        タイトル: {titles[0] if titles else ""}
        スライドタイプ: {', '.join(content_types)}
        内容: {truncated_content}
        """
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                max_tokens=200
            )
            logger.info("📊 プレゼンテーション内容を分析しました")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"❌ 内容分析でエラー: {e}")
            return f"プレゼンテーション「{topic}」には {len(slide_deck.slides)} スライドがあります。"
    
    def select_template(self, topic: str, slide_deck: SlideDeck, style: str = "professional") -> TemplateSelectionResult:
        """
        プレゼンテーション内容を分析して最適なテンプレートを選択
        
        Args:
            topic: プレゼンテーションのトピック
            slide_deck: スライドデッキの内容
            style: テンプレートのスタイル
            
        Returns:
            TemplateSelectionResult オブジェクト
        """
        # AIによる内容分析
        content_summary = self.analyze_content(topic, slide_deck)
        
        # スライドの種類を集計
        slide_types = {}
        for slide in slide_deck.slides:
            slide_type = slide.type.lower()
            slide_types[slide_type] = slide_types.get(slide_type, 0) + 1
        
        # 特定のキーワードがあるか確認
        keywords_present = []
        all_text = topic + " " + " ".join([slide.title for slide in slide_deck.slides]) + " " + " ".join([" ".join(slide.content) for slide in slide_deck.slides])
        all_text = all_text.lower()
        
        # 重要なキーワードのリスト
        keyword_categories = {
            "business": ["ビジネス", "会社", "企業", "戦略", "マーケット", "顧客", "提案", "営業", "business", "company", "corporate", "strategy", "market", "client", "proposal", "sales"],
            "academic": ["リサーチ", "学術", "論文", "分析", "調査", "結果", "考察", "research", "academic", "paper", "analysis", "study", "results", "discussion"],
            "technical": ["技術", "エンジニアリング", "システム", "開発", "コード", "アーキテクチャ", "technical", "engineering", "system", "development", "code", "architecture"],
            "creative": ["クリエイティブ", "デザイン", "アート", "創造", "表現", "creative", "design", "art", "creation", "expression"],
            "profile": ["プロフィール", "経歴", "人物", "履歴", "キャリア", "profile", "biography", "person", "history", "career"],
            "timeline": ["タイムライン", "歴史", "経過", "変遷", "過程", "timeline", "history", "progress", "transition", "process"]
        }
        
        for category, words in keyword_categories.items():
            for word in words:
                if word in all_text:
                    keywords_present.append(category)
                    break
        
        # 利用可能なテンプレート情報を整形
        template_info = "\n".join([
            f"- {name}: {metadata.description}" 
            for name, metadata in self.available_templates.items()
        ])
        
        # プロンプト作成
        prompt = f"""
        あなたはプレゼンテーションデザインの専門家です。以下の内容に最適なテンプレートを選んでください。
        
        トピック: {topic}
        スタイル: {style}
        内容サマリー: {content_summary}
        スライドタイプ別数: {slide_types}
        検出されたキーワードカテゴリ: {keywords_present}
        
        利用可能なテンプレート:
        {template_info}
        
        最も適したテンプレートを1つ選び、その理由とカスタマイズ提案を含めて回答してください。
        JSONフォーマットで回答してください:
        {{
            "template_name": "テンプレート名",
            "rationale": "選んだ理由の説明",
            "customization": {{
                "primary_color": "推奨カラー（任意）",
                "secondary_color": "推奨カラー（任意）",
                "font_family": "推奨フォント（任意）"
            }},
            "theme_recommendations": {{
                "is_dark_theme": true/false,
                "use_gradients": true/false
            }}
        }}
        """
        
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"}
            )
            
            result_json = response.choices[0].message.content
            result = json.loads(result_json)
            
            # 結果をモデルに変換
            template_result = TemplateSelectionResult(
                template_name=result["template_name"],
                rationale=result["rationale"],
                customization=result.get("customization", {}),
                theme_recommendations=result.get("theme_recommendations", {})
            )
            
            logger.info(f"🎨 テンプレート選択: {template_result.template_name} ({template_result.rationale[:30]}...)")
            return template_result
            
        except Exception as e:
            logger.error(f"❌ テンプレート選択中にエラー: {e}")
            # デフォルトのテンプレートを返す
            return TemplateSelectionResult(
                template_name="professional",
                rationale="エラーが発生したため、デフォルトのプロフェッショナルテンプレートを選択しました。"
            )
    
    def create_theme_from_selection(self, selection_result: TemplateSelectionResult) -> SlideTheme:
        """テンプレート選択結果からSlideThemeオブジェクトを作成"""
        
        # テンプレート名を大文字始まりに変換
        theme_name = selection_result.template_name.capitalize()
        
        # カスタマイズ情報を取得
        customization = selection_result.customization
        theme_recommendations = selection_result.theme_recommendations
        
        # デフォルト値
        primary_color = "#3498db"  # Blue
        secondary_color = "#2ecc71"  # Green
        text_color = "#F9FAFB"  # Light
        background_color = "#111827"  # Dark
        
        # ダークテーマかライトテーマか
        is_dark = theme_recommendations.get("is_dark_theme", True)
        if not is_dark:
            # ライトテーマの場合は色を反転
            text_color = "#111827"  # Dark text
            background_color = "#F9FAFB"  # Light background
        
        # カスタマイズ情報があれば上書き
        if "primary_color" in customization:
            primary_color = customization["primary_color"]
        if "secondary_color" in customization:
            secondary_color = customization["secondary_color"]
        if "text_color" in customization:
            text_color = customization["text_color"]
        if "background_color" in customization:
            background_color = customization["background_color"]
            
        # フォント情報
        font_family = customization.get("font_family", "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif")
        
        # テーマオブジェクトを作成
        theme = SlideTheme(
            name=theme_name,
            primary_color=primary_color,
            secondary_color=secondary_color,
            text_color=text_color,
            background_color=background_color,
            font_family=font_family
        )
        
        return theme

    # --- Flow2 enhancement ---
    def score(self, template: Any, slide_deck: SlideDeck) -> float:
        """Return suitability score (0.0-1.0) of a template for given slide deck.

        For now implements simple heuristics: penalize if slide count exceeds hard-coded max_text_count.
        Later can be replaced by ML model."""

        # Example heuristic: compare total bullet points vs template's capacity
        max_points_per_slide = getattr(template, "max_points", 6)
        total_points = sum(len(slide.content) for slide in slide_deck.slides if slide.content)
        capacity = max_points_per_slide * len(slide_deck.slides)

        score = min(1.0, total_points / capacity) if capacity else 0.0

        # Add weighting for image slides
        image_slides = sum(1 for s in slide_deck.slides if s.type == "image")
        if image_slides and hasattr(template, "supports_images") and not template.supports_images:
            score *= 0.5  # penalize
        return score

def select_template_for_presentation(topic: str, slide_deck: SlideDeck, style: str = "professional") -> SlideTheme:
    """
    プレゼンテーションに最適なテンプレートを選択し、テーマを作成
    
    Args:
        topic: プレゼンテーションのトピック
        slide_deck: スライドデッキの内容
        style: テンプレートのスタイル
        
    Returns:
        SlideThemeオブジェクト
    """
    agent = TemplateSelectorAgent()
    selection_result = agent.select_template(topic, slide_deck, style)
    theme = agent.create_theme_from_selection(selection_result)
    return theme 