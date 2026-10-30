from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from auth_system.models import RestaurantProfile
from delivery_APP.models import RestaurantApplication


class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.credentials = {
            'first_name': 'Олена',
            'last_name': 'Ковальчук',
            'city': 'Київ',
            'password1': 'VioletTree!8291',
            'password2': 'VioletTree!8291',
        }

    def test_user_can_register(self):
        response = self.client.post(reverse('register'), self.credentials)

        self.assertRedirects(response, reverse('home'))
        user = get_user_model().objects.get(username='olena.kovalchuk')
        self.assertEqual(user.customer_profile.city, 'Київ')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        home_response = self.client.get(reverse('home'))
        self.assertTrue(home_response.context['user'].is_authenticated)

    def test_registration_offers_requested_city_choices(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            [city for city, _label in response.context['form'].fields['city'].choices[1:]],
            [
                'Київ', 'Харків', 'Одеса', 'Дніпро', 'Львів', 'Запоріжжя',
                'Вінниця', 'Полтава', 'Чернігів', 'Черкаси', 'Житомир', 'Суми',
                'Хмельницький', 'Рівне', 'Чернівці', 'Кропивницький',
                'Івано-Франківськ', 'Тернопіль', 'Луцьк', 'Ужгород', 'Миколаїв',
                'Херсон', 'Кривий Ріг', 'Кременчук', 'Біла Церква',
                "Кам'янець-Подільський", 'Золочів',
            ],
        )

    def test_registered_user_can_log_in_with_name(self):
        self.client.post(reverse('register'), self.credentials)
        self.client.get(reverse('logout'))

        response = self.client.post(reverse('login'), {
            'username': 'Олена.Ковальчук',
            'password': self.credentials['password1'],
        })

        self.assertRedirects(response, reverse('home'))
        user = get_user_model().objects.get(username='olena.kovalchuk')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        home_response = self.client.get(reverse('home'))
        self.assertTrue(home_response.context['user'].is_authenticated)


class RestaurantAuthenticationTests(TestCase):
    restaurant_details = {
        'restaurant_name': 'Green Bistro',
        'city': 'Київ',
        'contact_first_name': 'Олена',
        'contact_last_name': 'Ковальчук',
        'business_type': 'perkarna',
        'corporate_email': 'owner@greenbistro.example',
        'contact_phone': '+380501234567',
    }

    def register_restaurant(self):
        return self.client.post(
            reverse('restaurant_register'),
            self.restaurant_details,
        )

    def set_up_logged_in_user(self):
        user = get_user_model().objects.create_user(
            username='olena.kovalchuk',
            email=self.restaurant_details['corporate_email'],
            password='VioletTree!8291',
            first_name='Олена',
            last_name='Ковальчук',
        )
        self.client.force_login(user)
        return user

    def test_anonymous_user_cannot_register_restaurant(self):
        response = self.client.get(reverse('restaurant_register'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('restaurant_register')}",
        )
        user = get_user_model().objects.create_user(
            username='olena.kovalchuk',
            password='VioletTree!8291',
        )
        login_response = self.client.post(reverse('login'), {
            'username': user.username,
            'password': 'VioletTree!8291',
            'next': reverse('restaurant_register'),
        })
        self.assertRedirects(login_response, reverse('restaurant_register'))
        application_response = self.client.post(
            reverse('restaurant_register'),
            self.restaurant_details,
        )

        self.assertTemplateUsed(application_response, 'wait.html')
        self.assertEqual(application_response.status_code, 200)
        application = RestaurantApplication.objects.get()
        self.assertEqual(application_response.context['application'], application)
        self.assertContains(application_response, f'#{application.pk}')
        self.assertEqual(application.owner, user)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_logged_in_user_submits_application_for_their_account(self):
        user = self.set_up_logged_in_user()

        response = self.register_restaurant()

        self.assertTemplateUsed(response, 'wait.html')
        self.assertEqual(response.status_code, 200)
        application = RestaurantApplication.objects.get()
        self.assertEqual(application.owner, user)
        self.assertEqual(application.city, 'Київ')
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_application_status_endpoint_returns_current_status(self):
        user = self.set_up_logged_in_user()
        application = RestaurantApplication.objects.create(
            owner=user,
            name='Green Bistro',
            contact_name='Олена Ковальчук',
            phone_number='+380501234567',
            email='owner@greenbistro.example',
            address='',
            opening_hours='',
        )

        response = self.client.get(
            reverse('restaurant_application_status', args=[application.pk]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'status': 'pending',
            'status_display': 'На розгляді',
        })

        application.status = 'approved'
        application.save(update_fields=['status'])
        response = self.client.get(
            reverse('restaurant_application_status', args=[application.pk]),
        )
        self.assertEqual(response.json()['status'], 'approved')

    def test_user_cannot_check_another_users_application(self):
        owner = get_user_model().objects.create_user(
            username='application-owner',
            password='password',
        )
        application = RestaurantApplication.objects.create(
            owner=owner,
            name='Green Bistro',
            contact_name='Олена Ковальчук',
            phone_number='+380501234567',
            email='owner@greenbistro.example',
            address='',
            opening_hours='',
        )
        self.set_up_logged_in_user()

        response = self.client.get(
            reverse('restaurant_application_status', args=[application.pk]),
        )

        self.assertEqual(response.status_code, 404)

    def test_restaurant_registration_offers_requested_city_choices(self):
        self.set_up_logged_in_user()
        response = self.client.get(reverse('restaurant_register'))

        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(
            [city for city, _label in response.context['form'].fields['city'].choices[1:]],
            [
                'Київ', 'Харків', 'Одеса', 'Дніпро', 'Львів', 'Запоріжжя',
                'Вінниця', 'Полтава', 'Чернігів', 'Черкаси', 'Житомир', 'Суми',
                'Хмельницький', 'Рівне', 'Чернівці', 'Кропивницький',
                'Івано-Франківськ', 'Тернопіль', 'Луцьк', 'Ужгород', 'Миколаїв',
                'Херсон', 'Кривий Ріг', 'Кременчук', 'Біла Церква',
                "Кам'янець-Подільський", 'Золочів',
            ],
        )

    def test_approved_restaurant_owner_can_log_in_with_corporate_email(self):
        user = self.set_up_logged_in_user()
        self.register_restaurant()
        application = RestaurantApplication.objects.get(
            corporate_email=self.restaurant_details['corporate_email'],
        )
        self.client.get(reverse('logout'))
        RestaurantProfile.objects.create(
            user=user,
            is_restaurant=True,
        )

        response = self.client.post(reverse('restaurant_login'), {
            'username': self.restaurant_details['corporate_email'],
            'password': 'VioletTree!8291',
        })

        self.assertRedirects(response, reverse('restaurant_home'))
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            application.owner_id,
        )

    def test_pending_restaurant_application_shows_clear_login_error(self):
        self.set_up_logged_in_user()
        self.register_restaurant()
        self.client.get(reverse('logout'))

        response = self.client.post(reverse('restaurant_login'), {
            'username': self.restaurant_details['corporate_email'],
            'password': 'VioletTree!8291',
        })

        self.assertContains(response, 'заявка ще на розгляді')
