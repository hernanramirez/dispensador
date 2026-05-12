from django import forms
from .models import Robot, Compartimiento, Programacion

class RobotForm(forms.ModelForm):
    class Meta:
        model = Robot
        fields = ['mac_address', 'is_connected', 'patient']


class CompartimientoForm(forms.ModelForm):
    class Meta:
        model = Compartimiento
        fields = ['robot', 'numero', 'is_empty', 'medicina']


class ProgramacionForm(forms.ModelForm):
    class Meta:
        model = Programacion
        fields = ['compartimiento', 'hora_dispensado', 'status']
        widgets = {
            'hora_dispensado': forms.TimeInput(attrs={'type': 'time'})
        }
