from django.db import migrations, models
from django.conf import settings


def set_default_creator(apps, schema_editor):
    Analysis = apps.get_model('analysis', 'Analysis')
    User = apps.get_model(settings.AUTH_USER_MODEL)
    default_user = User.objects.filter(is_superuser=True).first()  # Gets the first superuser
    if default_user:
        Analysis.objects.filter(created_by__isnull=True).update(created_by=default_user)


class Migration(migrations.Migration):
    dependencies = [
        # This should match your last migration file name
        ('analysis', '0001_initial'),  # Change '0001_initial' to your actual last migration
    ]

    operations = [
        # 1. First add the field as nullable
        migrations.AddField(
            model_name='analysis',
            name='created_by',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.PROTECT,
                null=True,
                blank=True,
                related_name='created_analyses'
            ),
        ),

        # 2. Populate the field
        migrations.RunPython(set_default_creator),

        # 3. Change to non-nullable
        migrations.AlterField(
            model_name='analysis',
            name='created_by',
            field=models.ForeignKey(
                to=settings.AUTH_USER_MODEL,
                on_delete=models.PROTECT,
                related_name='created_analyses'
            ),
        ),
    ]