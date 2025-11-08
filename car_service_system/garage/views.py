from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from bookings.models import Booking
from django.core.mail import send_mail
from django.conf import settings
from .models import Garage, GarageService, ServiceType
from .forms import GarageProfileForm, GarageServiceForm
# from accounts.models import User


# -------------------------------------------------------
# Garage Dashboard
# -------------------------------------------------------
@login_required
def garage_dashboard(request):
    if request.user.role != 'garage':
        messages.error(request, 'Unauthorized access.')
        return redirect('accounts:user_login')

    garage = Garage.objects.filter(user=request.user).first()
    services = GarageService.objects.filter(garage=garage) if garage else []
    return render(request, 'garage/garage_dashboard.html', {'garage': garage, 'services': services})


# -------------------------------------------------------
# Create or Edit Garage Profile
# -------------------------------------------------------
@login_required
def garage_profile(request):
    if request.user.role != 'garage':
        messages.error(request, 'Unauthorized access.')
        return redirect('accounts:user_login')

    garage, created = Garage.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = GarageProfileForm(request.POST, instance=garage)
        if form.is_valid():
            form.save()
            messages.success(request, 'Garage profile updated successfully.')
            return redirect('garage_dashboard')
    else:
        form = GarageProfileForm(instance=garage)
    return render(request, 'garage/garage_profile.html', {'form': form})


# -------------------------------------------------------
# Add New Service
# -------------------------------------------------------
@login_required
def add_service(request):
    if request.user.role != 'garage':
        messages.error(request, 'Unauthorized access.')
        return redirect('accounts:user_login')

    garage = Garage.objects.filter(user=request.user).first()
    if not garage:
        messages.error(request, 'Please create a garage profile first.')
        return redirect('garage_profile')
    
    if request.method == 'POST':
        form = GarageServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.garage = garage
            service.save()
            messages.success(request, 'Service added successfully!')
            return redirect('garage_dashboard')
    else:
        form = GarageServiceForm()
    return render(request, 'garage/add_service.html', {'form': form})


# -------------------------------------------------------
# Delete Service
# -------------------------------------------------------
@login_required
def delete_service(request, pk):
    service = get_object_or_404(GarageService, id=pk, garage__user=request.user)
    service.delete()
    messages.success(request, 'Service deleted successfully!')
    return redirect('garage_dashboard')

@login_required
def garage_bookings(request):
    """
    Display all bookings for the logged-in garage owner.
    """
    if not hasattr(request.user, 'role') or request.user.role != 'garage':
        messages.error(request, 'Unauthorized access.')
        return redirect('login')

    garage = Garage.objects.filter(user=request.user).first()
    if not garage:
        messages.warning(request, "Please create your garage profile first.")
        return redirect('garage_profile')

    bookings = Booking.objects.filter(garage=garage).order_by('-appointment_date')
    return render(request, 'garage/garage_bookings.html', {'bookings': bookings})


@login_required
def update_booking_status(request, booking_id):
    """
    Allows the garage owner to update booking status and send email to customer if 'Ready'.
    """
    if not hasattr(request.user, 'role') or request.user.role != 'garage':
        messages.error(request, 'Unauthorized access.')
        return redirect('login')

    booking = get_object_or_404(Booking, id=booking_id, garage__user=request.user)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        booking.status = new_status
        booking.save()

        # Send an email when booking marked 'Ready'
        if new_status.lower() == 'ready':
            subject = f"Your car is ready - {booking.garage.name}"
            message = (
                f"Dear {booking.customer.first_name or booking.customer.username},\n\n"
                f"Your booking for '{booking.service.name}' at {booking.garage.name} "
                f"is now marked as READY for pickup.\n\nThank you!\n{booking.garage.name}"
            )
            send_mail(
                subject,
                message,
                settings.EMAIL_HOST_USER,
                [booking.customer.email],
                fail_silently=True,
            )

        messages.success(request, f"Booking status updated to '{new_status}'.")
        return redirect('garage_bookings')

    return redirect('garage_bookings')
