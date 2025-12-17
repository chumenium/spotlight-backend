"""
S3 & CloudFront ユーティリティ
ファイルのアップロードとURL生成を管理
"""
import boto3
import io
from werkzeug.utils import secure_filename
from flask import current_app
import os


def get_s3_client():
    """S3クライアントを取得"""
    config = current_app.config
    access_key = config.get('AWS_ACCESS_KEY_ID')
    secret_key = config.get('AWS_SECRET_ACCESS_KEY')
    
    # AWS認証情報が設定されていない場合のエラーチェック
    if not access_key or not secret_key:
        raise ValueError(
            "AWS認証情報が設定されていません。"
            "環境変数 AWS_ACCESS_KEY_ID と AWS_SECRET_ACCESS_KEY を設定してください。"
        )
    
    return boto3.client(
        's3',
        region_name=config.get('S3_REGION', 'ap-northeast-1'),
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    )


def upload_to_s3(file_data, folder, filename, content_type='application/octet-stream', bucket_name=None):
    """
    S3にファイルをアップロード
    
    Args:
        file_data: バイナリデータ（bytes）
        folder: S3内のフォルダパス（例: "movie", "picture", "audio", "thumbnail"）
        filename: ファイル名
        content_type: MIMEタイプ
        bucket_name: バケット名（指定しない場合は設定から取得）
    
    Returns:
        str: アップロードされたファイルのキー（パス）
    """
    try:
        s3 = get_s3_client()
        if bucket_name is None:
            bucket = current_app.config.get('S3_BUCKET_NAME', 'spotlight-contents')
        else:
            bucket = bucket_name
        
        # セキュアなファイル名に変換
        safe_filename = secure_filename(filename)
        key = f"{folder}/{safe_filename}"
        
        # バイナリデータをアップロード
        # ACLが無効化されているバケットでも動作するように、まずACLなしで試行
        try:
            s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=file_data,
                ContentType=content_type,
                ACL='private'  # CloudFront経由でアクセスするためprivate
            )
        except Exception as acl_error:
            # ACLが無効化されている場合はACLなしで再試行
            if 'AccessControlListNotSupported' in str(acl_error) or 'InvalidArgument' in str(acl_error):
                s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=file_data,
                    ContentType=content_type
                )
            else:
                raise
        
        return key
    
    except Exception as e:
        raise


def get_cloudfront_url(folder, filename):
    """
    CloudFront URLを生成
    
    Args:
        folder: フォルダパス
        filename: ファイル名
    
    Returns:
        str: CloudFront URL
    """
    config = current_app.config
    cloudfront_domain = config.get('CLOUDFRONT_DOMAIN', '')
    # config.pyのデフォルト値'True'に合わせる
    use_cloudfront = config.get('USE_CLOUDFRONT', True)
    
    if use_cloudfront and cloudfront_domain:
        # CloudFront URLを使用
        safe_filename = secure_filename(filename)
        return f"https://{cloudfront_domain}/{folder}/{safe_filename}"
    else:
        # S3直接URL（フォールバック）
        bucket = config.get('S3_BUCKET_NAME', 'spotlight-contents')
        region = config.get('S3_REGION', 'ap-northeast-1')
        safe_filename = secure_filename(filename)
        return f"https://{bucket}.s3.{region}.amazonaws.com/{folder}/{safe_filename}"


def normalize_content_url(path):
    """
    DBから取得したパスをCloudFront URLに正規化
    
    Args:
        path: DBから取得したパス（相対パスまたはCloudFront URL）
    
    Returns:
        str: CloudFront URL（既に絶対URLの場合はそのまま返す）
    """
    if not path or not isinstance(path, str):
        return path or ''
    
    path = path.strip()
    
    # 既に絶対URL（CloudFront URLまたはS3 URL）の場合はそのまま返す（早期リターンで最適化）
    if path.startswith('http://') or path.startswith('https://'):
        return path
    
    # テキスト投稿の場合はそのまま返す（早期リターンで最適化）
    # テキスト投稿はURLではなくテキスト内容なので、そのまま返す
    if not path.startswith('/') and '/' not in path:
        # パスにスラッシュが含まれていない場合はテキスト投稿の可能性が高い
        # ただし、movie/filename.mp4のような形式の場合は処理する
        return path
    
    # アイコンパスの場合、CloudFront URLに変換
    # 例: /icon/filename.png -> https://d30se1secd7t6t.cloudfront.net/icon/filename.png
    if path.startswith('/icon/'):
        filename = path.replace('/icon/', '')
        return get_cloudfront_url('icon', filename)
    
    # 相対パスの場合、CloudFront URLに変換
    # 例: /content/movie/filename.mp4 -> https://d30se1secd7t6t.cloudfront.net/movie/filename.mp4
    if path.startswith('/content/'):
        # /content/movie/filename.mp4 -> movie/filename.mp4
        path_parts = path.replace('/content/', '').split('/', 1)
        if len(path_parts) == 2:
            folder = path_parts[0]  # movie, picture, audio, thumbnail
            filename = path_parts[1]
            return get_cloudfront_url(folder, filename)
    
    # movie/filename.mp4, picture/filename.jpg, audio/filename.mp3 のような形式の場合
    # 例: movie/filename.mp4 -> https://d30se1secd7t6t.cloudfront.net/movie/filename.mp4
    if '/' in path and not path.startswith('/'):
        path_parts = path.split('/', 1)
        if len(path_parts) == 2:
            folder = path_parts[0]  # movie, picture, audio, thumbnail, icon
            filename = path_parts[1]
            # 有効なフォルダ名かチェック
            if folder in ['movie', 'picture', 'audio', 'thumbnail', 'icon']:
                return get_cloudfront_url(folder, filename)
    
    # その他の形式の場合はそのまま返す（テキスト投稿など）
    return path


def list_s3_content_files(folders=None, bucket_name=None):
    """
    S3バケット内のコンテンツファイルをリストアップ
    spotlight-contentsバケットのmovie、picture、audioフォルダから取得
    
    Args:
        folders: 取得するフォルダのリスト（例: ["movie", "picture", "audio"]）
                 Noneの場合はすべてのコンテンツフォルダ（movie, picture, audio）を取得
        bucket_name: バケット名（Noneの場合はspotlight-contentsを使用）
    
    Returns:
        list: ファイル情報のリスト [{"folder": "movie", "filename": "xxx.mp4"}, ...]
    """
    try:
        s3 = get_s3_client()
        if bucket_name is None:
            bucket = current_app.config.get('S3_BUCKET_NAME', 'spotlight-contents')
        else:
            bucket = bucket_name
        
        if folders is None:
            folders = ['movie', 'picture', 'audio']
        
        all_files = []
        
        for folder in folders:
            try:
                # S3バケット内のファイルをリストアップ
                response = s3.list_objects_v2(
                    Bucket=bucket,
                    Prefix=f"{folder}/",
                    Delimiter='/'
                )
                
                if 'Contents' in response:
                    for obj in response['Contents']:
                        # フォルダ名自体は除外
                        key = obj['Key']
                        if key.endswith('/'):
                            continue
                        
                        # ファイル名を抽出（folder/filename形式からfilenameのみ）
                        filename = key.split('/')[-1]
                        if filename:  # 空でない場合のみ追加
                            all_files.append({
                                'folder': folder,
                                'filename': filename,
                                'key': key
                            })
            except Exception as e:
                continue
        
        return all_files
    
    except Exception as e:
        return []


def get_random_s3_content(bucket_name=None):
    """
    S3バケット内からランダムなコンテンツファイルを取得
    spotlight-contentsバケットのmovie、picture、audioフォルダからランダムに選択
    
    Args:
        bucket_name: バケット名（Noneの場合はspotlight-contentsを使用）
    
    Returns:
        dict: ランダムに選択されたファイル情報 {"folder": "movie", "filename": "xxx.mp4", "key": "movie/xxx.mp4"}
              Noneの場合はコンテンツが見つからない
    """
    import random
    
    files = list_s3_content_files(bucket_name=bucket_name)
    
    if not files:
        return None
    
    # ランダムに1件選択
    return random.choice(files)


def get_content_type_from_extension(content_type, extension):
    """
    拡張子からContent-Typeを決定
    
    Args:
        content_type: コンテンツタイプ（"video", "image", "audio"）
        extension: ファイル拡張子
    
    Returns:
        str: MIMEタイプ
    """
    mime_map = {
        'video': {
            'mp4': 'video/mp4',
            'mov': 'video/quicktime',
            'avi': 'video/x-msvideo'
        },
        'image': {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif'
        },
        'audio': {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4'
        }
    }
    
    if content_type in mime_map:
        return mime_map[content_type].get(extension.lower(), 'application/octet-stream')
    
    return 'application/octet-stream'



from urllib.parse import urlparse
from flask import current_app

def extract_s3_key_from_url(url):
    """
    CloudFront/S3 の URL から S3 の key（フォルダ/ファイル名）を抽出。
    例:
      https://xxx.cloudfront.net/icon/a.png → icon/a.png
    """
    if not url:
        return None

    try:
        path = urlparse(url).path  # "/icon/a.png"
        key = path.lstrip("/")      # "icon/a.png"
        return key
    except Exception:
        return None


def delete_from_s3(key, bucket_name=None):
    """
    S3 からオブジェクトを削除（key と bucket を指定）。
    bucket が None の場合はデフォルトバケットを使う。
    アプリケーションコンテキストなしでも動作するように環境変数から直接取得。
    """
    try:
        import os
        from flask import has_app_context
        
        # アプリケーションコンテキストがある場合はそれを使用、ない場合は環境変数から取得
        if has_app_context():
            try:
                if bucket_name is None:
                    bucket = current_app.config.get('S3_BUCKET_NAME', 'spotlight-contents')
                else:
                    bucket = bucket_name
                access_key = current_app.config.get('AWS_ACCESS_KEY_ID')
                secret_key = current_app.config.get('AWS_SECRET_ACCESS_KEY')
                region = current_app.config.get('S3_REGION', 'ap-northeast-1')
            except (RuntimeError, AttributeError):
                # フォールバック: 環境変数から取得
                if bucket_name is None:
                    bucket = os.getenv('S3_BUCKET_NAME', 'spotlight-contents')
                else:
                    bucket = bucket_name
                access_key = os.getenv('AWS_ACCESS_KEY_ID')
                secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                region = os.getenv('S3_REGION', 'ap-northeast-1')
        else:
            # アプリケーションコンテキストがない場合は環境変数から直接取得
            if bucket_name is None:
                bucket = os.getenv('S3_BUCKET_NAME', 'spotlight-contents')
            else:
                bucket = bucket_name
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            region = os.getenv('S3_REGION', 'ap-northeast-1')
        
        # S3クライアントを作成
        if access_key and secret_key:
            s3 = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            )
        else:
            # 認証情報がない場合はデフォルトの認証情報を使用（IAMロールなど）
            s3 = boto3.client('s3', region_name=region)

        s3.delete_object(Bucket=bucket, Key=key)

        return True

    except Exception as e:
        return False


def delete_file_from_url(url):
    """
    CloudFront URL を元に S3 のファイルを削除する統合関数。
    ・URLからkeyを抽出（例: https://xxx.cloudfront.net/movie/xxx.mp4 → movie/xxx.mp4）
    ・全て spotlight-contents バケットに統一
    """
    key = extract_s3_key_from_url(url)
    if not key:
        return False

    # 全て spotlight-contents バケットに統一
    # bucket_name=None を指定すると delete_from_s3 内でデフォルトバケット（spotlight-contents）を使用
    return delete_from_s3(key, bucket_name=None)
