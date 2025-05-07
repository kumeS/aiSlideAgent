"""
Monitoring and Orchestration Agents

This package provides monitoring and orchestration agents for the slide generation process.
"""

from .monitoring import MonitoringAgent, monitor_research_and_outline, monitor_slides_and_refine as _original_monitor_slides
from .orchestrator import OrchestratorAgent, orchestrate_slide_generation

__all__ = [
    "MonitoringAgent",
    "monitor_research_and_outline",
    "monitor_slides_and_refine",
    "OrchestratorAgent",
    "orchestrate_slide_generation"
]

def monitor_slides_and_refine(outline, theme, max_iterations=2):
    """
    Coordinate the slide generation and refinement process with monitoring.
    
    Args:
        outline: The outline to use for slide generation
        theme: The slide theme to use
        max_iterations: Maximum number of refinement iterations
        
    Returns:
        Tuple of (refined_html, qa_report)
    """
    print("\n🔄 スライド生成と改善プロセス:")
    print("  1. アウトラインを基にスライドのHTMLを生成")
    print("  2. 各スライド毎にテンプレートを適用 (全スライドで同じテーマを使用)")
    print("  3. スライドごとに個別HTMLを生成後、1つのHTMLドキュメントに統合")
    print("  4. スライド改善エージェントにより内容とデザインを評価・改良")
    
    # オリジナルの関数を呼び出す
    refined_html, qa_report = _original_monitor_slides(outline, theme)
    
    print("\n✅ スライド改善プロセスが完了しました")
    print(f"  最終出力: 単一のHTML文書 ({len(refined_html) // 1024}KB)")
    
    return refined_html, qa_report 