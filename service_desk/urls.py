# service_desk/urls.py
from django.urls import path
from . import views

app_name = "service_desk"

urlpatterns = [
    path('', views.index, name='index'),

    # Публичная заявка
    path('request/', views.create_incident_public, name='create_incident_public'),

    # Логин работников
    path('workers-login/', views.workers_login_redirect, name='workers_login'),

    # ITSM панель
    path('itsm/', views.itsm_dashboard, name='itsm_dashboard'),
    path('itsm/incidents/', views.incidents_list, name='incidents_list'),
    path('itsm/incidents/<int:pk>/', views.incident_detail, name='incident_detail'),

    # Услуги (только staff/admin)
    path('itsm/services/', views.services_list, name='services_list'),
    path('itsm/services/create/', views.service_create, name='service_create'),
    path('itsm/services/<int:pk>/edit/', views.service_edit, name='service_edit'),
    path('itsm/services/<int:pk>/delete/', views.service_delete, name='service_delete'),
]
