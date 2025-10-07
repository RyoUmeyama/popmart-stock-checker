# POP MART 在庫チェッカー

POP MARTのTHE MONSTERS（ラブブ等）コレクションの在庫状況を自動でチェックし、入荷時にメール通知するシステムです。

## 機能

- 6時間ごとに自動チェック
- 在庫ありの商品を検出したらメール通知
- キーワードフィルタリング（例: "LABUBU", "ラブブ"）
- GitHub Actions で完全無料運用

## セットアップ手順

### 1. GitHubリポジトリの作成

1. GitHubにログイン
2. 新しいリポジトリを作成（public/privateどちらでも可）
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
| `COLLECTION_ID` | コレクションID | THE MONSTERSは223 | `223` |
| `KEYWORD` | フィルタキーワード | 例: `LABUBU` または `ラブブ` | なし（全商品） |

### 4. 動作確認

1. リポジトリの `Actions` タブを開く
2. `Check POP MART Stock` ワークフローを選択
3. `Run workflow` をクリックして手動実行
4. 実行ログを確認

### 5. 自動実行

設定が完了すると、6時間ごとに自動実行されます：
- 0:00, 6:00, 12:00, 18:00 (UTC)
- 日本時間: 9:00, 15:00, 21:00, 3:00

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
  # 3時間ごと
  - cron: '0 */3 * * *'

  # 毎日1回（9:00 JST）
  - cron: '0 0 * * *'
```

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

### ワークフローが実行されない

- リポジトリが長期間更新されていない場合、GitHub Actionsが自動的に無効化されることがあります
- `Actions` タブから手動で有効化してください

## API仕様

POP MARTは以下のCDN APIを使用：

```
https://cdn-global.popmart.com/shop_productoncollection-{COLLECTION_ID}-1-1-jp-ja.json
```

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

## ライセンス

MIT License

## 注意事項

- APIの過度な使用は避けてください
- チェック頻度は適切に設定してください
