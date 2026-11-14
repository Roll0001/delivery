import re
from decimal import Decimal, ROUND_HALF_UP

import django.db.models.deletion
from django.db import migrations, models


def _weight_in_grams(value):
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


def create_orderable_dishes(apps, schema_editor):
    Dish = apps.get_model('delivery_APP', 'Dish')
    CartOfMenu = apps.get_model('delivery_APP', 'CartOfMenu')
    database = schema_editor.connection.alias

    for dish in Dish.objects.using(database).filter(
        restaurant__isnull=False,
    ).iterator():
        try:
            weight = _weight_in_grams(dish.weight)
        except ValueError as exc:
            raise ValueError(
                f'Dish {dish.pk} has an unsupported weight: {dish.weight!r}'
            ) from exc

        menu_item = CartOfMenu.objects.using(database).filter(
            restaurant_id=dish.restaurant_id,
            name=dish.name,
            catalog_dish__isnull=True,
        ).order_by('pk').first()
        if menu_item is None:
            menu_item = CartOfMenu(
                restaurant_id=dish.restaurant_id,
                name=dish.name,
            )

        menu_item.catalog_dish_id = dish.pk
        menu_item.name = dish.name
        menu_item.photo = dish.photo
        menu_item.ingridients = dish.ingridients
        menu_item.weight = weight
        menu_item.time_to_cook = dish.time_to_cook
        menu_item.price = dish.price
        menu_item.save(using=database)


class Migration(migrations.Migration):

    dependencies = [
        ('delivery_APP', '0015_delivery_completion_photo_and_tracking_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartofmenu',
            name='name',
            field=models.CharField(max_length=200),
        ),
        migrations.AddField(
            model_name='cartofmenu',
            name='catalog_dish',
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='orderable_item',
                to='delivery_APP.dish',
            ),
        ),
        migrations.RunPython(create_orderable_dishes, migrations.RunPython.noop),
    ]
