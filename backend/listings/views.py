from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, F, Sum, Max
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
import django_filters
import re
from pathlib import Path
import requests
import urllib.parse
from .models import House, Favorite
from .serializers import HouseSerializer, FavoriteSerializer
from .recommation import get_user_recommendations
from .permissions import IsAdminOrReadOnly
# Create your views here.

#房源模型 收藏
class HouseViewSet(viewsets.ModelViewSet):
    queryset = House.objects.all()
    serializer_class = HouseSerializer
    permission_classes = [IsAdminOrReadOnly] 
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'city', 'district', 'community', 'address', 'tags']
    ordering_fields = ['total_price', 'unit_price', 'area', 'created_at']
    filterset_fields = ['city', 'district', 'rooms', 'halls', 'orientation', 'building_type', 'decorate']

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        house = self.get_object()
        fav, created = Favorite.objects.get_or_create(user=request.user, house=house)
        if created:
            return Response({'message': '已收藏'}, status=status.HTTP_201_CREATED)
        return Response({'message': '已在收藏夹中'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['delete'], permission_classes=[permissions.IsAuthenticated])
    def unfavorite(self, request, pk=None):
        house = self.get_object()
        Favorite.objects.filter(user=request.user, house=house).delete()
        return Response({'message': '已取消收藏'})

    
    #推荐
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated], url_path='recommendations')
    def recommendations(self, request):
        """为当前用户生成房源推荐"""
        results = get_user_recommendations(request.user.id)
        houses = [item['house'] for item in results]
        serializer = self.get_serializer(houses, many=True)
        serialized_houses = list(serializer.data)

        items = []
        for item, house_data in zip(results, serialized_houses):
            items.append(
                {
                    'house': house_data,
                    'score': item.get('score'),
                    'source': item.get('source', 'collaborative'),
                }
            )

        summary = {
            'total': len(items),
            'collaborative': sum(1 for item in items if item['source'] == 'collaborative'),
            'random_fill': sum(1 for item in items if item['source'] == 'random_fill'),
        }
        return Response({'items': items, 'summary': summary})
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def similar(self, request, pk=None):
        current = self.get_object()
        qs = House.objects.exclude(id=current.id)

        # 基础条件: 同城 + 价格/面积在±30% 区间
        price_low = float(current.total_price) * 0.7 if current.total_price is not None else None
        price_high = float(current.total_price) * 1.3 if current.total_price is not None else None
        area_low = float(current.area) * 0.7 if current.area is not None else None
        area_high = float(current.area) * 1.3 if current.area is not None else None

        base = Q(city=current.city)
        if price_low is not None and price_high is not None:
            base &= Q(total_price__gte=price_low, total_price__lte=price_high)
        if area_low is not None and area_high is not None:
            base &= Q(area__gte=area_low, area__lte=area_high)

        candidates = qs.filter(base)

        # 简单打分: 小区/户型权重 + 价格、面积差的相似度
        items = []
        for h in candidates[:200]:
            score = 0.0
            if current.community and h.community == current.community:
                score += 3.0
            if current.rooms is not None and h.rooms == current.rooms:
                score += 1.2
            if current.halls is not None and h.halls == current.halls:
                score += 0.8
            # 价格与面积相似度（差值越小分越高）
            try:
                price_sim = 1.0 - abs(float(h.total_price) - float(current.total_price)) / float(current.total_price)
                area_sim = 1.0 - abs(float(h.area) - float(current.area)) / float(current.area)
                score += max(0.0, price_sim) * 2.0 + max(0.0, area_sim) * 1.5
            except Exception:
                pass
            items.append((score, h))

        items.sort(key=lambda x: x[0], reverse=True)
        top_houses = [h for _, h in items[:8]]
        serializer = HouseSerializer(top_houses, many=True, context={'request': request})
        return Response(serializer.data)
    
    # ====== 数据分析前端接口 ======
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='stats/average-price-by-district')
    # 按区域统计平均房价（画：柱状图）
    def stats_average_price_by_district(self, request):
        city = request.query_params.get('city')
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)

        # 优先使用 unit_price，缺失时回退到 total_price/area 的近似
        items = []
        by_district = {}
        fields = qs.values('district', 'unit_price', 'total_price', 'area')
        for row in fields:
            district = (row['district'] or '').strip() or '未注明'
            unit_price = row['unit_price']
            if unit_price is None:
                try:
                    if row['total_price'] is not None and row['area']:
                        unit_price = float(row['total_price']) * 10000.0 / float(row['area'])
                except Exception:
                    unit_price = None
            if unit_price is None:
                continue
            agg = by_district.setdefault(district, {'sum': 0.0, 'cnt': 0})
            agg['sum'] += float(unit_price)
            agg['cnt'] += 1
        for name, agg in by_district.items():
            if agg['cnt'] > 0:
                items.append({'name': name, 'value': round(agg['sum'] / agg['cnt'], 2)})
        # 升序方便前端展示
        items.sort(key=lambda x: x['value'])
        return Response(items)
    
    #房价区间统计（画：饼图 / 柱状图）
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='stats/price-range')
    def stats_price_range(self, request):
        city = request.query_params.get('city')
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)

        # 价格单位为万元
        bins = [0, 100, 200, 300, 400, 600, 800, 1000]
        labels = [
            '0-100万', '100-200万', '200-300万', '300-400万',
            '400-600万', '600-800万', '800-1000万', '1000万+'
        ]
        counts = [0] * len(labels)
        for tp in qs.values_list('total_price', flat=True):
            if tp is None:
                continue
            try:
                v = float(tp)
            except Exception:
                continue
            placed = False
            for i in range(len(bins) - 1):
                if bins[i] <= v < bins[i + 1]:
                    counts[i] += 1
                    placed = True
                    break
            if not placed:
                counts[-1] += 1
        data = [{
            'name': labels[i],
            'value': counts[i]
        } for i in range(len(labels))]
        return Response(data)
    
    #按建筑类型统计均价（画：柱状图）
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny],
            url_path='stats/avg-price-by-building-type')
    def stats_avg_price_by_building_type(self, request):
        city = request.query_params.get('city')
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)
        groups = {}
        for row in qs.values('building_type', 'unit_price', 'total_price', 'area'):
            key = (row['building_type'] or '').strip() or '未注明'
            unit_price = row['unit_price']
            if unit_price is None:
                try:
                    if row['total_price'] is not None and row['area']:
                        unit_price = float(row['total_price']) * 10000.0 / float(row['area'])
                except Exception:
                    unit_price = None
            if unit_price is None:
                continue
            agg = groups.setdefault(key, {'sum': 0.0, 'cnt': 0})
            agg['sum'] += float(unit_price)
            agg['cnt'] += 1
        data = [{'name': k, 'value': round(v['sum'] / v['cnt'], 2)} for k, v in groups.items() if v['cnt'] > 0]
        # 按均价降序
        data.sort(key=lambda x: x['value'], reverse=True)
        return Response(data)
        
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='stats/house-type-count')
    def stats_house_type_count(self, request):
        city = request.query_params.get('city')
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)
        # 组合 rooms + halls
        counts = {}
        for r, h in qs.values_list('rooms', 'halls'):
            rooms = r or 0
            halls = h or 0
            label = f"{rooms}室{halls}厅"
            counts[label] = counts.get(label, 0) + 1
        data = [{'name': k, 'value': v} for k, v in counts.items()]
        # 按数量降序
        data.sort(key=lambda x: x['value'], reverse=True)
        return Response(data)
    
    # 按区域统计房源数量（画：地图）
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='stats/district-map-count')
    def stats_district_map_count(self, request):
        city = request.query_params.get('city')
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)
        counts = {}
        for name in qs.values_list('district', flat=True):
            key = (name or '').strip() or '未注明'
            counts[key] = counts.get(key, 0) + 1
        data = [{'name': k, 'value': v} for k, v in counts.items()]
        # 降序
        data.sort(key=lambda x: x['value'], reverse=True)
        return Response(data)


    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='summary')
    def summary(self, request):
        """返回房源汇总统计，用于仪表盘显示（总房源、总面积、平均单价等）。"""
        city = request.query_params.get('city')
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)

        total_houses = qs.count()
        # 总面积（平方米）
        total_area = qs.aggregate(total=Sum('area'))['total'] or 0.0
        # 平均单价（优先 unit_price，否则用 total_price/area）
        unit_price_vals = list(qs.values_list('unit_price', flat=True))
        avg_unit_price = None
        try:
            if any(v for v in unit_price_vals if v is not None):
                valid = [float(v) for v in unit_price_vals if v is not None]
                avg_unit_price = sum(valid) / len(valid) if valid else None
        except Exception:
            avg_unit_price = None
        if avg_unit_price is None:
            # 回退到 total_price/area
            tmp = []
            for row in qs.values('total_price', 'area'):
                try:
                    if row['total_price'] is not None and row['area']:
                        tmp.append(float(row['total_price']) * 10000.0 / float(row['area']))
                except Exception:
                    pass
            avg_unit_price = sum(tmp) / len(tmp) if tmp else None

        # 平均总价（万元）
        avg_total_price = qs.aggregate(avg=Avg('total_price'))['avg'] or 0.0

        cities = qs.values('city').distinct().count()
        districts = qs.values('district').distinct().count()
        max_followers = qs.aggregate(maxf=Max('followers'))['maxf'] or 0

        # 热门户型（rooms+halls 组合）
        house_type_counts = {}
        for r, h in qs.values_list('rooms', 'halls'):
            key = f"{r}室{h}厅"
            house_type_counts[key] = house_type_counts.get(key, 0) + 1
        popular_house_type = '-'
        if house_type_counts:
            popular_house_type = max(house_type_counts.items(), key=lambda x: x[1])[0]

        result = {
            'total_houses': total_houses,
            'total_area_m2': float(total_area),
            'total_area_wan_m2': round(float(total_area) / 10000.0, 4),
            'avg_unit_price': round(float(avg_unit_price), 2) if avg_unit_price else 0,
            'avg_total_price': round(float(avg_total_price), 2) if avg_total_price else 0,
            'cities': cities,
            'districts': districts,
            'popular_house_type': popular_house_type,
            'avg_area': round(float(total_area) / total_houses, 2) if total_houses else 0,
            'max_followers': int(max_followers),
        }
        return Response(result)

    # 房价与面积散点数据（画：散点图）
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny],
            url_path='stats/price-area-scatter')
    def stats_price_area_scatter(self, request):
        city = request.query_params.get('city')
        limit = int(request.query_params.get('limit', 500))
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)
        data = []
        for row in qs.values('unit_price', 'total_price', 'area')[:2000]:
            unit_price = row['unit_price']
            if unit_price is None:
                try:
                    if row['total_price'] is not None and row['area']:
                        unit_price = float(row['total_price']) * 10000.0 / float(row['area'])
                except Exception:
                    unit_price = None
            if unit_price is None or not row['area']:
                continue
            try:
                data.append([round(float(unit_price), 2), round(float(row['area']), 2)])
            except Exception:
                continue
            if len(data) >= limit:
                break
        return Response(data)
    
    # 房源标题词云数据（画：词云图）

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny], url_path='stats/title-wordcloud')
    def stats_title_wordcloud(self, request):
        # 分词依赖可选安装
        try:
            import jieba  # type: ignore
        except Exception:
            jieba = None
        city = request.query_params.get('city')
        qs = House.objects.all()
        if city:
            qs = qs.filter(city=city)
        titles = list(qs.values_list('title', flat=True))
        words = []
        if jieba:
            for t in titles:
                if not t:
                    continue
                for w in jieba.lcut(t):
                    w = (w or '').strip()
                    if not w:
                        continue
                    if len(w) <= 1:
                        continue
                    words.append(w)
        else:
            # 简单退化：基于非中文字符分割
            import re
            for t in titles:
                if not t:
                    continue
                segs = re.split(r'[^\u4e00-\u9fa5]', t)
                for w in segs:
                    w = (w or '').strip()
                    if not w or len(w) <= 1:
                        continue
                    words.append(w)
        from collections import Counter
        counter = Counter(words)
        top_k = int(request.query_params.get('top', 100))
        items = [{'name': k, 'value': v} for k, v in counter.most_common(top_k)]
        return Response(items)
    
# 房源标签统计（画：柱状图）
class FavoriteFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name='house__city', lookup_expr='iexact')

    class Meta:
        model = Favorite
        fields = ['city']

# 收藏夹视图集，包含按城市统计收藏数量的接口
class FavoriteViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = [
        'house__title',
        'house__city',
        'house__district',
        'house__community',
        'house__address',
    ]
    ordering_fields = ['created_at', 'house__total_price', 'house__unit_price']
    ordering = ['-created_at']
    filterset_class = FavoriteFilter

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        city_counts = (
            Favorite.objects.filter(user=request.user)
            .values('house__city')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        city_options = []
        for item in city_counts:
            raw_city = (item.get('house__city') or '').strip()
            if not raw_city:
                continue
            city_options.append(
                {
                    'label': raw_city,
                    'value': raw_city,
                    'count': item.get('count', 0),
                }
            )
        if isinstance(response.data, dict):
            meta = response.data.get('meta')
            if not isinstance(meta, dict):
                meta = {}
                response.data['meta'] = meta
            meta['cities'] = city_options
        return response

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('house')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def proxy_image(request):
    """
    图片代理视图，用于绕过 CORB 限制
    通过后端服务器获取外部图片并转发给前端
    """
    url = request.query_params.get('url')
    if not url:
        return Response({'error': '缺少 url 参数'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 解码 URL
        image_url = urllib.parse.unquote(url)
        
        # 验证 URL 格式
        if not (image_url.startswith('http://') or image_url.startswith('https://')):
            return Response({'error': '无效的 URL'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 设置请求头，模拟浏览器请求
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': image_url.split('/')[0] + '//' + image_url.split('/')[2] if '/' in image_url else image_url,
        }
        
        # 请求图片
        response = requests.get(image_url, headers=headers, timeout=10, stream=True)
        response.raise_for_status()
        
        # 获取内容类型
        content_type = response.headers.get('Content-Type', 'image/jpeg')
        
        # 创建流式响应
        django_response = StreamingHttpResponse(
            response.iter_content(chunk_size=8192),
            content_type=content_type
        )
        
        # 设置缓存头
        django_response['Cache-Control'] = 'public, max-age=86400'  # 缓存 1 天
        django_response['Access-Control-Allow-Origin'] = '*'
        
        return django_response
        
    except requests.exceptions.RequestException as e:
        return Response({'error': f'无法获取图片: {str(e)}'}, status=status.HTTP_502_BAD_GATEWAY)
    except Exception as e:
        return Response({'error': f'服务器错误: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

