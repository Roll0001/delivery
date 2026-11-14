from io import BytesIO
import tempfile

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse

from PIL import Image

from auth_system.models import CourierProfile, CustomerProfile, RestaurantProfile
from delivery_APP.models import (
    CartOfMenu,
    Delivery,
    Dish,
    ProductType,
    RestaurantApplication,
    RestorantInfo,
)


class HomeAdminLinkTests(TestCase):
    def test_homepage_lists_dish_and_product_category_buttons(self):
        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        for _value, label in Dish.DISH_TYPE_CHOICES:
            self.assertContains(response, label)
        for _value, label in ProductType.PRODUCT_TYPE_CHOICES:
            self.assertContains(response, label)

    def test_homepage_dish_category_filters_by_category_and_customer_city(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        CustomerProfile.objects.create(user=user, city='Київ')
        restaurant = RestorantInfo.objects.create(
            name='Kyiv Bistro',
            city='Київ',
            address='Main street',
            phone_number='+380501234567',
            opening_hours='09:00-21:00',
        )
        other_city_restaurant = RestorantInfo.objects.create(
            name='Lviv Bistro',
            city='Львів',
            address='Central street',
            phone_number='+380501234568',
            opening_hours='09:00-21:00',
        )
        Dish.objects.create(
            restaurant=restaurant,
            name='Kyiv Pizza',
            dish_type='Pizza',
            ingridients='Cheese',
            weight='400 g',
            price=200,
        )
        Dish.objects.create(
            restaurant=restaurant,
            name='Kyiv Burger',
            dish_type='Burger',
            ingridients='Beef',
            weight='250 g',
            price=150,
        )
        Dish.objects.create(
            restaurant=other_city_restaurant,
            name='Lviv Pizza',
            dish_type='Pizza',
            ingridients='Tomato',
            weight='400 g',
            price=220,
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'), {'kind': 'dish', 'category': 'Pizza'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kyiv Pizza')
        self.assertNotContains(response, 'Kyiv Burger')
        self.assertNotContains(response, 'Lviv Pizza')

    def test_homepage_product_category_shows_matching_products(self):
        shop = RestorantInfo.objects.create(
            name='City Market',
            city='Київ',
            business_type='home',
            address='Market street',
            phone_number='+380501234569',
            opening_hours='08:00-21:00',
        )
        ProductType.objects.create(
            restaurant=shop,
            name='Coffee',
            product_type='Beverages',
            weight='250 g',
            price=180,
        )
        ProductType.objects.create(
            restaurant=shop,
            name='Tea',
            product_type='Beverages',
            weight='100 g',
            price=95,
        )
        ProductType.objects.create(
            restaurant=shop,
            name='Soap',
            product_type='home',
            weight='100 g',
            price=40,
        )

        response = self.client.get(
            reverse('home'),
            {'kind': 'product', 'category': 'Beverages'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Coffee')
        self.assertContains(response, 'Tea')
        self.assertNotContains(response, 'Soap')

    def test_customer_sees_restaurants_only_in_their_city(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        CustomerProfile.objects.create(user=user, city='Львів')
        RestorantInfo.objects.create(
            name='Lviv Bistro',
            city='Львів',
            address='Main street',
            phone_number='+380501234567',
            opening_hours='09:00-21:00',
        )
        RestorantInfo.objects.create(
            name='Kyiv Bistro',
            city='Київ',
            address='Central street',
            phone_number='+380501234568',
            opening_hours='09:00-21:00',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['customer_city'], 'Львів')
        self.assertContains(response, 'Lviv Bistro')
        self.assertNotContains(response, 'Kyiv Bistro')

    def test_guest_sees_restaurants_from_all_cities(self):
        RestorantInfo.objects.create(
            name='Lviv Bistro',
            city='Львів',
            address='Main street',
            phone_number='+380501234567',
            opening_hours='09:00-21:00',
        )
        RestorantInfo.objects.create(
            name='Kyiv Bistro',
            city='Київ',
            address='Central street',
            phone_number='+380501234568',
            opening_hours='09:00-21:00',
        )

        response = self.client.get(reverse('home'))

        self.assertContains(response, 'Lviv Bistro')
        self.assertContains(response, 'Kyiv Bistro')

    def test_restaurant_requests_page_loads(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='password',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('restoransaddlist'))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_cannot_view_restaurant_requests(self):
        response = self.client.get(reverse('restoransaddlist'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('restoransaddlist')}",
        )

    def test_staff_user_sees_restaurant_requests_link(self):
        admin = get_user_model().objects.create_user(
            username='admin',
            password='password',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.get(reverse('home'))

        self.assertContains(response, reverse('restoransaddlist'))
        self.assertContains(response, 'Заявки ресторанів')

    def test_regular_user_does_not_see_restaurant_requests_link(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertNotContains(response, reverse('restoransaddlist'))
        self.assertNotContains(response, 'Заявки ресторанів')

    def test_authenticated_user_sees_restaurant_registration_link(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, reverse('restaurant_register'))
        self.assertContains(response, 'Додати ресторан')
        self.assertContains(response, reverse('customer_orders'))

    def test_anonymous_user_does_not_see_restaurant_registration_link(self):
        response = self.client.get(reverse('home'))

        self.assertNotContains(response, reverse('restaurant_register'))
        self.assertNotContains(response, 'Додати ресторан')

    def test_approved_restaurant_owner_sees_management_link(self):
        user = get_user_model().objects.create_user(
            username='restaurant-owner',
            password='password',
        )
        RestaurantProfile.objects.create(user=user, is_restaurant=True)
        self.client.force_login(user)

        response = self.client.get(reverse('home'))

        self.assertContains(response, reverse('restaurant_home'))
        self.assertContains(response, 'Кабінет ресторану')


class RestaurantManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.owner = User.objects.create_user(username='owner', password='password')
        self.other_owner = User.objects.create_user(username='other', password='password')
        RestaurantProfile.objects.create(user=self.owner, is_restaurant=True)
        RestaurantProfile.objects.create(user=self.other_owner, is_restaurant=True)
        self.restaurant = RestorantInfo.objects.create(
            owner=self.owner,
            name='Green Bistro',
            address='Main street',
            phone_number='+380501234567',
            opening_hours='09:00-21:00',
        )
        self.other_restaurant = RestorantInfo.objects.create(
            owner=self.other_owner,
            name='Other Bistro',
            address='Other street',
            phone_number='+380501234568',
            opening_hours='10:00-22:00',
        )
        self.dish = CartOfMenu.objects.create(
            restaurant=self.restaurant,
            name='Soup',
            ingridients='Vegetables',
            weight=300,
            time_to_cook=15,
            price=120,
        )

    def test_owner_can_edit_own_dish(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('edit_dish', args=[self.dish.pk]), {
            'restaurant': self.restaurant.pk,
            'name': 'Updated soup',
            'ingridients': 'Fresh vegetables',
            'weight': '350',
            'time_to_cook': '20',
            'price': '150.00',
        })

        self.assertRedirects(response, reverse('restaurant_home'))
        self.dish.refresh_from_db()
        self.assertEqual(self.dish.name, 'Updated soup')
        self.assertEqual(self.dish.price, 150)

    def test_restaurant_owner_adds_dish_with_dish_model(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('create_dish'), {
            'name': 'Burger',
            'dish_type': 'Burger',
            'ingridients': 'Beef, bun',
            'weight': '250 g',
            'time_to_cook': '15',
            'price': '180.00',
        })

        self.assertRedirects(response, reverse('restaurant_home'))
        dish = Dish.objects.get()
        self.assertEqual(dish.restaurant, self.restaurant)
        self.assertEqual(dish.name, 'Burger')
        orderable_item = CartOfMenu.objects.get(catalog_dish=dish)
        self.assertEqual(orderable_item.weight, 250)
        self.assertEqual(orderable_item.price, dish.price)
        self.assertContains(self.client.get(reverse('restaurant_home')), 'Burger')

    def test_customer_can_order_dish_added_by_restaurant_owner(self):
        self.client.force_login(self.owner)
        self.client.post(reverse('create_dish'), {
            'name': 'Burger',
            'dish_type': 'Burger',
            'ingridients': 'Beef, bun',
            'weight': '250 g',
            'time_to_cook': '15',
            'price': '180.00',
        })
        dish = Dish.objects.get(name='Burger')
        orderable_item = CartOfMenu.objects.get(catalog_dish=dish)

        menu_response = self.client.get(
            reverse('restaurant_menu', args=[self.restaurant.pk]),
        )
        self.assertContains(
            menu_response,
            reverse('place_order', args=[orderable_item.pk]),
        )

        customer = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        self.client.force_login(customer)
        order_response = self.client.post(
            reverse('place_order', args=[orderable_item.pk]),
            {
                'name': 'Олена',
                'address': 'Main street 1',
                'city': 'Львів',
                'phone_number': '+380501234567',
                'quantity': '1',
                'payment_method': 'tothecourier',
            },
        )

        self.assertEqual(order_response.status_code, 200)
        self.assertEqual(Delivery.objects.get().cart, orderable_item)

    def test_shop_owner_adds_product_with_product_type_model(self):
        self.restaurant.business_type = 'home'
        self.restaurant.save(update_fields=['business_type'])
        self.client.force_login(self.owner)

        cabinet_response = self.client.get(reverse('restaurant_home'))
        self.assertContains(cabinet_response, 'Каталог товарів')
        self.assertNotContains(cabinet_response, reverse('restaurant_orders'))

        response = self.client.post(reverse('create_dish'), {
            'name': 'Face cream',
            'product_type': 'home',
            'weight': '50 ml',
            'price': '250.00',
        })

        self.assertRedirects(response, reverse('restaurant_home'))
        product = ProductType.objects.get()
        self.assertEqual(product.restaurant, self.restaurant)
        self.assertEqual(product.name, 'Face cream')
        self.assertContains(self.client.get(reverse('restaurant_home')), 'Face cream')

    def test_existing_shop_uses_approved_application_business_type(self):
        self.restaurant.business_type = ''
        self.restaurant.save(update_fields=['business_type'])
        RestaurantApplication.objects.create(
            owner=self.owner,
            name='Green Bistro',
            contact_name='Restaurant Owner',
            business_type='home',
            city='Київ',
            phone_number='+380501234567',
            email='owner@example.com',
            address='Main street',
            opening_hours='09:00-21:00',
            status='approved',
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('restaurant_home'))

        self.assertContains(response, 'Каталог товарів')
        self.assertNotContains(response, 'Страви')

    def test_owner_cannot_edit_or_delete_another_shops_product(self):
        other_product = ProductType.objects.create(
            restaurant=self.other_restaurant,
            name='Other product',
            weight='100 g',
            price=50,
        )
        self.client.force_login(self.owner)

        edit_response = self.client.get(reverse('edit_product', args=[other_product.pk]))
        delete_response = self.client.post(reverse('delete_product', args=[other_product.pk]))

        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(ProductType.objects.filter(pk=other_product.pk).exists())

    def test_owner_can_add_restaurant_information_without_photo(self):
        user = get_user_model().objects.create_user(
            username='new-restaurant-owner',
            password='password',
        )
        RestaurantProfile.objects.create(user=user, is_restaurant=True)
        self.client.force_login(user)

        response = self.client.post(reverse('add_restaurant_info'), {
            'name': 'New Market',
            'address': 'Market street 5',
            'phone_number': '+380501112233',
            'opening_hours': '08:00-20:00',
        })

        self.assertRedirects(response, reverse('restaurant_home'))
        restaurant = RestorantInfo.objects.get(owner=user)
        self.assertEqual(restaurant.name, 'New Market')
        self.assertEqual(restaurant.address, 'Market street 5')
        self.assertEqual(restaurant.phone_number, '+380501112233')
        self.assertEqual(restaurant.opening_hours, '08:00-20:00')
        self.assertFalse(restaurant.photo)

    def test_owner_can_update_restaurant_information(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('add_restaurant_info'), {
            'name': 'Updated Bistro',
            'address': 'Updated street 10',
            'phone_number': '+380501112233',
            'opening_hours': '08:00-20:00',
        })

        self.assertRedirects(response, reverse('restaurant_home'))
        self.restaurant.refresh_from_db()
        self.assertEqual(self.restaurant.name, 'Updated Bistro')
        self.assertEqual(self.restaurant.address, 'Updated street 10')
        self.assertEqual(self.restaurant.phone_number, '+380501112233')

    def test_owner_cannot_edit_or_delete_another_restaurants_dish(self):
        other_dish = CartOfMenu.objects.create(
            restaurant=self.other_restaurant,
            name='Other soup',
            ingridients='Vegetables',
            weight=300,
            time_to_cook=15,
            price=120,
        )
        self.client.force_login(self.owner)

        edit_response = self.client.get(reverse('edit_dish', args=[other_dish.pk]))
        delete_response = self.client.post(reverse('delete_dish', args=[other_dish.pk]))

        self.assertEqual(edit_response.status_code, 404)
        self.assertEqual(delete_response.status_code, 404)
        self.assertTrue(CartOfMenu.objects.filter(pk=other_dish.pk).exists())

    def test_owner_can_delete_own_dish_with_post(self):
        self.client.force_login(self.owner)

        response = self.client.post(reverse('delete_dish', args=[self.dish.pk]))

        self.assertRedirects(response, reverse('restaurant_home'))
        self.assertFalse(CartOfMenu.objects.filter(pk=self.dish.pk).exists())

    def test_owner_sees_only_orders_for_their_restaurants(self):
        own_order = Delivery.objects.create(
            cart=self.dish,
            name='Олена',
            address='Main street',
            phone_number='+380501234567',
            quantity=2,
        )
        other_dish = CartOfMenu.objects.create(
            restaurant=self.other_restaurant,
            name='Other soup',
            ingridients='Vegetables',
            weight=300,
            time_to_cook=15,
            price=80,
        )
        Delivery.objects.create(
            cart=other_dish,
            name='Іван',
            address='Other street',
            phone_number='+380501234568',
        )
        self.client.force_login(self.owner)

        response = self.client.get(reverse('restaurant_orders'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'orders.html')
        self.assertEqual(list(response.context['orders']), [own_order])
        self.assertEqual(response.context['orders'][0].total, 240)
        self.assertContains(response, '240.00')
        self.assertContains(response, 'Замовлення')
        self.assertNotContains(response, 'Іван')
        cabinet_response = self.client.get(reverse('restaurant_home'))
        self.assertContains(cabinet_response, reverse('restaurant_orders'))

    def test_non_restaurant_cannot_view_restaurant_orders(self):
        customer = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        self.client.force_login(customer)

        response = self.client.get(reverse('restaurant_orders'))

        self.assertRedirects(response, reverse('home'))

    def test_anonymous_user_is_redirected_from_restaurant_orders(self):
        response = self.client.get(reverse('restaurant_orders'))

        self.assertRedirects(response, reverse('restaurant_login'))

    def test_deleting_dish_with_get_is_not_allowed(self):
        self.client.force_login(self.owner)

        response = self.client.get(reverse('delete_dish', args=[self.dish.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(CartOfMenu.objects.filter(pk=self.dish.pk).exists())

    def test_owner_cannot_approve_restaurant_application(self):
        application = RestaurantApplication.objects.create(
            owner=self.owner,
            name='Pending Bistro',
            contact_name='Restaurant Owner',
            phone_number='+380501234567',
            email='owner@example.com',
            address='Main street',
            opening_hours='09:00-21:00',
        )
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse('approve_restaurant_request', args=[application.pk]),
        )

        application.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)
        self.assertEqual(application.status, 'pending')

    def test_staff_approval_enables_owner_restaurant_management(self):
        application = RestaurantApplication.objects.create(
            owner=self.owner,
            name='Approved Bistro',
            contact_name='Restaurant Owner',
            business_type='restaurant',
            city='Львів',
            phone_number='+380501234567',
            email='owner@example.com',
            address='Main street',
            opening_hours='09:00-21:00',
        )
        admin = get_user_model().objects.create_user(
            username='staff-admin',
            password='password',
            is_staff=True,
        )
        self.client.force_login(admin)

        response = self.client.post(
            reverse('approve_restaurant_request', args=[application.pk]),
        )

        self.assertRedirects(response, reverse('restoransaddlist'))
        application.refresh_from_db()
        self.assertEqual(application.status, 'approved')
        restaurant = RestorantInfo.objects.get(owner=self.owner, name='Approved Bistro')
        self.assertEqual(restaurant.city, 'Львів')
        self.assertEqual(restaurant.business_type, 'restaurant')

        self.client.force_login(self.owner)
        cabinet_response = self.client.get(reverse('restaurant_home'))
        self.assertEqual(cabinet_response.status_code, 200)
        self.assertContains(cabinet_response, 'Approved Bistro')


class CustomerOrderTests(TestCase):
    def setUp(self):
        self.restaurant = RestorantInfo.objects.create(
            name='Green Bistro',
            city='Львів',
            address='Main street',
            phone_number='+380501234567',
            opening_hours='09:00-21:00',
        )
        self.dish = CartOfMenu.objects.create(
            restaurant=self.restaurant,
            name='Soup',
            ingridients='Vegetables',
            weight=300,
            time_to_cook=15,
            price=120,
        )

    def test_restaurant_menu_uses_existing_template(self):
        response = self.client.get(
            reverse('restaurant_menu', args=[self.restaurant.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'menuofrestorant.html')
        self.assertContains(response, reverse('place_order', args=[self.dish.pk]))

    def test_customer_orders_page_lists_only_the_current_users_orders(self):
        customer = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        other_customer = get_user_model().objects.create_user(
            username='other-customer',
            password='password',
        )
        own_order = Delivery.objects.create(
            user=customer,
            cart=self.dish,
            name='Олена',
            address='Main street 1',
            phone_number='+380501234567',
            quantity=2,
            city='Львів',
            status='delivered',
        )
        Delivery.objects.create(
            user=other_customer,
            cart=self.dish,
            name='Іван',
            address='Main street 2',
            phone_number='+380501234568',
        )
        self.client.force_login(customer)

        response = self.client.get(reverse('customer_orders'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_orders.html')
        self.assertContains(response, f'Замовлення №{own_order.pk}')
        self.assertContains(response, '240.00 ₴')
        self.assertContains(
            response,
            reverse('completed_order', args=[own_order.tracking_token]),
        )
        self.assertNotContains(response, 'Іван')

    def test_customer_orders_page_requires_login(self):
        response = self.client.get(reverse('customer_orders'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('customer_orders')}",
        )

    def test_customer_can_place_order_as_guest(self):
        response = self.client.post(
            reverse('place_order', args=[self.dish.pk]),
            {
                'name': 'Олена',
                'address': 'Київ, вул. Центральна 1',
                'city': 'Львів',
                'phone_number': '+380501234567',
                'quantity': '2',
                'payment_method': 'tothecourier',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order.html')
        self.assertContains(response, 'Замовлення прийнято')
        self.assertContains(response, '240')
        order = Delivery.objects.get()
        self.assertIsNone(order.user)
        self.assertEqual(order.cart, self.dish)
        self.assertEqual(order.quantity, 2)
        self.assertEqual(order.payment_method, 'tothecourier')
        self.assertEqual(order.city, 'Львів')
        self.assertContains(
            response,
            reverse('completed_order', args=[order.tracking_token]),
        )

    def test_logged_in_customer_order_is_linked_to_account(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='password',
            first_name='Олена',
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse('place_order', args=[self.dish.pk]),
            {
                'name': 'Олена',
                'address': 'Київ, вул. Центральна 1',
                'city': 'Львів',
                'phone_number': '+380501234567',
                'quantity': '1',
                'payment_method': 'cart',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Delivery.objects.get().user, user)

    def test_invalid_quantity_does_not_create_order(self):
        response = self.client.post(
            reverse('place_order', args=[self.dish.pk]),
            {
                'name': 'Олена',
                'address': 'Київ, вул. Центральна 1',
                'city': 'Львів',
                'phone_number': '+380501234567',
                'quantity': '0',
                'payment_method': 'tothecourier',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('quantity', response.context['form'].errors)
        self.assertEqual(Delivery.objects.count(), 0)

    def test_delivery_city_is_required(self):
        response = self.client.post(
            reverse('place_order', args=[self.dish.pk]),
            {
                'name': 'Олена',
                'address': 'Львів, вул. Центральна 1',
                'phone_number': '+380501234567',
                'quantity': '1',
                'payment_method': 'tothecourier',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('city', response.context['form'].errors)
        self.assertEqual(Delivery.objects.count(), 0)

    def test_order_form_defaults_to_customer_delivery_city_when_available(self):
        user = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        CustomerProfile.objects.create(user=user, city='Львів')
        self.client.force_login(user)

        response = self.client.get(reverse('place_order', args=[self.dish.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['form']['city'].value(), 'Львів')

    def test_customer_must_choose_delivery_area_when_profile_city_is_too_general(self):
        user = get_user_model().objects.create_user(
            username='kyiv-customer',
            password='password',
        )
        CustomerProfile.objects.create(user=user, city='Київ')
        self.client.force_login(user)

        response = self.client.get(reverse('place_order', args=[self.dish.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['form']['city'].value())

    def test_order_page_get_does_not_create_order(self):
        response = self.client.get(reverse('place_order', args=[self.dish.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order.html')
        self.assertEqual(Delivery.objects.count(), 0)


class CourierDeliveryTests(TestCase):
    def setUp(self):
        self.courier = get_user_model().objects.create_user(
            username='courier',
            password='password',
        )
        CourierProfile.objects.create(
            user=self.courier,
            city='Львів',
            transport='bicycle',
        )
        self.restaurant = RestorantInfo.objects.create(
            name='Lviv Bistro',
            city='Львів',
            address='Market street',
            phone_number='+380501234567',
            opening_hours='09:00-21:00',
        )
        self.dish = CartOfMenu.objects.create(
            restaurant=self.restaurant,
            name='Soup',
            ingridients='Vegetables',
            weight=300,
            time_to_cook=15,
            price=120,
        )
        self.media_directory = tempfile.TemporaryDirectory()
        media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.addCleanup(self.media_directory.cleanup)
        self.client.force_login(self.courier)

    def completion_photo(self):
        image_buffer = BytesIO()
        Image.new('RGB', (1, 1), color='green').save(image_buffer, format='PNG')
        return SimpleUploadedFile(
            'delivery-proof.png',
            image_buffer.getvalue(),
            content_type='image/png',
        )

    def create_order(self, *, city='Львів', status='new', courier=None):
        return Delivery.objects.create(
            cart=self.dish,
            name='Олена',
            address='Market street 1',
            phone_number='+380501234567',
            city=city,
            status=status,
            courier=courier,
        )

    def test_courier_sees_only_unassigned_new_orders_in_their_city(self):
        matching_order = self.create_order()
        self.create_order(city='Київ Лівий берег')
        self.create_order(status='on_way', courier=self.courier)

        response = self.client.get(reverse('courier_home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['available_orders']),
            [matching_order],
        )
        self.assertContains(response, f'Замовлення №{matching_order.pk}')

    def test_courier_can_accept_a_matching_city_order(self):
        order = self.create_order()

        response = self.client.post(reverse('accept_delivery', args=[order.pk]))

        self.assertRedirects(response, reverse('courier_home'))
        order.refresh_from_db()
        self.assertEqual(order.courier, self.courier)
        self.assertEqual(order.status, 'on_way')

    def test_courier_cannot_accept_another_order_until_current_delivery_is_done(self):
        first_order = self.create_order()
        second_order = self.create_order()
        self.client.post(reverse('accept_delivery', args=[first_order.pk]))

        response = self.client.post(reverse('accept_delivery', args=[second_order.pk]))

        self.assertRedirects(response, reverse('courier_home'))
        first_order.refresh_from_db()
        second_order.refresh_from_db()
        self.assertEqual(first_order.status, 'on_way')
        self.assertEqual(second_order.status, 'new')
        self.assertIsNone(second_order.courier)
        dashboard = self.client.get(reverse('courier_home'))
        self.assertContains(dashboard, 'Спершу заверши активну доставку')
        self.assertNotContains(dashboard, reverse('accept_delivery', args=[second_order.pk]))

    def test_database_prevents_a_courier_from_having_two_active_deliveries(self):
        self.create_order(status='on_way', courier=self.courier)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.create_order(status='on_way', courier=self.courier)

    def test_courier_can_accept_next_order_after_completing_delivery(self):
        first_order = self.create_order()
        second_order = self.create_order()
        self.client.post(reverse('accept_delivery', args=[first_order.pk]))

        response = self.client.post(
            reverse('complete_delivery', args=[first_order.pk]),
            {'completion_photo': self.completion_photo()},
        )

        self.assertRedirects(response, reverse('courier_home'))
        first_order.refresh_from_db()
        self.assertEqual(first_order.status, 'delivered')
        self.client.post(reverse('accept_delivery', args=[second_order.pk]))
        second_order.refresh_from_db()
        self.assertEqual(second_order.courier, self.courier)
        self.assertEqual(second_order.status, 'on_way')

    def test_delivery_cannot_be_completed_without_a_photo(self):
        order = self.create_order(status='on_way', courier=self.courier)

        response = self.client.post(
            reverse('complete_delivery', args=[order.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'completion_photo',
            response.context['completion_form'].errors,
        )
        order.refresh_from_db()
        self.assertEqual(order.status, 'on_way')
        self.assertFalse(order.completion_photo)

    def test_completion_photo_is_saved_and_visible_to_customer(self):
        order = self.create_order(status='on_way', courier=self.courier)
        customer_url = reverse(
            'completed_order',
            args=[order.tracking_token],
        )

        pending_response = self.client.get(customer_url)
        self.assertEqual(pending_response.status_code, 200)
        self.assertContains(pending_response, 'Замовлення ще доставляється')

        response = self.client.post(
            reverse('complete_delivery', args=[order.pk]),
            {'completion_photo': self.completion_photo()},
        )

        self.assertRedirects(response, reverse('courier_home'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'delivered')
        self.assertTrue(order.completion_photo)
        customer_response = self.client.get(customer_url)
        self.assertEqual(customer_response.status_code, 200)
        self.assertContains(customer_response, 'Замовлення доставлено!')
        self.assertContains(customer_response, order.completion_photo.url)

    def test_tracking_page_rejects_unknown_token(self):
        import uuid

        response = self.client.get(
            reverse('completed_order', args=[uuid.uuid4()]),
        )

        self.assertEqual(response.status_code, 404)

    def test_courier_cannot_accept_an_order_from_another_city(self):
        order = self.create_order(city='Київ Правий берег')

        response = self.client.post(reverse('accept_delivery', args=[order.pk]))

        self.assertRedirects(response, reverse('courier_home'))
        order.refresh_from_db()
        self.assertIsNone(order.courier)
        self.assertEqual(order.status, 'new')

    def test_courier_can_only_complete_their_own_active_order(self):
        order = self.create_order(status='on_way', courier=None)

        response = self.client.post(
            reverse('complete_delivery', args=[order.pk]),
        )

        self.assertEqual(response.status_code, 404)
        order.refresh_from_db()
        self.assertEqual(order.status, 'on_way')

    def test_accepting_order_requires_post(self):
        order = self.create_order()

        response = self.client.get(reverse('accept_delivery', args=[order.pk]))

        self.assertEqual(response.status_code, 405)
        order.refresh_from_db()
        self.assertEqual(order.status, 'new')

    def test_non_courier_cannot_open_courier_order_list(self):
        customer = get_user_model().objects.create_user(
            username='customer',
            password='password',
        )
        self.client.force_login(customer)

        response = self.client.get(reverse('courier_home'))

        self.assertRedirects(response, reverse('home'))

    def test_anonymous_user_is_redirected_to_courier_login(self):
        self.client.logout()

        response = self.client.get(reverse('courier_home'))

        self.assertRedirects(
            response,
            f"{reverse('courier_login')}?next={reverse('courier_home')}",
        )
