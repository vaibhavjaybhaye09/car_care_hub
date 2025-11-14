from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import FileResponse
from .models import Booking
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import os


from .models import Booking, Invoice
from .forms import BookingForm
from garage.models import Garage, GarageService


# -------------------------------------------------------
# Customer books a service
# -------------------------------------------------------
@login_required
def book_service(request, garage_id=None):
    garage = get_object_or_404(Garage, id=garage_id) if garage_id else None

    if request.method == "POST":
        form = BookingForm(request.POST, user=request.user, garage=garage)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.customer = request.user
            booking.garage = garage
            booking.status = "Pending"
            booking.save()
            form.save_m2m()  # ✅ Save many-to-many services

            # Optional email
            send_mail(
                subject="Booking Confirmed",
                message=f"Your booking (ID: {booking.booking_id}) at {booking.garage.name} has been confirmed.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=True,
            )

            messages.success(request, "Booking confirmed successfully!")
            return redirect("bookings:booking_list")
    else:
        form = BookingForm(user=request.user, garage=garage, initial={"garage": garage})

    return render(
        request, "bookings/booking_form.html", {"form": form, "garage": garage}
    )


# -------------------------------------------------------
# Customer Booking List (shows all bookings + invoices)
# -------------------------------------------------------
@login_required
def booking_list(request):
    bookings = Booking.objects.filter(customer=request.user).order_by("-booked_on")
    return render(request, "bookings/booking_list.html", {"bookings": bookings})


# -------------------------------------------------------
# Garage Booking Management — all customer bookings
# -------------------------------------------------------
@login_required
def garage_bookings(request):
    garage = get_object_or_404(Garage, user=request.user)
    bookings = Booking.objects.filter(garage=garage).order_by("-booked_on")
    return render(request, "garage/garage_bookings.html", {"bookings": bookings})


# -------------------------------------------------------
# Update Booking Status (Garage Only)
# -------------------------------------------------------
from django.core.mail import send_mail
from customers.models import Notification
from django.conf import settings


@login_required
def update_booking_status(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, garage__user=request.user)

    if request.method == "POST":
        new_status = request.POST.get("status")
        booking.status = new_status
        booking.save()

        # ============================
        # 1️⃣ Generate invoice if completed
        # ============================
        if new_status == "Completed" and not hasattr(booking, "invoice"):
            total = sum(s.price for s in booking.services.all())
            Invoice.objects.create(booking=booking, amount=total)

        # ============================
        # 2️⃣ Email Notification to Customer
        # ============================
        if new_status == "Completed":
            try:
                send_mail(
                    subject="Your Car Service is Completed!",
                    message=(
                        f"Hello {booking.customer.username},\n\n"
                        f"Your car service at {booking.garage.name} is now completed.\n"
                        f"Booking ID: {booking.booking_id}\n"
                        f"You can visit the garage and pick it up.\n\n"
                        f"Thank you for choosing our service!"
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[booking.customer.email],
                    fail_silently=True,
                )
            except:
                pass

            # ============================
            # 3️⃣ In-App Notification
            # ============================
            Notification.objects.create(
                user=booking.customer,
                title="Service Completed",
                message=f"Your car service for booking {booking.booking_id} is now completed. Please collect your vehicle.",
            )

        messages.success(request, f"Booking status updated to {new_status}.")
        return redirect("garage_bookings")

    return render(request, "garage/update_booking_status.html", {"booking": booking})


@login_required
def booking_detail(request, pk):
    """Show details of a single booking for the customer."""
    booking = get_object_or_404(Booking, pk=pk, customer=request.user)
    return render(request, "bookings/booking_detail.html", {"booking": booking})


# -------------------------------------------------------
# Generate & Download Invoice (PDF)
# -------------------------------------------------------
@login_required
def download_invoice(request, pk):
    booking = get_object_or_404(Booking, pk=pk)

    # Ensure user has permission
    if booking.customer != request.user and booking.garage.user != request.user:
        messages.error(request, "Unauthorized access.")
        return redirect("bookings:booking_list")

    invoice_path = f"media/invoices/invoice_{booking.booking_id}.pdf"
    os.makedirs(os.path.dirname(invoice_path), exist_ok=True)

    # Generate invoice PDF
    c = canvas.Canvas(invoice_path, pagesize=A4)
    c.drawString(100, 800, "Smart Garage - Invoice")
    c.drawString(100, 780, f"Booking ID: {booking.booking_id}")
    c.drawString(100, 760, f"Customer: {booking.customer.username}")
    c.drawString(100, 740, f"Garage: {booking.garage.name}")
    c.drawString(100, 720, f"Date: {booking.appointment_date.strftime('%d %b %Y')}")
    c.drawString(100, 700, f"Status: {booking.status}")

    y = 680
    c.drawString(100, y, "Services:")
    for s in booking.services.all():
        y -= 20
        c.drawString(120, y, f"- {s.service_type.name} (₹{s.price})")

    y -= 40
    c.drawString(100, y, f"Total: ₹{sum(s.price for s in booking.services.all())}")

    c.showPage()
    c.save()

    return FileResponse(
        open(invoice_path, "rb"),
        as_attachment=True,
        filename=f"Invoice_{booking.booking_id}.pdf",
    )
