from django.core.cache import cache
from .models import ServiceType, GarageService

CACHE_TIMEOUT = 60 * 60  # 1 hour


def get_all_service_types():
    cache_key = "services:all"

    services = cache.get(cache_key)
    if services is None:
        services = list(
            ServiceType.objects.all()
            .order_by("name")
            .values("id", "name", "description", "parent_id")
        )
        cache.set(cache_key, services, CACHE_TIMEOUT)

    return services


def get_garage_services_cached(garage_id):
    cache_key = f"services:garage:{garage_id}"

    services = cache.get(cache_key)
    if services is None:
        services = list(
            GarageService.objects.filter(garage_id=garage_id)
            .select_related("service_type")
            .values(
                "id",
                "service_type__name",
                "price",
                "opening_hours",
                "custom_text",
            )
        )
        cache.set(cache_key, services, CACHE_TIMEOUT)

    return services


def clear_service_cache(garage_id=None):
    cache.delete("services:all")
    if garage_id:
        cache.delete(f"services:garage:{garage_id}")
