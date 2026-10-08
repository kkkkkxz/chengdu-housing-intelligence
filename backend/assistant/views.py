from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response
from .ai_client import generate_chat_reply

# Create your views here.
class AssistantChatView(APIView):
    """二手房分析平台 AI 助手对话接口。"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """处理一次对话请求。"""
        message = (request.data.get('message') or '').strip()
        raw_history = request.data.get('history') or []
        if not message:
            return Response({'message': '问题内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)

        formatted_history = []
        if isinstance(raw_history, list):
            for item in raw_history:
                role = (item or {}).get('role')
                content = (item or {}).get('content')
                if role in {'user', 'assistant'} and isinstance(content, str) and content.strip():
                    formatted_history.append({'role': role, 'content': content.strip()})

        try:
            reply = generate_chat_reply(user_message=message, history=formatted_history)
        except ValueError as exc:
            # 参数或模型返回结构异常，向前端返回可读信息
            return Response({'message': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as exc:  # pragma: no cover
            # 可能为网络、API 访问或模型返回异常，记录并返回实际错误信息便于定位
            error_msg = str(exc)
            # 这里返回 500 更合适，避免前端 502 兜底“服务暂不可用”逻辑被误读
            return Response({'message': f'AI 服务调用失败: {error_msg}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'reply': reply})