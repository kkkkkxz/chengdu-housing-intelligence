from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from . import views

router = DefaultRouter()
router.register(r'', views.UserManagementViewSet, basename='users')

app_name = 'users'

urlpatterns = [
    # 认证相关
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('profile/avatar/', views.update_avatar, name='update_avatar'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('check/username/', views.check_username, name='check_username'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    # 用户管理 - 仅管理员可访问
    path('', include(router.urls)),
]