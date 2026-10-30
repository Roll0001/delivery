from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import user_passes_test
from django.db.models import DecimalField, ExpressionWrapper, F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from auth_system.models import RestaurantProfile
from .forms import (
    DishForm,
    MenuDishForm,
    OrderForm,
    ProductTypeForm,
    RestaurantApplicationForm,
    RestorantInfoForm,
)
from .models import CartOfMenu, Delivery, Dish, ProductType, RestaurantApplication, RestorantInfo


def _business_type_for_owner(owner, restaurant):
    if restaurant.business_type:
        return restaurant.business_type

    approved_application = RestaurantApplication.objects.filter(
        owner=owner,
        status='approved',
    ).order_by('-created_at').first()
    return approved_application.business_type if approved_application else ''


def home(request):
    query = request.GET.get('q', '').strip()
    category_kind = request.GET.get('kind', '')
    category = request.GET.get('category', '')
    restaurants = RestorantInfo.objects.all().order_by('name')
    customer_profile = (
        getattr(request.user, 'customer_profile', None)
        if request.user.is_authenticated
        else None
    )
    customer_city = customer_profile.city if customer_profile else ''
    if customer_city:
        restaurants = restaurants.filter(city=customer_city)

    if query:
        restaurants = restaurants.filter(
            Q(name__icontains=query) | Q(address__icontains=query)
        )

    dish_choices = Dish.DISH_TYPE_CHOICES
    product_choices = ProductType.PRODUCT_TYPE_CHOICES
    catalog_dishes = Dish.objects.none()
    products = ProductType.objects.none()
    selected_category_label = ''

    if category_kind == 'dish':
        selected_category_label = dict(dish_choices).get(category, '')
        if selected_category_label:
            catalog_dishes = Dish.objects.filter(
                dish_type=category,
                restaurant__isnull=False,
            ).select_related('restaurant').order_by('name')
            if customer_city:
                catalog_dishes = catalog_dishes.filter(restaurant__city=customer_city)
            if query:
                catalog_dishes = catalog_dishes.filter(
                    Q(name__icontains=query)
                    | Q(ingridients__icontains=query)
                    | Q(restaurant__name__icontains=query)
                )
    elif category_kind == 'product':
        selected_category_label = dict(product_choices).get(category, '')
        if selected_category_label:
            products = ProductType.objects.filter(
                product_type=category,
                restaurant__isnull=False,
            ).select_related('restaurant').order_by('name')
            if customer_city:
                products = products.filter(restaurant__city=customer_city)
            if query:
                products = products.filter(
                    Q(name__icontains=query)
                    | Q(weight__icontains=query)
                    | Q(restaurant__name__icontains=query)
                )

    return render(request, 'home.html', {
        'restaurants': restaurants,
        'query': query,
        'customer_city': customer_city,
        'dish_type_choices': dish_choices,
        'product_type_choices': product_choices,
        'category_kind': category_kind,
        'category': category,
        'selected_category_label': selected_category_label,
        'catalog_dishes': catalog_dishes,
        'products': products,
    })


def restaurant_home(request):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    restaurants = RestorantInfo.objects.filter(owner=request.user).order_by('name')
    restaurant = restaurants.first()
    business_type = _business_type_for_owner(request.user, restaurant) if restaurant else ''
    is_restaurant = not business_type or business_type == 'restaurant'
    dishes = Dish.objects.none()
    products = ProductType.objects.none()
    legacy_dishes = CartOfMenu.objects.none()
    if restaurant:
        if is_restaurant:
            dishes = Dish.objects.filter(restaurant__owner=request.user).select_related('restaurant').order_by('name')
            legacy_dishes = CartOfMenu.objects.filter(
                restaurant__owner=request.user,
            ).select_related('restaurant').order_by('-price')
        else:
            products = ProductType.objects.filter(
                restaurant__owner=request.user,
            ).select_related('restaurant').order_by('name')

    return render(request, 'homepageforrestorant.html', {
        'restaurants': restaurants,
        'dishes': dishes,
        'legacy_dishes': legacy_dishes,
        'products': products,
        'is_restaurant': is_restaurant,
    })


def restaurant_orders(request):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    orders = Delivery.objects.filter(
        cart__restaurant__owner=request.user,
    ).select_related('cart', 'cart__restaurant').annotate(
        total=ExpressionWrapper(
            F('cart__price') * F('quantity'),
            output_field=DecimalField(max_digits=10, decimal_places=2),
        ),
    ).order_by('-order_time', '-pk')
    return render(request, 'orders.html', {'orders': orders})


def restaurant_menu(request, restaurant_id):
    restaurant = get_object_or_404(RestorantInfo, pk=restaurant_id)
    dishes = CartOfMenu.objects.filter(restaurant=restaurant).order_by('name')
    catalog_dishes = Dish.objects.filter(
        restaurant=restaurant,
    ).exclude(
        name__in=dishes.values('name'),
    ).order_by('name')

    return render(request, 'MenuOfRestorant.html', {
        'restaurant': restaurant,
        'dishes': dishes,
        'catalog_dishes': catalog_dishes,
    })


def place_order(request, dish_id):
    dish = get_object_or_404(
        CartOfMenu.objects.select_related('restaurant'),
        pk=dish_id,
        restaurant__isnull=False,
    )
    form = OrderForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        order = form.save(commit=False)
        order.cart = dish
        order.user = request.user if request.user.is_authenticated else None
        order.save()
        return render(request, 'order.html', {
            'dish': dish,
            'order': order,
            'total': dish.price * order.quantity,
        })

    return render(request, 'order.html', {
        'dish': dish,
        'form': form,
    })


@user_passes_test(lambda user: user.is_staff)
def restaurant_requests(request):
    applications = RestaurantApplication.objects.order_by('-created_at')
    return render(request, 'restoransaddlist.html', {'applications': applications})


@user_passes_test(lambda user: user.is_staff)
@require_POST
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
            'business_type': application.business_type,
            'city': application.city,
            'address': application.address,
            'phone_number': application.phone_number,
            'opening_hours': application.opening_hours,
            'photo': '',
        },
    )
    return redirect('restoransaddlist')


@user_passes_test(lambda user: user.is_staff)
@require_POST
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

    restaurant = RestorantInfo.objects.filter(owner=request.user).first()
    if not restaurant:
        return redirect('add_restaurant_info')

    business_type = _business_type_for_owner(request.user, restaurant)
    is_restaurant = not business_type or business_type == 'restaurant'
    item_form = DishForm if is_restaurant else ProductTypeForm
    form = item_form(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.restaurant = restaurant
        item.save()
        return redirect('restaurant_home')
    return render(request, 'createdish.html', {
        'form': form,
        'is_restaurant': is_restaurant,
        'item_label': 'страву' if is_restaurant else 'товар',
    })


def edit_catalog_item(request, item_id, model, item_form, is_restaurant):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    item = get_object_or_404(
        model.objects.filter(restaurant__owner=request.user),
        pk=item_id,
    )
    form = item_form(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('restaurant_home')
    return render(request, 'createdish.html', {
        'form': form,
        'editing': True,
        'is_restaurant': is_restaurant,
        'item_label': 'страву' if is_restaurant else 'товар',
    })


def edit_catalog_dish(request, dish_id):
    return edit_catalog_item(request, dish_id, Dish, DishForm, is_restaurant=True)


def edit_product(request, product_id):
    return edit_catalog_item(request, product_id, ProductType, ProductTypeForm, is_restaurant=False)


def edit_dish(request, dish_id):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    dish = get_object_or_404(
        CartOfMenu.objects.filter(restaurant__owner=request.user),
        pk=dish_id,
    )
    form = MenuDishForm(
        request.POST or None,
        request.FILES or None,
        instance=dish,
        user=request.user,
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('restaurant_home')
    return render(request, 'createdish.html', {
        'form': form,
        'editing': True,
        'is_restaurant': True,
        'item_label': 'страву',
    })


@require_POST
def delete_dish(request, dish_id):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    dish = get_object_or_404(
        CartOfMenu.objects.filter(restaurant__owner=request.user),
        pk=dish_id,
    )
    dish.delete()
    return redirect('restaurant_home')


@require_POST
def delete_catalog_dish(request, dish_id):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    dish = get_object_or_404(Dish.objects.filter(restaurant__owner=request.user), pk=dish_id)
    dish.delete()
    return redirect('restaurant_home')


@require_POST
def delete_product(request, product_id):
    if not request.user.is_authenticated:
        return redirect('restaurant_login')

    profile = getattr(request.user, 'restaurant_profile', None)
    if not profile or not profile.is_restaurant:
        return redirect('home')

    product = get_object_or_404(
        ProductType.objects.filter(restaurant__owner=request.user),
        pk=product_id,
    )
    product.delete()
    return redirect('restaurant_home')
