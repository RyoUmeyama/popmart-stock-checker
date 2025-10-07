# POP MART 在庫チェッカー

POP MARTのTHE MONSTERS（ラブブ等）コレクションの在庫状況を自動でチェックし、入荷時にメール通知するシステムです。

## 機能

- 5分ごとに自動チェック
- 在庫ありの商品を検出したらメール通知
- キーワードフィルタリング（オプション、例: "LABUBU", "ラブブ"）
- ページネーション対応（全商品を自動取得）
- 商品ごとの在庫状況表示（SKU別）
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
- 在庫がある場合のみメール通知が送信されます

## ローカルでのテスト

デバッグモードで動作確認：

```bash
# 依存関係をインストール
pip install -r requirements.txt

# デバッグモードで実行（メール送信なし）
DEBUG_MODE=true python check_stock.py

# キーワードフィルタを指定
DEBUG_MODE=true KEYWORD=LABUBU python check_stock.py
```

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

## ライセンス

MIT License

## 注意事項

- APIの過度な使用は避けてください
- チェック頻度は適切に設定してください
