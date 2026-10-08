from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User, UserLoginLog


class UserRegisterSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'phone', 'nike_name']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6},
            'email': {'required': True},
            'phone': {'required': False},
        }

    def validate(self, attrs):
        # 验证两次密码是否一致
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("两次密码输入不一致")

        # 检查用户名是否已存在
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError("用户名已存在")

        # 检查邮箱是否已存在
        email = attrs.get('email')
        if email and User.objects.filter(email=email).exists():
            raise serializers.ValidationError("邮箱已被注册")

        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user
    
class UserSerializer(serializers.ModelSerializer):
    """
    用户信息序列化器
    """
    avatar = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'nike_name', 'avatar',
            'gender', 'birthday', 'user_type', 'is_verified',
            'date_joined', 'last_login', 'password'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'email': {'required': True},
            'phone': {'required': False},
        }

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            url = obj.avatar.url
            if request and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url
        return ''
    
    def validate_email(self, value):
        """验证邮箱唯一性"""
        if value and value.strip():
            user_id = self.instance.id if self.instance else None
            if User.objects.filter(email=value).exclude(id=user_id).exists():
                raise serializers.ValidationError("邮箱已被注册")
        return value.strip() if value else None

    def validate_phone(self, value):
        """验证手机号唯一性"""
        if value and value.strip():
            user_id = self.instance.id if self.instance else None
            if User.objects.filter(phone=value).exclude(id=user_id).exists():
                raise serializers.ValidationError("手机号已被注册")
        return value.strip() if value else None

    def validate_username(self, value):
        """验证用户名唯一性"""
        if value:
            user_id = self.instance.id if self.instance else None
            if User.objects.filter(username=value).exclude(id=user_id).exists():
                raise serializers.ValidationError("用户名已存在")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    用户资料详情序列化器
    """
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'nike_name', 'avatar',
            'gender', 'birthday', 'user_type', 'is_verified',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'date_joined', 'last_login', 'user_type']

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.avatar:
            url = obj.avatar.url
            if request and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url
        return ''


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    用户资料更新序列化器
    """

    class Meta:
        model = User
        fields = [
            'email', 'phone', 'nike_name', 'avatar',
            'gender', 'birthday'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'phone': {'required': False},
        }

    def validate_email(self, value):
        """验证邮箱唯一性"""
        if value and value.strip():
            user_id = self.instance.id if self.instance else None
            if User.objects.filter(email=value).exclude(id=user_id).exists():
                raise serializers.ValidationError("邮箱已被注册")
        return value.strip() if value else None

    def validate_phone(self, value):
        """验证手机号唯一性"""
        if value and value.strip():
            user_id = self.instance.id if self.instance else None
            if User.objects.filter(phone=value).exclude(id=user_id).exists():
                raise serializers.ValidationError("手机号已被注册")
        return value.strip() if value else None

class UserLoginSerializer(serializers.Serializer):
    """用户登录序列化器"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        # 检查字段是否存在
        if not username:
            raise serializers.ValidationError({"username": "用户名不能为空"})
        if not password:
            raise serializers.ValidationError({"password": "密码不能为空"})

        # 验证用户凭据
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("用户名或密码错误")

        attrs['user'] = user
        return attrs

class PasswordChangeSerializer(serializers.Serializer):
    """密码修改序列化器"""
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码错误")
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("两次新密码输入不一致")
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError("新密码不能与原密码相同")
        return attrs

class UserLoginLogSerializer(serializers.ModelSerializer):
    """用户登录日志序列化器"""

    class Meta:
        model = UserLoginLog
        fields = ['id', 'ip_address', 'login_time', 'is_success', 'failure_reason']
        read_only_fields = ['id', 'login_time', 'is_success', 'failure_reason']

class UserProfileSerializer(serializers.ModelSerializer):
    """用户资料序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    nickname = serializers.CharField(source='user.nickname', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'nickname', 'avatar', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """用户资料更新序列化器"""
    nickname = serializers.CharField(source='user.nickname', required=False, allow_blank=True)
    gender = serializers.CharField(source='user.gender', required=False, allow_blank=True)
    birthday = serializers.DateField(source='user.birthday', required=False, allow_null=True)
    email = serializers.EmailField(source='user.email', required=False, allow_blank=True, allow_null=True)
    phone = serializers.CharField(source='user.phone', required=False, allow_blank=True, allow_null=True)
    user_type = serializers.CharField(source='user.user_type', required=False)

    class Meta:
        model = User
        fields = [
            'nickname', 'gender', 'birthday', 'email', 'phone', 'user_type',
        ]

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})

        # 唯一性校验（仅当变更时）
        email = user_data.get('email')
        phone = user_data.get('phone')

        if email is not None and email != instance.email:
            if email == '' or email is None:
                instance.email = None
                user_data.pop('email', None)
            elif User.objects.filter(email=email).exclude(id=instance.id).exists():
                raise serializers.ValidationError('邮箱已被占用')
        if phone is not None and phone != instance.phone:
            if phone == '' or phone is None:
                instance.phone = None
                user_data.pop('phone', None)
            elif User.objects.filter(phone=phone).exclude(id=instance.id).exists():
                raise serializers.ValidationError('手机号已被占用')

        # 更新用户信息
        if user_data:
            for attr, value in user_data.items():
                setattr(instance.user, attr, value)
            instance.save()

        return instance
    
class PasswordChangeSerializer(serializers.Serializer):
    """修改密码序列化器"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=6)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("新密码两次输入不一致")
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        if not user.check_password(self.validated_data['old_password']):
            raise serializers.ValidationError("原密码错误")

        user.set_password(self.validated_data['new_password'])
        user.save()
        return user