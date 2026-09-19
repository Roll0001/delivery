from django.db import models

# Create your models here.

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
