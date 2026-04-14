from django.contrib import admin

# Register your models here.
from .models import UserProfile, Robot, Compartimiento, Programacion, RegistroMedico

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)

@admin.register(Robot)
class RobotAdmin(admin.ModelAdmin):
    list_display = ('mac_address', 'is_connected', 'patient')
    list_filter = ('is_connected',)
    search_fields = ('mac_address',)

@admin.register(Compartimiento)
class CompartimientoAdmin(admin.ModelAdmin):
    list_display = ('robot', 'numero', 'is_empty', 'medicina')
    list_filter = ('robot', 'is_empty')
    search_fields = ('medicina',)

@admin.register(Programacion)
class ProgramacionAdmin(admin.ModelAdmin):
    list_display = ('compartimiento', 'hora_dispensado', 'status')
    list_filter = ('status', 'hora_dispensado')

@admin.register(RegistroMedico)
class RegistroMedicoAdmin(admin.ModelAdmin):
    list_display = ('programacion', 'fecha_hora', 'exitosa')
    list_filter = ('exitosa', 'fecha_hora')
    search_fields = ('mensaje_confirmacion',)
