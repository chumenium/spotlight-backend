from firebase_admin import messaging

def send_push_notification(token: str, title: str, body: str, data: dict = None):
    """
    FCMトークンに対してプッシュ通知を送信する関数
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=token,
            data=data or {},  # 任意の追加データ
        )

        response = messaging.send(message)
        print(f"📩通知送信できてる！！！！！！！！ Push Notification Sent! Response ID: {response}")
        return response

    except Exception as e:
        print(f"❌ 通知送信失敗！！！！！！！！Failed to send push notification: {e}")
        print("Token received:", repr(token))
        return None