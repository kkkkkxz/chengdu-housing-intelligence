from django.shortcuts import render
from rest_framework import generics, status, permissions, viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from django.contrib.auth import login, logout
from django.utils import timezone
from .models import User, UserLoginLog
from .serializers import (
    UserRegisterSerializer,
    UserLoginSerializer,
    UserSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
    PasswordChangeSerializer,
    UserLoginLogSerializer
)
from rest_framework.permissions import IsAuthenticated

class IsAdminUser(permissions.BasePermission):
    """
    自定义权限：只有管理员可以访问
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.user_type == 'admin'

class RegisterView(generics.CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]  # 允许所有人访问

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # 生成JWT令牌
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # 记录登录日志
        self._create_login_log(user, request, True)

        return Response(
            {
                'message': '注册成功',
                'user': UserSerializer(user, context={'request': request}).data,
                'access': access_token,
                'refresh': str(refresh),
            },
            status=status.HTTP_201_CREATED
        )

    def _create_login_log(self, user, request, is_success, failure_reason=''):
        """创建登录日志"""
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        UserLoginLog.objects.create(
            user=user,
            ip_address=ip_address,
            device=user_agent,
            browser='',  # 可以使用user_agents库解析
            operating_system='',  # 可以使用user_agents库解析
            is_success=is_success,
            failure_reason=failure_reason
        )

    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
class LoginView(generics.GenericAPIView):
    """用户登录视图"""
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # 生成JWT令牌
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # 更新用户最后登录信息
        user.last_login = timezone.now()
        user.last_login_ip = self._get_client_ip(request)
        user.save()

        # 记录登录日志
        self._create_login_log(user, request, True)

        return Response({
            'message': '登录成功',
            'user': UserSerializer(user, context={'request': request}).data,
            'access': access_token,
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)
    
    def _create_login_log(self, user, request, is_success, failure_reason=''):
        """创建登录日志"""
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')

        UserLoginLog.objects.create(
            user=user,
            ip_address=ip_address,
            device=user_agent,
            browser='',  # 可以使用user_agents库解析
            operating_system='',  # 可以使用user_agents库解析
            is_success=is_success,
            failure_reason=failure_reason
        )

    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class LogoutView(generics.GenericAPIView):
    """用户登出视图"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        return Response({'message': '登出成功'}, status=status.HTTP_200_OK) 

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_info(request):
    """获取用户信息"""
    user = request.user
    return Response({
        'user': UserSerializer(user, context={'request': request}).data,
        'permissions': user.get_all_permissions(),
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def update_avatar(request):
    """头像上传接口，接收 multipart/form-data 文件字段 avatar"""
    # 确保 DRF 使用 multipart/form-data 解析
    # 手动触发解析以避免某些代理/前端环境导致的解析失败
    if not hasattr(request, 'FILES') or request.FILES is None:
        # DRF 会在第一次访问 .data/.FILES 时解析；此处访问以确保解析执行
        _ = request.data  # noqa: F841

    file = request.FILES.get('avatar')
    if not file and 'avatar' in request.data:
        return Response({'message': '请以 multipart/form-data 上传文件字段 avatar'}, status=status.HTTP_400_BAD_REQUEST)
    if not file:
        return Response({'message': '未提供头像文件'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    # 使用 FileField.save 以确保存储后端实际写盘并生成路径
    # 文件名可使用原名；存储后端会处理重名
    user.avatar.save(file.name, file, save=True)

    data = UserSerializer(user, context={'request': request}).data
    resp = {'message': '头像已更新', 'user': data}
    return Response(resp, status=status.HTTP_200_OK)

class UserProfileView(generics.RetrieveUpdateAPIView):
    """用户资料视图"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserProfileSerializer

    def patch(self, request, *args, **kwargs):
        # 允许部分字段更新：映射到 User 与 UserProfile
        return super().patch(request, *args, **kwargs)
    
class PasswordChangeView(generics.GenericAPIView):
    """修改密码视图"""
    serializer_class = PasswordChangeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message': '密码修改成功'}, status=status.HTTP_200_OK)

class UserManagementViewSet(viewsets.ModelViewSet):
    """用户管理视图集 - 仅管理员可访问"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'phone', 'nike_name']
    ordering_fields = ['date_joined', 'username', 'email']
    ordering = ['-date_joined']

    def get_queryset(self):
        queryset = User.objects.all()
        user_type = self.request.query_params.get('user_type', None)
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        return queryset

    def perform_create(self, serializer):
        # 创建用户时设置密码
        user = serializer.save()
        if 'password' in self.request.data:
            user.set_password(self.request.data['password'])
            user.save()

    def perform_update(self, serializer):
        # 更新用户时，如果提供了密码则设置密码
        user = serializer.save()
        if 'password' in self.request.data and self.request.data['password']:
            user.set_password(self.request.data['password'])
            user.save()

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_username(request):
    """检查用户名是否已存在"""
    username = request.data.get('username', '').strip()
    if not username:
        return Response({'exists': False, 'error': '用户名不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    exists = User.objects.filter(username=username).exists()
    return Response({'exists': exists, 'username': username}, status=status.HTTP_200_OK)
