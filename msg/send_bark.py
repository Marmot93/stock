import requests


def send_bark(bark_url: str, title: str, content: str):
    """
    通用的Bark消息推送函数
    :param bark_url: Bark推送链接
    :param title: 推送标题
    :param content: 推送内容
    :return: 是否发送成功
    """
    # 构建Bark URL
    if not bark_url.endswith('/'):
        bark_url += '/'
    
    notification_url = f"{bark_url}{title}/{content}"
    
    try:
        response = requests.get(notification_url)
        if response.status_code == 200:
            print(f"✅ 成功发送通知: {title}")
            return True
        else:
            print(f"❌ 发送通知失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 发送通知时发生异常: {e}")
        return False