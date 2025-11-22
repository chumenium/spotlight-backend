# AWS S3 & CloudFront 接続設定ガイド

このドキュメントでは、SpotLightバックエンドをAWS S3とCloudFrontに接続するための設定手順を説明します。

## 📋 目次

1. [前提条件](#前提条件)
2. [AWS S3バケットの設定](#aws-s3バケットの設定)
3. [CloudFront Distributionの設定](#cloudfront-distributionの設定)
4. [IAMユーザーの作成と権限設定](#iamユーザーの作成と権限設定)
5. [環境変数の設定](#環境変数の設定)
6. [動作確認](#動作確認)
7. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

- AWSアカウントを持っていること
- EC2インスタンスにプロジェクトがデプロイ済みであること
- S3バケットとCloudFront Distributionが既に構築済みであること

---

## AWS S3バケットの設定

### 1. S3バケットの確認

1. AWSコンソールにログインし、S3サービスに移動
2. 使用するS3バケットを確認
3. バケット名とリージョンをメモしておく

### 2. バケットポリシーの確認

S3バケットがCloudFrontからのアクセスを許可しているか確認します。

**バケットポリシーの例（CloudFront OAC使用時）:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::account-id:distribution/distribution-id"
                }
            }
        }
    ]
}
```

### 3. ブロックパブリックアクセス設定

S3バケットはプライベートに設定されている必要があります。

1. S3バケットを選択
2. 「アクセス許可」タブを開く
3. 「ブロックパブリックアクセス」が有効になっていることを確認

---

## CloudFront Distributionの設定

### 1. CloudFront Distributionの確認

1. AWSコンソールでCloudFrontサービスに移動
2. 使用するDistributionを選択
3. **Distribution Domain Name**をメモしておく（例: `d30se1secd7t6t.cloudfront.net`）

### 2. Origin Access Control (OAC) の確認

CloudFrontでS3のプライベートコンテンツにアクセスするには、Origin Access Control (OAC) が設定されている必要があります。

1. CloudFront Distributionの「Origins」タブを開く
2. S3 Originを選択
3. 「Origin access」で「Origin access control settings (recommended)」が設定されていることを確認

### 3. キャッシュ動作の確認

1. CloudFront Distributionの「Behaviors」タブを開く
2. デフォルトの動作（`*`）を確認
3. 必要に応じて、以下の設定を確認：
   - **Viewer Protocol Policy**: `Redirect HTTP to HTTPS` または `HTTPS Only`（推奨）
   - **Allowed HTTP Methods**: `GET, HEAD, OPTIONS` または必要に応じて追加
   - **Cache Policy**: 適切なキャッシュポリシーを設定

---

## IAMユーザーの作成と権限設定

### 1. IAMユーザーの作成

1. AWSコンソールでIAMサービスに移動
2. 「ユーザー」→「ユーザーを追加」をクリック
3. ユーザー名を入力（例: `spotlight-s3-user`）
4. 「プログラムによるアクセス」を選択
5. 「ユーザーを作成」をクリック

### 2. アクセスキーの取得

1. 作成したIAMユーザーを選択
2. 「セキュリティ認証情報」タブを開く
3. 「アクセスキーを作成」をクリック
4. **アクセスキーID**と**シークレットアクセスキー**をメモしておく
   - ⚠️ **重要**: シークレットアクセスキーは一度しか表示されません

### 3. 権限ポリシーの設定

IAMユーザーにS3への読み書き権限を付与します。

1. IAMユーザーの「アクセス許可」タブを開く
2. 「直接アタッチされたポリシー」→「ポリシーをアタッチ」をクリック
3. 以下のポリシーを作成または選択：

**最小限の権限ポリシー（推奨）:**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "arn:aws:s3:::your-bucket-name"
        }
    ]
}
```

**注意**: `your-bucket-name` を実際のバケット名に置き換えてください。

---

## 環境変数の設定

### EC2サーバーでの設定

EC2サーバーにSSH接続し、プロジェクトルートディレクトリで`.env`ファイルを作成または編集します。

#### ステップ1: `.env`ファイルの作成

```bash
# プロジェクトルートディレクトリに移動
cd /path/to/spotlight-backend

# .envファイルを作成（既に存在する場合は編集）
nano .env
# または
vi .env
```

#### ステップ2: 環境変数の設定

`.env`ファイルに以下の内容を追加または更新します：

```env
# ============================================
# AWS S3 & CloudFront設定（必須）
# ============================================
S3_BUCKET_NAME=your-bucket-name
S3_REGION=ap-northeast-1
CLOUDFRONT_DOMAIN=d30se1secd7t6t.cloudfront.net

# AWS認証情報（必須 - IAMユーザーの認証情報）
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

# CloudFrontを使用するか（True/False）
USE_CLOUDFRONT=True
```

#### ステップ3: 実際の値に置き換え

以下の値を実際の値に置き換えてください：

| 環境変数 | 説明 | 取得方法 |
|---------|------|---------|
| `S3_BUCKET_NAME` | S3バケット名 | AWS S3コンソールで確認 |
| `S3_REGION` | S3リージョン（例: `ap-northeast-1`） | AWS S3コンソールで確認 |
| `CLOUDFRONT_DOMAIN` | CloudFront Distribution Domain Name | CloudFrontコンソールで確認（例: `d30se1secd7t6t.cloudfront.net`） |
| `AWS_ACCESS_KEY_ID` | IAMユーザーのアクセスキーID | IAMコンソールで作成したアクセスキー |
| `AWS_SECRET_ACCESS_KEY` | IAMユーザーのシークレットアクセスキー | IAMコンソールで作成したアクセスキー |

#### ステップ4: ファイルの保存と権限設定

```bash
# .envファイルを保存（nanoの場合は Ctrl+O → Enter → Ctrl+X）
# viの場合は :wq で保存して終了

# セキュリティのため、.envファイルの権限を制限
chmod 600 .env
```

### 設定値の確認例

```bash
# 環境変数が正しく読み込まれているか確認（オプション）
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('S3_BUCKET_NAME:', os.getenv('S3_BUCKET_NAME')); print('CLOUDFRONT_DOMAIN:', os.getenv('CLOUDFRONT_DOMAIN'))"
```

---

## 動作確認

### 1. アプリケーションの再起動

環境変数を設定した後、アプリケーションを再起動します。

```bash
# アプリケーションを停止（実行中の場合）
# Ctrl+C または
pkill -f "python.*app.py"

# アプリケーションを起動
python app.py
# または
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

### 2. エラーの確認

アプリケーション起動時にエラーが表示されないことを確認します。

**正常な場合:**
```
✅ Firebase Admin SDK initialized successfully.
SpotLight API Server Starting...
```

**エラーが表示される場合:**
- AWS認証情報が設定されていない場合:
  ```
  ValueError: AWS認証情報が設定されていません。
  環境変数 AWS_ACCESS_KEY_ID と AWS_SECRET_ACCESS_KEY を設定してください。
  ```
  → `.env`ファイルの設定を確認してください

### 3. テストアップロード

コンテンツをアップロードして、S3へのアップロードとCloudFront URLの生成が正常に動作するか確認します。

**APIエンドポイント:**
```
POST /api/content/add
```

**リクエスト例:**
```json
{
  "type": "image",
  "title": "テスト画像",
  "file": "base64エンコードされた画像データ",
  "thumbnail": "base64エンコードされたサムネイルデータ"
}
```

**正常なレスポンス:**
```json
{
  "status": "success",
  "message": "コンテンツを追加しました。",
  "data": {
    "contentID": 123,
    "contentpath": "https://d30se1secd7t6t.cloudfront.net/picture/filename.jpg",
    "thumbnailpath": "https://d30se1secd7t6t.cloudfront.net/thumbnail/filename_thumb.jpg"
  }
}
```

### 4. CloudFront URLの確認

レスポンスで返されたCloudFront URLにブラウザでアクセスし、コンテンツが正しく配信されるか確認します。

---

## トラブルシューティング

### 問題1: S3アップロードエラー

**エラーメッセージ:**
```
⚠️ S3アップロードエラー: An error occurred (AccessDenied) when calling the PutObject operation
```

**解決方法:**
1. IAMユーザーの権限を確認
2. S3バケット名が正しいか確認
3. IAMユーザーに適切な権限が付与されているか確認

### 問題2: CloudFront URLがアクセスできない

**エラーメッセージ:**
```
403 Forbidden
Access Denied
```

**解決方法:**
1. CloudFront DistributionのOrigin Access Control (OAC) 設定を確認
2. S3バケットポリシーがCloudFrontからのアクセスを許可しているか確認
3. CloudFront Distributionがデプロイ済みか確認（デプロイには数分かかることがあります）

### 問題3: ACLエラー

**エラーメッセージ:**
```
⚠️ ACLが無効化されているため、ACLなしでアップロードします
```

**説明:**
これはエラーではありません。新しいS3バケットではACLが無効化されている場合があり、コードが自動的にACLなしでアップロードを再試行します。正常な動作です。

### 問題4: 環境変数が読み込まれない

**解決方法:**
1. `.env`ファイルがプロジェクトルート（`app.py`がある場所）にあるか確認
2. `.env`ファイルの構文エラーがないか確認（`=`の前後にスペースを入れない）
3. アプリケーションを再起動

### 問題5: CloudFront URLが生成されない

**確認事項:**
1. `CLOUDFRONT_DOMAIN`環境変数が正しく設定されているか
2. `USE_CLOUDFRONT=True`が設定されているか
3. CloudFront Distribution Domain Nameが正しいか（`https://`は含めない）

---

## セキュリティのベストプラクティス

### 1. IAMユーザーの権限

- **最小限の権限の原則**: IAMユーザーには必要最小限の権限のみを付与
- **特定のバケットへのアクセスのみ**: すべてのS3バケットへのアクセス権限は付与しない

### 2. アクセスキーの管理

- **定期的なローテーション**: アクセスキーは定期的に更新する
- **漏洩時の対応**: アクセスキーが漏洩した場合は、すぐに無効化して新しいキーを発行

### 3. .envファイルの保護

- **権限設定**: `.env`ファイルの権限を`600`に設定（所有者のみ読み書き可能）
- **Git管理外**: `.env`ファイルは`.gitignore`に含まれていることを確認

### 4. CloudFrontのセキュリティ

- **HTTPSのみ**: CloudFront DistributionでHTTPSのみを許可
- **Origin Access Control**: S3バケットへの直接アクセスをブロックし、CloudFront経由のみ許可

---

## 参考リンク

- [AWS S3 ドキュメント](https://docs.aws.amazon.com/s3/)
- [AWS CloudFront ドキュメント](https://docs.aws.amazon.com/cloudfront/)
- [AWS IAM ドキュメント](https://docs.aws.amazon.com/iam/)
- [Boto3 ドキュメント](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

---

## サポート

設定で問題が発生した場合は、以下を確認してください：

1. AWSコンソールでの設定が正しいか
2. 環境変数が正しく設定されているか
3. IAMユーザーの権限が適切か
4. CloudFront Distributionがデプロイ済みか

問題が解決しない場合は、チームチャットまたはIssueで報告してください。

---

**最終更新**: 2024年11月  
**バージョン**: 1.0.0

