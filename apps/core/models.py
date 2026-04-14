from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class UserProfile(models.Model):
    """
    Perfil de usuario para manejar los roles: Administrador, Paciente, Cuidador.
    """
    class RoleChoices(models.TextChoices):
        ADMIN = 'ADMIN', _('Administrador')
        PATIENT = 'PATIENT', _('Paciente')
        CAREGIVER = 'CAREGIVER', _('Cuidador')

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("Usuario")
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.PATIENT,
        verbose_name=_("Rol")
    )
    
    class Meta:
        verbose_name = _("Perfil de Usuario")
        verbose_name_plural = _("Perfiles de Usuario")

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"


class Robot(models.Model):
    """
    Robot dispensador basado en ESP32.
    """
    mac_address = models.CharField(
        max_length=17, 
        unique=True, 
        verbose_name=_("MAC Address"),
        help_text=_("Ejemplo: 00:1B:44:11:3A:B7")
    )
    is_connected = models.BooleanField(
        default=False, 
        verbose_name=_("Conectado")
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='robots',
        limit_choices_to={'profile__role': UserProfile.RoleChoices.PATIENT},
        verbose_name=_("Paciente Asignado")
    )
    
    class Meta:
        verbose_name = _("Robot")
        verbose_name_plural = _("Robots")

    def __str__(self):
        return f"Robot {self.mac_address}"


class Compartimiento(models.Model):
    """
    Cada uno de los 8 compartimientos del robot.
    """
    robot = models.ForeignKey(
        Robot, 
        on_delete=models.CASCADE, 
        related_name='compartimientos'
    )
    numero = models.PositiveSmallIntegerField(
        verbose_name=_("Número de Compartimiento")
    )
    is_empty = models.BooleanField(
        default=True, 
        verbose_name=_("Está vacío")
    )
    medicina = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_("Medicina contenida")
    )

    class Meta:
        verbose_name = _("Compartimiento")
        verbose_name_plural = _("Compartimientos")
        unique_together = ('robot', 'numero')
        ordering = ['robot', 'numero']

    def __str__(self):
        estado = "Vacío" if self.is_empty else f"Cargado ({self.medicina})"
        return f"{self.robot} - Comp {self.numero} [{estado}]"


class Programacion(models.Model):
    """
    Horario de dispensado para un compartimiento.
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', _('Pendiente')
        DISPENSED = 'DISPENSED', _('Dispensado')
        FAILED = 'FAILED', _('Fallido')

    compartimiento = models.ForeignKey(
        Compartimiento, 
        on_delete=models.CASCADE, 
        related_name='programaciones'
    )
    hora_dispensado = models.TimeField(
        verbose_name=_("Hora de dispensado")
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
        verbose_name=_("Estado")
    )

    class Meta:
        verbose_name = _("Programación")
        verbose_name_plural = _("Programaciones")
        ordering = ['hora_dispensado']

    def __str__(self):
        return f"{self.compartimiento} a las {self.hora_dispensado} ({self.get_status_display()})"


class RegistroMedico(models.Model):
    """
    Historial inmutable de eventos confirmados por el robot vía MQTT.
    """
    programacion = models.ForeignKey(
        Programacion, 
        on_delete=models.PROTECT, 
        related_name='registros'
    )
    fecha_hora = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Fecha y Hora")
    )
    mensaje_confirmacion = models.TextField(
        blank=True, 
        verbose_name=_("Mensaje de Confirmación (Raw)")
    )
    exitosa = models.BooleanField(
        default=True,
        verbose_name=_("Toma Exitosa")
    )

    class Meta:
        verbose_name = _("Registro Médico")
        verbose_name_plural = _("Registros Médicos")
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Registro: {self.programacion.compartimiento.medicina} - {self.fecha_hora}"
