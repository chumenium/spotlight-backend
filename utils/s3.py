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
                print(f"⚠️ ACLが無効化されているため、ACLなしでアップロードします: {key}")
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
        print(f"⚠️ S3アップロードエラー: {e}")
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
    
    # 既に絶対URL（CloudFront URLまたはS3 URL）の場合はそのまま返す
    if path.startswith('http://') or path.startswith('https://'):
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
    
    # その他の形式の場合はそのまま返す（テキスト投稿など）
    return path


def list_s3_content_files(folders=None):
    """
    S3バケット内のコンテンツファイルをリストアップ
    
    Args:
        folders: 取得するフォルダのリスト（例: ["movie", "picture", "audio"]）
                 Noneの場合はすべてのコンテンツフォルダを取得
    
    Returns:
        list: ファイル情報のリスト [{"folder": "movie", "filename": "xxx.mp4"}, ...]
    """
    try:
        s3 = get_s3_client()
        bucket = current_app.config.get('S3_BUCKET_NAME', 'spotlight-contents')
        
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
                print(f"⚠️ S3リスト取得エラー ({folder}): {e}")
                continue
        
        return all_files
    
    except Exception as e:
        print(f"⚠️ S3リスト取得エラー: {e}")
        return []


def get_random_s3_content():
    """
    S3バケット内からランダムなコンテンツファイルを取得
    
    Returns:
        dict: ランダムに選択されたファイル情報 {"folder": "movie", "filename": "xxx.mp4", "key": "movie/xxx.mp4"}
              Noneの場合はコンテンツが見つからない
    """
    import random
    
    files = list_s3_content_files()
    
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



def delete_from_s3(key, bucket_name=None):
    """
    S3にアップロードされたファイルを削除する

    Args:
        key: S3内のファイルパス（例: "movie/test.mp4"）
        bucket_name: バケット名（指定しない場合は設定から取得）

    Returns:
        bool: True（削除成功） / False（ファイルなし、または失敗）
    """
    try:
        s3 = get_s3_client()

        # バケット名取得
        # if bucket_name is None:
        #     bucket = current_app.config.get('S3_BUCKET_NAME', 'spotlight-contents')
        # else:
        bucket = bucket_name

        # 削除処理
        response = s3.delete_object(
            Bucket=bucket,
            Key=key
        )

        # 削除成功か判定（S3は存在しないキーでも成功扱いになる）  
        return True
    
    except Exception as e:
        print(f"⚠️ S3削除エラー: {e}")
        return False


from urllib.parse import urlparse

def extract_s3_key_from_url(url):
    """
    CloudFront/S3 の URL から key を抽出する
    例: https://xxx.cloudfront.net/icon/a.png → icon/a.png
    """
    try:
        path = urlparse(url).path  # /icon/a.png
        print(path)
        return path.lstrip('/')    # icon/a.png へ変換
    except Exception:
        return None

def delete_file_from_url(url, bucket_name=None):
    key = extract_s3_key_from_url(url)
    if not key:
        print("キーの抽出に失敗しました")
        return False
    print(key)
    return delete_from_s3(key, bucket_name=bucket_name)