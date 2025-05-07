#!/usr/bin/env python3
"""
エージェント間でデータを共有するためのデータストアモジュール
"""

import json
import logging
from typing import Any

class AgentDataStore:
    """エージェント間でデータを共有するためのグローバルデータストア"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentDataStore, cls).__new__(cls)
            cls._instance._data = {}
        return cls._instance
    
    def set(self, key: str, value: Any) -> None:
        """データを保存"""
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """データを取得"""
        return self._data.get(key, default)
    
    def clear(self) -> None:
        """全てのデータをクリア"""
        self._data.clear()
    
    def save_to_file(self, file_path: str) -> None:
        """データをJSONファイルに保存"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.getLogger(__name__).error(f"データの保存に失敗しました: {str(e)}")
    
    def load_from_file(self, file_path: str) -> bool:
        """JSONファイルからデータを読み込み"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            return True
        except Exception as e:
            logging.getLogger(__name__).error(f"データの読み込みに失敗しました: {str(e)}")
            return False

# グローバルデータストアのインスタンスを作成
agent_data_store = AgentDataStore() 