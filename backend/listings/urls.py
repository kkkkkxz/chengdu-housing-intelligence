from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HouseViewSet, FavoriteViewSet, proxy_image

router = DefaultRouter()
router.register(r'houses', HouseViewSet, basename='house')
router.register(r'favorites', FavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
    path('proxy-image/', proxy_image, name='proxy_image'),
]