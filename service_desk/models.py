from django.db import models
from django.contrib.auth.models import User


class Service(models.Model):
    name = models.CharField("Название услуги", max_length=255)
    description = models.TextField("Описание", blank=True)
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    is_active = models.BooleanField("Активна", default=True)

    def __str__(self):
        return self.name


class Incident(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('done', 'Выполнена'),
        ('cancelled', 'Отменена'),
    ]

    service = models.ForeignKey(Service, verbose_name="Услуга",
                                on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        User,
        verbose_name="Создано пользователем",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incidents'
    )
    comment = models.TextField("Комментарий клиента / описание проблемы")
    status = models.CharField("Статус", max_length=20,
                              choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(
        User,
        verbose_name="Назначено тех. специалисту",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    def __str__(self):
        return f"Инцидент #{self.id} ({self.get_status_display()})"
