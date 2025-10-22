#!/usr/bin/env python3
"""
POP MART 全商品在庫確認ツール
指定したコレクションの全商品と在庫状況を表示します
"""

import os
import sys
import requests
import json
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))


def get_jst_now():
    """Get current time in JST"""
    return datetime.now(JST)


def fetch_all_products(collection_id=223):
    """
    指定したコレクションの全商品を取得

    Args:
        collection_id: コレクションID（デフォルト: 223 = THE MONSTERS）

    Returns:
        list: 商品リスト
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://www.popmart.com/',
    }

    all_products = []
    page = 1
    collection_name = None
    total_products = None

    print(f"🔍 コレクションID {collection_id} の商品を取得中...")

    while True:
        url = f"https://cdn-global.popmart.com/shop_productoncollection-{collection_id}-1-{page}-jp-ja.json"

        try:
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code == 404:
                # 404は次のページがないことを意味する
                break

            response.raise_for_status()
            data = response.json()

            if page == 1:
                collection_name = data.get('name', 'Unknown')
                total_products = data.get('total', 0)
                print(f"📦 コレクション: {collection_name}")
                print(f"📊 総商品数（API報告）: {total_products}件")
                print()

            products = data.get('productData', [])
            if not products:
                break

            all_products.extend(products)
            print(f"   ページ{page}: {len(products)}件取得（累計: {len(all_products)}件）")

            page += 1

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                break
            print(f"❌ HTTPエラー: {e}")
            break
        except Exception as e:
            print(f"❌ エラー: {e}")
            break

    print(f"\n✅ 取得完了: {len(all_products)}件")

    if total_products and len(all_products) < total_products:
        print(f"⚠️  警告: API報告値({total_products}件)より少ない商品数です")
        print(f"   これはPOP MART API仕様による制限の可能性があります")

    return all_products, collection_name


def analyze_products(products):
    """
    商品リストを分析

    Args:
        products: 商品リスト

    Returns:
        dict: 分析結果
    """
    in_stock = []
    out_of_stock = []

    for product in products:
        total_stock = 0
        sku_details = []

        for sku in product.get('skus', []):
            stock = sku.get('stock', {})
            online_stock = stock.get('onlineStock', 0)

            if online_stock > 0:
                sku_details.append({
                    'price': sku.get('price', 0),
                    'currency': sku.get('currency', 'JPY'),
                    'stock': online_stock
                })

            total_stock += online_stock

        product_info = {
            'id': product.get('id'),
            'title': product.get('title'),
            'is_new': product.get('isNew', False),
            'is_hot': product.get('isHot', False),
            'total_stock': total_stock,
            'sku_details': sku_details,
            'url': f"https://www.popmart.com/jp/products/{product.get('id')}"
        }

        if total_stock > 0:
            in_stock.append(product_info)
        else:
            out_of_stock.append(product_info)

    return {
        'in_stock': in_stock,
        'out_of_stock': out_of_stock,
        'total': len(products)
    }


def print_product_list(products, show_all=False, filter_keyword=None):
    """
    商品リストを表示

    Args:
        products: 商品リスト
        show_all: 全商品を表示（デフォルト: False）
        filter_keyword: フィルタキーワード（部分一致）
    """
    results = analyze_products(products)

    print("\n" + "="*80)
    print("📊 在庫状況サマリー")
    print("="*80)
    print(f"総商品数: {results['total']}件")
    print(f"在庫あり: {len(results['in_stock'])}件 ✅")
    print(f"売り切れ: {len(results['out_of_stock'])}件 ❌")
    print()

    # フィルタリング
    if filter_keyword:
        filtered_in_stock = [p for p in results['in_stock'] if filter_keyword.lower() in p['title'].lower()]
        filtered_out_of_stock = [p for p in results['out_of_stock'] if filter_keyword.lower() in p['title'].lower()]

        print(f"🔍 キーワードフィルタ: '{filter_keyword}'")
        print(f"   該当商品: {len(filtered_in_stock) + len(filtered_out_of_stock)}件")
        print()

        results['in_stock'] = filtered_in_stock
        results['out_of_stock'] = filtered_out_of_stock

    # 在庫ありの商品を表示
    if results['in_stock']:
        print("="*80)
        print("✅ 在庫あり商品")
        print("="*80)
        for idx, product in enumerate(results['in_stock'], 1):
            badges = []
            if product['is_new']:
                badges.append('🆕')
            if product['is_hot']:
                badges.append('🔥')

            badge_str = ' '.join(badges)
            print(f"\n{idx}. {product['title']} {badge_str}")
            print(f"   商品ID: {product['id']}")
            print(f"   総在庫: {product['total_stock']}個")

            for sku in product['sku_details']:
                print(f"   - {sku['price']:,} {sku['currency']}: {sku['stock']}個")

            print(f"   🔗 {product['url']}")

    # 売り切れ商品を表示（show_all=Trueの場合のみ）
    if show_all and results['out_of_stock']:
        print("\n" + "="*80)
        print("❌ 売り切れ商品")
        print("="*80)
        for idx, product in enumerate(results['out_of_stock'], 1):
            badges = []
            if product['is_new']:
                badges.append('🆕')
            if product['is_hot']:
                badges.append('🔥')

            badge_str = ' '.join(badges)
            print(f"\n{idx}. {product['title']} {badge_str}")
            print(f"   商品ID: {product['id']}")
            print(f"   🔗 {product['url']}")

    # JSONで保存
    output_file = 'all_products.json'
    output_data = {
        'timestamp': get_jst_now().isoformat(),
        'collection_id': os.environ.get('COLLECTION_ID', '223'),
        'total': results['total'],
        'in_stock_count': len(results['in_stock']),
        'out_of_stock_count': len(results['out_of_stock']),
        'products': [
            {
                'id': p['id'],
                'title': p['title'],
                'is_new': p['is_new'],
                'is_hot': p['is_hot'],
                'total_stock': p['total_stock'],
                'sku_details': p['sku_details'],
                'url': p['url']
            }
            for p in results['in_stock'] + results['out_of_stock']
        ]
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 全商品データを {output_file} に保存しました")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description='POP MART 全商品在庫確認ツール')
    parser.add_argument('--collection-id', type=int, default=223, help='コレクションID（デフォルト: 223）')
    parser.add_argument('--show-all', action='store_true', help='売り切れ商品も全て表示')
    parser.add_argument('--filter', type=str, help='商品名でフィルタ（部分一致）')

    args = parser.parse_args()

    print("="*80)
    print("POP MART 全商品在庫確認ツール")
    print(f"実行時刻: {get_jst_now().strftime('%Y-%m-%d %H:%M:%S')} (JST)")
    print("="*80)
    print()

    # 環境変数からコレクションIDを取得（コマンドライン引数が優先）
    collection_id = int(os.environ.get('COLLECTION_ID', args.collection_id))

    # 全商品を取得
    products, collection_name = fetch_all_products(collection_id)

    if not products:
        print("❌ 商品を取得できませんでした")
        sys.exit(1)

    # 商品リストを表示
    print_product_list(products, show_all=args.show_all, filter_keyword=args.filter)

    print("\n" + "="*80)
    print("✅ 完了")
    print("="*80)


if __name__ == '__main__':
    main()
