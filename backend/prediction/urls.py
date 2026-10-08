# backend/prediction/urls.py

from django.urls import path
from .views import DistrictsListView, DistrictDetailView, PredictPriceView, ModelStatusView

urlpatterns = [
    path('districts/', DistrictsListView.as_view(), name='districts-list'),
    path('districts/<str:district>/', DistrictDetailView.as_view(), name='district-detail'),
    path('predict/', PredictPriceView.as_view(), name='predict-price'),
    path('status/', ModelStatusView.as_view(), name='model-status'),
]