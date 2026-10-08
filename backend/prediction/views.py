from django.shortcuts import render

# Create your views here.
# backend/prediction/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import os
import logging
from .model_manager import model_manager
from .serializers import PricePredictionSerializer
import pandas as pd

logger = logging.getLogger(__name__)

class DistrictsListView(APIView):
    """获取所有区县列表"""
    
    def get(self, request):
        """返回所有区县列表"""
        districts = []
        for district in model_manager.district_models.keys():
            districts.append({
                'value': district,
                'label': district,
                'avg_price': model_manager.district_avg_prices.get(district, 0),
                'sample_count': model_manager.district_models[district]['n_samples']
            })
        
        # 按区县名称排序
        districts.sort(key=lambda x: x['label'])
        
        return Response({
            'success': True,
            'data': districts
        })

class DistrictDetailView(APIView):
    """获取区县详情（默认参数）"""
    
    def get(self, request, district):
        """返回区县的默认参数"""
        if district not in model_manager.district_models:
            return Response({
                'success': False,
                'message': f'区县 {district} 不存在'
            }, status=status.HTTP_404_NOT_FOUND)
        
        model_info = model_manager.district_models[district]
        
        # 获取该区县的一些典型值作为默认参数
        default_params = {
            'area': 85,  # 默认面积
            'rooms': '3',
            'halls': '2',
            'orientation': '南',
            'decorate': '精装',
            'floor_level': '中',
            'has_metro': False,
            'has_vr': False,
            'has_elevator': True,
            '满两年': False,
            '满五年': False,
            '唯一住房': False
        }
        
        return Response({
            'success': True,
            'data': {
                'district': district,
                'avg_price': model_info['avg_price'],
                'best_model': model_info['best_model_name'],
                'test_mae': model_info.get('test_mae', 0),
                'test_r2': model_info.get('test_r2', 0),
                'default_params': default_params
            }
        })

class PredictPriceView(APIView):
    """房价预测API"""
    
    def post(self, request):
        """接收前端参数，返回预测价格"""
        
        serializer = PricePredictionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': '参数验证失败',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            data = serializer.validated_data
            district = data['district']
            
            # 构建特征字典
            features = {
                'area': data['area'],
                'unit_price': data.get('unit_price', 0),  # 后端计算
                'orientation': data['orientation'],
                'decorate': data['decorate'],
                'building_type': data.get('building_type', '板楼'),
                'rooms': data['rooms'],
                'halls': data['halls'],
                'floor_level': data['floor_level'],
                'has_vr': 1 if data.get('has_vr', False) else 0,
                'has_metro': 1 if data.get('has_metro', False) else 0,
                'has_elevator': 1 if data.get('has_elevator', False) else 0,
                '满两年': 1 if data.get('满两年', False) else 0,
                '满五年': 1 if data.get('满五年', False) else 0,
                '唯一住房': 1 if data.get('唯一住房', False) else 0
            }
            
            # 调用模型预测
            prediction = model_manager.predict_by_district(district, features)
            
            return Response({
                'success': True,
                'data': prediction
            })
            
        except Exception as e:
            logger.error(f"预测失败: {e}", exc_info=True)
            return Response({
                'success': False,
                'message': f'预测失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ModelStatusView(APIView):
    """模型状态API"""
    
    def get(self, request):
        """返回模型状态信息"""
        return Response({
            'success': True,
            'data': {
                'model_loaded': True,
                'districts_count': len(model_manager.district_models),
                'total_samples': sum([info['n_samples'] for info in model_manager.district_models.values()]),
                'overall_mae': model_manager.overall_mae if hasattr(model_manager, 'overall_mae') else 0
            }
        })
