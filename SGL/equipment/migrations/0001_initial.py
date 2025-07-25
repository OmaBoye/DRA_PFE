# Generated by Django 5.2 on 2025-06-17 16:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('analysis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LaboratoryEquipment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=50)),
                ('ip_address', models.CharField(max_length=15)),
                ('protocol', models.CharField(choices=[('HL7', 'HL7'), ('REST', 'REST'), ('TCP', 'TCP')], max_length=20)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentTestRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sent_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processed', 'Processed')], max_length=20)),
                ('analysis', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analysis.analysis')),
                ('equipment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='equipment.laboratoryequipment')),
            ],
        ),
        migrations.CreateModel(
            name='EquipmentResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('raw_data', models.JSONField()),
                ('received_at', models.DateTimeField(auto_now_add=True)),
                ('is_parsed', models.BooleanField(default=False)),
                ('test_request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='equipment.equipmenttestrequest')),
            ],
        ),
    ]
