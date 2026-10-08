# listings/permissions.py
from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    自定义权限：
    - 安全方法（GET, HEAD, OPTIONS）允许所有用户访问。
    - 非安全方法（POST, PUT, PATCH, DELETE）仅允许 user_type='admin' 的用户访问。
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and getattr(request.user, 'user_type', '') == 'admin'