"""
Наповнення Nosh демо-закладами, магазинами та меню.

Куди покласти:  <твій_додаток>/management/commands/seed_data.py
(у папках management/ і commands/ мають бути порожні __init__.py)

Запуск:
    python manage.py seed_data              # усі 27 міст з CITY_CHOICES
    python manage.py seed_data --cities 5   # лише перші 5 міст

Скрипт можна запускати повторно: наявні заклади (за назвою + містом) пропускаються.
"""
import hashlib
from decimal import Decimal
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from ...models import CartOfMenu, Dish, ProductType, RestorantInfo

RESTAURANT_BUSINESS_TYPE = "restaurant"  # ключ з BUSINESS_TYPE_CHOICES

# (назва, тип страви для Dish, [(страва, інгредієнти, вага, хвилин, ціна)])
RESTAURANTS = [
    ("Піцерія «Мамма Міа»", "Pizza", [
        ("Маргарита", "Томати, моцарела, базилік", "450 г", 20, 189),
        ("Пепероні", "Салямі пепероні, моцарела, соус", "480 г", 20, 219),
        ("Чотири сири", "Моцарела, дор-блю, пармезан, чеддер", "470 г", 22, 239),
        ("Карбонара", "Спагеті, бекон, яйце, пармезан", "350 г", 18, 179),
        ("Тирамісу", "Маскарпоне, савоярді, кава, какао", "150 г", 5, 99),
    ]),
    ("Суші «Токіо»", "Sushi", [
        ("Філадельфія", "Лосось, вершковий сир, рис, норі", "260 г", 25, 289),
        ("Каліфорнія", "Краб, авокадо, огірок, ікра масаго", "240 г", 25, 249),
        ("Рамен із куркою", "Локшина, курка, яйце, бульйон", "450 г", 20, 199),
        ("Місо-суп", "Місо-паста, тофу, водорості вакаме", "300 мл", 10, 99),
        ("Гьоза", "Свинина, капуста, імбир, тісто", "200 г", 15, 149),
    ]),
    ("Бургер Хаус", "Burger", [
        ("Чізбургер", "Яловичина, чеддер, салат, булочка", "280 г", 12, 149),
        ("Бекон-бургер", "Яловичина, бекон, соус BBQ, цибуля", "320 г", 14, 179),
        ("Курячий бургер", "Куряче філе, салат, соус, булочка", "270 г", 12, 139),
        ("Картопля фрі", "Картопля, сіль", "150 г", 8, 69),
        ("Нагетси", "Куряче філе, паніровка", "180 г", 10, 99),
    ]),
    ("Українська хата", "Ukrainian", [
        ("Борщ із пампушками", "Буряк, капуста, м'ясо, часник", "400 г", 15, 129),
        ("Вареники з картоплею", "Тісто, картопля, смажена цибуля", "300 г", 15, 109),
        ("Деруни зі сметаною", "Картопля, цибуля, сметана", "250 г", 15, 99),
        ("Голубці", "Капуста, фарш, рис, томатний соус", "350 г", 20, 139),
        ("Узвар", "Сухофрукти, вода, мед", "300 мл", 3, 39),
    ]),
]

# (назва, тип товару для ProductType, тип закладу (business_type), [(товар, вага, ціна)])
SHOPS = [
    ("Продмаркет «Сусід»", "supermarket", "delicacies", [
        ("Молоко 2,5%", "900 мл", 42), ("Хліб пшеничний", "500 г", 28),
        ("Яйця курячі, 10 шт", "10 шт", 68), ("Сир кисломолочний", "350 г", 59),
        ("Макарони", "400 г", 35), ("Яблука", "1 кг", 45),
    ]),
    ("М'ясна лавка", "meat&fish", "delicacies", [
        ("Курячі стегна", "1 кг", 119), ("Свинна шия", "1 кг", 229),
        ("Філе лосося", "500 г", 329), ("Фарш домашній", "500 г", 135),
        ("Ковбаски для гриля", "600 г", 169),
    ]),
    ("Аптека «Здоров'я»", "apteka", "pharmacy", [
        ("Вітамін C", "30 таб.", 89), ("Пластир медичний", "20 шт", 35),
        ("Бинт стерильний", "1 шт", 25), ("Антисептик", "100 мл", 59),
        ("Термометр", "1 шт", 149),
    ]),
    ("Дім і побут", "home", "home", [
        ("Засіб для миття посуду", "500 мл", 59), ("Губки для посуду, 5 шт", "5 шт", 32),
        ("Пакети для сміття", "30 шт", 45), ("Свічки", "10 шт", 79),
        ("Рушники паперові", "2 рулони", 69),
    ]),
]


def placeholder(seed):
    """Кольоровий плейсхолдер замість фото (потім заміни на справжні в адмінці)."""
    h = hashlib.md5(seed.encode()).digest()
    color = tuple(110 + b % 110 for b in h[:3])
    img = Image.new("RGB", (800, 600), color)
    d = ImageDraw.Draw(img)
    light = tuple(min(255, c + 40) for c in color)
    d.ellipse((200, 100, 600, 500), fill=light)
    d.ellipse((290, 190, 510, 410), fill=color)
    buf = BytesIO()
    img.save(buf, "JPEG", quality=80)
    return ContentFile(buf.getvalue(), name=f"{h.hex()[:12]}.jpg")


class Command(BaseCommand):
    help = "Додає демо-ресторани, магазини та меню для різних міст"

    def add_arguments(self, parser):
        parser.add_argument("--cities", type=int, default=0, help="Скільки міст взяти (0 = усі)")

    @transaction.atomic
    def handle(self, *args, **opts):
        city_field = RestorantInfo._meta.get_field("city")

        cities = [c for c, _ in city_field.choices if c]
        if opts["cities"]:
            cities = cities[: opts["cities"]]
        if not cities:
            raise CommandError("У CITY_CHOICES немає міст.")

        created = 0
        for ci, city in enumerate(cities, start=1):
            for ri, (name, kind, items) in enumerate(RESTAURANTS, start=1):
                place, is_new = self._place(name, city, RESTAURANT_BUSINESS_TYPE, ci, ri)
                if not is_new:
                    continue
                created += 1
                for dname, ingr, weight, minutes, price in items:
                    seed = f"{city}{name}{dname}"
                    dish = Dish.objects.create(
                        restaurant=place, name=dname, photo=placeholder(seed),
                        dish_type=kind, ingridients=ingr[:100], weight=weight,
                        time_to_cook=minutes, price=Decimal(price),
                    )
                    CartOfMenu.objects.create(
                        catalog_dish=dish, restaurant=place, name=dname,
                        photo=dish.photo.name,
                        ingridients=ingr, weight=Decimal(self._grams(weight)),
                        time_to_cook=minutes, price=Decimal(price),
                    )

            for si, (name, ptype, btype, items) in enumerate(SHOPS, start=1):
                place, is_new = self._place(name, city, btype, ci, si + 10)
                if not is_new:
                    continue
                created += 1
                for pname, weight, price in items:
                    seed = f"{city}{name}{pname}"
                    ProductType.objects.create(
                        restaurant=place, name=pname, photo=placeholder(seed),
                        product_type=ptype, weight=weight, time_to_cook=0,
                        price=Decimal(price),
                    )
                    CartOfMenu.objects.create(
                        restaurant=place, name=pname, photo=placeholder(seed),
                        ingridients=pname, weight=Decimal(self._grams(weight)),
                        time_to_cook=0, price=Decimal(price),
                    )

        self.stdout.write(self.style.SUCCESS(f"Готово: додано закладів — {created}"))

    def _place(self, name, city, business_type, ci, idx):
        obj = RestorantInfo.objects.filter(name=name, city=city).first()
        if obj:
            return obj, False
        obj = RestorantInfo.objects.create(
            name=name, city=city, business_type=business_type,
            photo=placeholder(f"{city}{name}"),
            address=f"вул. Центральна, {ci * 3 + idx}",
            phone_number=f"+38050{ci:02d}{idx:02d}{(ci * idx) % 100:02d}"[:15],
            opening_hours="09:00–22:00",
        )
        return obj, True

    @staticmethod
    def _grams(text):
        """'450 г' -> 450, '1 кг' -> 1000, '300 мл' -> 300, '10 шт' -> 10."""
        digits = "".join(ch for ch in text.split()[0].replace(",", ".") if ch.isdigit() or ch == ".")
        value = float(digits or 0)
        if "кг" in text:
            value *= 1000
        return round(value)
