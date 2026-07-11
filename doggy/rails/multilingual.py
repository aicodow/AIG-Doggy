"""多语言拒绝消息动作。"""

DEFAULT_REFUSALS: dict[str, dict[str, str]] = {
    "content_safety": {
        "en": "I'm sorry, I can't respond to that.",
        "zh": "抱歉，我无法回应此内容。",
        "ja": "申し訳ありませんが、その内容には応答できません。",
        "ko": "죄송합니다만, 해당 내용에 응답할 수 없습니다.",
        "es": "Lo siento, no puedo responder a eso.",
        "de": "Es tut mir leid, ich kann darauf nicht antworten.",
        "fr": "Désolé, je ne peux pas répondre à cela.",
    },
    "topic_control": {
        "en": "This topic is outside my service scope.",
        "zh": "抱歉，此话题超出了我的服务范围。",
        "ja": "このトピックはサービス範囲外です。",
        "ko": "이 주제는 서비스 범위를 벗어납니다.",
    },
    "jailbreak": {
        "en": "I'm sorry, I can't process this request.",
        "zh": "抱歉，我无法处理此请求。",
        "ja": "このリクエストは処理できません。",
        "ko": "이 요청을 처리할 수 없습니다.",
    },
    "pii": {
        "en": "Please do not share personal information.",
        "zh": "请勿在对话中分享个人隐私数据。",
        "ja": "会話の中で個人情報を共有しないでください。",
        "ko": "대화에서 개인정보를 공유하지 마십시오.",
    },
}


def get_refusal_message(language: str = "en", reason: str = "content_safety") -> str:
    """根据语言和原因获取拒绝消息。

    Args:
        language: 语言代码 (en/zh/ja/ko/es/de/fr)，默认 en。
        reason: 拒绝原因 (content_safety/topic_control/jailbreak/pii)。

    Returns:
        对应语言的拒绝消息字符串。
    """
    reason_msgs = DEFAULT_REFUSALS.get(reason, DEFAULT_REFUSALS["content_safety"])
    return reason_msgs.get(language, reason_msgs["en"])
