# Generated by Django 5.2 on 2025-06-15 19:35

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0003_remove_patient_user_account'),
        ('samples', '0003_remove_sample_paid_sample_current_technician_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='batch',
            options={},
        ),
        migrations.AlterModelOptions(
            name='custodylog',
            options={'ordering': ['-transferred_at']},
        ),
        migrations.AlterModelOptions(
            name='sample',
            options={'ordering': ['-collection_date']},
        ),
        migrations.AlterModelOptions(
            name='sampletype',
            options={'ordering': ['name'], 'verbose_name': 'Sample Type'},
        ),
        migrations.AddField(
            model_name='batch',
            name='batch_qr_code',
            field=models.ImageField(blank=True, null=True, upload_to='qr_codes/batches/'),
        ),
        migrations.AddField(
            model_name='sample',
            name='qr_code',
            field=models.ImageField(blank=True, null=True, upload_to='qr_codes/samples/'),
        ),
        migrations.AddField(
            model_name='sample',
            name='qr_token',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='sample',
            name='qr_token_expires',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='batch',
            name='samples',
            field=models.ManyToManyField(related_name='batches', to='samples.sample'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='barcode',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='collection_date',
            field=models.DateTimeField(),
        ),
        migrations.AlterField(
            model_name='sample',
            name='current_technician',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='current_samples', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='sample',
            name='notes',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='patient',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='samples', to='patients.patient'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='received_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='rejection_notes',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='rejection_reason',
            field=models.CharField(blank=True, choices=[('hemolyzed', 'Hemolyzed'), ('insufficient', 'Insufficient Volume'), ('contaminated', 'Contaminated')], max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='sample',
            name='sample_type',
            field=models.ManyToManyField(to='samples.sampletype'),
        ),
        migrations.AlterField(
            model_name='sample',
            name='status',
            field=models.CharField(choices=[('collected', 'Collected'), ('received', 'Received in Lab'), ('processing', 'Processing'), ('analyzed', 'Analyzed'), ('reported', 'Reported'), ('archived', 'Archived'), ('rejected', 'Rejected')], default='collected', max_length=20),
        ),
        migrations.AlterField(
            model_name='sampletype',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='sampletype',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='sampletype',
            name='processing_days',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
