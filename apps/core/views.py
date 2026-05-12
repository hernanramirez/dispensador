from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.utils.translation import gettext_lazy as _

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.http import JsonResponse
import json
import os

from .models import Robot, Compartimiento, Programacion, RegistroMedico
from .forms import RobotForm, CompartimientoForm, ProgramacionForm
from .mqtt_client import publish_dispense, publish_load

# --- Robot Views ---

class RobotListView(LoginRequiredMixin, ListView):
    model = Robot
    template_name = "core/robot_list.html"
    context_object_name = "robots"


class RobotCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Robot
    form_class = RobotForm
    template_name = "core/robot_form.html"
    success_message = _("Robot successfully created")
    success_url = reverse_lazy("core:robot_list")


class RobotUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Robot
    form_class = RobotForm
    template_name = "core/robot_form.html"
    success_message = _("Robot successfully updated")
    success_url = reverse_lazy("core:robot_list")


class RobotDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Robot
    template_name = "core/robot_confirm_delete.html"
    success_message = _("Robot successfully deleted")
    success_url = reverse_lazy("core:robot_list")


# --- Compartimiento Views ---

class CompartimientoListView(LoginRequiredMixin, ListView):
    model = Compartimiento
    template_name = "core/compartimiento_list.html"
    context_object_name = "compartimientos"


class CompartimientoCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Compartimiento
    form_class = CompartimientoForm
    template_name = "core/compartimiento_form.html"
    success_message = _("Compartimiento successfully created")
    success_url = reverse_lazy("core:compartimiento_list")


class CompartimientoUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Compartimiento
    form_class = CompartimientoForm
    template_name = "core/compartimiento_form.html"
    success_message = _("Compartimiento successfully updated")
    success_url = reverse_lazy("core:compartimiento_list")


class CompartimientoDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Compartimiento
    template_name = "core/compartimiento_confirm_delete.html"
    success_message = _("Compartimiento successfully deleted")
    success_url = reverse_lazy("core:compartimiento_list")


@login_required
def compartimiento_dispense(request, pk):
    compartimiento = get_object_or_404(Compartimiento, pk=pk)
    
    # Intentamos publicar
    if publish_dispense(compartimiento.numero, compartimiento.medicina):
        messages.success(request, f"Comando de dispensado enviado al compartimiento {compartimiento.numero}.")
    else:
        messages.error(request, "Error al enviar el comando MQTT.")
        
    return redirect("core:compartimiento_list")


@login_required
def compartimiento_load(request, pk):
    compartimiento = get_object_or_404(Compartimiento, pk=pk)
    
    # Intentamos publicar
    if publish_load(compartimiento.numero, compartimiento.medicina):
        # Asumimos que al cargarlo, ya no está vacío
        compartimiento.is_empty = False
        compartimiento.save()
        messages.success(request, f"Comando de carga enviado. El compartimiento {compartimiento.numero} ahora contiene {compartimiento.medicina}.")
    else:
        messages.error(request, "Error al enviar el comando MQTT.")
        
    return redirect("core:compartimiento_list")


@login_required
def robot_status_api(request):
    """
    Returns the latest robot status from the shared file for the real-time dashboard.
    """
    status_data = None
    if os.path.exists('/tmp/robot_status.json'):
        try:
            with open('/tmp/robot_status.json', 'r') as f:
                status_data = json.load(f)
        except Exception:
            pass
    
    if status_data:
        return JsonResponse({
            'status': 'success',
            'data': status_data
        })
    else:
        return JsonResponse({
            'status': 'error',
            'data': {
                'estado_motor': 'Desconectado',
                'compartimiento_actual': '-'
            }
        })


# --- Programacion Views ---

class ProgramacionListView(LoginRequiredMixin, ListView):
    model = Programacion
    template_name = "core/programacion_list.html"
    context_object_name = "programaciones"


class ProgramacionCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Programacion
    form_class = ProgramacionForm
    template_name = "core/programacion_form.html"
    success_message = _("Programación successfully created")
    success_url = reverse_lazy("core:programacion_list")


class ProgramacionUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Programacion
    form_class = ProgramacionForm
    template_name = "core/programacion_form.html"
    success_message = _("Programación successfully updated")
    success_url = reverse_lazy("core:programacion_list")


class ProgramacionDeleteView(LoginRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Programacion
    template_name = "core/programacion_confirm_delete.html"
    success_message = _("Programación successfully deleted")
    success_url = reverse_lazy("core:programacion_list")


# --- Registro Medico Views ---

class RegistroMedicoListView(LoginRequiredMixin, ListView):
    model = RegistroMedico
    template_name = "core/registro_list.html"
    context_object_name = "registros"

