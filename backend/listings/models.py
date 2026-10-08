#file:c:\project\backend\listings\models.py
from django.db import models
from django.conf import settings  # 修正：从 django.conf 导入 settings

# Create your models here.

class House(models.Model):
    """
    二手房房源模型
    """
    title = models.CharField(max_length=255)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50, blank=True)
    community = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    area = models.FloatField(help_text='建筑面积(㎡)')
    rooms = models.IntegerField(default=0, help_text='室')
    halls = models.IntegerField(default=0, help_text='厅')
    orientation = models.CharField(max_length=20, blank=True)
    floor = models.CharField(max_length=50, blank=True)
    decorate = models.CharField(max_length=50, blank=True)
    building_type = models.CharField(max_length=50, blank=True)
    followers = models.IntegerField(default=0)
    link = models.URLField(max_length=500, blank=True)
    cover = models.URLField(max_length=500, blank=True)
    tags = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    longitude = models.FloatField(null=True, blank=True, help_text='经度')
    latitude = models.FloatField(null=True, blank=True, help_text='纬度')


    class Meta:
        db_table = 'house'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
    
class Favorite(models.Model):
    """
    收藏模型
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'favorite'
        unique_together = ('user', 'house')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user_id}-{self.house_id}'