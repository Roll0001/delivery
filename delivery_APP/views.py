from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from auth_system.models import RestaurantProfile
from .forms import DishForm, RestaurantApplicationForm, RestorantInfoForm
from .models import CartOfMenu, RestaurantApplication, RestorantInfo


def home(request):
    query = request.GET.get('q', '').strip()
    restaurants = RestorantInfo.objects.all().order_by('name')
    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) | Q(address__icontains=query)
        )

    return render(request, 'home.html', {
        'restaurants': restaurants,
        'query': query,
    })


def restaurant_home(request):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    restaurants = RestorantInfo.objects.filter(owner=request.user).order_by('name')
    dishes = CartOfMenu.objects.filter(restaurant__owner=request.user).select_related('restaurant').order_by('-price')
    return render(request, 'homepageforrestorant.html', {
        'restaurants': restaurants,
        'dishes': dishes,
    })


def restaurant_menu(request, restaurant_id):
    restaurant = get_object_or_404(RestorantInfo, pk=restaurant_id)
    dishes = CartOfMenu.objects.filter(restaurant=restaurant).order_by('name')

    return render(request, 'MenuOfRestorant.html', {
        'restaurant': restaurant,
        'dishes': dishes,
    })


def restaurant_requests(request):
    applications = RestaurantApplication.objects.order_by('-created_at')
    return render(request, 'restoransaddlist.html', {'applications': applications})


def approve_restaurant_request(request, request_id):
    application = get_object_or_404(RestaurantApplication, pk=request_id)
    application.status = 'approved'
    application.save()

    if application.owner:
        profile, _ = RestaurantProfile.objects.get_or_create(user=application.owner)
        profile.is_restaurant = True
        profile.save()

    restaurant, _ = RestorantInfo.objects.update_or_create(
        owner=application.owner,
        defaults={
            'name': application.name,
            'address': application.address,
            'phone_number': application.phone_number,
            'opening_hours': application.opening_hours,
            'photo': '',
        },
    )
    return redirect('restoransaddlist')


def reject_restaurant_request(request, request_id):
    application = get_object_or_404(RestaurantApplication, pk=request_id)
    application.status = 'rejected'
    application.save()
    return redirect('restoransaddlist')


def add_restaurant_info(request):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    restaurant = RestorantInfo.objects.filter(owner=request.user).first()
    form = RestorantInfoForm(request.POST or None, request.FILES or None, instance=restaurant)
    if request.method == 'POST' and form.is_valid():
        instance = form.save(commit=False)
        instance.owner = request.user
        instance.save()
        return redirect('restaurant_home')
    return render(request, 'addrestorantinfo.html', {'form': form})


def add_dish(request):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    restaurants = RestorantInfo.objects.filter(owner=request.user)
    if not restaurants.exists():
        return redirect('add_restaurant_info')

    form = DishForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('restaurant_home')
    return render(request, 'createdish.html', {'form': form})
