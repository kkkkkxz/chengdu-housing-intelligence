# backend/prediction/serializers.py

from rest_framework import serializers

class PricePredictionSerializer(serializers.Serializer):
    """房价预测请求序列化器"""
    district = serializers.CharField(required=True, max_length=100)
    area = serializers.FloatField(required=True, min_value=10, max_value=500)
    rooms = serializers.CharField(required=True, max_length=10)
    halls = serializers.CharField(required=True, max_length=10)
    orientation = serializers.CharField(required=True, max_length=20)
    decorate = serializers.CharField(required=True, max_length=20)
    building_type = serializers.CharField(required=False, max_length=20, default='板楼')
    floor_level = serializers.CharField(required=True, max_length=10)
    has_metro = serializers.BooleanField(required=False, default=False)
    has_vr = serializers.BooleanField(required=False, default=False)
    has_elevator = serializers.BooleanField(required=False, default=False)
    满两年 = serializers.BooleanField(required=False, default=False)
    满五年 = serializers.BooleanField(required=False, default=False)
    唯一住房 = serializers.BooleanField(required=False, default=False)
    unit_price = serializers.FloatField(required=False, default=0)