import logging
from celery import shared_task
import paho.mqtt.publish as publish
from django.conf import settings
from apps.core.models import Programacion

logger = logging.getLogger(__name__)

def publish_mqtt_message(topic, payload):
    """
    Función de utilidad para publicar mensajes MQTT en el broker configurado.
    """
    broker = getattr(settings, 'MQTT_BROKER_HOST', 'localhost')
    port = getattr(settings, 'MQTT_BROKER_PORT', 1883)
    
    try:
        publish.single(topic, payload=payload, hostname=broker, port=port)
        logger.info(f"Publicado en {topic}: {payload}")
    except Exception as e:
        logger.error(f"Error publicando en MQTT: {e}")

@shared_task
def check_programaciones_y_dispensar():
    """
    Esta tarea debe ser ejecutada por Celery Beat (por ejemplo, cada minuto),
    para revisar programaciones que coincidan con la hora actual.
    Para simplificar, asume que filtraremos programaciones pendientes en la hora.
    """
    from django.utils import timezone
    now = timezone.localtime().time()
    
    # Tolerancia +/- 1 minuto dependiendo de la frecuencia de celery beat
    # Esto es solo representativo.
    programaciones = Programacion.objects.filter(
        status=Programacion.StatusChoices.PENDING,
        hora_dispensado__hour=now.hour,
        hora_dispensado__minute=now.minute
    )

    for prog in programaciones:
        comp_num = prog.compartimiento.numero
        topic = f"esp32/dispensar/{comp_num}"
        # Publicar la orden
        publish_mqtt_message(topic, payload="DISPENSE")
        logger.info(f"Orden de dispensado enviada para compartimiento {comp_num}")

@shared_task
def cargar_compartimiento_manual(numero_compartimiento):
    """
    Ejemplo de tarea para indicar al robot que se va a cargar un compartimiento manualmente.
    """
    topic = f"esp32/cargar/{numero_compartimiento}"
    publish_mqtt_message(topic, payload="LOAD")
    logger.info(f"Estado de carga activado para compartimiento {numero_compartimiento}")
