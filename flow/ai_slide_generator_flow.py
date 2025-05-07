# ai_slide_generator_flow.py
# ------------------------------------------------------------
# 実行するとカレントフォルダに ai_slide_generator_flow.html を生成
# ------------------------------------------------------------
import json
from pathlib import Path

# ──────────────────────────────────────────────
# 1) グラフデータ定義（ノード / リンク）
# ──────────────────────────────────────────────
nodes = [
    # id,                label,                                         group
    ("user",      "ユーザー入力\n（トピックと深度設定）",                        "actor"),
    ("monitor",   "モニタリングエージェント\n（調整と最適化）",                   "agent"),
    ("research",  "調査エージェント\n（多層ウェブ検索）",                      "agent"),
    ("outline",   "アウトラインエージェント\n（スライド構造設計）",             "agent"),
    ("template",  "テンプレートセレクター\n（スライドデザイン選択）",           "agent"),
    ("slide",     "スライド作成エージェント\n（HTML / CSS 生成）",             "agent"),
    ("refine",    "品質改善エージェント\n（アクセシビリティ＆一貫性）",         "agent"),
    ("output",    "AIスライド出力\n（最終プレゼンテーション）",                 "output"),
    ("search",    "検索ツール\n（低/中/高 深度設定）",                         "tool"),
    ("render",    "レンダリングツール",                                      "tool"),
    ("storage",   "ファイル保存",                                            "storage"),
]

links = [
    # source,   target,   label,                   main?,   curve(optional)
    ("user",     "monitor",  "1. トピックと深度設定",       True,     0.3),
    ("monitor",  "research", "2. 検索深度に基づく指示",     True,     0.1),
    ("research", "monitor",  "3. 調査結果を返却",          True,     0.1),
    ("monitor",  "outline",  "4. 情報を転送",             True,     0.1),
    ("outline",  "template", "5. アウトライン情報",        True,     0.1),
    ("template", "slide",    "6. テンプレート選択",        True,     0.1),
    ("slide",    "refine",   "7. スライドコンテンツ",       True,     0.3),
    ("refine",   "output",   "8. 最終スライド",            True,     0.3),  # userからoutputへ変更

    ("research", "search",   "検索実行",                   False,    0.1),
    ("search",   "research", "結果返却",                   False,    0.2),
    ("monitor",  "research", "必要に応じて追加調査",        False,    0.3),
    ("refine",   "slide",    "イテレーティブな改善",        False,    0.3),  # 反復的な改善プロセス
    ("slide",    "render",   "HTML 生成",                 False,    0.2),
    ("render",   "storage",  "保存",                      False,    0.0),
    ("output",   "storage",  "HTML保存",                  False,    0.2),  # 出力から保存へのリンクを追加
]

# ノードとリンクをJSON形式に変換 (curveを追加)
nodes_json = json.dumps([{"id": n[0], "label": n[1], "group": n[2]} for n in nodes], ensure_ascii=False)
links_json = json.dumps([{
    "source": l[0], 
    "target": l[1], 
    "label": l[2], 
    "main": l[3],
    "curve": l[4] if len(l) > 4 else 0
} for l in links], ensure_ascii=False)

# ──────────────────────────────────────────────
# 2) HTML 生成
# ──────────────────────────────────────────────
html = f"""
<!DOCTYPE html>
<meta charset="utf-8" />
<title>AI Slide Generator Flow</title>
<style>
  html,body,svg{{height:100%;width:100%;margin:0;padding:0;background:#F9FAFB;font-family:'Noto Sans JP',sans-serif;}}
  .node rect{{rx:8;ry:8;stroke-width:0;box-shadow:0 4px 6px rgba(0,0,0,0.1);}}
  .label {{pointer-events:none;font-size:14px;fill:#fff;font-weight:500;}}
  .label tspan {{text-anchor:middle;dominant-baseline:middle;}}
  .link {{fill:none;stroke-width:2.5px;}}
  .link.primary {{stroke-width:3px;}}
  .link.secondary{{stroke-dasharray:5 3;stroke-width:2px;}}
  .link-label {{fill:#334155;font-size:13px;font-weight:bold;pointer-events:none;background:white;}}
  .link-label rect {{fill:white;opacity:0.8;rx:4;ry:4;}}
  .link-label text {{text-anchor:middle;dominant-baseline:middle;}}
  .title {{font-size:24px;font-weight:bold;fill:#1E293B;text-anchor:middle;}}
  .subtitle {{font-size:16px;fill:#475569;text-anchor:middle;}}
  .legend {{font-size:14px;fill:#475569;}}
  .legend-title {{font-size:16px;font-weight:bold;fill:#1E293B;}}
  .legend-item {{display:flex;align-items:center;margin-bottom:5px;}}
  .legend-color {{display:inline-block;width:15px;height:15px;margin-right:5px;border-radius:3px;}}
</style>
<body>
<svg></svg>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<script>

const nodes = {nodes_json};
const links = {links_json};

const colorScale = {{
    "actor":   "#1E293B",
    "agent":   "#6366F1",
    "tool":    "#F59E0B",
    "storage": "#4CAF50",
    "output":  "#EC4899"  // 出力ノード用の色を追加
}};

// 初期矩形サイズ（テキスト行数で自動拡張）
nodes.forEach(n => {{
  const lines = n.label.split('\\n').length;
  // 幅と高さを大きくし、日本語テキストを適切に表示
  n.width  = 220;  // 幅を拡大
  n.height = 40 + (lines-1)*24;  // 高さと行間隔を拡大
  // ラベルを改行で分割して配列として保存（tspan用）
  n.labelLines = n.label.split('\\n');
}});

const svg  = d3.select("svg");
const defs = svg.append("defs");

// タイトルと凡例を追加
const title = svg.append("text")
    .attr("class", "title")
    .attr("x", "50%")
    .attr("y", 40)
    .text("AI スライド生成システム - フロー図");

const subtitle = svg.append("text")
    .attr("class", "subtitle")
    .attr("x", "50%")
    .attr("y", 70)
    .text("検索深度＆反復改善プロセス対応版");

// 凡例
const legend = svg.append("g")
    .attr("class", "legend")
    .attr("transform", "translate(20, 90)");

legend.append("text")
    .attr("class", "legend-title")
    .text("凡例");

const legendItems = [
    {{ label: "ユーザー", color: colorScale.actor }},
    {{ label: "エージェント", color: colorScale.agent }},
    {{ label: "ツール", color: colorScale.tool }},
    {{ label: "ストレージ", color: colorScale.storage }},
    {{ label: "出力", color: colorScale.output }}  // 凡例に出力を追加
];

legendItems.forEach((item, i) => {{
    const g = legend.append("g")
        .attr("transform", `translate(0, ${{25 + i * 25}})`);
    
    g.append("rect")
        .attr("width", 15)
        .attr("height", 15)
        .attr("rx", 3)
        .attr("fill", item.color);
    
    g.append("text")
        .attr("x", 25)
        .attr("y", 12)
        .text(item.label);
}});

// 検索深度の説明
const depthExplanation = svg.append("g")
    .attr("class", "legend")
    .attr("transform", "translate(20, 200)");

depthExplanation.append("text")
    .attr("class", "legend-title")
    .text("検索深度");

const depthItems = [
    {{ label: "low: 基本的な検索（高速）", description: "主要情報のみ" }},
    {{ label: "medium: バランス型（標準）", description: "一般的な詳細度" }},
    {{ label: "high: 詳細検索（時間がかかる）", description: "より多くの情報源と深い調査" }}
];

depthItems.forEach((item, i) => {{
    depthExplanation.append("text")
        .attr("x", 0)
        .attr("y", 25 + i * 25)
        .text(item.label);
}});

// 矢印マーカー - メイン用とサブ用で分ける
defs.append("marker")
    .attr("id","arrow-main")
    .attr("viewBox","0 -5 10 10")
    .attr("refX",20).attr("refY",0)  // 矢印の位置調整
    .attr("markerWidth",10).attr("markerHeight",10)  // 矢印サイズ拡大
    .attr("orient","auto")
  .append("path")
    .attr("d","M0,-6L12,0L0,6")
    .attr("fill","#475569");

defs.append("marker")
    .attr("id","arrow-sub")
    .attr("viewBox","0 -5 10 10")
    .attr("refX",20).attr("refY",0)
    .attr("markerWidth",8).attr("markerHeight",8)
    .attr("orient","auto")
  .append("path")
    .attr("d","M0,-5L10,0L0,5")
    .attr("fill","#94A3B8");

const contentG = svg.append("g");
const gLink = contentG.append("g")
const gNode = contentG.append("g").attr("cursor","grab");

// リンクはカーブさせるために直線ではなくpath要素を使用
const link = gLink.selectAll("path").data(links).enter().append("path")
  .attr("id", (d,i) => `link${{i}}`)
  .attr("class", d => "link " + (d.main ? "primary" : "secondary"))
  .attr("stroke", d => d.main ? "#475569" : "#94A3B8")
  .attr("marker-end", d => d.main ? "url(#arrow-main)" : "url(#arrow-sub)");

// リンクラベルの背景と合わせて表示
const linkLabelGroups = gLink.selectAll("g.link-label")
  .data(links.filter(d => d.label))
  .enter().append("g")
  .attr("class", "link-label");

// ラベル背景用の矩形
linkLabelGroups.append("rect")
  .attr("width", d => d.label.length * 10 + 10)
  .attr("height", 22)
  .attr("x", -20)
  .attr("y", -11);

// ラベルテキスト
linkLabelGroups.append("text")
  .text(d => d.label);

// ノード
const node = gNode.selectAll("g").data(nodes).enter().append("g").attr("class","node");
node.append("rect")
    .attr("width", d => d.width)
    .attr("height", d => d.height)
    .attr("fill", d => colorScale[d.group] || "#6B7280");

// テキスト要素を追加し、改行ごとにtspanを作成
const nodeText = node.append("text")
    .attr("class","label")
    .attr("x", d => d.width/2)
    .attr("y", d => d.height/2)
    .attr("text-anchor","middle");

// 各行に対してtspan要素を作成
nodeText.each(function(d) {{
    const text = d3.select(this);
    const lineCount = d.labelLines.length;
    const lineHeight = 22; // 行の高さ
    const totalHeight = lineHeight * lineCount;
    const startY = d.height/2 - totalHeight/2 + lineHeight/2;
    
    d.labelLines.forEach((line, i) => {{
        text.append("tspan")
            .attr("x", d.width/2)
            .attr("y", startY + i * lineHeight)
            .text(line);
    }});
}});

// フォースシミュレーションの設定
const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(280).strength(0.7))  // リンク距離を拡大
    .force("charge", d3.forceManyBody().strength(-1200))  // 反発力を大幅に強化
    .force("center", d3.forceCenter(svg.node().clientWidth/2, svg.node().clientHeight/2))
    .force("collision", d3.forceCollide().radius(d => Math.max(d.width, d.height) / 1.3 + 20))  // 衝突範囲を拡大
    .force("x", d3.forceX().strength(0.05))  // X方向の整列力を追加
    .force("y", d3.forceY().strength(0.05));  // Y方向の整列力を追加

// ティック関数 - 座標更新時の処理
simulation.on("tick", () => {{
  // ノードの位置更新
  node.attr("transform", d => `translate(${{d.x - d.width/2}},${{d.y - d.height/2}})`);
  
  // リンクをカーブさせる
  link.attr("d", d => {{
    const dx = d.target.x - d.source.x;
    const dy = d.target.y - d.source.y;
    const dr = Math.sqrt(dx * dx + dy * dy) * (d.curve ? 1/d.curve : 9999);
    
    if (d.curve) {{
      // カーブしたパス
      return `M${{d.source.x}},${{d.source.y}} A${{dr}},${{dr}} 0 0,1 ${{d.target.x}},${{d.target.y}}`;
    }} else {{
      // 直線
      return `M${{d.source.x}},${{d.source.y}} L${{d.target.x}},${{d.target.y}}`;
    }}
  }});
  
  // リンクラベルの位置更新
  linkLabelGroups.attr("transform", d => {{
    // リンクの中間点を計算（カーブの場合はカーブの頂点を考慮）
    const dx = d.target.x - d.source.x;
    const dy = d.target.y - d.source.y;
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    
    let x, y;
    
    if (d.curve) {{
      // カーブパスの中間点（少し調整）
      const midX = (d.source.x + d.target.x) / 2;
      const midY = (d.source.y + d.target.y) / 2;
      const dr = Math.sqrt(dx * dx + dy * dy) * (1/d.curve);
      
      // カーブの弧に合わせて位置調整
      const offset = d.curve * 40;
      const perpX = -dy / Math.sqrt(dx*dx + dy*dy) * offset;
      const perpY = dx / Math.sqrt(dx*dx + dy*dy) * offset;
      
      x = midX + perpX;
      y = midY + perpY;
    }} else {{
      // 直線の中間点
      x = (d.source.x + d.target.x) / 2;
      y = (d.source.y + d.target.y) / 2;
    }}
    
    return `translate(${{x}},${{y}})`;
  }});
}});

// ズーム機能の設定
const zoom = d3.zoom().on("zoom",(e) => {{
  contentG.attr("transform", e.transform);
}});
svg.call(zoom);

// ドラッグ機能の設定
node.call(d3.drag()
    .on("start", (e,d) => {{
      if (!e.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }})
    .on("drag", (e,d) => {{
      d.fx = e.x;
      d.fy = e.y;
    }})
    .on("end", (e,d) => {{
      if (!e.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }}));

// 初期ズームレベルを設定
svg.call(zoom.transform, d3.zoomIdentity.scale(0.8).translate(
  svg.node().clientWidth * 0.1, 
  svg.node().clientHeight * 0.1
));

// 20秒間シミュレーションを実行して安定させる
for (let i = 0; i < 20; ++i) simulation.tick();

</script>
"""

# ──────────────────────────────────────────────
# 3) HTML 書き出し
# ──────────────────────────────────────────────
out_path = Path("ai_slide_generator_flow.html")
out_path.write_text(html, encoding="utf-8")
print(f"✅ 生成完了: {out_path.resolve()}")
