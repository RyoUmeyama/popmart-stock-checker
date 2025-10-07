# POP MART 在庫チェッカー

POP MARTのTHE MONSTERS（ラブブ等）コレクションの在庫状況を自動でチェックし、入荷時にメール通知するシステムです。

## 機能

- 5分ごとに自動チェック
- **新規入荷商品のみメール通知**（重複通知を防止）
- キーワードフィルタリング（オプション、例: "LABUBU", "ラブブ"）
- ページネーション対応（全商品を自動取得）
- 商品ごとの在庫状況表示（SKU別）
- 在庫変動の追跡（前回との差分検知）
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
- 既に通知済みの商品は2回目以降スキップされます（重複通知防止）

#### 通知ロジック

1. **初回検出**: 在庫ありの商品を発見 → メール送信 → 商品IDを記録
2. **2回目以降**: 同じ商品が在庫あり → メール送信しない
3. **新商品入荷**: 新しい商品IDを検出 → メール送信
4. **全て売り切れ**: 履歴をクリア → 次回再入荷時に再度通知

このロジックにより、予約商品など長期間在庫がある商品について繰り返し通知されることを防ぎます。

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
```

**注意**: ローカルテストでは `stock_history.json` が作成されます。このファイルは在庫追跡に使用されるため、`.gitignore` に追加済みです。

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

### ワークフローが実行されない

- リポジトリが長期間更新されていない場合、GitHub Actionsが自動的に無効化されることがあります
- `Actions` タブから手動で有効化してください

### 在庫があるのにメールが来ない

- `KEYWORD` Secretを設定している場合、キーワードに一致しない商品は通知されません
- キーワードフィルタを解除するには `KEYWORD` Secretを削除してください
- **既に通知済みの商品は再度通知されません**。これは重複通知を防ぐための仕様です
- 在庫履歴をリセットしたい場合は、GitHub Actionsの `Actions` → `Caches` から `stock-history-` で始まるキャッシュを削除してください

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

### 在庫変動検知の仕組み

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

### GitHub Actions Cache

- キーパターン: `stock-history-{run_id}`
- リストアキー: `stock-history-` （最新のキャッシュを自動取得）
- キャッシュは7日間保持されます（GitHub Actions仕様）

## ライセンス

MIT License

## 注意事項

- APIの過度な使用は避けてください
- チェック頻度は適切に設定してください
