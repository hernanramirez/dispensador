import json
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
import paho.mqtt.client as mqtt
import os

from apps.core.models import Compartimiento, Robot, Programacion, RegistroMedico

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Starts the MQTT listener to receive updates from the ESP32'

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.stdout.write(self.style.SUCCESS('Connected successfully to MQTT Broker!'))
            # Suscribirse a los tópicos relevantes
            client.subscribe("esp32/pulse/+")
            client.subscribe("esp32Pill/motor/status/+")
            self.stdout.write(self.style.SUCCESS('Subscribed to topics: esp32/pulse/+, esp32Pill/motor/status/+'))
        else:
            self.stderr.write(self.style.ERROR(f'Failed to connect to MQTT Broker. Reason code: {reason_code}'))

    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode('utf-8')
        topic = msg.topic
        
        self.stdout.write(f"Received message on {topic}: {payload}")
        
        try:
            # Procesar confirmación de toma
            if topic.startswith("esp32/pulse/"):
                compartment_number = int(topic.split('/')[-1])
                
                if payload.strip() == "Tomado":
                    # Intentamos buscar el compartimiento. Asumimos el primer robot si no hay id
                    # En un entorno multi-robot, el tópico debería incluir la mac_address del robot
                    # Ej: robot = Robot.objects.first()
                    # compartimiento = Compartimiento.objects.filter(robot=robot, numero=compartment_number).first()
                    compartimientos = Compartimiento.objects.filter(numero=compartment_number)
                    if compartimientos.exists():
                        for c in compartimientos:
                            c.is_empty = True
                            c.save()
                            
                            # Registrar en RegistroMedico
                            programacion = Programacion.objects.filter(
                                compartimiento=c, 
                                status=Programacion.StatusChoices.PENDING
                            ).order_by('hora_dispensado').first()
                            
                            if programacion:
                                programacion.status = Programacion.StatusChoices.DISPENSED
                                programacion.save()
                                
                                RegistroMedico.objects.create(
                                    programacion=programacion,
                                    mensaje_confirmacion=payload,
                                    exitosa=True
                                )
                                self.stdout.write(self.style.SUCCESS(f"Medical Log created for Programacion ID {programacion.id}"))
                            else:
                                self.stdout.write(self.style.WARNING(f"Compartment {compartment_number} was taken, but no pending Programacion was found to log it."))
                                
                        self.stdout.write(self.style.SUCCESS(f"Compartment {compartment_number} set to EMPTY."))
                    else:
                        self.stdout.write(self.style.WARNING(f"Compartment {compartment_number} not found in DB."))
            
            # Procesar status
            elif topic.startswith("esp32Pill/motor/status"):
                # Registramos el estado en un archivo temporal para compartirlo con las vistas web
                status_data = json.loads(payload)
                with open('/tmp/robot_status.json', 'w') as f:
                    json.dump(status_data, f)
                self.stdout.write(self.style.SUCCESS(f"Robot Status Update Cached: {status_data}"))
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error processing message: {e}"))

    def handle(self, *args, **options):
        self.stdout.write('Starting MQTT Listener...')
        
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"{settings.MQTT_CLIENT_ID}_listener")
        
        if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
            client.username_pw_set(settings.MQTT_USERNAME, settings.MQTT_PASSWORD)
            
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        
        try:
            client.connect(
                host=settings.MQTT_BROKER_HOST,
                port=settings.MQTT_BROKER_PORT,
                keepalive=settings.MQTT_KEEPALIVE
            )
            client.loop_forever()
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\nStopping MQTT Listener...'))
            client.disconnect()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Connection error: {e}'))
