from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Garage, GarageService, ServiceType
from .forms import GarageProfileForm, GarageServiceForm, ServiceTypeForm
from bookings.models import Booking, Invoice
# from accounts.models import User


# -------------------------------------------------------
# Garage Dashboard
# -------------------------------------------------------
@login_required
def garage_dashboard(request):
    if request.user.role != "garage":
        messages.error(request, "Unauthorized access.")
        return redirect("accounts:login")

    garage = Garage.objects.filter(user=request.user).first()
    services = GarageService.objects.filter(garage=garage)
    # garage = Garage.objects.filter(user=request.user).first()
    if not garage:
        messages.warning(request, "Please complete your garage profile first.")
        return redirect("garage_profile")
    services = GarageService.objects.filter(garage=garage)
    # Fetch reviews for this garage

    reviews = garage.reviews.select_related("customer").order_by("-date")

    # Calculate average rating
    from django.db.models import Avg

    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0

    # Add to context
    return render(
        request,
        "garage/garage_dashboard.html",
        {
            "garage": garage,
            "services": services,
            "reviews": reviews,
            "avg_rating": round(avg_rating, 1),
        },
    )


# return render(request, 'garage/garage_dashboard.html', {'garage': garage, 'services': services})
# return render(request, 'garage/garage_dashboard.html', {'garage': garage, 'services': services})


# -------------------------------------------------------
# Create or Edit Garage Profile
# -------------------------------------------------------
@login_required
def garage_profile(request):
    if request.user.role != "garage":
        messages.error(request, "Unauthorized access.")
        return redirect("accounts:login")

    garage, created = Garage.objects.get_or_create(user=request.user)
    if request.method == "POST":
        # form = GarageProfileForm(request.POST, instance=garage)
        form = GarageProfileForm(request.POST, request.FILES, instance=garage)
        if form.is_valid():
            form.save()
            messages.success(request, "Garage profile updated successfully.")
            return redirect("garage_dashboard")
    else:
        form = GarageProfileForm(instance=garage)
    return render(
        request, "garage/garage_profile.html", {"form": form, "garage": garage}
    )


# -------------------------------------------------------
# Add New Service
# -------------------------------------------------------
@login_required
def add_service(request):
    if request.user.role != "garage":
        messages.error(request, "Unauthorized access.")
        return redirect("login")

    garage = get_object_or_404(Garage, user=request.user)
    if request.method == "POST":
        form = GarageServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.garage = garage
            service.save()
            messages.success(request, "Service added successfully!")
            return redirect("garage_dashboard")
    else:
        form = GarageServiceForm()
    return render(request, "garage/add_service.html", {"form": form})


# -------------------------------------------------------
# Delete Service
# -------------------------------------------------------
@login_required
def delete_service(request, pk):
    service = get_object_or_404(GarageService, id=pk, garage__user=request.user)
    service.delete()
    messages.success(request, "Service deleted successfully!")
    return redirect("garage_dashboard")


@login_required
def service_type_list(request):
    service_types = ServiceType.objects.all().order_by("name")
    return render(
        request, "garage/service_type_list.html", {"service_types": service_types}
    )


@login_required
def add_service_type(request):
    if request.method == "POST":
        form = ServiceTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service type added successfully!")
            return redirect("service_type_list")
    else:
        form = ServiceTypeForm()
    return render(request, "garage/service_type_form.html", {"form": form})


@login_required
def edit_service_type(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)
    if request.method == "POST":
        form = ServiceTypeForm(request.POST, instance=service_type)
        if form.is_valid():
            form.save()
            messages.success(request, "Service type updated successfully!")
            return redirect("service_type_list")
    else:
        form = ServiceTypeForm(instance=service_type)
    return render(
        request, "garage/service_type_form.html", {"form": form, "edit_mode": True}
    )


@login_required
def delete_service_type(request, pk):
    service_type = get_object_or_404(ServiceType, pk=pk)
    if request.method == "POST":
        service_type.delete()
        messages.success(request, "Service type deleted successfully!")
        return redirect("service_type_list")
    return render(
        request,
        "garage/service_type_confirm_delete.html",
        {"service_type": service_type},
    )


@login_required
def garage_bookings(request):
    """Show all customer bookings for the logged-in garage"""
    garage = get_object_or_404(Garage, user=request.user)
    bookings = Booking.objects.filter(garage=garage).order_by("-booked_on")
    return render(request, "garage/garage_bookings.html", {"bookings": bookings})


@login_required
def update_booking_status(request, booking_id):
    """Allow the garage to update booking status and generate invoice when completed"""
    booking = get_object_or_404(Booking, id=booking_id, garage__user=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        booking.status = new_status
        booking.save()

        # 🧾 Automatically create invoice when marked Completed
        if new_status == "Completed" and not hasattr(booking, "invoice"):
            total = sum(service.price for service in booking.services.all())
            Invoice.objects.create(booking=booking, amount=total)
            messages.success(request, "Invoice generated successfully.")

        messages.success(request, f"Booking marked as {new_status}.")
        return redirect("garage_bookings")

    return render(request, "garage/update_booking_status.html", {"booking": booking})
