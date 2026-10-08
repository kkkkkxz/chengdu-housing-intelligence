# 第一个文件（serializers.py 类的部分）
from rest_framework import serializers
from .models import House, Favorite

class HouseSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    class Meta:
        model = House
        fields = '__all__'

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or getattr(user, 'is_anonymous', True):
            return False
        return Favorite.objects.filter(user=user, house=obj).exists()

    def get_cover(self, obj):
        """返回可由浏览器直接访问的绝对图片 URL。"""
        from django.conf import settings
        import urllib.parse
        
        # 优先处理外部完整 URL 或协议相对 URL（例如 //...）
        cover = getattr(obj, 'cover', None)
        link = getattr(obj, 'link', None)
        
        request = self.context.get('request')
        
        # 处理外部图片 URL - 使用代理绕过 CORB
        if cover:
            s = str(cover).strip()
            # 如果是完整的外部 URL，使用代理
            if s.lower().startswith('http://') or s.lower().startswith('https://'):
                if request is not None:
                    # 使用图片代理，避免 CORB 限制
                    proxy_url = request.build_absolute_uri('/api/listings/proxy-image/')
                    encoded_url = urllib.parse.quote(s, safe='')
                    return f"{proxy_url}?url={encoded_url}"
                return s
            elif s.startswith('//'):
                # 协议相对 URL，添加 https
                s = 'https:' + s
                if request is not None:
                    proxy_url = request.build_absolute_uri('/api/listings/proxy-image/')
                    encoded_url = urllib.parse.quote(s, safe='')
                    return f"{proxy_url}?url={encoded_url}"
                return s

        # 回退：有时图片 URL 可能被放在 link 字段（部分 CSV 来源），若 link 看起来像图片则使用它
        if link:
            l = str(link).strip()
            if l.lower().startswith('http://') or l.lower().startswith('https://'):
                if any(l.lower().endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg')):
                    if request is not None:
                        proxy_url = request.build_absolute_uri('/api/listings/proxy-image/')
                        encoded_url = urllib.parse.quote(l, safe='')
                        return f"{proxy_url}?url={encoded_url}"
                    return l

        # 如果 cover 存在但为相对路径，尝试使用 request 构造绝对 URL
        if cover:
            s = str(cover).strip()
            
            # 如果路径不是完整 URL，需要处理为媒体文件路径
            if not (s.lower().startswith('http://') or s.lower().startswith('https://') or s.startswith('//')):
                # 如果路径不是以 /media 开头，需要添加 MEDIA_URL 前缀
                if not s.startswith(settings.MEDIA_URL):
                    # 移除路径开头的 / 和 media/，避免重复
                    s_clean = s.lstrip('/').lstrip('media/')
                    s = settings.MEDIA_URL.rstrip('/') + '/' + s_clean
                # 确保路径以 / 开头
                if not s.startswith('/'):
                    s = '/' + s
                
                # 使用 request 构造绝对 URL
                try:
                    if request is not None:
                        return request.build_absolute_uri(s)
                except Exception:
                    pass
                
                # 如果没有 request，返回相对路径（前端会通过代理访问）
                return s

        # 最后回退原样返回（可能为 None）
        return cover

class FavoriteSerializer(serializers.ModelSerializer):
    house = HouseSerializer(read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'house', 'created_at')

