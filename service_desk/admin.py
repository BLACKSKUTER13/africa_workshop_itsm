# service_desk/admin.py
from django.contrib import admin
from .models import Service, Incident

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)

@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ("id", "service", "status", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "service", "assigned_to")
    search_fields = ("comment",)
