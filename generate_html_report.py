#!/usr/bin/env python3
"""
POP MART 在庫レポート HTML生成ツール
all_products.json から視覚的なHTMLレポートを生成します
"""

import json
import os
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def generate_html_report(json_file='all_products.json', output_file='stock_report.html'):
    """
    JSONデータからHTMLレポートを生成

    Args:
        json_file: 入力JSONファイル
        output_file: 出力HTMLファイル
    """

    # JSONデータを読み込み
    if not os.path.exists(json_file):
        print(f"❌ {json_file} が見つかりません")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    timestamp = data.get('timestamp', '')
    collection_id = data.get('collection_id', '')
    total = data.get('total', 0)
    in_stock_count = data.get('in_stock_count', 0)
    out_of_stock_count = data.get('out_of_stock_count', 0)
    products = data.get('products', [])

    # 在庫ありと売り切れを分類
    in_stock_products = [p for p in products if p['total_stock'] > 0]
    out_of_stock_products = [p for p in products if p['total_stock'] == 0]

    # 新着・人気商品を抽出
    new_products = [p for p in products if p.get('is_new', False)]
    hot_products = [p for p in products if p.get('is_hot', False)]

    # HTML生成
    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>POP MART 在庫レポート</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}

        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}

        .stat-card:hover {{
            transform: translateY(-5px);
        }}

        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            margin: 10px 0;
        }}

        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat-card.in-stock .number {{
            color: #28a745;
        }}

        .stat-card.out-of-stock .number {{
            color: #dc3545;
        }}

        .stat-card.total .number {{
            color: #667eea;
        }}

        .section {{
            padding: 30px 40px;
        }}

        .section-title {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .filter-tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .filter-tab {{
            padding: 10px 20px;
            background: #e9ecef;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }}

        .filter-tab:hover {{
            background: #dee2e6;
        }}

        .filter-tab.active {{
            background: #667eea;
            color: white;
        }}

        .product-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .product-card {{
            background: white;
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            transition: all 0.3s;
            position: relative;
        }}

        .product-card:hover {{
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            transform: translateY(-3px);
        }}

        .product-card.in-stock {{
            border-left: 5px solid #28a745;
        }}

        .product-card.out-of-stock {{
            border-left: 5px solid #dc3545;
            opacity: 0.7;
        }}

        .product-badges {{
            display: flex;
            gap: 5px;
            margin-bottom: 10px;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
        }}

        .badge.new {{
            background: #ffc107;
            color: #000;
        }}

        .badge.hot {{
            background: #ff5722;
            color: white;
        }}

        .badge.in-stock {{
            background: #28a745;
            color: white;
        }}

        .badge.out-of-stock {{
            background: #dc3545;
            color: white;
        }}

        .product-title {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
            min-height: 50px;
        }}

        .product-id {{
            color: #999;
            font-size: 0.85em;
            margin-bottom: 10px;
        }}

        .product-stock {{
            font-size: 1.2em;
            font-weight: bold;
            margin: 10px 0;
        }}

        .product-stock.available {{
            color: #28a745;
        }}

        .product-stock.unavailable {{
            color: #dc3545;
        }}

        .product-link {{
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            font-size: 0.9em;
            transition: background 0.3s;
        }}

        .product-link:hover {{
            background: #5568d3;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}

        .hidden {{
            display: none;
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}

            .product-grid {{
                grid-template-columns: 1fr;
            }}

            .stats {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎨 POP MART 在庫レポート</h1>
            <div class="subtitle">THE MONSTERS コレクション (ID: {collection_id})</div>
            <div class="subtitle">更新日時: {timestamp}</div>
        </div>

        <div class="stats">
            <div class="stat-card total">
                <div class="label">総商品数</div>
                <div class="number">{total}</div>
            </div>
            <div class="stat-card in-stock">
                <div class="label">在庫あり</div>
                <div class="number">{in_stock_count}</div>
            </div>
            <div class="stat-card out-of-stock">
                <div class="label">売り切れ</div>
                <div class="number">{out_of_stock_count}</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">商品一覧</h2>

            <div class="filter-tabs">
                <button class="filter-tab active" onclick="filterProducts('all')">全て ({total})</button>
                <button class="filter-tab" onclick="filterProducts('in-stock')">在庫あり ({in_stock_count})</button>
                <button class="filter-tab" onclick="filterProducts('out-of-stock')">売り切れ ({out_of_stock_count})</button>
                <button class="filter-tab" onclick="filterProducts('new')">新着 ({len(new_products)})</button>
                <button class="filter-tab" onclick="filterProducts('hot')">人気 ({len(hot_products)})</button>
            </div>

            <div class="product-grid" id="productGrid">
"""

    # 商品カードを生成
    for product in products:
        product_id = product['id']
        title = product['title']
        is_new = product.get('is_new', False)
        is_hot = product.get('is_hot', False)
        total_stock = product['total_stock']
        url = product['url']

        stock_class = 'in-stock' if total_stock > 0 else 'out-of-stock'
        stock_status = f'{total_stock}個在庫あり' if total_stock > 0 else '売り切れ'
        stock_status_class = 'available' if total_stock > 0 else 'unavailable'

        # データ属性を設定
        data_attrs = f'data-stock="{stock_class}"'
        if is_new:
            data_attrs += ' data-new="true"'
        if is_hot:
            data_attrs += ' data-hot="true"'

        html += f"""
                <div class="product-card {stock_class}" {data_attrs}>
                    <div class="product-badges">
"""

        if is_new:
            html += '                        <span class="badge new">🆕 NEW</span>\n'
        if is_hot:
            html += '                        <span class="badge hot">🔥 HOT</span>\n'

        html += f"""                        <span class="badge {stock_class}">{stock_status}</span>
                    </div>

                    <div class="product-title">{title}</div>
                    <div class="product-id">商品ID: {product_id}</div>

                    <div class="product-stock {stock_status_class}">
                        {stock_status}
                    </div>

                    <a href="{url}" target="_blank" class="product-link">商品ページを見る →</a>
                </div>
"""

    # フッターのタイムスタンプを追加
    current_time = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')

    html += f"""
            </div>
        </div>

        <div class="footer">
            <p>POP MART Stock Checker - Generated at {current_time}</p>
            <p>データは5分ごとに自動更新されています</p>
        </div>
    </div>

    <script>
        function filterProducts(filter) {{
            // タブのアクティブ状態を更新
            document.querySelectorAll('.filter-tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            event.target.classList.add('active');

            // 商品カードをフィルタリング
            const cards = document.querySelectorAll('.product-card');

            cards.forEach(card => {{
                let show = false;

                switch(filter) {{
                    case 'all':
                        show = true;
                        break;
                    case 'in-stock':
                        show = card.dataset.stock === 'in-stock';
                        break;
                    case 'out-of-stock':
                        show = card.dataset.stock === 'out-of-stock';
                        break;
                    case 'new':
                        show = card.dataset.new === 'true';
                        break;
                    case 'hot':
                        show = card.dataset.hot === 'true';
                        break;
                }}

                if (show) {{
                    card.classList.remove('hidden');
                }} else {{
                    card.classList.add('hidden');
                }}
            }});
        }}
    </script>
</body>
</html>
"""

    # HTMLファイルに書き込み
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTMLレポートを生成しました: {output_file}")
    print(f"📊 総商品数: {total}件")
    print(f"✅ 在庫あり: {in_stock_count}件")
    print(f"❌ 売り切れ: {out_of_stock_count}件")
    print(f"\n💡 ブラウザで開いてください:")
    print(f"   open {output_file}")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='POP MART 在庫レポート HTML生成')
    parser.add_argument('--input', default='all_products.json', help='入力JSONファイル')
    parser.add_argument('--output', default='stock_report.html', help='出力HTMLファイル')

    args = parser.parse_args()

    generate_html_report(args.input, args.output)


if __name__ == '__main__':
    main()
