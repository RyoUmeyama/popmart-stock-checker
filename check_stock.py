#!/usr/bin/env python3
"""
POP MART Stock Checker
Checks for THE MONSTERS (LABUBU) stock availability and sends email notifications
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
import requests
import json

STOCK_HISTORY_FILE = 'stock_history.json'
JST = timezone(timedelta(hours=9))


def get_jst_now():
    """Get current time in JST"""
    return datetime.now(JST)


def load_previous_stock():
    """Load previous stock status from file"""
    if os.path.exists(STOCK_HISTORY_FILE):
        try:
            with open(STOCK_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_current_stock(product_ids):
    """Save current stock status to file"""
    try:
        with open(STOCK_HISTORY_FILE, 'w') as f:
            json.dump({'product_ids': list(product_ids), 'timestamp': get_jst_now().isoformat()}, f)
    except Exception as e:
        print(f"Warning: Could not save stock history: {e}")


def check_stock(collection_id=223, keyword=None, debug=False):
    """
    Check stock availability for products in a collection

    Args:
        collection_id: Collection ID to check (default: 223 for THE MONSTERS)
        keyword: Filter products by keyword (e.g., "LABUBU", "ラブブ")
        debug: If True, print debug information

    Returns:
        list: List of in-stock products
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.popmart.com/',
        }

        # Fetch all pages
        # URL pattern: shop_productoncollection-{collection_id}-1-{page}-jp-ja.json
        all_products = []
        page = 1
        total_products = None
        collection_name = None

        while True:
            api_url = f"https://cdn-global.popmart.com/shop_productoncollection-{collection_id}-1-{page}-jp-ja.json"

            try:
                response = requests.get(api_url, headers=headers, timeout=30)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                # 404 means no more pages
                if e.response.status_code == 404:
                    break
                raise

            data = response.json()

            if page == 1:
                total_products = data.get('total', 0)
                collection_name = data.get('name', 'Unknown')

            products = data.get('productData', [])
            if not products:
                break

            all_products.extend(products)

            # If we've fetched all products, stop
            if total_products and len(all_products) >= total_products:
                break

            page += 1

        if debug:
            print(f"\n=== DEBUG MODE ===")
            print(f"Collection: {collection_name}")
            print(f"Total products: {total_products}")
            print(f"Fetched products: {len(all_products)}")
            print(f"Pages fetched: {page}")
            print("==================\n")

        in_stock_products = []

        for product in all_products:
            product_title = product.get('title', '')

            # Filter by keyword if specified
            if keyword and keyword.lower() not in product_title.lower():
                continue

            # Check all SKUs for this product
            product_skus = []
            total_stock = 0
            for sku in product.get('skus', []):
                stock = sku.get('stock', {})
                online_stock = stock.get('onlineStock', 0)

                if online_stock > 0:
                    product_skus.append({
                        'price': sku.get('price', 0),
                        'currency': sku.get('currency', 'JPY'),
                        'stock': online_stock
                    })
                    total_stock += online_stock

            # If any SKU has stock, add the product once
            if product_skus:
                in_stock_products.append({
                    'id': product.get('id'),
                    'title': product_title,
                    'skus': product_skus,
                    'total_stock': total_stock,
                    'url': f"https://www.popmart.com/jp/products/{product.get('id')}"
                })

                if debug:
                    print(f"✓ IN STOCK: {product_title}")
                    for sku_info in product_skus:
                        print(f"  Price: {sku_info['price']} {sku_info['currency']} - 在庫あり")
                    print(f"  URL: https://www.popmart.com/jp/products/{product.get('id')}\n")

        if debug and not in_stock_products:
            print("✗ No products in stock")

        return in_stock_products

    except Exception as e:
        print(f"Error checking stock: {e}")
        raise


def send_email_notification(smtp_server, smtp_port, username, password, recipient, products):
    """
    Send email notification about in-stock products

    Args:
        smtp_server: SMTP server address
        smtp_port: SMTP server port
        username: SMTP username
        password: SMTP password
        recipient: Recipient email address
        products: List of in-stock products
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = username
        msg['To'] = recipient
        msg['Subject'] = f'POP MART - {len(products)}件の商品が入荷しました！'

        # Create text version
        text_lines = [
            'POP MARTで商品が入荷しました。',
            f'\nチェック日時: {get_jst_now().strftime("%Y-%m-%d %H:%M:%S")} (JST)',
            f'\n入荷商品数: {len(products)}件\n'
        ]

        for i, product in enumerate(products, 1):
            text_lines.append(f"\n{i}. {product['title']}")
            for sku in product['skus']:
                text_lines.append(f"   価格: {sku['price']:,} {sku['currency']} - 在庫あり")
            text_lines.append(f"   URL: {product['url']}")

        text = '\n'.join(text_lines)

        # Create HTML version
        html_lines = [
            '<html><body>',
            '<h2>POP MART - 商品が入荷しました！</h2>',
            f'<p><strong>チェック日時:</strong> {get_jst_now().strftime("%Y-%m-%d %H:%M:%S")} (JST)</p>',
            f'<p><strong>入荷商品数:</strong> {len(products)}件</p>',
            '<hr>'
        ]

        for i, product in enumerate(products, 1):
            html_lines.append(f'<h3>{i}. {product["title"]}</h3>')
            html_lines.append('<ul>')
            for sku in product['skus']:
                html_lines.append(f'<li><strong>価格:</strong> {sku["price"]:,} {sku["currency"]} - 在庫あり</li>')
            html_lines.append('</ul>')
            html_lines.append(f'<p><a href="{product["url"]}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">商品ページを見る</a></p>')
            html_lines.append('<hr>')

        html_lines.append('</body></html>')
        html = '\n'.join(html_lines)

        part1 = MIMEText(text, 'plain', 'utf-8')
        part2 = MIMEText(html, 'html', 'utf-8')

        msg.attach(part1)
        msg.attach(part2)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)

        print(f"Email notification sent successfully ({len(products)} products)")

    except Exception as e:
        print(f"Error sending email: {e}")
        raise


def main():
    """Main function"""
    # Configuration
    collection_id_str = os.environ.get('COLLECTION_ID', '223')
    collection_id = int(collection_id_str) if collection_id_str else 223  # 223 = THE MONSTERS
    keyword = os.environ.get('KEYWORD', '')  # Optional: filter by keyword (e.g., "LABUBU")

    # Check for debug mode
    debug_mode = os.environ.get('DEBUG_MODE', 'false').lower() == 'true'

    # Get email configuration from environment variables
    smtp_server = os.environ.get('SMTP_SERVER')
    smtp_port = int(os.environ.get('SMTP_PORT', '587'))
    smtp_username = os.environ.get('SMTP_USERNAME')
    smtp_password = os.environ.get('SMTP_PASSWORD')
    recipient_email = os.environ.get('RECIPIENT_EMAIL')

    # In debug mode, email configuration is optional
    if not debug_mode and not all([smtp_server, smtp_username, smtp_password, recipient_email]):
        print("Error: Missing email configuration. Please set environment variables:")
        print("  SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, RECIPIENT_EMAIL")
        sys.exit(1)

    print(f"Checking POP MART stock (Collection ID: {collection_id})")
    if keyword:
        print(f"Filtering by keyword: {keyword}")
    print(f"Timestamp: {get_jst_now().strftime('%Y-%m-%d %H:%M:%S')} (JST)")
    if debug_mode:
        print("DEBUG MODE: ON")

    # Check for in-stock products
    in_stock_products = check_stock(collection_id=collection_id, keyword=keyword, debug=debug_mode)

    if in_stock_products:
        # Load previous stock status
        previous_stock = load_previous_stock()
        previous_product_ids = set(previous_stock.get('product_ids', []))

        # Get current product IDs
        current_product_ids = {p['id'] for p in in_stock_products}

        # Find newly added products (not in previous stock)
        new_product_ids = current_product_ids - previous_product_ids
        new_products = [p for p in in_stock_products if p['id'] in new_product_ids]

        print(f"✓ Found {len(in_stock_products)} product(s) in stock!")
        if new_products:
            print(f"✓ {len(new_products)} new product(s) detected!")
            if not debug_mode:
                send_email_notification(
                    smtp_server,
                    smtp_port,
                    smtp_username,
                    smtp_password,
                    recipient_email,
                    new_products
                )
            else:
                print("(Debug mode: email not sent)")
        else:
            print("✓ No new products (all already notified)")

        # Save current stock status
        save_current_stock(current_product_ids)
    else:
        print("✗ No products in stock")
        # Clear stock history when no products in stock
        save_current_stock(set())


if __name__ == "__main__":
    main()
