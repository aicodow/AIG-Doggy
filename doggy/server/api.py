"""核心 API 路由 —— /v1/chat/completions 和 /v1/messages。"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from doggy.auth.middleware import authenticate
from doggy.server.bootstrap import engine

log = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["chat"])


@router.post("/chat/completions")
async def chat_completions(request: Request):
    """OpenAI 兼容的聊天完成接口。

    请求链路：认证 → 限流 → 引擎 → 审计 → 响应
    """
    # 认证
    app_ctx = await authenticate(request)

    body = await request.json()
    messages = body.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    # 注入应用上下文
    messages = [{"role": "context", "content": {"app_id": app_ctx.app_id, "policy": app_ctx.policy_name}}] + messages

    # 调用引擎
    try:
        response = await engine.generate_async(
            messages=messages,
            protocol="openai",
        )
    except Exception as e:
        log.exception("请求处理失败 app_id=%s", app_ctx.app_id)
        raise HTTPException(status_code=500, detail=str(e))

    return response


@router.post("/messages")
async def messages_endpoint(request: Request):
    """Anthropic 兼容的消息接口。"""
    app_ctx = await authenticate(request)

    body = await request.json()
    messages = body.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="messages is required")

    messages = [{"role": "context", "content": {"app_id": app_ctx.app_id, "policy": app_ctx.policy_name}}] + messages

    try:
        response = await engine.generate_async(
            messages=messages,
            protocol="anthropic",
        )
    except Exception as e:
        log.exception("请求处理失败 app_id=%s", app_ctx.app_id)
        raise HTTPException(status_code=500, detail=str(e))

    return response


@router.post("/guardrails/check")
async def guardrails_check(request: Request):
    """纯护栏检查接口（不调用 LLM）。"""
    app_ctx = await authenticate(request)

    body = await request.json()
    messages = body.get("messages", [])

    return await engine.check_async(messages=messages)