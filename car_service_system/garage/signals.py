from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ServiceType, GarageService
from .cache_utils import clear_service_cache

@receiver(post_save, sender=ServiceType)
@receiver(post_delete, sender=ServiceType)
def clear_service_type_cache(sender, **kwargs):
    clear_service_cache()

@receiver(post_save, sender=GarageService)
@receiver(post_delete, sender=GarageService)
def clear_garage_service_cache(sender, instance, **kwargs):
    clear_service_cache(garage_id=instance.garage_id)
