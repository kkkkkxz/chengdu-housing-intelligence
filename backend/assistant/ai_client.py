"""对接大模型的客户端封装（Django 调试版）。"""

from __future__ import annotations

import os
import sys
import logging
import traceback
from typing import Dict, List, Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

# 尝试导入 Django settings（仅在 Django 环境中使用）
try:
    from django.conf import settings as django_settings
    DJANGO_AVAILABLE = True
except Exception:
    django_settings = None
    DJANGO_AVAILABLE = False


def _get_setting_value(name: str, default: str = '') -> str:
    """优先读取环境变量，其次读取 Django settings（如果已配置），最后使用默认值。"""
    env_val = os.getenv(name)
    if env_val is not None and str(env_val).strip():
        return str(env_val).strip()
    if DJANGO_AVAILABLE and django_settings is not None:
        try:
            if hasattr(django_settings, name):
                setting_val = getattr(django_settings, name)
                if setting_val is not None and str(setting_val).strip():
                    return str(setting_val).strip()
        except Exception:
            pass
    return default


# 配置项
# 不提供代码内置密钥，部署时请通过环境变量 MODELSCOPE_API_KEY 注入。
MODELSCOPE_API_KEY = _get_setting_value('MODELSCOPE_API_KEY', '')
MODELSCOPE_BASE_URL = _get_setting_value('MODELSCOPE_BASE_URL', 'https://api-inference.modelscope.cn/v1')
MODELSCOPE_MODEL_ID = _get_setting_value('MODELSCOPE_MODEL_ID', 'deepseek-ai/DeepSeek-V4-Flash')
REQUEST_TIMEOUT = int(_get_setting_value('MODELSCOPE_TIMEOUT', '30'))  # 30秒超时

DEFAULT_SYSTEM_PROMPT = (
    '你是一个二手房数据分析可视化与预测平台的智能助手。'
    '请用简体中文回答，语气专业且友好，善于结合房源指标（价格、户型、区域、配套、收藏等）'
    '解释系统提供的图表、预测结果与操作步骤，并主动提示数据来源、指标含义及可能的风险点。'
)


def _build_client() -> OpenAI:
    """构造 OpenAI 兼容客户端，带超时配置。"""
    if not MODELSCOPE_API_KEY:
        raise ValueError('缺少 MODELSCOPE_API_KEY 配置，无法调用大模型服务。')
    return OpenAI(
        base_url=MODELSCOPE_BASE_URL,
        api_key=MODELSCOPE_API_KEY,
        timeout=REQUEST_TIMEOUT,
    )


def _build_messages(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
) -> List[Dict[str, str]]:
    """组装对话消息上下文。"""
    messages: List[Dict[str, str]] = [
        {'role': 'system', 'content': (system_prompt or DEFAULT_SYSTEM_PROMPT).strip()},
    ]
    if history:
        for item in history:
            role = item.get('role')
            content = (item.get('content') or '').strip()
            if role in {'user', 'assistant'} and content:
                messages.append({'role': role, 'content': content})
    messages.append({'role': 'user', 'content': (user_message or '').strip()})
    return messages


def generate_chat_reply(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    system_prompt: Optional[str] = None,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    stream: bool = False,
) -> str:
    """生成模型回复文本（非流式）。"""
    if stream:
        raise ValueError('当前接口暂不支持 stream=True，请设置 stream=False。')

    print("\n" + "=" * 50)
    print("[Django AI Client] 开始调用大模型")
    print(f"  - API Key前缀: {MODELSCOPE_API_KEY[:10]}...")
    print(f"  - Base URL: {MODELSCOPE_BASE_URL}")
    print(f"  - Model ID: {MODELSCOPE_MODEL_ID}")
    print(f"  - 用户消息: {user_message[:50]}")
    print(f"  - 历史消息数: {len(history) if history else 0}")
    sys.stdout.flush()  # 强制刷新输出

    client = _build_client()
    messages = _build_messages(user_message, history, system_prompt)

    try:
        print("[Django AI Client] 发送请求...")
        sys.stdout.flush()
        response = client.chat.completions.create(
            model=MODELSCOPE_MODEL_ID,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=False,
            # 注意：这里没有 extra_body，与独立测试脚本保持一致
        )
        print("[Django AI Client] 请求成功，开始解析响应")
        sys.stdout.flush()
    except Exception as e:
        print("[Django AI Client] 请求失败！")
        print("异常类型:", type(e).__name__)
        print("异常内容:", str(e))
        traceback.print_exc()
        sys.stdout.flush()
        raise ValueError(f"大模型服务请求失败: {str(e)}") from e

    # 解析标准 OpenAI 响应
    try:
        content = response.choices[0].message.content
        if content and isinstance(content, str):
            reply = content.strip()
            if reply:
                print("[Django AI Client] 成功提取回复，长度:", len(reply))
                print("=" * 50 + "\n")
                return reply
    except (AttributeError, IndexError, TypeError) as e:
        print("[Django AI Client] 解析响应字段失败")
        traceback.print_exc()
        raise ValueError(f"模型返回数据格式异常: {str(e)}")

    # 兼容 fallback
    if hasattr(response, 'text') and response.text:
        return response.text.strip()

    raise ValueError("未能从模型响应中提取文本结果")


# 独立测试入口（与 Django 无关）
if __name__ == '__main__':
    print("独立测试模式")
    api_key = os.getenv('MODELSCOPE_API_KEY')
    if not api_key:
        print("警告：未设置环境变量 MODELSCOPE_API_KEY，使用代码中的默认 key")
    else:
        print(f"使用环境变量中的 API Key: {api_key[:10]}...")
    try:
        result = generate_chat_reply("9.9和9.11谁大")
        print("\n最终回复:", result)
    except Exception as e:
        print("测试失败:", e)
        traceback.print_exc()
