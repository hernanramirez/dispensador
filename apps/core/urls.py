from django.urls import path
from . import views

app_name = "core"
urlpatterns = [
    # Robot
    path("robot/", views.RobotListView.as_view(), name="robot_list"),
    path("robot/create/", views.RobotCreateView.as_view(), name="robot_create"),
    path("robot/<int:pk>/update/", views.RobotUpdateView.as_view(), name="robot_update"),
    path("robot/<int:pk>/delete/", views.RobotDeleteView.as_view(), name="robot_delete"),
    path("robot/api/status/", views.robot_status_api, name="robot_status_api"),

    # Compartimiento
    path("compartimiento/", views.CompartimientoListView.as_view(), name="compartimiento_list"),
    path("compartimiento/create/", views.CompartimientoCreateView.as_view(), name="compartimiento_create"),
    path("compartimiento/<int:pk>/update/", views.CompartimientoUpdateView.as_view(), name="compartimiento_update"),
    path("compartimiento/<int:pk>/delete/", views.CompartimientoDeleteView.as_view(), name="compartimiento_delete"),
    path("compartimiento/<int:pk>/dispense/", views.compartimiento_dispense, name="compartimiento_dispense"),
    path("compartimiento/<int:pk>/load/", views.compartimiento_load, name="compartimiento_load"),

    # Programacion
    path("programacion/", views.ProgramacionListView.as_view(), name="programacion_list"),
    path("programacion/create/", views.ProgramacionCreateView.as_view(), name="programacion_create"),
    path("programacion/<int:pk>/update/", views.ProgramacionUpdateView.as_view(), name="programacion_update"),
    path("programacion/<int:pk>/delete/", views.ProgramacionDeleteView.as_view(), name="programacion_delete"),

    # Registro Medico
    path("registro/", views.RegistroMedicoListView.as_view(), name="registro_list"),
]
