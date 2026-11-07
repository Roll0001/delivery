from django.urls import path

from auth_system import views

urlpatterns = [
    path('register/', views.register_page, name='register'),
    path('login/', views.login_page, name='login'),
    path('logout/', views.logout_page, name='logout'),
    path('courier-register/', views.courier_register_page, name='courier_register'),
    path('courier-login/', views.courier_login_page, name='courier_login'),
    path('restaurant-login/', views.restaurant_login_page, name='restaurant_login'),
    path('restaurant-register/', views.restaurant_register_page, name='restaurant_register'),
    path(
        'restaurant-application/<int:application_id>/status/',
        views.restaurant_application_status,
        name='restaurant_application_status',
    ),
]
