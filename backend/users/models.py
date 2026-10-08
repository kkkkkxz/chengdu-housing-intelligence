from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

"""
用户模型,继承自Django内置的AbstractUser模型，添加了额外的字段以满足应用需求。
"""
class User(AbstractUser):
    GENDER_CHOICES = [
        ('male', '男'),
        ('female', '女'),
        ('other', '其他'),
    ]

    USER_TYPE_CHOICES = [
        ('user', '用户'),
        ('admin', '管理员'),
    ]

    email = models.EmailField('邮箱',unique=True, blank=True, null=True)
    phone = models.CharField('手机号', max_length=11, unique=True, blank=True, null=True)
    nike_name = models.CharField('昵称', max_length=50, blank=True, null=True)
    avatar = models.ImageField('头像', upload_to='avatars/%Y/%m/%d', blank=True, null=True)
    gender = models.CharField('性别', max_length=10, choices=GENDER_CHOICES, blank=True)
    birthday = models.DateField('生日', blank=True, null=True)
    user_type = models.CharField('用户类型', max_length=10, choices=USER_TYPE_CHOICES, default='user')
    is_verified = models.BooleanField('是否验证', default=False)
    last_login_ip = models.GenericIPAddressField('最后登录IP', blank=True, null=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'auth_users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-date_joined']

    def __str__(self):
        return self.username
    
class UserLoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    ip_address = models.GenericIPAddressField('登录IP地址')
    device = models.CharField('登录设备', max_length=200,blank=True)
    browser = models.CharField('登录浏览器', max_length=100,blank=True)
    operating_system = models.CharField('登录操作系统', max_length=100,blank=True)
    login_time = models.DateTimeField('登录时间', auto_now_add=True)
    is_success = models.BooleanField('是否登录成功', default=True)
    failure_reason = models.CharField('登录失败原因',max_length=200,blank=True)

    class Meta:
        db_table = 'user_login_log'
        verbose_name = '用户登录日志'
        verbose_name_plural = '用户登录日志'
        ordering = ['-login_time']

    def __str__(self):
        return f"{self.user.username} - {self.ip_address} - {self.login_time}"
