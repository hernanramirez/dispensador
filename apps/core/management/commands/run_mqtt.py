import json
import logging
import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.core.models import RegistroMedico, Programacion

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Inicia el listener daemon de MQTT para recibir confirmaciones del ESP32'

    def handle(self, *args, **options):
        broker_host = getattr(settings, 'MQTT_BROKER_HOST', 'localhost')
        broker_port = getattr(settings, 'MQTT_BROKER_PORT', 1883)

        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message

        try:
            self.stdout.write(self.style.SUCCESS(f"Conectando al broker MQTT {broker_host}:{broker_port}..."))
            client.connect(broker_host, broker_port, 60)
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write("Cerrando listener MQTT.")
        except Exception as e:
            self.stderr.write(f"Error en listener MQTT: {e}")

    def on_connect(self, client, userdata, flags, rc):
        # rc = 0 significa conexión exitosa
        if rc == 0:
            self.stdout.write(self.style.SUCCESS("Conectado exitosamente. Suscribiéndose a esp32/confirmacion"))
            client.subscribe("esp32/confirmacion")
        else:
            self.stderr.write(f"Fallo de conexión, código: {rc}")

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        logger.info(f"Mensaje recibido en {msg.topic}: {payload}")
        
        try:
            # Ejemplo esperado de payload: {"programacion_id": 12, "exitosa": true, "mensaje": "Tomada"}
            data = json.loads(payload)
            prog_id = data.get("programacion_id")
            
            if prog_id:
                prog = Programacion.objects.get(id=prog_id)
                
                # Crear el Log
                registro = RegistroMedico.objects.create(
                    programacion=prog,
                    exitosa=data.get("exitosa", True),
                    mensaje_confirmacion=payload
                )

                # Actualizar el estado de la programación
                prog.status = Programacion.StatusChoices.DISPENSED if registro.exitosa else Programacion.StatusChoices.FAILED
                prog.save()

                # Notificar a los clientes vía WebSockets
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Enviar alerta al cuidador/paciente
                    # Aquí asumo que el paciente al que está asignado el robot (y compartimiento) será notificado
                    user_to_alert = prog.compartimiento.robot.patient
                    if user_to_alert:
                        group_name = f"user_alerts_{user_to_alert.id}"
                        async_to_sync(channel_layer.group_send)(
                            group_name,
                            {
                                "type": "send_alert",
                                "message": f"Medicina tomada: {prog.compartimiento.medicina} ({'Confirmado' if registro.exitosa else 'Fallo'})"
                            }
                        )
        except Programacion.DoesNotExist:
            logger.error("Programación no encontrada para la confirmación MQTT.")
        except json.JSONDecodeError:
            logger.error("El payload no es un JSON válido.")
        except Exception as e:
            logger.error(f"Error procesando mensaje MQTT: {e}")
