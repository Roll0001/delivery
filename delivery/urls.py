"""
URL configuration for delivery project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

from delivery_APP import views as delivery_app_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('auth_system.urls')),
    path('', delivery_app_views.home, name='home'),
    path('restaurant-home/', delivery_app_views.restaurant_home, name='restaurant_home'),
    path('menu/<int:restaurant_id>/', delivery_app_views.restaurant_menu, name='restaurant_menu'),
    path('restoransaddlist/', delivery_app_views.restaurant_requests, name='restoransaddlist'),
    path('restaurant-request/<int:request_id>/approve/', delivery_app_views.approve_restaurant_request, name='approve_restaurant_request'),
    path('restaurant-request/<int:request_id>/reject/', delivery_app_views.reject_restaurant_request, name='reject_restaurant_request'),
    path('addrestorantinfo/', delivery_app_views.add_restaurant_info, name='add_restaurant_info'),
    path('createdish/', delivery_app_views.add_dish, name='create_dish'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
