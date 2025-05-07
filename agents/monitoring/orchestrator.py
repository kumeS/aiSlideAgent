"""
Orchestrator Agent Implementation

This module provides a central orchestration agent that coordinates 
the entire slide generation process, analyzing outputs from each agent
and directing the flow to the next appropriate agent.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union

from agents import client, DEFAULT_MODEL
from agents.research import ResearchAgent, ResearchResult, search_deep
from agents.outline import OutlineAgent, SlideDeck, generate_outline
from agents.slide_writer import SlideWriterAgent, SlideDeckHTML, SlideTheme, generate_slides
from agents.refiner import RefinerAgent, refine_presentation
from agents.template_selector import select_template_for_presentation
from agents.monitoring.monitoring import MonitoringAgent

# Configure logging
logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """
    OrchestratorAgent is the central coordinator (司令塔) for the entire
    slide generation process. It:
    
    1. Analyzes the input requirements
    2. Directs the research process and evaluates results
    3. Oversees outline generation and ensures quality
    4. Coordinates template selection based on topic and outline
    5. Manages slide generation and refinement iterations
    6. Makes adaptive decisions based on intermediate results
    7. Provides detailed process reports
    """
    
    def __init__(self, model: str = DEFAULT_MODEL, verbose: bool = True):
        self.model = model
        self.verbose = verbose
        self.monitoring_agent = MonitoringAgent(model=model)
        self.process_log = []
        self.start_time = None
        
    def log_step(self, step: str, status: str, details: Optional[Dict] = None):
        """Record a process step in the internal log"""
        timestamp = time.time()
        log_entry = {
            "timestamp": timestamp,
            "step": step,
            "status": status,
            "details": details or {}
        }
        self.process_log.append(log_entry)
        
        if self.verbose:
            elapsed = "N/A"
            if self.start_time:
                elapsed_sec = timestamp - self.start_time
                minutes, seconds = divmod(elapsed_sec, 60)
                elapsed = f"{int(minutes)}分 {int(seconds)}秒"
                
            if status == "start":
                logger.info(f"🔄 開始: {step} ({elapsed})")
            elif status == "complete":
                logger.info(f"✅ 完了: {step} ({elapsed})")
            elif status == "error":
                logger.error(f"❌ エラー: {step} - {details.get('error', 'Unknown error')} ({elapsed})")
            else:
                logger.info(f"ℹ️ {status}: {step} ({elapsed})")
    
    def analyze_requirements(self, topic: str, slide_count: int, depth: str, style: str) -> Dict:
        """
        Analyze the input requirements to determine the best approach
        for generating the slides.
        """
        self.log_step("要件分析", "start")
        
        # Use the AI to determine the complexity and knowledge requirements
        try:
            prompt = f"""
            分析対象のスライド生成要件:
            トピック: {topic}
            スライド枚数: {slide_count}枚
            検索深度: {depth}
            スタイル: {style}
            
            この要件に基づき、以下を分析してください:
            1. トピックの複雑さ (1-10のスケール)
            2. 必要な専門知識レベル (1-10のスケール)
            3. 視覚的要素の重要性 (1-10のスケール)
            4. 推奨される検索深度（与えられた深度と異なる場合）
            5. 推奨されるスライド枚数（与えられた枚数と異なる場合）
            6. 特に注意すべき点（箇条書きで3つまで）
            
            JSON形式で回答してください:
            {{
              "complexity": 5,
              "expertise_needed": 5,
              "visual_importance": 5,
              "recommended_depth": "medium",
              "recommended_slide_count": 5,
              "special_considerations": ["考慮点1", "考慮点2", "考慮点3"]
            }}
            """
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "あなたはプレゼンテーション分析の専門家です。JSONのみで回答してください。"},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            import json
            analysis = json.loads(response.choices[0].message.content)
            
            # Log completion
            self.log_step("要件分析", "complete", analysis)
            return analysis
            
        except Exception as e:
            error_details = {"error": str(e)}
            self.log_step("要件分析", "error", error_details)
            # Return defaults if AI analysis fails
            return {
                "complexity": 5,
                "expertise_needed": 5,
                "visual_importance": 5,
                "recommended_depth": depth,
                "recommended_slide_count": slide_count,
                "special_considerations": []
            }
    
    def execute_research(self, topic: str, depth: str, requirements: Dict) -> Tuple[ResearchResult, bool]:
        """
        Execute and evaluate the research process.
        
        Returns:
            Tuple of (research_result, success_flag)
        """
        self.log_step("リサーチ実行", "start", {"topic": topic, "depth": depth})
        
        try:
            # 要件に基づいて深度を調整
            adjusted_depth = depth
            if requirements["complexity"] > 7 and depth == "low":
                logger.info("⚠️ トピックの複雑さが高いため深度を調整します: low → medium")
                adjusted_depth = "medium"
            elif requirements["complexity"] < 4 and depth == "high":
                logger.info("⚠️ トピックの複雑さが低いため深度を調整します: high → medium")
                adjusted_depth = "medium"
                
            # リサーチエージェントの初期化
            research_agent = ResearchAgent()
            
            # リサーチ実行
            research_result = research_agent.search_deep(topic, adjusted_depth)
            
            # リサーチの充実度を評価
            metrics = {
                "primary_results_count": len(research_result.primary_results),
                "secondary_results_count": len(research_result.secondary_results),
                "knowledge_gaps_count": len(research_result.knowledge_gaps),
                "summary_length": len(research_result.summary) if research_result.summary else 0
            }
            
            # 評価基準
            min_primary = 3
            min_summary_length = 500
            
            # 成功判定
            success = (metrics["primary_results_count"] >= min_primary and 
                      metrics["summary_length"] >= min_summary_length)
            
            self.log_step("リサーチ実行", "complete", {
                "metrics": metrics,
                "success": success,
                "adjusted_depth": adjusted_depth
            })
            
            return research_result, success
            
        except Exception as e:
            error_details = {"error": str(e)}
            self.log_step("リサーチ実行", "error", error_details)
            raise
    
    def generate_and_evaluate_outline(self, research_result: ResearchResult, slide_count: int, requirements: Dict) -> Tuple[SlideDeck, bool]:
        """
        Generate and evaluate an outline based on research results.
        
        Returns:
            Tuple of (outline, success_flag)
        """
        self.log_step("アウトライン生成", "start", {"slide_count": slide_count})
        
        try:
            # 要件に基づいてスライド数を調整
            adjusted_slide_count = slide_count
            if requirements.get("recommended_slide_count") and abs(requirements["recommended_slide_count"] - slide_count) <= 2:
                adjusted_slide_count = requirements["recommended_slide_count"]
                if adjusted_slide_count != slide_count:
                    logger.info(f"⚠️ 要件に基づきスライド数を調整します: {slide_count} → {adjusted_slide_count}")
            
            # アウトライン生成
            outline_agent = OutlineAgent()
            outline = outline_agent.generate_outline(research_result, adjusted_slide_count)
            
            # アウトラインの質を評価
            metrics = {
                "slide_count": len(outline.slides),
                "total_content_length": sum(len("".join(slide.content)) for slide in outline.slides),
                "has_title_slide": any(slide.type == "title" for slide in outline.slides),
                "has_conclusion": any("conclusion" in slide.title.lower() for slide in outline.slides)
            }
            
            # 評価基準
            success = (metrics["slide_count"] >= adjusted_slide_count * 0.8 and 
                      metrics["has_title_slide"] and
                      metrics["has_conclusion"])
            
            self.log_step("アウトライン生成", "complete", {
                "metrics": metrics,
                "success": success,
                "adjusted_slide_count": adjusted_slide_count
            })
            
            return outline, success
            
        except Exception as e:
            error_details = {"error": str(e)}
            self.log_step("アウトライン生成", "error", error_details)
            raise
    
    def select_appropriate_template(self, topic: str, outline: SlideDeck, style: str, requirements: Dict) -> SlideTheme:
        """
        Select the most appropriate template based on topic, outline and style.
        """
        self.log_step("テンプレート選択", "start", {"style": style})
        
        try:
            # 視覚的要素の重要性が高い場合は特定のスタイルを優先
            adjusted_style = style
            if requirements["visual_importance"] > 7 and style == "professional":
                logger.info("⚠️ 視覚的要素の重要性が高いためスタイルを調整します: professional → modern")
                adjusted_style = "modern"
            
            # テンプレート選択
            slide_theme = select_template_for_presentation(topic, outline, adjusted_style)
            
            self.log_step("テンプレート選択", "complete", {
                "selected_theme": slide_theme.name,
                "adjusted_style": adjusted_style
            })
            
            return slide_theme
            
        except Exception as e:
            error_details = {"error": str(e)}
            self.log_step("テンプレート選択", "error", error_details)
            raise
    
    def generate_and_refine_slides(self, outline: SlideDeck, theme: SlideTheme, style: str, requirements: Dict) -> Tuple[str, Dict]:
        """
        Generate slides and iteratively refine them.
        
        Returns:
            Tuple of (html_content, qa_report)
        """
        self.log_step("スライド生成と改善", "start")
        
        try:
            # モニタリングエージェントを使用してスライド生成と改善のプロセスを実行
            iterations = 2
            if requirements["complexity"] > 7 or requirements["expertise_needed"] > 7:
                iterations = 3  # 複雑なトピックには追加の改善サイクル
            
            refined_html, qa_report = self.monitoring_agent.coordinate_slides_and_refiner(outline, theme)
            
            # QAレポートに基づいて成功判定
            success = qa_report.get("overall_score", 0) >= 7.0
            
            self.log_step("スライド生成と改善", "complete", {
                "qa_score": qa_report.get("overall_score", 0),
                "success": success,
                "iterations": iterations
            })
            
            return refined_html, qa_report
            
        except Exception as e:
            error_details = {"error": str(e)}
            self.log_step("スライド生成と改善", "error", error_details)
            raise
    
    def orchestrate_slide_generation(self, topic: str, slide_count: int = 5, 
                                   style: str = "professional", depth: str = "low") -> Tuple[str, Dict]:
        """
        Orchestrate the entire slide generation process from start to finish.
        
        Args:
            topic: The presentation topic
            slide_count: Number of slides to generate
            style: Presentation style
            depth: Research depth (low/medium/high)
            
        Returns:
            Tuple of (html_content, process_report)
        """
        # 開始時間の記録
        self.start_time = time.time()
        self.process_log = []
        
        logger.info(f"🚀 司令塔エージェント: 「{topic}」のスライド生成プロセスを開始します")
        logger.info(f"📊 パラメータ: {slide_count}枚 / スタイル:{style} / 深度:{depth}")
        
        try:
            # 1. 要件を分析
            requirements = self.analyze_requirements(topic, slide_count, depth, style)
            
            # 2. リサーチを実行
            research_result, research_success = self.execute_research(topic, depth, requirements)
            
            if not research_success:
                logger.warning("⚠️ リサーチ結果が不十分ですが、続行します")
            
            # 3. アウトラインを生成・評価
            outline, outline_success = self.generate_and_evaluate_outline(research_result, slide_count, requirements)
            
            if not outline_success:
                logger.warning("⚠️ アウトラインの質が理想的ではありませんが、続行します")
                
            # 4. 適切なテンプレートを選択
            slide_theme = self.select_appropriate_template(topic, outline, style, requirements)
            
            # 5. スライドを生成して改善
            html_content, qa_report = self.generate_and_refine_slides(outline, slide_theme, style, requirements)
            
            # 6. プロセスレポートの生成
            end_time = time.time()
            elapsed_time = end_time - self.start_time
            minutes, seconds = divmod(elapsed_time, 60)
            
            process_report = {
                "topic": topic,
                "parameters": {
                    "slide_count": slide_count,
                    "style": style,
                    "depth": depth
                },
                "requirements_analysis": requirements,
                "process_log": self.process_log,
                "qa_report": qa_report,
                "timing": {
                    "start_time": self.start_time,
                    "end_time": end_time,
                    "elapsed_seconds": elapsed_time,
                    "elapsed_friendly": f"{int(minutes)}分 {int(seconds)}秒"
                }
            }
            
            logger.info(f"✅ 司令塔エージェント: スライド生成プロセスが完了しました ({int(minutes)}分 {int(seconds)}秒)")
            
            return html_content, process_report
            
        except Exception as e:
            error_message = f"スライド生成プロセスでエラーが発生しました: {str(e)}"
            logger.error(f"❌ 司令塔エージェント: {error_message}")
            
            # エラー時も最低限のレポートを生成
            end_time = time.time()
            elapsed_time = end_time - self.start_time
            minutes, seconds = divmod(elapsed_time, 60)
            
            error_report = {
                "topic": topic,
                "parameters": {
                    "slide_count": slide_count,
                    "style": style,
                    "depth": depth
                },
                "error": str(e),
                "process_log": self.process_log,
                "timing": {
                    "start_time": self.start_time,
                    "end_time": end_time,
                    "elapsed_seconds": elapsed_time,
                    "elapsed_friendly": f"{int(minutes)}分 {int(seconds)}秒"
                }
            }
            
            # エラーを再スロー
            raise Exception(error_message)

# モジュールレベルの関数として公開
def orchestrate_slide_generation(topic: str, slide_count: int = 5, 
                              style: str = "professional", depth: str = "low") -> Tuple[str, Dict]:
    """
    Orchestrate the slide generation process using the orchestrator agent.
    
    Args:
        topic: The presentation topic
        slide_count: Number of slides to generate
        style: Presentation style
        depth: Research depth (low/medium/high)
        
    Returns:
        Tuple of (html_content, process_report)
    """
    orchestrator = OrchestratorAgent()
    return orchestrator.orchestrate_slide_generation(topic, slide_count, style, depth)