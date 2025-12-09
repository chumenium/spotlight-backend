# 管理者API ドキュメント

## 概要

管理者専用のAPIエンドポイント一覧です。すべてのエンドポイントは以下の共通仕様があります：

- **認証**: JWT認証必須（`@jwt_required`デコレータ）
- **権限**: 管理者権限が必要（`uid_admin_auth(uid)`でチェック）
- **メソッド**: すべてPOSTメソッド
- **レスポンス形式**: JSON形式
- **エラーハンドリング**: 管理者以外からのアクセスの場合は400エラーを返す

---

## エンドポイント一覧

### 1. `/api/admin/getuser` - 全ユーザ情報取得

**説明**: システム内の全ユーザ情報を取得します。ページネーション対応（最大300件ずつ）。

**リクエスト**:
```json
{
  "offset": 0
}
```

**リクエストパラメータ**:
- `offset` (integer, 必須): 取得開始位置（0, 300, 600...のように300件ずつ増やす）

**レスポンス（成功）**:
```json
{
  "status": "success",
  "userdatas": [
    {
      "userID": "ユーザのID",
      "username": "ユーザ名",
      "iconimgpath": "ユーザアイコンのURL（CloudFront URL）",
      "admin": false,
      "spotlightnum": 10,
      "reportnum": 2,
      "reportednum": 0
    }
  ]
}
```

**レスポンスフィールド説明**:
- `userID`: ユーザの一意ID
- `username`: ユーザ名
- `iconimgpath`: ユーザアイコンのURL（CloudFront URL形式）
- `admin`: 管理者フラグ（`true`/`false`）
- `spotlightnum`: そのユーザの合計スポットライト数
- `reportnum`: ユーザが通報した数
- `reportednum`: ユーザが関連するコンテンツ・コメントが通報された回数

**ステータスコード**: 200（成功）、400（エラー）

---

### 2. `/api/admin/enableadmin` - ユーザを管理者にする

**説明**: 指定されたユーザを管理者権限に変更します。

**リクエスト**:
```json
{
  "userID": "対象ユーザのID"
}
```

**リクエストパラメータ**:
- `userID` (string, 必須): 管理者にしたいユーザのID

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "{userID}を管理者に変更"
}
```

**ステータスコード**: 200（成功）、400（エラー）

---

### 3. `/api/admin/disableadmin` - ユーザを一般ユーザにする

**説明**: 指定されたユーザの管理者権限を解除し、一般ユーザに変更します。

**リクエスト**:
```json
{
  "userID": "対象ユーザのID"
}
```

**リクエストパラメータ**:
- `userID` (string, 必須): 一般ユーザにしたいユーザのID

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "{userID}を一般ユーザに変更"
}
```

**ステータスコード**: 200（成功）、400（エラー）

---

### 4. `/api/admin/content` - コンテンツ情報取得

**説明**: システム内の全コンテンツ情報を取得します。ページネーション対応（最大300件ずつ）。

**リクエスト**:
```json
{
  "offset": 0
}
```

**リクエストパラメータ**:
- `offset` (integer, 必須): 取得開始位置（0, 300, 600...のように300件ずつ増やす）

**レスポンス（成功）**:
```json
{
  "status": "success",
  "contents": [
    {
      "contentID": "コンテンツのID",
      "spotlightnum": 5,
      "playnum": 100,
      "contentpath": "コンテンツURL（CloudFront URL）",
      "thumbnailpath": "サムネイルURL（CloudFront URL）",
      "title": "コンテンツタイトル",
      "tag": "タグ",
      "posttimestamp": "2024-01-01 12:00:00",
      "userID": "投稿したユーザのID",
      "username": "ユーザネーム",
      "commentnum": 3,
      "reportnum": 1
    }
  ]
}
```

**レスポンスフィールド説明**:
- `contentID`: コンテンツの一意ID
- `spotlightnum`: コンテンツのスポットライト数
- `playnum`: 再生回数
- `contentpath`: コンテンツURL（CloudFront URL形式）
- `thumbnailpath`: サムネイルURL（CloudFront URL形式）
- `title`: コンテンツタイトル
- `tag`: タグ
- `posttimestamp`: コンテンツの投稿時間
- `userID`: 投稿したユーザのID
- `username`: ユーザネーム
- `commentnum`: コメント数
- `reportnum`: 通報された件数

**ステータスコード**: 200（成功）、400（エラー）

---

### 5. `/api/admin/report` - 通報情報取得

**説明**: システム内の全通報情報を取得します。ページネーション対応（最大300件ずつ）。

**リクエスト**:
```json
{
  "offset": 0
}
```

**リクエストパラメータ**:
- `offset` (integer, 必須): 取得開始位置（0, 300, 600...のように300件ずつ増やす）

**レスポンス（成功）**:
```json
{
  "status": "success",
  "reports": [
    {
      "reportID": "通報のID",
      "reporttype": "content",
      "reportuidID": "通報したユーザのID",
      "username": "通報したユーザの名前",
      "targetuidID": "通報されたユーザのID",
      "targetusername": "通報されたユーザの名前",
      "contentID": "通報されたコンテンツのID",
      "comCTID": "通報されたコメントのコンテンツID",
      "comCMID": "通報されたコメントのコメントID",
      "commenttext": "コメントテキスト",
      "title": "通報されたコンテンツのタイトル",
      "processflag": false,
      "reason": "通報の理由",
      "detail": "通報の詳細（任意）",
      "reporttimestamp": "2024-01-01 12:00:00"
    }
  ]
}
```

**レスポンスフィールド説明**:
- `reportID`: 通報の一意ID
- `reporttype`: 通報の種類（`"user"`, `"content"`, `"comment"`）
- `reportuidID`: 通報したユーザのID
- `username`: 通報したユーザの名前
- `targetuidID`: 通報されたユーザのID（該当する場合）
- `targetusername`: 通報されたユーザの名前（該当する場合）
- `contentID`: 通報されたコンテンツのID（該当する場合）
- `comCTID`: 通報されたコメントのコンテンツID（該当する場合）
- `comCMID`: 通報されたコメントのコメントID（該当する場合）
- `commenttext`: コメントテキスト（該当する場合）
- `title`: 通報されたコンテンツのタイトル（該当する場合）
- `processflag`: 通報の処理状態（`true`/`false`）
- `reason`: 通報の理由
- `detail`: 通報の詳細（任意、`null`の場合あり）
- `reporttimestamp`: 通報の時間

**ステータスコード**: 200（成功）、400（エラー）

---

### 6. `/api/admin/deletecontent` - コンテンツ削除

**説明**: 指定されたコンテンツを削除します。S3からもファイルが削除されます。

**リクエスト**:
```json
{
  "contentID": "削除したいコンテンツのID"
}
```

**リクエストパラメータ**:
- `contentID` (string, 必須): 削除したいコンテンツのID

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "該当コンテンツを削除"
}
```

**ステータスコード**: 200（成功）、400（エラー）

**注意**: この操作は不可逆です。コンテンツとS3上のファイルが削除されます。

---

### 7. `/api/admin/deletecomment` - コメント削除

**説明**: 指定されたコメントを削除します。

**リクエスト**:
```json
{
  "contentID": "コメントがあるコンテンツのID",
  "commentID": "削除したいコメントのID"
}
```

**リクエストパラメータ**:
- `contentID` (string, 必須): 削除したいコメントがあるコンテンツのID
- `commentID` (string, 必須): 削除したいコメントのID

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "該当コメントを削除"
}
```

**ステータスコード**: 200（成功）、400（エラー）

---

### 8. `/api/admin/processreport` - 通報を処理済みにする

**説明**: 指定された通報を処理済みにマークします。

**リクエスト**:
```json
{
  "reportID": "処理したい通報のID"
}
```

**リクエストパラメータ**:
- `reportID` (string, 必須): 処理したい通報のID

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "通報を処理"
}
```

**ステータスコード**: 200（成功）、400（エラー）

---

### 9. `/api/admin/unprocessreport` - 通報の処理済みを解除

**説明**: 指定された通報の処理済み状態を解除します。

**リクエスト**:
```json
{
  "reportID": "処理解除したい通報のID"
}
```

**リクエストパラメータ**:
- `reportID` (string, 必須): 処理解除したい通報のID

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "通報を処理解除"
}
```

**ステータスコード**: 200（成功）、400（エラー）

---

## エラーレスポンス

すべてのエンドポイントで、以下のエラーレスポンスが返される可能性があります：

### 管理者権限なし
```json
{
  "status": "error",
  "message": "管理者以外からのアクセス"
}
```
**ステータスコード**: 400

### その他のエラー
```json
{
  "status": "error",
  "message": "エラーメッセージ"
}
```
**ステータスコード**: 400

---

## 認証ヘッダー

すべてのリクエストには、JWTトークンを含む認証ヘッダーが必要です：

```
Authorization: Bearer <JWT_TOKEN>
```

---

## ページネーション

`/api/admin/getuser`、`/api/admin/content`、`/api/admin/report`エンドポイントは、ページネーションに対応しています。

- 最大取得件数: 300件
- `offset`パラメータで取得開始位置を指定
- 例: 0（1-300件目）、300（301-600件目）、600（601-900件目）...

---

## 注意事項

1. **管理者権限**: すべてのエンドポイントは管理者権限が必要です。一般ユーザがアクセスした場合、400エラーが返されます。

2. **削除操作**: `/api/admin/deletecontent`と`/api/admin/deletecomment`は不可逆な操作です。実行前に十分確認してください。

3. **S3削除**: `/api/admin/deletecontent`でコンテンツを削除すると、S3上のファイルも自動的に削除されます。

4. **URL形式**: コンテンツやアイコンのURLは、CloudFront URL形式で返されます（例: `https://d30se1secd7t6t.cloudfront.net/movie/xxx.mp4`）。

