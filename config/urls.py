# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Стандартные Django-авторизации
    path('accounts/', include('django.contrib.auth.urls')),

    # Logout исправленный — после выхода перебрасывает на главную
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),

    # Основные URL приложения
    path('', include('service_desk.urls')),
]
