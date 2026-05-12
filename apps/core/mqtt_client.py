import paho.mqtt.publish as publish
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_mqtt_auth():
    """
    Returns the auth dictionary for paho-mqtt based on settings.
    """
    if settings.MQTT_USERNAME and settings.MQTT_PASSWORD:
        return {
            'username': settings.MQTT_USERNAME,
            'password': settings.MQTT_PASSWORD
        }
    return None

def publish_message(topic: str, payload: str):
    """
    Publishes a single message to the configured MQTT broker and disconnects.
    Useful for triggering actions from Django views.
    """
    try:
        publish.single(
            topic,
            payload=payload,
            hostname=settings.MQTT_BROKER_HOST,
            port=settings.MQTT_BROKER_PORT,
            client_id=f"{settings.MQTT_CLIENT_ID}_publisher",
            auth=get_mqtt_auth(),
            keepalive=settings.MQTT_KEEPALIVE
        )
        logger.info(f"Successfully published to {topic}: {payload}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish to {topic}: {e}")
        return False

def publish_dispense(compartment_number: int, medicine_name: str):
    """
    Publish a command to dispense a specific compartment.
    Topic: esp32Pill/motor/dispense/{compartment_number}
    """
    topic = f"esp32Pill/motor/dispense/{compartment_number}"
    return publish_message(topic, medicine_name)

def publish_load(compartment_number: int, medicine_name: str):
    """
    Publish a command to load a specific compartment.
    Topic: esp32Pill/motor/load/{compartment_number}
    """
    topic = f"esp32Pill/motor/load/{compartment_number}"
    return publish_message(topic, medicine_name)
