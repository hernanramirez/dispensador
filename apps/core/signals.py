from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from apps.core.models import UserProfile

User = get_user_model()

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Crea automáticamente un UserProfile cuando se crea un usuario.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Por si el usuario no tiene perfil por algún error en el pasado
        UserProfile.objects.get_or_create(user=instance)
