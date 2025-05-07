# AI Slide Generator

OpenAI APIとエージェントSDKを活用した、自動プレゼンテーションスライド生成ツール

## 概要

AI Slide Generatorは、OpenAI API（GPT-4o）と OpenAI Agents SDKを使用して任意のトピックに関するプレゼンテーションスライドを自動生成するコマンドラインツールです。トピックを入力するだけで、AIがリサーチを行い、アウトラインを作成し、視覚的に美しいHTMLスライドを生成します。

主な機能：
- トピックに関する情報を自動的にリサーチ（複数ソースから情報収集）
- 論理的なアウトラインの作成とスライド構造設計
- トピックに適したテンプレート・デザインの自動選択
- Reveal.js/Tailwindベースの高品質なHTMLスライドの生成
- 著作権フリーの高品質画像検索と挿入
- スライド品質の検証と改善（アクセシビリティ、一貫性、正確性）
- 単体でのリサーチ結果出力（基本検索または詳細分析）
- エージェント間のシームレスなデータ連携と処理フロー

## 動作環境

本プロジェクトは以下の環境でテストおよび動作確認を行っています：

### テスト済み環境

- **OS**: macOS Sonoma 15.3.1
- **Python**: 3.12.3
- **ブラウザ**: Safari 17.3, Chrome 123, Firefox 127

### 必要環境

- **OS**: macOS 10.15以上、Windows 10以上、または Linux (Ubuntu 20.04+)
- **Python**: 3.12+
- **メモリ**: 最小4GB、推奨8GB以上
- **ディスク容量**: 最小500MB（生成されたスライドの保存用に追加容量が必要）
- **ネットワーク**: インターネット接続（OpenAI APIへのアクセスとウェブ検索機能のため）
- **API**:
  - OpenAI APIキー（GPT-4o、GPT-4o-mini対応）
  - OpenAI Assistants API対応

### 互換性メモ

- **macOS**: Apple Silicon (M1/M2/M3) プロセッサにネイティブ対応、Intel Macでも動作確認済み
- **GPUアクセラレーション**: 必須ではありませんが、CUDA対応GPUがあれば一部処理が高速化されます
- **ディスプレイ**: 最小解像度1280×800以上を推奨（スライドプレビュー表示のため）

## 技術スタック

- Python 3.12+
- OpenAI API (GPT-4o, GPT-4o-mini)
- OpenAI Agents SDK 0.0.14
- Reveal.js (スライドフレームワーク)
- Tailwind CSS (スタイリング)
- Jinja2 (テンプレートエンジン)
- BeautifulSoup4 (WebページのHTMLパース)
- 各種Python依存ライブラリ

## システムアーキテクチャ

プロジェクトは5層アーキテクチャで構成されています：

1. **UI層** - コマンドラインインターフェース（app.py）
2. **エージェント層** - 機能別の独立したAIエージェント（agents/）
3. **ツール層** - ウェブ検索、HTMLレンダリングなどのユーティリティ
4. **ストレージ層** - ファイル保存、読み込み機能、エージェント間データ共有
5. **監視層** - 各エージェントの動作を監視し調整

## エージェント構成と連携ワークフロー

プロジェクトは以下の専門化されたAIエージェントから構成され、連携して動作します：

- **ResearchAgent**: 複数レイヤの深層情報収集とウェブリサーチ
- **OutlineAgent**: 論理的なスライド構造設計と最適なセクション分割
- **TemplateSelectorAgent**: トピックに最適なテンプレートの選択
- **SlideWriterAgent**: HTML/CSSコンテンツとスライド生成
- **ImageFetchAgent**: テーマに適した著作権フリー画像の検索・取得
- **RefinerAgent**: 品質保証、アクセシビリティ確保、一貫性チェック、コンテンツ充実度評価
- **MonitoringAgent**: 他エージェントの動作監視と品質管理
- **OrchestratorAgent**: 全体のワークフロー管理と最適化（司令塔）

### 統合ワークフロー

このワークフローでは、MonitoringAgentが基本的な調整を行い、オプションとして司令塔モードではOrchestratorAgentが全体プロセスを高度に管理します：

1. **要件分析ステージ**：
   - 通常モード: アプリケーションがパラメータを直接渡す
   - 司令塔モード: OrchestratorAgentがトピックの複雑さ、専門性、視覚的重要性などを分析

2. **リサーチ＆アウトライン生成ステージ**：
   - ResearchAgentが`search_deep`機能でウェブ検索と情報収集を実行
   - OutlineAgentが収集された情報を分析し、論理的なスライド構造を設計
   - MonitoringAgentが`monitor_research_and_outline`関数を通じて品質を評価・改善
   - 司令塔モード: さらに要件に基づいた最適化とより深い分析を実施

3. **テンプレート選択ステージ**：
   - TemplateSelectorAgentがトピックとアウトラインを分析し最適なテーマを選択
   - 司令塔モード: 要件分析結果に基づく動的なスタイル調整

4. **スライド生成＆改善ステージ**：
   - SlideWriterAgentがアウトラインとテーマに基づいてHTML/CSSを生成
   - ImageFetchAgentが適切な画像を検索・取得
   - RefinerAgentが生成されたスライドの品質を評価・改善（詳細は「品質評価機能」セクション参照）
   - MonitoringAgentが`monitor_slides_and_refine`関数を通じて反復的な改善を調整
   - 司令塔モード: トピックの複雑さに応じた反復回数の最適化と品質メトリクスの強化

### 品質評価機能

RefinerAgentは生成されたスライドの品質を複数の基準で自動評価し、必要に応じて改善するシステムを実装しています：

#### 評価指標と基準

1. **コンテンツ充実度（Content Richness Score）**:
   - 各スライドのテキスト量が最適範囲内か（minimal：50-150字、balanced：150-300字、detailed：300-600字）
   - 箇条書きの項目数が適切か（最低3項目、最大7項目）
   - 抽象的な表現ではなく具体的な情報や例が含まれているか

2. **一貫性スコア（Consistency Score）**:
   - スライド間の論理的な繋がりがあるか
   - フォントや色使いなどデザイン要素の一貫性
   - 専門用語の説明や使用の一貫性

3. **正確性スコア（Accuracy Score）**:
   - 事実情報の正確さ（研究ソースとの整合性）
   - 引用や参照の適切性
   - 数値やデータの正確さ

4. **視覚的バランス（Visual Balance Score）**:
   - テキストと画像のバランス
   - 空白スペースの適切な使用
   - 情報密度の適切さ

5. **アクセシビリティスコア（Accessibility Score）**:
   - 色のコントラスト比
   - フォントサイズの適切さ
   - スクリーンリーダー対応

#### PASS基準とフィードバックループ

生成されたスライドは、設定された閾値に基づいてPASS/FAIL判定されます：

- **PASS**: 全指標が基準値（70%）以上
- **CONDITIONAL PASS**: 一部指標が基準値を下回るが、全体平均は基準値以上
- **FAIL**: 複数指標が基準値を大幅に下回る、または全体平均が基準値未満

FAIL判定の場合、RefinerAgentは以下のフィードバックループを実行します：

1. 具体的な改善点を特定（例：「スライド3のコンテンツが不足しています」）
2. SlideWriterAgentに詳細なフィードバックを提供
3. SlideWriterAgentが問題のスライドを再生成
4. 再生成されたスライドを再評価

このフィードバックループは、全てのスライドがPASS基準を満たすか、最大再試行回数（デフォルト：3回）に達するまで継続されます。

#### 使用例

```bash
# 品質チェック機能を有効にしてスライド生成
python app.py slide "量子コンピューティング" --quality-check --min-quality 80

# 詳細な品質レポートを出力
python app.py slide "AIの倫理" --quality-check --quality-report

# 特定の品質指標に焦点を当てる
python app.py slide "気候変動" --quality-check --focus-metrics "content,accuracy"
```

#### 品質レポート出力例

```
📊 スライド品質評価レポート:
-----------------------------
スライド全体の品質スコア: 85/100

個別スライド評価:
- スライド1: 92/100 ✅ (内容充実度: 高, 視覚的バランス: 優)
- スライド2: 88/100 ✅ (内容充実度: 中, 視覚的バランス: 高)
- スライド3: 65/100 ⚠️ (内容充実度: 低, 視覚的バランス: 中)
  → 改善済み: 内容を追加し具体例を挿入
- スライド4: 90/100 ✅ (内容充実度: 高, 視覚的バランス: 高)
- スライド5: 87/100 ✅ (内容充実度: 中, 視覚的バランス: 高)

実施した改善:
- スライド3に具体的なデータと例を追加
- スライド2と5の表現を統一し一貫性を向上
- 全スライドの色コントラストを調整しアクセシビリティを改善
```

### エージェント間データ連携

エージェント間のデータ共有と連携を強化するため、以下の機能を実装しています：

1. **グローバルデータストア**: `AgentDataStore`クラスによるエージェント間データ共有
2. **連続的な処理フロー**: 検索結果から自動的に次のエージェント（アウトライン、テンプレート選択など）へ処理を引き継ぐ仕組み
3. **データ永続化**: 検索結果やエージェント処理結果をJSONファイルとして保存・読み込み可能
4. **堅牢なエラー処理**: ウェブページへのアクセス失敗時に代替URLを試行する機能

エージェント間のデータ連携は`AgentDataStore`クラスによって実現されています：

```python
# グローバルデータストアの使用例
from app import agent_data_store

# データの保存
agent_data_store.set("research_results", research_data)

# データの取得
research_data = agent_data_store.get("research_results")

# データをファイルに保存
agent_data_store.save_to_file("project_data.json")

# ファイルからデータを読み込み
agent_data_store.load_from_file("project_data.json")
```

### システム連携図

```
【統合ワークフロー】
                                        ┌──────────────────────────┐
                                        │ オプション: 司令塔モード  │
                                        └───────────┬──────────────┘
                                                    │
                                                    ↓
┌───────────────┐     ┌─────────────────────┐     ┌───────────────────────┐
│ アプリケーション │────→│ モニタリング層      │────→│ 要件分析             │
└───────────────┘     │ (モニタリング/司令塔) │     └──────────┬────────────┘
                      └─────────────────────┘                 │
                                │                             │
                                │                             ↓
┌───────────────────────────────────────────────────┐    ┌────────────────────┐
│ 専門エージェント実行チェーン                       │←───│ 最適パラメータ設定  │
│ ┌─────────┐   ┌──────────┐   ┌───────────────┐   │    └────────────────────┘
│ │リサーチ   │→ │アウトライン│→ │テンプレート選択│   │
│ │エージェント│   │エージェント │   │エージェント   │   │
│ └─────────┘   └──────────┘   └───────────────┘   │
│        │                              │           │
│        ↓                              ↓           │
│ ┌──────────────┐           ┌────────────────┐    │
│ │改善エージェント│←──────────│スライド生成    │    │
│ └──────────────┘           │エージェント     │    │
│                           └────────────────┘    │
└───────────────────────────────────────────────────┘
                   ↑                      │
                   │                      │
                   └──────────────────────┘
                     継続的な品質監視・
                      フィードバック
```

### データ連携ワークフロー

```
┌──────────────────────┐
│ リサーチエージェント  │
└──────────┬───────────┘
           │ --store "research_data"
           ↓
┌──────────────────────┐
│ グローバルデータストア │ ←── --store-file "data.json" で永続化
└──────────┬───────────┘
           │ --next-agent outline
           ↓
┌──────────────────────┐
│ アウトラインエージェント│
└──────────┬───────────┘
           │ 
           ↓
┌──────────────────────┐
│ テンプレート選択     │
└──────────┬───────────┘
           │
           ↓
┌──────────────────────┐
│ 最終スライド生成      │
└──────────────────────┘
```

### フォールバックメカニズム

システムには堅牢性を確保するためのフォールバックメカニズムが組み込まれています：

```
┌──────────────────────┐
│ 処理開始              │
└──────────┬───────────┘
           ↓
┌──────────────────────┐     ┌──────────────────────┐
│ モニタリング/         │  No │ 直線的な基本処理     │
│ オーケストレーション  ├────→│ (シンプルな順次実行)  │
│ 成功？               │     └──────────────────────┘
└──────────┬───────────┘
           │ Yes
           ↓
┌──────────────────────┐     ┌──────────────────────┐
│ API接続OK？          │  No │ オフラインモード     │
│ クォータ残量あり？    ├────→│ (キャッシュ・合成結果)│
└──────────┬───────────┘     └──────────────────────┘
           │ Yes
           ↓
┌──────────────────────┐     ┌──────────────────────┐
│ 各エージェント実行    │     │ 単純化された         │
│ 成功？               ├─No─→│ フォールバック機能   │
└──────────┬───────────┘     └──────────────────────┘
           │ Yes
           ↓
┌──────────────────────┐
│ 結果出力             │
└──────────────────────┘
```

## プロジェクト構造

```
ai-slide-generator/
├── agents/              # エージェントモジュール
│   ├── research/        # リサーチエージェント
│   ├── outline/         # アウトライン生成エージェント
│   ├── slide_writer/    # スライド生成エージェント
│   ├── refiner/         # スライド改善エージェント
│   ├── template_selector/ # テンプレート選択エージェント
│   ├── image_fetch/     # 画像取得エージェント
│   └── monitoring/      # モニタリング・司令塔エージェント
├── static/              # 静的ファイル
│   ├── images/          # 画像リソース
│   ├── output/          # 出力用ディレクトリ 
│   └── slide_assets/    # スライド用アセット
├── templates/           # スライドテンプレート
│   └── themes/          # テーマ別テンプレート
├── tests/               # テストコード
├── logs/                # ログファイル保存ディレクトリ
├── reports/             # レポート・分析結果
├── flow/                # ワークフロー定義
├── app.py               # メインアプリケーション
├── .env                 # 環境変数
└── README.md            # このファイル
```

## インストール手順

1. リポジトリをクローン:
```bash
git clone https://github.com/yourusername/ai-slide-generator.git
cd ai-slide-generator
```

2. Python仮想環境を作成して有効化:
```bash
python -m venv .venv
source .venv/bin/activate  # macOSとLinux
# または
.venv\Scripts\activate  # Windows
```

3. 依存パッケージをインストール:
```bash
pip install -r requirements.txt
```

4. 環境変数の設定:
```bash
cp .env.template .env
# .envファイルを編集して、OPENAI_API_KEYを設定
```

```
OPENAI_API_KEY=sk-your_api_key
OPENAI_MODEL=gpt-4o-mini  # デフォルトモデル、省略可
```

5. 動作確認:
```bash
python app.py research "テスト" --basic
```

## 使用方法

AI Slide Generatorには3つの主要コマンドがあります：

### 1. スライド生成

```bash
python app.py slide "トピック名" --slides 5 --depth medium --style professional
```

オプション：
- `--slides`, `-s`: 生成するスライド枚数 (デフォルト: 5)
- `--depth`, `-d`: 検索深度 (low/medium/high)
- `--style`: スライドスタイル (professional/modern/minimal/business)
- `--output`, `-o`: 出力先のHTMLファイルパス
- `--open`, `-b`: 生成後にブラウザで開く
- `--orchestrator`: 司令塔エージェントを使用（全プロセスを一括管理）

### 2. リサーチ機能

```bash
# 基本検索モード
python app.py research "トピック名" --basic --results 10

# 詳細リサーチモード
python app.py research "トピック名" --depth medium --output research.json --format json

# 検索後に自動的にアウトラインを生成
python app.py research "トピック名" --store "research_data" --next-agent outline

# 検索結果をJSON形式で標準出力
python app.py research "トピック名" --json
```

オプション：
- `--depth`, `-d`: 検索深度 (low/medium/high)
- `--basic`, `-b`: 基本検索モードを有効化（単純な検索結果のみ、詳細分析なし）
- `--results`, `-r`: 検索結果の表示件数 (デフォルト: 10、基本モード時に有効)
- `--output`, `-o`: 出力先のファイルパス
- `--format`, `-f`: 出力形式 (json/markdown/txt)
- `--json`, `-j`: 結果をJSON形式で標準出力に表示
- `--quiet`, `-q`: ファイル出力時に詳細な結果表示を抑制する
- `--store`, `-s`: 検索結果をデータストアに保存するキー名（次のエージェントで使用するため）
- `--store-file`: 検索結果をグローバルデータストアファイルに保存するためのJSONファイルパス
- `--next-agent`: 検索後に自動的に実行する次のエージェント（outline, slides, templateなど）

### 3. JSONからのスライド生成

```bash
# app.pyを使用する方法
python app.py json-to-slides quantum_research.json --slides 5 --open

# または直接run_slides.pyを使用する方法（より多くのオプションあり）
python run_slides.py quantum_research.json --slides 5 --text-density balanced --icons True --open
```

オプション：
- `--slides`, `-s`: 生成するスライド枚数 (デフォルト: 5)
- `--style`: スライドスタイル (professional/modern/minimal/business)
- `--output`, `-o`: 出力先のディレクトリまたはHTMLファイルパス
- `--open`, `-b`: 生成後にブラウザで開く
- `--text-density`: テキスト密度 (minimal/balanced/detailed)
- `--icons`: SVGアイコンの表示/非表示

## テスト環境と実行方法

### 動作環境
- Python 3.10以上
- 依存パッケージ: requirements.txtに記載
- OpenAI API キー（アカウント作成が必要）
- インターネット接続（検索機能、API接続用）

### 基本機能テスト

以下のコマンドで機能をテストできます：

1. **基本検索機能（クイックリサーチ）**:
```bash
python app.py research "人工知能の基礎" --basic --results 5 --json
```
- 基本検索モードで簡単な検索を実行し、結果をJSON形式で表示します
- 成功基準: 検索結果が表示され、エラーが発生しないこと

2. **詳細リサーチ機能**:
```bash
python app.py research "量子コンピューティング" --depth medium --output quantum_research.json
```
- より詳細な検索と分析を実行し、結果をJSONファイルに保存します
- 成功基準: quantum_research.jsonファイルが生成され、内容が正しいフォーマットであること

3. **JSONからのスライド生成**:
```bash
python run_slides.py quantum_research.json --slides 5 --open
```
- 前のステップで生成したJSONファイルを使用してスライドを生成し、ブラウザで開きます
- 成功基準: HTMLスライドが生成され、ブラウザで正しく表示されること

4. **統合ワークフロー（スライド直接生成）**:
```bash
python app.py slide "AI駆動開発" --slides 8 --depth medium --style modern --text-density balanced --open
```
- トピックから直接スライドを生成（リサーチからスライド生成までを一括実行）
- 成功基準: 完全なスライドセットが生成され、内容が適切であること

5. **データストア連携機能**:
```bash
python app.py research "気候変動対策" --depth low --store "climate_data" --store-file "climate_research.json" --next-agent outline
```
- データストアを使用してエージェント間の連携をテストします
- 成功基準: climate_research.jsonが生成され、アウトラインが自動的に生成されること

6. **テキスト密度設定機能**:
```bash
python run_slides.py quantum_research.json --slides 5 --text-density detailed --open
```
- テキスト密度を変更してスライド内容の詳細度をコントロールする機能をテストします
- 成功基準: 詳細なコンテンツを含むスライドが生成されること

7. **スタイル切替機能**:
```bash
python app.py slide "未来技術" --slides 6 --style minimal --open
```
- 異なるスライドスタイルでの生成をテストします
- 成功基準: minimalスタイルのスライドが生成されること

8. **研究データの保存と再利用**:
```bash
# ステップ1: データを保存
python app.py research "宇宙探査" --depth medium --output space_research.json
# ステップ2: 保存したデータからスライド生成
python app.py json-to-slides space_research.json --slides 7 --style business --open
```
- 研究データの保存と再利用の流れをテストします
- 成功基準: 両方のコマンドが正常に実行され、スライドが生成されること

9. **オフライン動作テスト**:
```bash
# ネットワーク接続をオフにしてから実行
python app.py slide "人工知能" --slides 4 --depth low --open
```
- オフライン時のフォールバック機能をテストします
- 成功基準: エラーではなく、キャッシュや合成データに基づいたスライドが生成されること

10. **カスタム出力ディレクトリ**:
```bash
python app.py slide "ブロックチェーン" --slides 5 --output ./custom_output/blockchain_slides.html --open
```
- カスタム出力先の指定機能をテストします
- 成功基準: 指定したパスにファイルが生成されること

11. **スライド品質評価機能**:
```bash
python app.py slide "人工知能倫理" --slides 6 --quality-check --quality-report --open
```
- スライドの品質を自動評価し、必要に応じて改善するプロセスをテストします
- 成功基準: 品質レポートが表示され、低品質スライドが自動的に改善されること

12. **品質基準カスタマイズ**:
```bash
python app.py slide "データサイエンス" --quality-check --min-quality 85 --focus-metrics "content,accuracy" --open
```
- 品質チェックの基準をカスタマイズする機能をテストします
- 成功基準: 指定した基準（85%）とメトリクス（コンテンツと正確性）で評価が実行されること

### トラブルシューティング

- **API接続エラー**: `.env`ファイルのAPIキーが正しく設定されているか確認してください
- **モジュールエラー**: `pip install -r requirements.txt`を実行して依存パッケージを再インストールしてください
- **生成結果が不十分**: `--depth`パラメータを上げるか、`--text-density`を`detailed`に設定して試してください
- **HTMLファイルが開かない**: `-o/--open`フラグを追加するか、手動でブラウザからHTMLファイルを開いてください
- **app.pyでのスライド生成エラー**: 現在、app.pyファイルの3330行付近にインデントエラーがあり、`app.py slide`コマンドが失敗する場合があります。その場合は代わりに`run_slides.py`を使用してJSONファイルからスライドを直接生成してください。例:
  ```bash
  # 代替手順
  python app.py research "AI駆動開発" --depth medium --output ai_research.json
  python run_slides.py ai_research.json --slides 8 --text-density balanced --open
  ```
- **スライド品質が低い**: `--quality-check`フラグを追加して品質評価・改善機能を有効化してください。特に重要な指標がある場合は`--focus-metrics`オプションで指定できます。
- **品質チェックに時間がかかる**: 品質チェックはAPI呼び出しを追加で行うため処理時間が延びます。`--min-quality`値を下げる（デフォルト70%）か、`--max-refinement-iterations`を減らす（デフォルト3回）ことで高速化できます。

## 改訂履歴

- **v1.0.0**: 初期リリース - 基本的なスライド生成機能
- **v1.1.0**: 詳細リサーチモードとフォールバックメカニズムの追加
- **v1.2.0**: 司令塔エージェントによる高度なワークフロー管理を実装
- **v1.3.0**: エージェント間データ連携機能の強化、堅牢な実行フローを実装