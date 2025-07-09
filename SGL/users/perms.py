from django.contrib.auth.management import create_permissions
from django.contrib.auth.models import Permission


def add_result_permissions(apps, schema_editor):
    create_permissions(apps.get_model('results'))

    Group = apps.get_model('auth', 'Group')
    tech_group, _ = Group.objects.get_or_create(name='Technicians')
    tech_group.permissions.add(
        *Permission.objects.filter(
            codename__in=['add_result', 'change_result', 'export_hl7']
        )
    )