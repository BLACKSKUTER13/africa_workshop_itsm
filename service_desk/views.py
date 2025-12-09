from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q

from .models import Service, Incident, Message
from .forms import PublicIncidentForm, ServiceForm


# ========= РОЛИ =========

def is_admin(user):
    """Администратор может всё (superuser или staff)."""
    return user.is_superuser or user.is_staff


def is_tech(user):
    """Тех. специалист: состоит в группе 'Tech'."""
    return user.groups.filter(name='Tech').exists()


def is_employee(user):
    """Обычный сотрудник: состоит в группе 'Employee'."""
    return user.groups.filter(name='Employee').exists()


# ========= ПУБЛИЧНАЯ ЧАСТЬ =========

def index(request):
    services = Service.objects.filter(is_active=True)
    return render(request, "index.html", {"services": services})


def create_incident_public(request):
    if request.method == "POST":
        form = PublicIncidentForm(request.POST)
        if form.is_valid():
            incident = form.save(commit=False)
            if request.user.is_authenticated:
                incident.created_by = request.user
            incident.status = "new"
            incident.save()
            return render(request, "request_success.html", {"incident": incident})
    else:
        form = PublicIncidentForm()

    return render(request, "create_incident_public.html", {"form": form})


def workers_login_redirect(request):
    return redirect("/accounts/login/")


# ========= ITSM ПАНЕЛЬ =========

@login_required
def itsm_dashboard(request):
    """Стартовая страница ITSM: все роли видят инциденты, услуги и мессенджер."""
    user = request.user
    context = {
        "is_admin": is_admin(user),
        "is_tech": is_tech(user),
        "is_employee": is_employee(user),
    }
    return render(request, "itsm/dashboard.html", context)


# ========= ИНЦИДЕНТЫ =========

@login_required
def incidents_list(request):
    """
    Все роли видят список инцидентов.

    • Админ — полный контроль.
    • Тех. специалист — работает с инцидентами (может менять статус).
    • Сотрудник — видит инциденты, но не изменяет их.
    """
    incidents = Incident.objects.all().order_by("-created_at")
    return render(request, "itsm/incidents_list.html", {"incidents": incidents})


@login_required
def incident_detail(request, pk):
    """
    Карточка инцидента с разными правами:

    • Админ — может менять статус и назначать техника.
    • Тех. специалист — может менять статус, но не назначает ответственного.
    • Сотрудник — только просмотр.
    """
    user = request.user
    incident = get_object_or_404(Incident, pk=pk)

    can_edit_status = False
    can_assign = False

    if is_admin(user):
        can_edit_status = True
        can_assign = True
    elif is_tech(user):
        can_edit_status = True
        can_assign = False
    else:
        can_edit_status = False
        can_assign = False

    if request.method == "POST":
        action = request.POST.get("action")

        # Назначение техника (отдельная форма, только админ)
        if action == "assign":
            if not can_assign:
                return HttpResponseForbidden("Недостаточно прав для назначения ответственного")

            assigned_to_id = request.POST.get("assigned_to")
            if assigned_to_id:
                try:
                    assigned_user = User.objects.get(id=assigned_to_id)
                    incident.assigned_to = assigned_user
                except User.DoesNotExist:
                    pass
            else:
                # возможность снять назначение
                incident.assigned_to = None

            incident.save()
            return redirect("service_desk:incident_detail", pk=incident.pk)

        # Изменение статуса (админ + тех)
        else:
            if not can_edit_status:
                return HttpResponseForbidden("Недостаточно прав для изменения статуса")

            new_status = request.POST.get("status")
            if new_status in dict(Incident.STATUS_CHOICES):
                incident.status = new_status
                incident.save()
            return redirect("service_desk:incident_detail", pk=incident.pk)

    techs = None
    if can_assign:
        techs = User.objects.filter(groups__name="Tech").order_by("username")

    context = {
        "incident": incident,
        "status_choices": Incident.STATUS_CHOICES,
        "can_edit": can_edit_status,
        "can_assign": can_assign,
        "techs": techs,
    }
    return render(request, "itsm/incident_detail.html", context)


# ========= УСЛУГИ =========

@login_required
def services_list(request):
    """
    • Админ + Сотрудник — могут создавать/редактировать/удалять услуги.
    • Тех. специалист — видит услуги, но не может их менять.
    """
    user = request.user
    services = Service.objects.all()
    # ВАЖНО: здесь даём права и админу, и employee
    can_manage = is_admin(user) or is_employee(user)

    return render(
        request,
        "itsm/services_list.html",
        {
            "services": services,
            "can_manage": can_manage,
        },
    )


@login_required
def service_create(request):
    user = request.user
    # Только админ и employee
    if not (is_admin(user) or is_employee(user)):
        return HttpResponseForbidden("Недостаточно прав для создания услуги")

    if request.method == "POST":
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("service_desk:services_list")
    else:
        form = ServiceForm()

    return render(request, "itsm/service_form.html", {"form": form, "title": "Создать услугу"})


@login_required
def service_edit(request, pk):
    user = request.user
    # Только админ и employee
    if not (is_admin(user) or is_employee(user)):
        return HttpResponseForbidden("Недостаточно прав для редактирования услуги")

    service = get_object_or_404(Service, pk=pk)

    if request.method == "POST":
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            return redirect("service_desk:services_list")
    else:
        form = ServiceForm(instance=service)

    return render(request, "itsm/service_form.html", {"form": form, "title": "Редактировать услугу"})


@login_required
def service_delete(request, pk):
    user = request.user
    # Только админ и employee
    if not (is_admin(user) or is_employee(user)):
        return HttpResponseForbidden("Недостаточно прав для удаления услуги")

    service = get_object_or_404(Service, pk=pk)

    if request.method == "POST":
        service.delete()
        return redirect("service_desk:services_list")

    return render(request, "itsm/service_confirm_delete.html", {"service": service})


# ========= ЧАТ =========

@login_required
def chat_list(request):
    """Все авторизованные пользователи могут пользоваться мессенджером."""
    users = User.objects.exclude(id=request.user.id).order_by("username")
    return render(request, "chat/chat_list.html", {"users": users})


@login_required
def chat_room(request, user_id):
    other = get_object_or_404(User, id=user_id)
    return render(request, "chat/chat_room.html", {"other": other})


@login_required
def api_get_messages(request, user_id):
    other = get_object_or_404(User, id=user_id)
    user = request.user

    messages = Message.objects.filter(
        Q(sender=user, receiver=other) | Q(sender=other, receiver=user)
    ).order_by("created_at")

    data = {
        "messages": [
            {
                "text": m.text,
                "is_me": m.sender_id == user.id,
                "created": m.created_at.strftime("%d.%m.%Y %H:%M"),
            }
            for m in messages
        ]
    }
    return JsonResponse(data)


@login_required
def api_send_message(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "error": "Только POST"}, status=405)

    receiver_id = request.POST.get("receiver_id")
    text = (request.POST.get("text") or "").strip()

    if not receiver_id or not text:
        return JsonResponse({"status": "error", "error": "Поля receiver_id и text обязательны"}, status=400)

    receiver = User.objects.filter(id=receiver_id).first()
    if not receiver:
        return JsonResponse({"status": "error", "error": "Получатель не найден"}, status=404)

    Message.objects.create(sender=request.user, receiver=receiver, text=text)
    return JsonResponse({"status": "ok"})
