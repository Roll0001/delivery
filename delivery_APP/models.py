from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.
class CartOfMenu(models.Model):
    restaurant = models.ForeignKey(
        'RestorantInfo',
        on_delete=models.CASCADE,
        related_name='dishes',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='media/dish_photos/', blank=True, default='')
    ingridients = models.TextField()
    weight = models.DecimalField(max_digits=7, decimal_places=0)
    time_to_cook = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

    @property
    def ingredients(self):
        return self.ingridients

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('new', 'Нове'),
        ('cooking', 'Готується'),
        ('on_way', 'В дорозі'),
        ('delivered', 'Доставлено'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries',
    )
    name = models.CharField(max_length=100, default='')
    address = models.TextField(default='')
    phone_number = models.CharField(max_length=15, default='')
    order_time = models.DateTimeField(default=timezone.now)
    cart = models.ForeignKey(CartOfMenu, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    def __str__(self):
        return f'Замовлення #{self.pk}'

class RestorantInfo(models.Model):
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='media/restorant_photos/')
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    opening_hours = models.CharField(max_length=50)   

    def __str__(self):
        return self.name

     

