# POP MART 在庫チェッカー

POP MARTのTHE MONSTERS（ラブブ等）コレクションの在庫状況を自動でチェックし、入荷時にメール通知するシステムです。

## 機能

- 5分ごとに自動チェック
- **新規入荷商品のみメール通知**（重複通知を防止）
- **再販予定商品の検知とメール通知**（upTime検知機能）
- キーワードフィルタリング（オプション、例: "LABUBU", "ラブブ"）
- ページネーション対応（全商品を自動取得）
- 商品ごとの在庫状況表示（SKU別）
- 在庫変動の追跡（前回との差分検知）
- **全商品リスト表示ツール**（`list_all_products.py`）
- **視覚的なHTMLレポート生成**（`generate_html_report.py`）
- GitHub Actions で完全無料運用（publicリポジトリ）

## セットアップ手順

### 1. GitHubリポジトリの作成

1. GitHubにログイン
2. 新しい**public**リポジトリを作成（GitHub Actions無料枠を使用するため）
3. このフォルダの内容をリポジトリにプッシュ

```bash
cd popmart-stock-checker
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. メール設定（Gmail の例）

#### Gmailでアプリパスワードを生成

1. Googleアカウントにログイン
2. [アプリパスワード](https://myaccount.google.com/apppasswords) にアクセス
3. 「アプリを選択」→「その他（カスタム名）」→「popmart-checker」
4. 「生成」をクリック
5. 表示された16桁のパスワードをコピー

### 3. GitHub Secretsの設定

リポジトリの `Settings` → `Secrets and variables` → `Actions` → `New repository secret` で以下を追加：

#### 必須のSecrets

| Secret名 | 値 | 例 |
|---------|-----|-----|
| `SMTP_SERVER` | SMTPサーバー | `smtp.gmail.com` |
| `SMTP_PORT` | SMTPポート | `587` |
| `SMTP_USERNAME` | メールアドレス | `your-email@gmail.com` |
| `SMTP_PASSWORD` | アプリパスワード | `abcd efgh ijkl mnop` |
| `RECIPIENT_EMAIL` | 通知先メールアドレス | `your-email@gmail.com` |

#### オプションのSecrets

| Secret名 | 値 | 説明 | デフォルト |
|---------|-----|-----|-----|
| `COLLECTION_ID` | コレクションID | THE MONSTERSは223、Disneyは241 | `223` |
| `KEYWORD` | フィルタキーワード | 商品名でフィルタ（例: `LABUBU`）。設定しない場合は全商品をチェック | なし（全商品） |
| `DEBUG_MODE` | デバッグモード | `true` でメール送信をスキップ（ログのみ） | `false` |

### 4. 動作確認

1. リポジトリの `Actions` タブを開く
2. `Check POP MART Stock` ワークフローを選択
3. `Run workflow` をクリックして手動実行
4. 実行ログを確認

### 5. 自動実行

設定が完了すると、5分ごとに自動実行されます。
- GitHub ActionsのログでチェックステータスとSKU別在庫状況を確認できます
- **新しく在庫が追加された商品のみメール通知が送信されます**
- **再販予定商品が検知された場合もメール通知が送信されます**
- 既に通知済みの商品は2回目以降スキップされます（重複通知防止）

#### 通知ロジック

##### 在庫通知
1. **初回検出**: 在庫ありの商品を発見 → メール送信 → 商品IDを記録
2. **2回目以降**: 同じ商品が在庫あり → メール送信しない
3. **新商品入荷**: 新しい商品IDを検出 → メール送信
4. **全て売り切れ**: 履歴をクリア → 次回再入荷時に再度通知

このロジックにより、予約商品など長期間在庫がある商品について繰り返し通知されることを防ぎます。

##### 再販予定通知（upTime検知機能）
1. **再販予定検知**: `upTime`が未来の日時の商品を発見 → メール送信 → 商品IDを記録
2. **2回目以降**: 同じ商品が再販予定 → メール送信しない
3. **新たな再販予定**: 新しい商品IDで再販予定を検出 → メール送信
4. **再販開始**: `upTime`が過去になると履歴をクリア → 在庫通知に切り替え

**例**: "THE MONSTERS PIN FOR LOVE シリーズ" が 2025-10-23 15:00 に販売開始予定の場合、事前にメール通知が送信されます。

## ローカルでのテスト

デバッグモードで動作確認：

```bash
# 依存関係をインストール
pip install -r requirements.txt

# デバッグモードで実行（メール送信なし）
DEBUG_MODE=true python check_stock.py

# キーワードフィルタを指定
DEBUG_MODE=true KEYWORD=LABUBU python check_stock.py

# 在庫履歴をリセット
rm stock_history.json

# 全商品リストを表示
python list_all_products.py

# 特定のキーワードでフィルタ
python list_all_products.py --filter "LABUBU"

# 売り切れ商品も含めて全て表示
python list_all_products.py --show-all

# 別のコレクションを指定
python list_all_products.py --collection-id 241

# HTMLレポートを生成してブラウザで開く
python list_all_products.py && python generate_html_report.py && open stock_report.html
```

**注意**: ローカルテストでは以下のファイルが作成されます。これらのファイルは在庫追跡に使用されるため、`.gitignore` に追加済みです：
- `stock_history.json` - 在庫履歴
- `uptime_history.json` - 再販予定履歴（upTime追跡）
- `all_products.json` - 全商品データ（JSON）
- `stock_report.html` - 視覚的なHTMLレポート

## カスタマイズ

### チェック頻度を変更

`.github/workflows/check-stock.yml` の `cron` 設定を変更：

```yaml
schedule:
  # 現在の設定（5分ごと）
  - cron: '*/5 * * * *'

  # 3時間ごと
  - cron: '0 */3 * * *'

  # 毎日1回（0:00 UTC = 9:00 JST）
  - cron: '0 0 * * *'
```

**注意**: 頻繁なチェックはGitHub Actionsの実行時間を消費します。publicリポジトリは無制限ですが、APIへの負荷を考慮してください。

### 他のコレクションをチェック

コレクションIDを確認：
1. POP MARTのコレクションページを開く
2. URLから数字を確認（例: `/collection/223`）
3. `COLLECTION_ID` Secretに設定

## 信頼性機能

### SMTPリトライロジック

メール送信の信頼性を向上させるため、自動リトライ機能を実装しています：

- **最大3回まで自動再試行**: 一時的なネットワークエラーやSMTP接続問題に対応
- **30秒のタイムアウト**: 長時間の接続待ちを防止
- **5秒の待機時間**: 各リトライ間隔
- **詳細なログ出力**: 成功/失敗/リトライ状況を明確に表示

#### 対象エラー

以下のエラーが発生した場合、自動的に再試行します：
- `SMTPServerDisconnected`: SMTP接続が予期せず切断
- `SMTPConnectError`: SMTP接続エラー
- `TimeoutError`: 接続タイムアウト

#### ログ例

```
⚠ SMTP connection error (attempt 1/3): Connection unexpectedly closed
  Retrying in 5 seconds...
✓ Email sent successfully to recipient@example.com
```

全ての試行が失敗した場合のみ、エラーとしてワークフローが失敗します。

## トラブルシューティング

### メールが届かない

1. GitHub Actionsのログを確認
2. Secretsが正しく設定されているか確認
3. Gmailの場合、アプリパスワードを使用しているか確認
4. スパムフォルダを確認
5. **Gmail SMTP認証エラー（454エラー）が発生する場合**:
   - GitHub ActionsのIPアドレスがGmailにブロックされている可能性があります
   - `DEBUG_MODE` Secretを `true` に設定してメール送信をスキップし、ログで在庫状況を確認できます
   - 別のSMTPサービス（SendGrid、Mailgun等）の使用を検討してください

### 一時的なSMTP接続エラー

**症状**: `Connection unexpectedly closed` エラーが時々発生

**原因**: Gmail SMTPサーバーまたはGitHub Actionsの一時的なネットワーク問題

**対策**: 自動リトライロジックにより3回まで再試行されます。ほとんどの一時的なエラーは自動的に解決されます

### ワークフローが実行されない

- リポジトリが長期間更新されていない場合、GitHub Actionsが自動的に無効化されることがあります
- `Actions` タブから手動で有効化してください

### 在庫があるのにメールが来ない / 再販予定なのにメールが来ない

- `KEYWORD` Secretを設定している場合、キーワードに一致しない商品は通知されません
- キーワードフィルタを解除するには `KEYWORD` Secretを削除してください
- **既に通知済みの商品は再度通知されません**。これは重複通知を防ぐための仕様です
- 在庫履歴をリセットしたい場合は、GitHub Actionsの `Actions` → `Caches` から `stock-history-` で始まるキャッシュを削除してください
- upTime履歴も同様に `stock-history-` キャッシュに含まれます

## API仕様

POP MARTは以下のCDN APIを使用（ページネーション対応）：

```
https://cdn-global.popmart.com/shop_productoncollection-{COLLECTION_ID}-1-{PAGE}-jp-ja.json
```

- `{COLLECTION_ID}`: コレクションID（例: 223 = THE MONSTERS, 241 = Disney）
- `{PAGE}`: ページ番号（1から開始、404が返るまで自動取得）

レスポンス例：
```json
{
  "total": 101,
  "name": "THE MONSTERS",
  "productData": [
    {
      "id": "5737",
      "title": "商品名",
      "skus": [
        {
          "price": 2255,
          "stock": {
            "onlineStock": 10
          },
          "currency": "JPY"
        }
      ]
    }
  ]
}
```

**在庫判定**: `skus[].stock.onlineStock > 0` の場合、在庫ありと判定します。

## 技術詳細

### メール送信モジュール (email_utils.py)

プロジェクトには堅牢なメール送信ユーティリティ (`email_utils.py`) が含まれています。

#### 使用方法

```python
from email_utils import send_email_with_retry

success = send_email_with_retry(
    smtp_server='smtp.gmail.com',
    smtp_port=587,
    username='your@email.com',
    password='app_password',
    from_email='your@email.com',
    to_email='recipient@email.com',
    subject='件名',
    text_content='プレーンテキスト',
    html_content='<html>HTMLコンテンツ</html>',
    max_retries=3,
    retry_delay=5,
    timeout=30
)
```

#### 特徴

- 自動リトライ（デフォルト3回）
- タイムアウト設定（デフォルト30秒）
- 詳細なログ出力
- HTML/テキスト両対応

このモジュールは他のプロジェクトでも再利用可能です。

### 全商品リスト表示ツール (list_all_products.py)

コレクション内の全商品と在庫状況を一覧表示するツールです。

#### 使用方法

```bash
# 基本的な使い方（在庫ありの商品のみ表示）
python list_all_products.py

# 売り切れ商品も含めて全て表示
python list_all_products.py --show-all

# 商品名でフィルタリング
python list_all_products.py --filter "PIN FOR LOVE"
python list_all_products.py --filter "LABUBU" --show-all

# 別のコレクションを指定
python list_all_products.py --collection-id 241
```

#### 出力

- コンソール: 在庫状況のサマリーと商品リスト
- `all_products.json`: 全商品データ（JSON形式）

#### 表示内容

- 商品ID
- 商品名
- 在庫状況（SKU別）
- 新着/人気バッジ
- 商品URL

このツールは、特定の商品の在庫状況を手動で確認したい場合や、コレクション全体の商品数を把握したい場合に便利です。

### HTMLレポート生成ツール (generate_html_report.py)

`all_products.json` から視覚的なHTMLレポートを生成するツールです。

#### 使用方法

```bash
# 基本的な使い方
python generate_html_report.py

# カスタム入出力ファイル
python generate_html_report.py --input all_products.json --output stock_report.html

# ワンライナーで全て実行
python list_all_products.py && python generate_html_report.py && open stock_report.html
```

#### 特徴

- **美しいデザイン**: グラデーション背景とカードレイアウト
- **統計サマリー**: 総商品数、在庫あり、売り切れの数を一目で確認
- **フィルタリング機能**: 全て / 在庫あり / 売り切れ / 新着 / 人気
- **商品カード**:
  - 🆕 NEW バッジ（新着商品）
  - 🔥 HOT バッジ（人気商品）
  - 在庫状況（色分け：緑=在庫あり、赤=売り切れ）
  - 商品ページへの直リンク
- **レスポンシブデザイン**: スマートフォンでも見やすい

#### 出力例

HTMLレポートは以下の情報を含みます：
- コレクション名とID
- 更新日時（JST）
- 在庫状況の統計
- 全商品の詳細（フィルタ可能）

ブラウザで開くと、視覚的に全商品の在庫状況を確認できます。

### 在庫変動検知の仕組み

#### 在庫履歴（stock_history.json）
在庫履歴は `stock_history.json` に保存され、GitHub Actions Cacheで実行間で永続化されます：

```json
{
  "product_ids": ["5737", "4110", ...],
  "timestamp": "2025-10-07T13:42:15.123456"
}
```

- 前回チェック時に在庫があった商品IDのリストを記録
- 新しいチェックで検出された商品IDと比較
- 差分（新規に在庫が追加された商品）のみメール通知
- 全商品が在庫切れの場合は履歴をクリア（再入荷時に通知するため）

#### upTime履歴（uptime_history.json）
再販予定商品の履歴は `uptime_history.json` に保存されます：

```json
{
  "product_ids": ["6935", "6936", ...],
  "timestamp": "2025-10-22T16:50:15.123456"
}
```

- 前回チェック時に再販予定だった商品IDのリストを記録
- 新しいチェックで検出された商品IDと比較
- 差分（新規に再販予定が追加された商品）のみメール通知
- 再販予定がなくなった場合は履歴をクリア

**upTimeの判定ロジック**:
- `upTime > 現在時刻`: 販売開始前（予約可能） → "カートに入れる"
- `upTime < 現在時刻` かつ `onlineStock > 0`: 販売中（在庫あり） → "カートに入れる"
- `upTime < 現在時刻` かつ `onlineStock = 0`: 売り切れ → "再入荷を通知"

### GitHub Actions Cache

- キーパターン: `stock-history-{run_id}`
- リストアキー: `stock-history-` （最新のキャッシュを自動取得）
- キャッシュは7日間保持されます（GitHub Actions仕様）

## ライセンス

MIT License

## 注意事項

- APIの過度な使用は避けてください
- チェック頻度は適切に設定してください
