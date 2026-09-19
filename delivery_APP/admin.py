from django.contrib import admin

from delivery_APP.models import CartOfMenu, RestorantInfo, Delivery

# Register your models here.
admin.site.register(CartOfMenu)
admin.site.register(Delivery)
admin.site.register(RestorantInfo)