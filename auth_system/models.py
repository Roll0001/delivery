from django.contrib.auth import get_user_model
from django.db import models


class RestaurantProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name='restaurant_profile')
    is_restaurant = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ресторан: {self.user.username}"


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
