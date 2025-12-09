# service_desk/views.py

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import User

from .models import Service, Incident, Message
from .forms import PublicIncidentForm, ServiceForm

# --------------------------- ПУБЛИКА -----------------------------

def index(request):
    services = Service.objects.filter(is_active=True)
    return render(request, 'index.html', {'services': services})


def create_incident_public(request):
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
    return redirect('/accounts/login/')


# --------------------------- ПРАВА -------------------------------

def itsm_access(user):
    return user.is_authenticated


def services_edit_access(user):
    """Разрешено сотрудникам и админам."""
    return (
        user.is_superuser
        or user.is_staff
        or not user.groups.filter(name="Tech").exists()
    )


# --------------------------- ITSM -------------------------------

@login_required
@user_passes_test(itsm_access)
def itsm_dashboard(request):
    is_tech = request.user.groups.filter(name="Tech").exists()
    is_admin = request.user.is_superuser or request.user.is_staff
    return render(request, 'itsm/dashboard.html', {
        "is_tech": is_tech,
        "is_admin": is_admin
    })


@login_required
@user_passes_test(itsm_access)
def incidents_list(request):
    user = request.user

    # Админ и техник → видят все
    if user.is_superuser or user.is_staff or user.groups.filter(name='Tech').exists():
        incidents = Incident.objects.all()
    else:
        return HttpResponseForbidden("Нет доступа.")

    incidents = incidents.order_by('-created_at')
    return render(request, 'itsm/incidents_list.html', {'incidents': incidents})


@login_required
@user_passes_test(itsm_access)
def incident_detail(request, pk):
    incident = get_object_or_404(Incident, pk=pk)
    user = request.user

    # Может ли менять статус?
    can_edit_status = (
        user.is_superuser
        or user.is_staff
        or user.groups.filter(name='Tech').exists()
    )

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "status" and can_edit_status:
            new_status = request.POST.get("status")
            if new_status in dict(Incident.STATUS_CHOICES):
                incident.status = new_status
                incident.save()

        if action == "assign" and (user.is_superuser or user.is_staff):
            tech_id = request.POST.get("assigned_to")
            if tech_id:
                tech = User.objects.filter(id=tech_id).first()
                incident.assigned_to = tech
            else:
                incident.assigned_to = None
            incident.save()

        return redirect("service_desk:incident_detail", pk=incident.pk)

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
#               УСЛУГИ
# ========================================

@login_required
def services_list(request):
    """Смотреть услуги могут все сотрудники."""
    services = Service.objects.all()

    # employee и admin могут создавать услуги → передаем флаг в шаблон
    can_edit = (
        request.user.is_superuser
        or request.user.is_staff
        or not request.user.groups.filter(name="Tech").exists()
    )

    return render(request, 'itsm/services_list.html', {
        'services': services,
        'can_edit': can_edit
    })


@login_required
def service_create(request):
    """Создавать услугу могут admin / staff / employee, но НЕ Tech."""
    if request.user.groups.filter(name="Tech").exists():
        return HttpResponseForbidden("Нет прав на создание услуг.")

    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('service_desk:services_list')
    else:
        form = ServiceForm()

    return render(request, 'itsm/service_form.html', {
        'form': form,
        'title': 'Создать услугу'
    })


@login_required
def service_edit(request, pk):
    """Редактировать услугу могут admin / staff / employee, но НЕ Tech."""
    if request.user.groups.filter(name="Tech").exists():
        return HttpResponseForbidden("Нет прав на редактирование услуг.")

    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect('service_desk:services_list')
    else:
        form = ServiceForm(instance=service)

    return render(request, 'itsm/service_form.html', {
        'form': form,
        'title': 'Редактировать услугу'
    })


@login_required
def service_delete(request, pk):
    """Удалять услугу могут admin / staff / employee, но НЕ Tech."""
    if request.user.groups.filter(name="Tech").exists():
        return HttpResponseForbidden("Нет прав на удаление услуг.")

    service = get_object_or_404(Service, pk=pk)

    if request.method == 'POST':
        service.delete()
        return redirect('service_desk:services_list')

    return render(request, 'itsm/service_confirm_delete.html', {
        'service': service
    })


# ----------------------------- ЧАТ -------------------------------

@login_required
def chat_list(request):
    users = User.objects.exclude(id=request.user.id)
    return render(request, "chat/chat_list.html", {"users": users})


@login_required
def chat_room(request, user_id):
    other = get_object_or_404(User, id=user_id)
    return render(request, "chat/chat_room.html", {"other": other})


@login_required
def api_get_messages(request, user_id):
    other = get_object_or_404(User, id=user_id)

    messages = Message.objects.filter(
        sender__in=[request.user, other],
        receiver__in=[request.user, other]
    ).order_by("created_at")

    return JsonResponse({
        "messages": [
            {
                "id": m.id,
                "sender": m.sender.username,
                "text": m.text,
                "created_at": m.created_at.strftime("%H:%M"),
                "is_me": m.sender == request.user
            }
            for m in messages
        ]
    })


@login_required
def api_send_message(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "error": "POST required"}, status=405)

    receiver_id = request.POST.get("receiver_id")
    text = request.POST.get("text")

    receiver = User.objects.filter(id=receiver_id).first()
    if not receiver:
        return JsonResponse({"status": "error", "error": "Receiver not found"}, status=404)

    Message.objects.create(
        sender=request.user,
        receiver=receiver,
        text=text
    )

    return JsonResponse({"status": "ok"})
