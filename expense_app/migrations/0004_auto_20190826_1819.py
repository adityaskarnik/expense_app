# Generated by Django 2.2.3 on 2019-08-26 18:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expense_app', '0003_auto_20181216_0635'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenses',
            name='amount',
            field=models.IntegerField(max_length=500),
        ),
    ]
