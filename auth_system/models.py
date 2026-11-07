from django.contrib.auth import get_user_model
from django.db import models

from delivery_APP.models import CITY_CHOICES, COURIER_CITY_CHOICES

COURIER_TRANSPORT_CHOICES = [
    ('electric_bicycle', 'Електричний велосипед'),
    ('motorcycle', 'Мотоцикл'),
    ('bicycle', 'Велосипед'),
    ('car', 'Автомобіль'),
    ('walking', 'Піший'),
]


class RestaurantProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='restaurant_profile')
    is_restaurant = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ресторан: {self.user.username}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='customer_profile',
    )
    city = models.CharField(max_length=100, choices=CITY_CHOICES)

    def __str__(self):
        return f"Покупець: {self.user.username}"


class CourierProfile(models.Model):
    user = models.OneToOneField(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='courier_profile',
    )
    city = models.CharField(max_length=100, choices=COURIER_CITY_CHOICES)
    transport = models.CharField(max_length=30, choices=COURIER_TRANSPORT_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Кур'єр: {self.user.get_full_name()}"


class User(models.Model):
    username = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.EmailField(blank=True, default="")
    password = models.CharField(max_length=100)


class Worker(models.Model):
    username = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    email = models.EmailField(blank=True, default="")
    password = models.CharField(max_length=100)
    position = models.CharField(max_length=100)


class Restorant(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    image = models.ImageField(upload_to='media/restorant_photos/')
    opening_hours = models.CharField(max_length=100)
