# init_roles.py

"""
Инициализация ролей и тестовых пользователей.
Запуск:
    python init_roles.py
"""

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from service_desk.models import Incident, Service


def create_groups_and_permissions():
    print("→ Обновляю группы и права...")

    # --- Tech ---
    tech_group, _ = Group.objects.get_or_create(name="Tech")
    print("  ✓ Группа Tech существует")

    # Права для техников: просмотр + изменение инцидентов
    incident_ct = ContentType.objects.get_for_model(Incident)

    perms = Permission.objects.filter(
        content_type=incident_ct,
        codename__in=["view_incident", "change_incident"]
    )

    tech_group.permissions.set(perms)
    print("  ✓ Технику добавлены права на инциденты")


def recreate_admin():
    User.objects.filter(username="admin").delete()

    admin = User.objects.create_superuser(
        username="admin",
        email="",
        password="admin12345"
    )
    print("  ✓ Создан админ admin/admin12345")


def recreate_tech():
    User.objects.filter(username="tech1").delete()

    tech = User.objects.create_user(
        username="tech1",
        password="tech12345"
    )
    tech.is_staff = False
    tech.is_superuser = False
    tech.save()

    tech_group = Group.objects.get(name="Tech")
    tech.groups.add(tech_group)

    print("  ✓ Создан техник tech1/tech12345")


def recreate_employee():
    User.objects.filter(username="employee1").delete()

    emp = User.objects.create_user(
        username="employee1",
        password="emp12345"
    )
    emp.is_staff = False
    emp.is_superuser = False
    emp.save()

    print("  ✓ Создан сотрудник employee1/emp12345")


def main():
    create_groups_and_permissions()
    recreate_admin()
    recreate_tech()
    recreate_employee()

    print("\nГотово!")
    print("  • admin / admin12345  (админ)")
    print("  • tech1 / tech12345   (техник)")
    print("  • employee1 / emp12345 (сотрудник)")


if __name__ == "__main__":
    main()
