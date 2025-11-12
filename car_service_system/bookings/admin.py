from django.contrib import admin
from .models import Booking

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'customer', 'garage', 'status', 'appointment_date')
    list_filter = ('status', 'garage', 'appointment_date')
    search_fields = ('customer__email', 'vehicle__registration_number', 'garage__name')
