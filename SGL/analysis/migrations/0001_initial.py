# Generated by Django 5.2 on 2025-06-17 15:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('samples', '0004_alter_batch_options_alter_custodylog_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalysisType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('code', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('category', models.CharField(choices=[('blood', 'Blood Analysis'), ('urine', 'Urine Analysis'), ('tissue', 'Tissue Analysis'), ('molecular', 'Molecular Analysis'), ('microbiology', 'Microbiology')], default='blood', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('minimum_sample_volume', models.CharField(blank=True, max_length=50)),
                ('sample_storage_conditions', models.CharField(blank=True, max_length=100)),
                ('default_parameters', models.JSONField(default=list)),
                ('turnaround_time', models.PositiveIntegerField(default=24, help_text='Standard turnaround time in hours')),
                ('is_auto_verifiable', models.BooleanField(default=False, help_text='Can results be auto-verified without manual review?')),
                ('is_blood_panel', models.BooleanField(default=False)),
                ('blood_panels', models.JSONField(blank=True, default=list, null=True)),
                ('test_cost', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('insurance_codes', models.JSONField(blank=True, default=list)),
                ('sample_types', models.ManyToManyField(related_name='analysis_types', to='samples.sampletype')),
            ],
            options={
                'verbose_name': 'Analysis Type',
                'verbose_name_plural': 'Analysis Types',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Analysis',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('verified', 'Verified'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('priority', models.CharField(choices=[('routine', 'Routine (3-5 days)'), ('urgent', 'Urgent (24 hours)'), ('stat', 'STAT (<1 hour)')], default='routine', max_length=20)),
                ('started_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('technician', models.CharField(blank=True, max_length=100)),
                ('notes', models.TextField(blank=True)),
                ('selected_panels', models.JSONField(blank=True, default=list)),
                ('instrument_used', models.CharField(blank=True, max_length=100)),
                ('qc_status', models.CharField(blank=True, max_length=50)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_analyses', to=settings.AUTH_USER_MODEL)),
                ('sample', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='analyses', to='samples.sample')),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_analyses', to=settings.AUTH_USER_MODEL)),
                ('analysis_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='analyses', to='analysis.analysistype')),
            ],
            options={
                'verbose_name_plural': 'Analyses',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['status'], name='analysis_an_status_718090_idx'), models.Index(fields=['priority'], name='analysis_an_priorit_1e727f_idx'), models.Index(fields=['sample', 'analysis_type'], name='analysis_an_sample__393818_idx')],
            },
        ),
    ]
