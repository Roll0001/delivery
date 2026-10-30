from django.contrib import admin

from delivery_APP.models import CartOfMenu, RestorantInfo, Delivery, Dish, ProductType, RestaurantApplication

# Register your models here.
admin.site.register(CartOfMenu)
admin.site.register(Delivery)
admin.site.register(RestorantInfo)
admin.site.register(ProductType)
admin.site.register(Dish)
admin.site.register(RestaurantApplication)