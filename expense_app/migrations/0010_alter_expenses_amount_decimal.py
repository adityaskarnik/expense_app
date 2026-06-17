# Generated manually to allow decimal expense amounts.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('expense_app', '0009_auto_20260617_0359'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expenses',
            name='amount',
            field=models.DecimalField(decimal_places=2, max_digits=12),
        ),
    ]
