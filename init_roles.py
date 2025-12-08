# init_roles.py
"""
Инициализация ролей и тестовых пользователей для проекта
"Африканская мастерская по ремонту ПК".

Запускать:
    python init_roles.py
(из корня проекта, с активированным venv)
"""

import os
import django

# 1. Подключение Django-настроек
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from service_desk.models import Incident


def create_groups_and_permissions():
    print("→ Настраиваю группы и права...")

    # Создаём группу "Tech"
    tech_group, created = Group.objects.get_or_create(name="Tech")
    if created:
        print("  ✓ Создана группа Tech")
    else:
        print("  = Группа Tech уже существует")

    # Добавляем права к инцидентам
    incident_ct = ContentType.objects.get_for_model(Incident)

    perms = Permission.objects.filter(
        content_type=incident_ct,
        codename__in=["view_incident", "change_incident"]
    )

    for perm in perms:
        tech_group.permissions.add(perm)
        print(f"    • добавлено право: {perm.codename}")

    print("  ✓ Права для группы Tech настроены")


def recreate_admin_user():
    print("→ Создаю суперпользователя admin...")

    # Полностью удаляем admin, если он есть
    User.objects.filter(username="admin").delete()

    admin = User.objects.create_superuser(
        username="admin",
        email="",
        password="admin12345"
    )

    print("  ✓ Создан новый суперпользователь:")
    print("    логин: admin")
    print("    пароль: admin12345")


def recreate_tech_user():
    print("→ Создаю пользователя-техника...")

    User.objects.filter(username="tech1").delete()

    tech_user = User.objects.create_user(
        username="tech1",
        password="tech12345"
    )

    tech_user.is_staff = False        # ← ТЕХНИК НЕ staff!
    tech_user.is_superuser = False
    tech_user.save()

    tech_group = Group.objects.get(name="Tech")
    tech_user.groups.add(tech_group)

    print("  ✓ Создан техник:")
    print("    логин: tech1")
    print("    пароль: tech12345")
    print("    группа: Tech")


def recreate_employee_user():
    print("→ Создаю сотрудника...")

    User.objects.filter(username="employee1").delete()

    employee = User.objects.create_user(
        username="employee1",
        password="emp12345"
    )

    employee.is_staff = False
    employee.is_superuser = False
    employee.save()

    print("  ✓ Создан обычный сотрудник:")
    print("    логин: employee1")
    print("    пароль: emp12345")


def main():
    create_groups_and_permissions()
    recreate_admin_user()
    recreate_tech_user()
    recreate_employee_user()

    print("\nГотово! Созданы пользователи:")
    print("  • admin / admin12345  (админ, superuser)")
    print("  • tech1 / tech12345   (техник, группа Tech)")
    print("  • employee1 / emp12345 (сотрудник)")
    print("\nМожно логиниться!")


if __name__ == "__main__":
    main()
