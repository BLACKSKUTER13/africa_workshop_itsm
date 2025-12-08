# service_desk/views.py

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.contrib.auth.models import User

from .models import Service, Incident
from .forms import PublicIncidentForm, ServiceForm


# ========================================
#        ПУБЛИЧНАЯ ЧАСТЬ САЙТА
# ========================================

def index(request):
    """Каталог услуг + кнопка отправки заявки + вход для работников."""
    services = Service.objects.filter(is_active=True)
    return render(request, 'index.html', {'services': services})


def create_incident_public(request):
    """Форма отправки заявки с главной страницы."""
    if request.method == 'POST':
        form = PublicIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            incident.status = 'new'
            if request.user.is_authenticated:
                incident.created_by = request.user
            incident.save()
            return render(request, 'request_success.html', {'incident': incident})
    else:
        form = PublicIncidentForm()

    return render(request, 'create_incident_public.html', {'form': form})


def workers_login_redirect(request):
    """Кнопка 'Вход для работников' → стандартная логин-страница Django."""
    return redirect('/accounts/login/')


# ========================================
#               ITSM
# ========================================

@login_required
def itsm_dashboard(request):
    """Главная страница ITSM."""
    return render(request, 'itsm/dashboard.html')


@login_required
def incidents_list(request):
    """
    Роли:
    - Админ/staff → видит все инциденты
    - Техник (группа Tech) → только назначенные
    - Обычный сотрудник → только созданные им
    """
    user = request.user

    if user.is_superuser or user.is_staff:
        incidents = Incident.objects.all().order_by('-created_at')

    elif user.groups.filter(name='Tech').exists():
        incidents = Incident.objects.filter(
            assigned_to=user
        ).order_by('-created_at')

    else:
        incidents = Incident.objects.filter(
            created_by=user
        ).order_by('-created_at')

    return render(request, 'itsm/incidents_list.html', {'incidents': incidents})


@login_required
def incident_detail(request, pk):
    """
    Доступ:
    ✔ Админ/staff → всегда
    ✔ Техник → если назначен
    ✔ Сотрудник → если он автор
    """
    incident = get_object_or_404(Incident, pk=pk)
    user = request.user

    # Может ли менять статус?
    can_edit_status = (
        user.is_superuser or
        user.is_staff or
        (user.groups.filter(name='Tech').exists() and incident.assigned_to == user)
    )

    # Может ли видеть инцидент? (доступ в принципе)
    allowed = (
        user.is_superuser or
        user.is_staff or
        incident.created_by == user or
        incident.assigned_to == user
    )

    if not allowed:
        return HttpResponseForbidden("У вас нет доступа к этому инциденту.")

    # =============================
    #           POST ОБРАБОТКА
    # =============================
    if request.method == "POST":
        action = request.POST.get("action")

        # --- Изменение статуса ---
        if action == "status" and can_edit_status:
            new_status = request.POST.get("status")
            if new_status in dict(Incident.STATUS_CHOICES):
                incident.status = new_status
                incident.save()

        # --- Назначение технику (только admin/staff) ---
        if action == "assign" and (user.is_superuser or user.is_staff):
            tech_id = request.POST.get("assigned_to")
            if tech_id:
                tech = User.objects.filter(id=tech_id).first()
                incident.assigned_to = tech
            else:
                incident.assigned_to = None  # снять назначение
            incident.save()

        return redirect("service_desk:incident_detail", pk=incident.pk)

    # Список техников (только для админа/staff)
    techs = None
    if user.is_superuser or user.is_staff:
        techs = User.objects.filter(groups__name="Tech")

    return render(request, 'itsm/incident_detail.html', {
        'incident': incident,
        'can_edit': can_edit_status,
        'status_choices': Incident.STATUS_CHOICES,
        'techs': techs,
    })


# ========================================
#          УСЛУГИ (ТОЛЬКО staff/admin)
# ========================================

def is_admin(user):
    return user.is_superuser or user.is_staff


@user_passes_test(is_admin)
def services_list(request):
    services = Service.objects.all()
    return render(request, 'itsm/services_list.html', {'services': services})


@user_passes_test(is_admin)
def service_create(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('service_desk:services_list')
    else:
        form = ServiceForm()
    return render(request, 'itsm/service_form.html', {'form': form, 'title': 'Создать услугу'})


@user_passes_test(is_admin)
def service_edit(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect('service_desk:services_list')
    else:
        form = ServiceForm(instance=service)
    return render(request, 'itsm/service_form.html', {'form': form, 'title': 'Редактировать услугу'})


@user_passes_test(is_admin)
def service_delete(request, pk):
    service = get_object_or_404(Service, pk=pk)
    if request.method == 'POST':
        service.delete()
        return redirect('service_desk:services_list')
    return render(request, 'itsm/service_confirm_delete.html', {'service': service})
