import uuid

from django.db import migrations, models


def populate_tracking_tokens(apps, schema_editor):
    Delivery = apps.get_model('delivery_APP', 'Delivery')
    for delivery in Delivery.objects.filter(tracking_token__isnull=True).iterator():
        delivery.tracking_token = uuid.uuid4()
        delivery.save(update_fields=['tracking_token'])


def clear_tracking_tokens(apps, schema_editor):
    Delivery = apps.get_model('delivery_APP', 'Delivery')
    Delivery.objects.update(tracking_token=None)


class Migration(migrations.Migration):

    dependencies = [
        ('delivery_APP', '0014_delivery_city_delivery_courier_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='delivery',
            name='tracking_token',
            field=models.UUIDField(blank=True, null=True, editable=False),
        ),
        migrations.AddField(
            model_name='delivery',
            name='completion_photo',
            field=models.ImageField(blank=True, upload_to='delivery_proofs/%Y/%m/'),
        ),
        migrations.RunPython(
            populate_tracking_tokens,
            clear_tracking_tokens,
        ),
        migrations.AlterField(
            model_name='delivery',
            name='tracking_token',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
