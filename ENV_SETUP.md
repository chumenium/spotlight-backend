# 環境変数の設定方法

このドキュメントでは、SpotLightバックエンドの環境変数の設定方法を説明します。

## 📋 設定方法

### 方法1: `.env`ファイルを使用（推奨）

プロジェクトルートに`.env`ファイルを作成し、環境変数を設定します。

#### ステップ1: `.env`ファイルを作成

プロジェクトのルートディレクトリ（`app.py`がある場所）に`.env`ファイルを作成してください。

**Windows PowerShell:**
```powershell
# .env.exampleがある場合
Copy-Item .env.example .env

# または新規作成
New-Item .env
```

**Windows コマンドプロンプト:**
```cmd
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

#### ステップ2: `.env`ファイルを編集

`.env`ファイルをテキストエディタで開き、以下の内容を設定してください：

```env
# ============================================
# Flask設定
# ============================================
SECRET_KEY=your-secret-key-change-in-production
DEBUG=True
HOST=0.0.0.0
PORT=5000

# ============================================
# データベース設定
# ============================================
DB_HOST=localhost
DB_PORT=5432
DB_NAME=spotlight
DB_USER=toudai
DB_PASSWORD=kcsf2026

# ============================================
# JWT設定
# ============================================
JWT_SECRET=your-jwt-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_EXP_HOURS=24

# ============================================
# AWS S3 & CloudFront設定（必須）
# ============================================
S3_BUCKET_NAME=spotlight-contents
S3_REGION=ap-northeast-1
S3_ORIGIN_DOMAIN=spotlight-contents.s3.ap-northeast-1.amazonaws.com
CLOUDFRONT_DOMAIN=d30se1secd7t6t.cloudfront.net

# AWS認証情報（必須 - 実際の値に置き換えてください）
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key

# CloudFrontを使用するかどうか
USE_CLOUDFRONT=True
```

#### ステップ3: 実際の値を設定

**重要:** 以下の値を実際の値に置き換えてください：

1. **AWS認証情報**
   - `AWS_ACCESS_KEY_ID`: AWS IAMユーザーのアクセスキーID
   - `AWS_SECRET_ACCESS_KEY`: AWS IAMユーザーのシークレットアクセスキー
   - これらの値は、AWS IAMコンソールで作成したユーザーの認証情報です

2. **SECRET_KEY**（本番環境の場合）
   - ランダムな文字列を生成して設定してください
   - 例: `python -c "import secrets; print(secrets.token_hex(32))"`

3. **JWT_SECRET**（本番環境の場合）
   - ランダムな文字列を生成して設定してください

### 方法2: システムの環境変数として設定

`.env`ファイルを使用しない場合は、システムの環境変数として設定することもできます。

#### Windows PowerShell:
```powershell
$env:AWS_ACCESS_KEY_ID="your-access-key-id"
$env:AWS_SECRET_ACCESS_KEY="your-secret-access-key"
$env:CLOUDFRONT_DOMAIN="d30se1secd7t6t.cloudfront.net"
```

#### Windows コマンドプロンプト:
```cmd
set AWS_ACCESS_KEY_ID=your-access-key-id
set AWS_SECRET_ACCESS_KEY=your-secret-access-key
set CLOUDFRONT_DOMAIN=d30se1secd7t6t.cloudfront.net
```

#### macOS/Linux:
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export CLOUDFRONT_DOMAIN="d30se1secd7t6t.cloudfront.net"
```

## 🔐 セキュリティに関する注意事項

1. **`.env`ファイルはGitにコミットしないでください**
   - `.env`ファイルには機密情報が含まれています
   - `.gitignore`に`.env`が含まれていることを確認してください

2. **本番環境では必ず環境変数を設定してください**
   - デフォルト値は開発環境用です
   - 本番環境では強力な`SECRET_KEY`と`JWT_SECRET`を設定してください

3. **AWS認証情報の管理**
   - AWS認証情報は絶対に公開しないでください
   - IAMユーザーには最小限の権限（S3へのアクセスのみ）を付与してください

## ✅ 設定の確認

環境変数が正しく設定されているか確認するには、アプリケーションを起動してください：

```bash
python app.py
```

エラーが表示されない場合は、環境変数が正しく読み込まれています。

AWS認証情報が設定されていない場合、S3アップロード時に以下のエラーが表示されます：
```
ValueError: AWS認証情報が設定されていません。
環境変数 AWS_ACCESS_KEY_ID と AWS_SECRET_ACCESS_KEY を設定してください。
```

## 📝 必要な環境変数の一覧

### 必須（S3/CloudFrontを使用する場合）
- `AWS_ACCESS_KEY_ID`: AWSアクセスキーID
- `AWS_SECRET_ACCESS_KEY`: AWSシークレットアクセスキー
- `CLOUDFRONT_DOMAIN`: CloudFrontドメイン名

### 推奨（デフォルト値で動作しますが、本番環境では設定推奨）
- `SECRET_KEY`: Flaskの秘密鍵
- `JWT_SECRET`: JWTトークンの秘密鍵
- `S3_BUCKET_NAME`: S3バケット名（デフォルト: `spotlight-contents`）
- `S3_REGION`: S3リージョン（デフォルト: `ap-northeast-1`）
- `USE_CLOUDFRONT`: CloudFrontを使用するか（デフォルト: `True`）

### オプション
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: データベース設定
- `HOST`, `PORT`: サーバー設定
- `DEBUG`: デバッグモード（デフォルト: `False`）

