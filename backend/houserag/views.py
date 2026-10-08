# houserag/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .rag_utils import ask_question, clear_session_history

@csrf_exempt  
@require_http_methods(["POST"])
def rag_ask(request):
    try:
        data = json.loads(request.body)
        question = data.get('question', '').strip()
        session_id = data.get('session_id', 'default')  # 前端传递 session_id
        if not question:
            return JsonResponse({'error': '问题不能为空'}, status=400)
        
        answer = ask_question(question, session_id=session_id)
        return JsonResponse({'answer': answer, 'session_id': session_id})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def rag_clear(request):
    """清除指定会话的历史"""
    data = json.loads(request.body)
    session_id = data.get('session_id', 'default')
    clear_session_history(session_id)
    return JsonResponse({'status': 'cleared', 'session_id': session_id})