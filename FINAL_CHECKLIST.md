# フロントエンド・バックエンド 最終確認チェックリスト

## ✅ バックエンド側の確認

### 1. S3 & CloudFront設定
- [x] `config.py`にCloudFrontドメイン設定済み: `d30se1secd7t6t.cloudfront.net`
- [x] `utils/s3.py`にS3アップロード機能実装済み
- [x] `utils/s3.py`にCloudFront URL生成機能実装済み
- [x] `utils/s3.py`に既存データ互換性機能（`normalize_content_url`）実装済み

### 2. コンテンツアップロードAPI
- [x] `POST /api/content/add` - S3にアップロード後、CloudFront URLを返す
- [x] 動画・画像・音声・サムネイルをS3にアップロード
- [x] CloudFront URLをDBに保存

### 3. コンテンツ取得API
- [x] `POST /api/content/detail` - 既存データの相対パスをCloudFront URLに変換
- [x] `POST /api/content/serch` - 検索結果のサムネイルURLを正規化
- [x] `POST /api/users/getusercontents` - ユーザーコンテンツ一覧のサムネイルURLを正規化
- [x] `POST /api/users/getspotlightcontents` - スポットライト一覧のサムネイルURLを正規化
- [x] `POST /api/content/getplaylistdetail` - プレイリスト詳細のサムネイルURLを正規化

### 4. アイコン処理
- [x] `POST /api/users/changeicon` - バックエンドサーバーに保存（S3には保存しない）
- [x] `GET /icon/<filename>` - バックエンドサーバーから配信
- [x] アイコンパスは相対パス `/icon/{filename}` 形式で返す

### 5. 環境変数設定
- [x] `.env`ファイルの設定方法をドキュメント化
- [x] AWS認証情報の設定方法を説明
- [x] CloudFrontドメインの設定確認

## ✅ フロントエンド側の確認

### 1. 設定ファイル
- [x] `lib/config/app_config.dart` - CloudFront URL設定済み: `d30se1secd7t6t.cloudfront.net`
- [x] `lib/config/app_config.dart` - バックエンドURL設定済み

### 2. コンテンツURL処理
- [x] `lib/models/post.dart` - `_buildFullUrl`関数で絶対URLを自動判定
- [x] `lib/models/post.dart` - CloudFront URLはそのまま使用
- [x] `lib/models/post.dart` - コンテンツとサムネイルは`mediaBaseUrl`（CloudFront）と結合

### 3. アイコンURL処理
- [x] `lib/models/post.dart` - アイコンは`backendUrl`（バックエンドサーバー）と結合
- [x] `lib/models/comment.dart` - コメント内のアイコンURL処理実装済み

### 4. エラーハンドリング
- [x] 絶対URLの自動判定機能実装済み
- [x] 相対パスの場合の適切な処理

## 📋 動作確認項目

### バックエンド側
1. [ ] `.env`ファイルにAWS認証情報が設定されている
2. [ ] `boto3`がインストールされている
3. [ ] コンテンツアップロードが正常に動作する
4. [ ] CloudFront URLが正しく生成される
5. [ ] 既存データ（相対パス）がCloudFront URLに変換される
6. [ ] アイコンがバックエンドサーバーから配信される

### フロントエンド側
1. [ ] CloudFront URLが正しく表示される
2. [ ] サムネイルが正しく表示される
3. [ ] アイコンが正しく表示される
4. [ ] 既存データ（相対パス）が正しく処理される
5. [ ] 新規データ（CloudFront URL）が正しく処理される

## 🔍 確認すべきポイント

### 1. 環境変数の設定
```env
AWS_ACCESS_KEY_ID=your-aws-access-key-id
AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
CLOUDFRONT_DOMAIN=d30se1secd7t6t.cloudfront.net
S3_BUCKET_NAME=spotlight-contents
S3_REGION=ap-northeast-1
USE_CLOUDFRONT=True
```

**注意:** 実際のAWS認証情報は`.env`ファイルに設定してください。このファイルには含めないでください。

### 2. S3バケットの構造
```
spotlight-contents/
├── movie/          # 動画ファイル
├── picture/        # 画像ファイル
├── audio/         # 音声ファイル
└── thumbnail/     # サムネイル画像
```

### 3. URL形式の確認

**コンテンツURL（CloudFront経由）:**
- 動画: `https://d30se1secd7t6t.cloudfront.net/movie/{filename}.mp4`
- 画像: `https://d30se1secd7t6t.cloudfront.net/picture/{filename}.jpg`
- 音声: `https://d30se1secd7t6t.cloudfront.net/audio/{filename}.mp3`
- サムネイル: `https://d30se1secd7t6t.cloudfront.net/thumbnail/{filename}_thumb.jpg`

**アイコンURL（バックエンドサーバー経由）:**
- アイコン: `http://54.150.123.156:5000/icon/{filename}.png`

## ⚠️ 注意事項

1. **既存データの互換性**
   - 古いデータ（相対パス）は自動的にCloudFront URLに変換される
   - 新規データは最初からCloudFront URLで保存される

2. **アイコンの処理**
   - アイコンはS3ではなくバックエンドサーバーに保存される
   - フロントエンド側で`backendUrl`と結合する必要がある

3. **エラーハンドリング**
   - CloudFront URLが404を返す場合の処理を確認
   - バックエンドサーバーがダウンした場合のアイコン表示を確認

## 🎯 次のステップ

1. バックエンドサーバーを起動
2. フロントエンドアプリを起動
3. コンテンツのアップロードをテスト
4. コンテンツの視聴をテスト
5. アイコンの表示をテスト
6. 既存データの表示をテスト

## ✅ 完了

すべての実装が完了し、動作確認の準備が整いました。

