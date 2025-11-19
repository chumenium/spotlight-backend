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


def upload_to_s3(file_data, folder, filename, content_type='application/octet-stream'):
    """
    S3にファイルをアップロード
    
    Args:
        file_data: バイナリデータ（bytes）
        folder: S3内のフォルダパス（例: "movie", "picture", "audio", "thumbnail"）
        filename: ファイル名
        content_type: MIMEタイプ
    
    Returns:
        str: アップロードされたファイルのキー（パス）
    """
    try:
        s3 = get_s3_client()
        bucket = current_app.config.get('S3_BUCKET_NAME', 'spotlight-contents')
        
        # セキュアなファイル名に変換
        safe_filename = secure_filename(filename)
        key = f"{folder}/{safe_filename}"
        
        # バイナリデータをアップロード
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=file_data,
            ContentType=content_type,
            ACL='private'  # CloudFront経由でアクセスするためprivate
        )
        
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

