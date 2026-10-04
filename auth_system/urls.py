from django.urls import path

from auth_system import views

urlpatterns = [
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('restaurant-login/', views.restaurant_login_page, name='restaurant_login'),
    path('restaurant-register/', views.restaurant_register_page, name='restaurant_register'),
]
