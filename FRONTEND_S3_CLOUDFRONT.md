# フロントエンド側：S3 & CloudFront 対応ガイド

このドキュメントでは、バックエンドがS3とCloudFrontを使用するようになった際に、フロントエンド側で必要な対応を説明します。

## 📋 目次

1. [変更点の概要](#変更点の概要)
2. [URL形式の変更](#url形式の変更)
3. [コンテンツ表示の対応](#コンテンツ表示の対応)
4. [CORS設定の確認](#cors設定の確認)
5. [エラーハンドリング](#エラーハンドリング)
6. [キャッシュの扱い](#キャッシュの扱い)
7. [実装例](#実装例)

---

## 変更点の概要

### 以前（ローカルファイル配信）
- コンテンツURL: 相対パス（例: `content/movie/filename.mp4`）
- 配信方法: EC2サーバーから直接配信

### 現在（S3 & CloudFront配信）
- コンテンツURL: 絶対URL（例: `https://d30se1secd7t6t.cloudfront.net/movie/filename.mp4`）
- 配信方法: CloudFront経由でS3から配信

### 影響を受けるAPIレスポンス

以下のAPIレスポンスで、URL形式が変更されます：

1. **POST `/api/content/add`**
   - `contentpath`: CloudFront URL
   - `thumbnailpath`: CloudFront URL

2. **POST `/api/content/detail`**
   - `contentpath`: CloudFront URL
   - `iconimgpath`: アイコンURL（変更なし）

3. **POST `/api/content/getplaylistdetail`**
   - `thumbnailpath`: CloudFront URL

4. **POST `/api/content/serch`**
   - `thumbnailurl`: CloudFront URL

5. **その他のコンテンツ一覧API**
   - サムネイルやコンテンツのURLがCloudFront URLに変更

---

## URL形式の変更

### 変更前（相対パス）

```json
{
  "contentpath": "content/movie/filename.mp4",
  "thumbnailpath": "content/thumbnail/filename_thumb.jpg"
}
```

### 変更後（CloudFront URL）

```json
{
  "contentpath": "https://d30se1secd7t6t.cloudfront.net/movie/filename.mp4",
  "thumbnailpath": "https://d30se1secd7t6t.cloudfront.net/thumbnail/filename_thumb.jpg"
}
```

### 対応方法

**重要**: フロントエンド側では、APIから返されたURLをそのまま使用できます。相対パスから絶対URLへの変換処理は不要です。

```dart
// ❌ 不要な処理（削除）
String getFullUrl(String path) {
  return 'https://your-api-domain.com/$path';
}

// ✅ 正しい実装（APIから返されたURLをそのまま使用）
String contentUrl = response.data['contentpath'];
// 例: "https://d30se1secd7t6t.cloudfront.net/movie/filename.mp4"
```

---

## コンテンツ表示の対応

### 1. 画像の表示

画像（サムネイル、アイコン）は、CloudFront URLをそのまま使用できます。

#### Flutter (Dart) の例

```dart
// サムネイル表示
Image.network(
  contentData['thumbnailpath'], // CloudFront URL
  fit: BoxFit.cover,
  errorBuilder: (context, error, stackTrace) {
    return Icon(Icons.error);
  },
)

// アイコン表示
CircleAvatar(
  backgroundImage: NetworkImage(userData['iconimgpath']),
)
```

#### React/Next.js の例

```jsx
// サムネイル表示
<img 
  src={contentData.thumbnailpath} 
  alt={contentData.title}
  onError={(e) => {
    e.target.src = '/default-thumbnail.jpg';
  }}
/>

// Next.js Image コンポーネント使用時
<Image
  src={contentData.thumbnailpath}
  alt={contentData.title}
  width={300}
  height={200}
  onError={() => setError(true)}
/>
```

### 2. 動画の表示

動画プレーヤーでCloudFront URLを使用します。

#### Flutter (Dart) の例

```dart
import 'package:video_player/video_player.dart';

// 動画プレーヤーの初期化
VideoPlayerController _controller = VideoPlayerController.networkUrl(
  Uri.parse(contentData['contentpath']), // CloudFront URL
);

await _controller.initialize();
_controller.play();
```

#### React の例

```jsx
<video 
  src={contentData.contentpath} 
  controls
  onError={(e) => {
    console.error('動画読み込みエラー:', e);
  }}
>
  お使いのブラウザは動画タグをサポートしていません。
</video>
```

### 3. 音声の表示

音声プレーヤーでCloudFront URLを使用します。

#### Flutter (Dart) の例

```dart
import 'package:audioplayers/audioplayers.dart';

final player = AudioPlayer();
await player.play(UrlSource(contentData['contentpath'])); // CloudFront URL
```

#### React の例

```jsx
<audio 
  src={contentData.contentpath} 
  controls
  onError={(e) => {
    console.error('音声読み込みエラー:', e);
  }}
>
  お使いのブラウザは音声タグをサポートしていません。
</audio>
```

---

## CORS設定の確認

CloudFrontから配信されるコンテンツにブラウザからアクセスするには、CloudFront DistributionでCORS設定が必要です。

### CloudFront側の設定確認

1. AWSコンソールでCloudFront Distributionを開く
2. 「Behaviors」タブを選択
3. デフォルトの動作（`*`）を編集
4. 「Response headers policy」でCORS設定を確認

### 必要なCORSヘッダー

CloudFront Distributionで以下のCORSヘッダーが返されることを確認：

- `Access-Control-Allow-Origin: *` または特定のドメイン
- `Access-Control-Allow-Methods: GET, HEAD, OPTIONS`
- `Access-Control-Allow-Headers: *`

### フロントエンド側での確認

ブラウザの開発者ツールで、CloudFront URLへのリクエストを確認：

1. **Network タブ**を開く
2. CloudFront URLにアクセス
3. レスポンスヘッダーにCORSヘッダーが含まれているか確認

**エラーが発生する場合:**
```
Access to fetch at 'https://xxx.cloudfront.net/...' from origin 'https://your-app.com' 
has been blocked by CORS policy
```

→ CloudFront DistributionのCORS設定を確認してください。

---

## エラーハンドリング

### 1. 画像読み込みエラー

CloudFront URLが無効な場合や、ファイルが存在しない場合のエラーハンドリングを実装します。

#### Flutter (Dart) の例

```dart
Image.network(
  contentData['thumbnailpath'],
  fit: BoxFit.cover,
  loadingBuilder: (context, child, loadingProgress) {
    if (loadingProgress == null) return child;
    return Center(
      child: CircularProgressIndicator(
        value: loadingProgress.expectedTotalBytes != null
            ? loadingProgress.cumulativeBytesLoaded /
                loadingProgress.expectedTotalBytes!
            : null,
      ),
    );
  },
  errorBuilder: (context, error, stackTrace) {
    // デフォルト画像を表示
    return Image.asset('assets/default-thumbnail.png');
  },
)
```

#### React の例

```jsx
const [imageError, setImageError] = useState(false);
const [imageLoading, setImageLoading] = useState(true);

<img
  src={imageError ? '/default-thumbnail.jpg' : contentData.thumbnailpath}
  onLoad={() => setImageLoading(false)}
  onError={() => {
    setImageError(true);
    setImageLoading(false);
  }}
  style={{ display: imageLoading ? 'none' : 'block' }}
/>
{imageLoading && <div>読み込み中...</div>}
```

### 2. 動画読み込みエラー

#### Flutter (Dart) の例

```dart
try {
  await _controller.initialize();
  _controller.play();
} catch (e) {
  print('動画読み込みエラー: $e');
  // エラーメッセージを表示
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('エラー'),
      content: Text('動画を読み込めませんでした。'),
    ),
  );
}
```

#### React の例

```jsx
const [videoError, setVideoError] = useState(false);

<video
  src={contentData.contentpath}
  controls
  onError={() => {
    setVideoError(true);
    console.error('動画読み込みエラー');
  }}
>
  {videoError && (
    <div>
      動画を読み込めませんでした。
    </div>
  )}
</video>
```

### 3. ネットワークエラー

CloudFrontへのアクセスが失敗した場合の処理を実装します。

```dart
// Flutter の例
try {
  final response = await http.get(Uri.parse(cloudFrontUrl));
  if (response.statusCode == 200) {
    // 正常
  } else if (response.statusCode == 403) {
    // アクセス拒否（OAC設定の問題の可能性）
    print('アクセスが拒否されました');
  } else if (response.statusCode == 404) {
    // ファイルが見つからない
    print('ファイルが見つかりません');
  }
} catch (e) {
  // ネットワークエラー
  print('ネットワークエラー: $e');
}
```

---

## キャッシュの扱い

CloudFrontは自動的にコンテンツをキャッシュします。フロントエンド側で追加のキャッシュ処理は基本的に不要です。

### CloudFrontのキャッシュ動作

- **初回アクセス**: S3から取得してキャッシュ
- **2回目以降**: CloudFrontのエッジロケーションから配信（高速）
- **キャッシュ期限**: CloudFront Distributionの設定に従う

### フロントエンド側での考慮事項

1. **画像のキャッシュ**
   - ブラウザが自動的にキャッシュするため、追加処理は不要
   - 必要に応じて、画像ライブラリのキャッシュ機能を使用

2. **動画のキャッシュ**
   - 動画プレーヤーが自動的にキャッシュを管理
   - 大きな動画ファイルは、Rangeリクエストで部分読み込み（CloudFrontが対応）

3. **キャッシュの無効化（開発時）**
   - 開発中に最新のコンテンツを確認したい場合:
     - ブラウザのキャッシュをクリア
     - または、CloudFront Distributionでキャッシュを無効化

---

## 実装例

### Flutter (Dart) の完全な実装例

```dart
import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class ContentDetailPage extends StatefulWidget {
  final Map<String, dynamic> contentData;

  const ContentDetailPage({Key? key, required this.contentData}) : super(key: key);

  @override
  State<ContentDetailPage> createState() => _ContentDetailPageState();
}

class _ContentDetailPageState extends State<ContentDetailPage> {
  VideoPlayerController? _controller;
  bool _isVideoError = false;

  @override
  void initState() {
    super.initState();
    _initializeVideo();
  }

  Future<void> _initializeVideo() async {
    try {
      final contentUrl = widget.contentData['contentpath'];
      
      // CloudFront URLをそのまま使用
      _controller = VideoPlayerController.networkUrl(
        Uri.parse(contentUrl),
      );
      
      await _controller!.initialize();
      _controller!.play();
      
      setState(() {});
    } catch (e) {
      print('動画初期化エラー: $e');
      setState(() {
        _isVideoError = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.contentData['title'])),
      body: Column(
        children: [
          // サムネイル表示
          Image.network(
            widget.contentData['thumbnailpath'],
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) {
              return Container(
                height: 200,
                color: Colors.grey,
                child: Icon(Icons.error),
              );
            },
          ),
          
          // 動画プレーヤー
          if (_controller != null && !_isVideoError)
            AspectRatio(
              aspectRatio: _controller!.value.aspectRatio,
              child: VideoPlayer(_controller!),
            )
          else if (_isVideoError)
            Container(
              height: 200,
              color: Colors.grey,
              child: Center(
                child: Text('動画を読み込めませんでした'),
              ),
            ),
          
          // コンテンツ情報
          Padding(
            padding: EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  widget.contentData['title'],
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 8),
                Text('投稿者: ${widget.contentData['username']}'),
                Text('再生回数: ${widget.contentData['playnum']}'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }
}
```

### React の完全な実装例

```jsx
import React, { useState, useEffect, useRef } from 'react';

function ContentDetail({ contentData }) {
  const [videoError, setVideoError] = useState(false);
  const [imageError, setImageError] = useState(false);
  const videoRef = useRef(null);

  useEffect(() => {
    // 動画エラーハンドリング
    const video = videoRef.current;
    if (video) {
      video.addEventListener('error', () => {
        setVideoError(true);
      });
    }
  }, []);

  return (
    <div className="content-detail">
      {/* サムネイル */}
      <img
        src={imageError ? '/default-thumbnail.jpg' : contentData.thumbnailpath}
        alt={contentData.title}
        onError={() => setImageError(true)}
        style={{ width: '100%', height: 'auto' }}
      />

      {/* 動画プレーヤー */}
      {!videoError ? (
        <video
          ref={videoRef}
          src={contentData.contentpath}
          controls
          style={{ width: '100%' }}
        >
          お使いのブラウザは動画タグをサポートしていません。
        </video>
      ) : (
        <div className="video-error">
          動画を読み込めませんでした。
        </div>
      )}

      {/* コンテンツ情報 */}
      <div className="content-info">
        <h2>{contentData.title}</h2>
        <p>投稿者: {contentData.username}</p>
        <p>再生回数: {contentData.playnum}</p>
      </div>
    </div>
  );
}

export default ContentDetail;
```

---

## チェックリスト

フロントエンド側で実装すべき項目：

- [ ] APIレスポンスのURL形式がCloudFront URLになっていることを確認
- [ ] 相対パスから絶対URLへの変換処理を削除（不要）
- [ ] 画像表示でCloudFront URLをそのまま使用
- [ ] 動画表示でCloudFront URLをそのまま使用
- [ ] 音声表示でCloudFront URLをそのまま使用
- [ ] 画像読み込みエラーハンドリングを実装
- [ ] 動画読み込みエラーハンドリングを実装
- [ ] ネットワークエラーハンドリングを実装
- [ ] CORSエラーが発生しないことを確認
- [ ] デフォルト画像/動画のフォールバックを実装

---

## トラブルシューティング

### 問題1: CORSエラーが発生する

**エラーメッセージ:**
```
Access to fetch at 'https://xxx.cloudfront.net/...' from origin '...' 
has been blocked by CORS policy
```

**解決方法:**
1. CloudFront DistributionのCORS設定を確認
2. バックエンド担当者に連絡して、CloudFront側の設定を確認

### 問題2: 画像が表示されない

**確認事項:**
1. CloudFront URLが正しいか（ブラウザで直接アクセスして確認）
2. エラーハンドリングが実装されているか
3. ネットワークタブでエラーレスポンスを確認

### 問題3: 動画が再生されない

**確認事項:**
1. CloudFront URLが正しいか
2. 動画ファイル形式がサポートされているか（MP4推奨）
3. 動画プレーヤーのエラーハンドリングを確認

---

## 参考情報

- [CloudFront CORS設定](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/header-caching.html#header-caching-web-cors)
- [Flutter Video Player](https://pub.dev/packages/video_player)
- [React Video要素](https://developer.mozilla.org/ja/docs/Web/HTML/Element/video)

---

**最終更新**: 2024年11月  
**バージョン**: 1.0.0

