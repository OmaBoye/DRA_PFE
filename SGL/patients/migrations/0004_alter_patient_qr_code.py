# Generated by Django 5.2 on 2025-06-30 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_remove_patient_user_account'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='qr_code',
            field=models.ImageField(blank=True, upload_to='patient_qr_codes/'),
        ),
    ]
