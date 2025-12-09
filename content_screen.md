# コンテンツ画面API ドキュメント

## 概要

ホーム画面で表示するコンテンツを取得するAPIです。ランダム、新着順、古い順の3つの表示モードを切り替えることができます。

すべてのAPIは以下の共通仕様があります：
- **認証**: JWT認証必須（`@jwt_required`デコレータ）
- **メソッド**: POST
- **レスポンス形式**: JSON形式
- **取得件数**: 5件ずつ
- **ループ機能**: 最後の投稿まで行くと、最初の投稿にループ戻りします

---

## API一覧

### 1. `/api/content/getcontents/random` - 完全ランダム取得

**説明**: 完全ランダムで5件のコンテンツを取得します。重複を避けるために、既に取得したコンテンツIDを除外できます。

**エンドポイント**: `POST /api/content/getcontents/random`

**リクエスト**:
```json
{
  "excludeContentIDs": [1, 2, 3]
}
```

**リクエストパラメータ**:
- `excludeContentIDs` (array, 任意): 除外するコンテンツIDのリスト（重複防止用）

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "5件のコンテンツを取得",
  "data": [
    {
      "title": "コンテンツタイトル",
      "contentpath": "https://d30se1secd7t6t.cloudfront.net/movie/xxx.mp4",
      "thumbnailpath": "https://d30se1secd7t6t.cloudfront.net/thumbnail/xxx.jpg",
      "spotlightnum": 10,
      "posttimestamp": "2024-01-01T12:00:00",
      "playnum": 100,
      "link": "https://example.com",
      "username": "ユーザー名",
      "user_id": "ユーザーID",
      "iconimgpath": "https://d30se1secd7t6t.cloudfront.net/icon/xxx.png",
      "spotlightflag": false,
      "textflag": false,
      "commentnum": 5,
      "contentID": 123
    }
  ],
  "isLooped": false
}
```

**レスポンスフィールド説明**:
- `status`: ステータス（"success" または "error"）
- `message`: メッセージ
- `data`: コンテンツ情報の配列（最大5件）
  - `title`: コンテンツタイトル
  - `contentpath`: コンテンツURL（CloudFront URL）
  - `thumbnailpath`: サムネイルURL（CloudFront URL）
  - `spotlightnum`: スポットライト数
  - `posttimestamp`: 投稿日時（ISO 8601形式）
  - `playnum`: 再生回数
  - `link`: リンクURL
  - `username`: 投稿者名
  - `user_id`: 投稿者ID
  - `iconimgpath`: アイコンURL（CloudFront URL）
  - `spotlightflag`: スポットライトフラグ（現在のユーザーがスポットライトを当てているか）
  - `textflag`: テキスト投稿フラグ
  - `commentnum`: コメント数
  - `contentID`: コンテンツID
- `isLooped`: ループしたかどうか（最後まで行って最初に戻った場合`true`）

**ステータスコード**: 200（成功）、400（エラー）

**特徴**:
- 完全ランダムで取得（`ORDER BY RANDOM()`）
- テキスト投稿は除外
- ブロックしたユーザーのコンテンツは除外
- 重複を避けるために`excludeContentIDs`で除外IDを指定可能

---

### 2. `/api/content/getcontents/newest` - 新着順取得

**説明**: 新着順で5件のコンテンツを取得します。画面スクロール中に新着投稿があった場合は、その投稿を優先的に表示します。

**エンドポイント**: `POST /api/content/getcontents/newest`

**リクエスト**:
```json
{}
```

**リクエストパラメータ**: なし

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "5件のコンテンツを取得",
  "data": [
    {
      "title": "コンテンツタイトル",
      "contentpath": "https://d30se1secd7t6t.cloudfront.net/movie/xxx.mp4",
      "thumbnailpath": "https://d30se1secd7t6t.cloudfront.net/thumbnail/xxx.jpg",
      "spotlightnum": 10,
      "posttimestamp": "2024-01-01T12:00:00",
      "playnum": 100,
      "link": "https://example.com",
      "username": "ユーザー名",
      "user_id": "ユーザーID",
      "iconimgpath": "https://d30se1secd7t6t.cloudfront.net/icon/xxx.png",
      "spotlightflag": false,
      "textflag": false,
      "commentnum": 5,
      "contentID": 123
    }
  ],
  "isLooped": false
}
```

**レスポンスフィールド説明**: ランダム取得APIと同じ

**ステータスコード**: 200（成功）、400（エラー）

**特徴**:
- 新着投稿を優先的に表示（`LMcontentID`より大きいIDを優先）
- 投稿日時の降順で取得（`ORDER BY contentID DESC`）
- 最後まで行ったら最初に戻る（ループ機能）
- ブロックしたユーザーのコンテンツは除外

**動作**:
1. 新着投稿（`LMcontentID`より大きいID）を優先的に取得
2. 新着投稿が不足している場合、通常の新着順で取得
3. 最後まで行ったら最初に戻る（ループ）

---

### 3. `/api/content/getcontents/oldest` - 古い順取得

**説明**: 古い順で5件のコンテンツを取得します。画面スクロール中に新着投稿があった場合は、その投稿を最後のキューに入れます。

**エンドポイント**: `POST /api/content/getcontents/oldest`

**リクエスト**:
```json
{}
```

**リクエストパラメータ**: なし

**レスポンス（成功）**:
```json
{
  "status": "success",
  "message": "5件のコンテンツを取得",
  "data": [
    {
      "title": "コンテンツタイトル",
      "contentpath": "https://d30se1secd7t6t.cloudfront.net/movie/xxx.mp4",
      "thumbnailpath": "https://d30se1secd7t6t.cloudfront.net/thumbnail/xxx.jpg",
      "spotlightnum": 10,
      "posttimestamp": "2024-01-01T12:00:00",
      "playnum": 100,
      "link": "https://example.com",
      "username": "ユーザー名",
      "user_id": "ユーザーID",
      "iconimgpath": "https://d30se1secd7t6t.cloudfront.net/icon/xxx.png",
      "spotlightflag": false,
      "textflag": false,
      "commentnum": 5,
      "contentID": 123
    }
  ],
  "isLooped": false
}
```

**レスポンスフィールド説明**: ランダム取得APIと同じ

**ステータスコード**: 200（成功）、400（エラー）

**特徴**:
- 古い順で取得（`ORDER BY contentID ASC`）
- 新着投稿があれば最後のキューに入れる
- 最後まで行ったら最初に戻る（ループ機能）
- ブロックしたユーザーのコンテンツは除外

**動作**:
1. 通常の古い順で取得（`lastcontetid`より大きいID）
2. 新着投稿（`LMcontentID`より大きいID）があれば、最後のキューに追加
3. 不足分がある場合、最初から取得（ループ）

---

## エラーレスポンス

すべてのエンドポイントで、以下のエラーレスポンスが返される可能性があります：

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

## フロントエンド実装のヒント

### 表示モードの切り替え

フロントエンドで表示モードを切り替えるには、以下のように実装します：

```dart
enum ContentDisplayMode {
  random,   // ランダム
  newest,   // 新着順
  oldest    // 古い順
}

ContentDisplayMode currentMode = ContentDisplayMode.random;

// モードに応じてAPIエンドポイントを切り替え
String getApiEndpoint() {
  switch (currentMode) {
    case ContentDisplayMode.random:
      return '/api/content/getcontents/random';
    case ContentDisplayMode.newest:
      return '/api/content/getcontents/newest';
    case ContentDisplayMode.oldest:
      return '/api/content/getcontents/oldest';
  }
}
```

### ループ機能の実装

`isLooped`フラグを使用して、ループしたことをユーザーに通知できます：

```dart
if (response['isLooped'] == true) {
  // 最初に戻ったことをユーザーに通知
  showMessage('最初の投稿に戻りました');
}
```

### 重複防止（ランダムモード）

ランダムモードでは、既に取得したコンテンツIDを除外できます：

```dart
List<int> fetchedContentIDs = [];

// APIリクエスト時に除外IDを送信
Map<String, dynamic> requestBody = {
  'excludeContentIDs': fetchedContentIDs,
};

// レスポンスを受け取ったら、取得したIDを記録
for (var content in response['data']) {
  fetchedContentIDs.add(content['contentID']);
}
```

### 無限スクロールの実装

無限スクロールを実装する場合、最後のコンテンツIDを記録して、次のリクエストで使用します：

```dart
int? lastContentID;

// 次のページを取得
Future<void> loadNextPage() async {
  // 最後のコンテンツIDを記録
  if (lastContentID != null) {
    // 次のリクエストで使用（必要に応じて）
  }
  
  // APIリクエスト
  var response = await apiClient.post(
    getApiEndpoint(),
    body: requestBody,
  );
  
  // 最後のコンテンツIDを更新
  if (response['data'].isNotEmpty) {
    lastContentID = response['data'].last['contentID'];
  }
}
```

---

## 注意事項

1. **テキスト投稿の除外**: すべてのAPIで、テキスト投稿（`textflag = true`）は除外されます。

2. **ブロックユーザーの除外**: ブロックしたユーザー、またはブロックされているユーザーのコンテンツは自動的に除外されます。

3. **ループ機能**: 最後の投稿まで行くと、自動的に最初の投稿に戻ります。`isLooped`フラグでループしたことを検知できます。

4. **新着投稿の優先表示**: 新着順モードでは、画面スクロール中に新着投稿があった場合、その投稿を優先的に表示します。

5. **新着投稿のキュー**: 古い順モードでは、新着投稿があれば最後のキューに入れます。

6. **URL形式**: すべてのコンテンツURL、サムネイルURL、アイコンURLはCloudFront URL形式で返されます。

---

## 実装例（Dart/Flutter）

```dart
class ContentScreenAPI {
  final String baseUrl = 'https://your-backend-url.com';
  final String? token;
  
  ContentScreenAPI(this.token);
  
  Future<Map<String, dynamic>> getRandomContents({
    List<int>? excludeContentIDs,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/content/getcontents/random'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        if (excludeContentIDs != null)
          'excludeContentIDs': excludeContentIDs,
      }),
    );
    
    return jsonDecode(response.body);
  }
  
  Future<Map<String, dynamic>> getNewestContents() async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/content/getcontents/newest'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({}),
    );
    
    return jsonDecode(response.body);
  }
  
  Future<Map<String, dynamic>> getOldestContents() async {
    final response = await http.post(
      Uri.parse('$baseUrl/api/content/getcontents/oldest'),
      headers: {
        'Authorization': 'Bearer $token',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({}),
    );
    
    return jsonDecode(response.body);
  }
}
```

---

## まとめ

- **ランダム**: `/api/content/getcontents/random` - 完全ランダムで5件取得
- **新着順**: `/api/content/getcontents/newest` - 新着投稿を優先的に表示
- **古い順**: `/api/content/getcontents/oldest` - 新着投稿を最後のキューに

すべてのAPIでループ機能が実装されており、最後の投稿まで行くと自動的に最初の投稿に戻ります。

