#!/usr/bin/env python3
"""
ロギング設定モジュール
"""

import logging
import datetime
from pathlib import Path
import os
import sys

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

def setup_logging(topic=None):
    """
    ロギングの設定を行う関数
    """
    # ログディレクトリがなければ作成
    os.makedirs("logs", exist_ok=True)
    
    # 現在時刻をログファイル名に含める
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if topic:
        # Sanitize topic for filename
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)
        safe_topic = safe_topic[:30]  # Limit length
        log_filename = f"{timestamp}_{safe_topic}.log"
    else:
        log_filename = f"{timestamp}_ai_slide_generator.log"
    
    log_file = logs_dir / log_filename
    
    # 既存のハンドラがあれば削除（再設定時の重複を防止）
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # ファイルハンドラ - すべてのログを記録
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    # コンソールハンドラ - 警告以上のみ表示
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    # ルートロガーの設定
    logging.basicConfig(
        level=logging.INFO,  # INFOレベル以上を記録
        handlers=[file_handler, console_handler]
    )
    
    # 他ライブラリのロギングレベルを調整
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    # アプリケーション固有のロガーはINFOレベルで
    logging.getLogger("agents").setLevel(logging.INFO)
    
    return log_file 