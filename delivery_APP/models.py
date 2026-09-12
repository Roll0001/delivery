from django.db import models

# Create your models here.
class CartOfMenu(models.Model):
    name = models.CharField(max_length=100)
    ingridients = models.TextField()
    weight = models.FloatField()
    price = models.FloatField()

class Delivery(models.Model):
    pass 