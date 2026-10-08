# houserag/urls.py
from django.urls import path
from . import views

app_name = 'houserag'
urlpatterns = [
    path('ask/', views.rag_ask, name='ask'),
    path('clear/', views.rag_clear, name='clear'),
]