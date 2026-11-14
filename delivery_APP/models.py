import re
import uuid
from decimal import Decimal, ROUND_HALF_UP

from django.db import models
from django.conf import settings
from django.utils import timezone


def weight_in_grams(value):
    match = re.search(r'\d+(?:[.,]\d+)?', str(value))
    if not match:
        raise ValueError('Weight must contain a numeric amount.')

    weight = Decimal(match.group().replace(',', '.'))
    if 'кг' in str(value).lower():
        weight *= 1000
    if weight <= 0 or weight > 10000000:
        raise ValueError('Weight is outside the supported range.')
    weight = weight.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    if weight <= 0 or weight > 9999999:
        raise ValueError('Weight is outside the supported range.')
    return weight


CITY_CHOICES = [
    ('Київ', 'Київ'),
    ('Харків', 'Харків'),
    ('Одеса', 'Одеса'),
    ('Дніпро', 'Дніпро'),
    ('Львів', 'Львів'),
    ('Запоріжжя', 'Запоріжжя'),
    ('Вінниця', 'Вінниця'),
    ('Полтава', 'Полтава'),
    ('Чернігів', 'Чернігів'),
    ('Черкаси', 'Черкаси'),
    ('Житомир', 'Житомир'),
    ('Суми', 'Суми'),
    ('Хмельницький', 'Хмельницький'),
    ('Рівне', 'Рівне'),
    ('Чернівці', 'Чернівці'),
    ('Кропивницький', 'Кропивницький'),
    ('Івано-Франківськ', 'Івано-Франківськ'),
    ('Тернопіль', 'Тернопіль'),
    ('Луцьк', 'Луцьк'),
    ('Ужгород', 'Ужгород'),
    ('Миколаїв', 'Миколаїв'),
    ('Херсон', 'Херсон'),
    ('Кривий Ріг', 'Кривий Ріг'),
    ('Кременчук', 'Кременчук'),
    ('Біла Церква', 'Біла Церква'),
    ("Кам'янець-Подільський", "Кам'янець-Подільський"),
    ('Золочів', 'Золочів'),
]

COURIER_CITY_CHOICES = [
    ('Біла Церква', 'Біла Церква'),
    ('Бориспіль', 'Бориспіль'),
    ('Боярка', 'Боярка'),
    ('Бровари', 'Бровари'),
    ('Буковель', 'Буковель'),
    ('Черкаси', 'Черкаси'),
    ('Чернігів', 'Чернігів'),
    ('Чернівці', 'Чернівці'),
    ('Чорноморськ', 'Чорноморськ'),
    ('Дніпро', 'Дніпро'),
    ('Дрогобич', 'Дрогобич'),
    ('Ірпінь - Буча', 'Ірпінь - Буча'),
    ('Івано-Франківськ', 'Івано-Франківськ'),
    ('Камʼянець-Подільський', 'Камʼянець-Подільський'),
    ("Кам'янське", "Кам'янське"),
    ('Харків', 'Харків'),
    ('Хмельницький', 'Хмельницький'),
    ('Коломия', 'Коломия'),
    ('Ковель', 'Ковель'),
    ('Кременчук', 'Кременчук'),
    ('Кропивницький', 'Кропивницький'),
    ('Кривий Ріг', 'Кривий Ріг'),
    ('Київ Лівий берег', 'Київ Лівий берег'),
    ('Київ Правий берег', 'Київ Правий берег'),
    ('Луцьк', 'Луцьк'),
    ('Львів', 'Львів'),
    ('Мукачево', 'Мукачево'),
    ('Миколаїв', 'Миколаїв'),
    ('Одеса', 'Одеса'),
    ('Одеса (Котовського)', 'Одеса (Котовського)'),
    ('Олександрія', 'Олександрія'),
    ('Павлоград', 'Павлоград'),
    ('Полтава', 'Полтава'),
    ('Рівне', 'Рівне'),
    ('Самбір', 'Самбір'),
    ('Суми', 'Суми'),
    ('Тернопіль', 'Тернопіль'),
    ('Трускавець', 'Трускавець'),
    ('Ужгород', 'Ужгород'),
    ('Вінниця', 'Вінниця'),
    ('Вишгород', 'Вишгород'),
    ('Запоріжжя', 'Запоріжжя'),
    ('Житомир', 'Житомир'),
]

# Create your models here.
class RestaurantApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На розгляді'),
        ('approved', 'Схвалено'),
        ('rejected', 'Відхилено'),
    ]
    BUSINESS_TYPE_CHOICES = [
        ('restaurant', 'Ресторан'),
        ('perkarna', 'Перкарня'),
        ('beauty', 'Товари для краси'),
        ('electronics', 'Електроніка'),
        ('fashion', 'Мода'),
        ('flowers', 'Квіти та рослини'),
        ('delicacies', 'Делікатеси'),
        ('home', 'Товари для дому'),
        ('ice_cream', 'Морозиво'),
        ('jewelry', 'Ювелірні вироби'),
        ('optics', 'Оптика'),
        ('pharmacy', 'Аптека'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_applications',
        verbose_name='Власник',
    )
    name = models.CharField(max_length=200, verbose_name='Назва ресторану')
    photo = models.ImageField(upload_to='media/restaurant_photos/', blank=True, default='')
    contact_name = models.CharField(max_length=150, verbose_name='Контактна особа')
    contact_first_name = models.CharField(max_length=100, blank=True, default='', verbose_name="Ім'я контактної особи")
    contact_last_name = models.CharField(max_length=100, blank=True, default='', verbose_name='Прізвище контактної особи')
    business_type = models.CharField(max_length=50, choices=BUSINESS_TYPE_CHOICES, blank=True, default='', verbose_name='Тип магазину/ресторана')
    corporate_email = models.EmailField(blank=True, default='', verbose_name='Корпоративна email адреса')
    contact_phone = models.CharField(max_length=25, blank=True, default='', verbose_name='Номер контактної особи')
    city = models.CharField(max_length=100, choices=CITY_CHOICES, blank=True, default='', verbose_name='Місто')
    phone_number = models.CharField(max_length=25, verbose_name='Телефон')
    email = models.EmailField(blank=True, default='', verbose_name='Email')
    address = models.TextField(verbose_name='Адреса')
    opening_hours = models.CharField(max_length=100, verbose_name='Години роботи')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Dish(models.Model):
    DISH_TYPE_CHOICES = [
        ('Fast Food', 'Фаст-фуд'),
        ('Burger', 'Бургери'),
        ('American', 'Американська кухня'),
        ('Asian', 'Азіатська кухня'),
        ('World', 'Міжнародна кухня'),
        ('Ukrainian', 'Українська кухня'),
        ('Baking', 'Випічка'),
        ('Pizza', 'Піца'),
        ('Sushi', 'Суші'),
        ('Italian', 'Італійська кухня'),
        ('Healthy', 'Корисна їжа'),
        ('Grill', 'Гриль'),
        ('Alcohol', 'Алкоголь'),
        ('Georgian', 'Грузинська кухня'),
        ('Arabian', 'Арабська кухня'),
        ('Sweets', 'Солодощі'),
        ('Beverages', 'Чай і кава'),
        ('For Gyrmans', 'Для гурманів'),


    ]

    restaurant = models.ForeignKey(
        'RestorantInfo',
        on_delete=models.CASCADE,
        related_name='catalog_dishes',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200, verbose_name='Назва')
    photo = models.ImageField(upload_to='media/dish_photos/', blank=True, default='')
    dish_type = models.CharField(max_length=50, choices=DISH_TYPE_CHOICES, verbose_name='Тип страви')
    ingridients = models.CharField(max_length=100, verbose_name='Інгредієнти')
    weight = models.CharField(max_length=100, verbose_name='Вага')
    time_to_cook = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)


    # status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    # created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductType(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('supermarket', 'Супермаркет'),
        ('Alcohol', 'Алкоголь'),
        ('smoking', 'Для паління'),
        ('meat&fish', 'Мясо і риба'),
        ('Sweets', 'Солодощі'),
        ('Beverages', 'Чай і кава'),
        ('for gyrmans', 'Для гурманів'),
        ('home', 'Для дому'),
        ('apteka', 'Ліки'),
        ('other', 'Інше'),

    ]

    restaurant = models.ForeignKey(
        'RestorantInfo',
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200, verbose_name='Назва')
    photo = models.ImageField(upload_to='media/dish_photos/', blank=True, default='')
    product_type = models.CharField(max_length=50, choices=PRODUCT_TYPE_CHOICES, blank=True, default='', verbose_name='Тип продукту')
    weight = models.CharField(max_length=100, verbose_name='Вага')
    time_to_cook = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)


    # status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    # created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CartOfMenu(models.Model):
    catalog_dish = models.OneToOneField(
        'Dish',
        on_delete=models.CASCADE,
        related_name='orderable_item',
        null=True,
        blank=True,
    )
    restaurant = models.ForeignKey(
        'RestorantInfo',
        on_delete=models.CASCADE,
        related_name='dishes',
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    photo = models.ImageField(upload_to='media/dish_photos/', blank=True, default='')
    ingridients = models.TextField()
    weight = models.DecimalField(max_digits=7, decimal_places=0)
    time_to_cook = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.name

    @property
    def ingredients(self):
        return self.ingridients

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('new', 'Нове'),
        ('cooking', 'Готується'),
        ('on_way', 'В дорозі'),
        ('delivered', 'Доставлено'),
    ]
    PAYMENT_CHOICES = [
        ('tothecourier', "Готівкою кур'єру"),
        ('cart', 'Карткою'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deliveries',
    )
    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_deliveries',
    )
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    completion_photo = models.ImageField(
        upload_to='delivery_proofs/%Y/%m/',
        blank=True,
    )
    city = models.CharField(
        max_length=100,
        choices=COURIER_CITY_CHOICES,
        blank=True,
        default='',
    )
    name = models.CharField(max_length=100, default='')
    address = models.TextField(default='')
    phone_number = models.CharField(max_length=15, default='')
    order_time = models.DateTimeField(default=timezone.now)
    cart = models.ForeignKey(CartOfMenu, on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    payment_method = models.CharField(
        choices=PAYMENT_CHOICES,
        max_length=20,
        default='tothecourier',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['courier'],
                condition=models.Q(status__in=['cooking', 'on_way']),
                name='one_active_delivery_per_courier',
            ),
        ]

    def __str__(self):
        return f'Замовлення #{self.pk}'

class RestorantInfo(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurants',
        verbose_name='Власник',
    )
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='media/restorant_photos/')
    business_type = models.CharField(
        max_length=50,
        choices=RestaurantApplication.BUSINESS_TYPE_CHOICES,
        blank=True,
        default='',
        verbose_name='Тип закладу',
    )
    city = models.CharField(max_length=100, choices=CITY_CHOICES, blank=True, default='', verbose_name='Місто')
    address = models.TextField()
    phone_number = models.CharField(max_length=15)
    opening_hours = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Order(models.Model):
    payment = [
        ('tothecourier', "кур'єру"),
        ('cart', 'карткою'),

    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
    )
    username = models.CharField(max_length=100, default='')
    address = models.TextField(default='')
    phone_number = models.CharField(max_length=15, default='')
    payment_method = models.CharField(choices=payment, max_length=50, default='tothecourier')
    def __str__(self):
        return f'Замовлення #{self.pk}'
