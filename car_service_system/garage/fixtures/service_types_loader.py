from garage.models import ServiceType
from django.db import IntegrityError

data = {
    "General Maintenance": [
        "Oil & Filter Change", "Coolant Top-Up", "Windshield Washer Refill",
        "Air Filter Replacement", "Wiper Blade Replacement", "Spark Plug Replacement"
    ],
    "Engine Services": [
        "Engine Diagnostics (OBD Scanning)", "Engine Overhaul", "Timing Belt/Chain Replacement",
        "Engine Oil Leak Repair", "Cylinder Head Repair", "Fuel Injector Cleaning"
    ],
    "Brake System Services": [
        "Brake Pad Replacement", "Brake Disc/Drum Replacement", "Brake Fluid Replacement",
        "ABS Diagnostics", "Handbrake Adjustment"
    ],
    "Transmission & Clutch": [
        "Manual Clutch Replacement", "Transmission Fluid Change", "Gearbox Overhaul",
        "Automatic Transmission Service", "Differential Oil Change"
    ],
    "Suspension & Steering": [
        "Shock Absorber Replacement", "Suspension Bush Replacement", "Wheel Alignment",
        "Power Steering Fluid Change", "Steering Rack Repair"
    ],
    "Electrical & Battery": [
        "Battery Check & Replacement", "Alternator Repair", "Starter Motor Replacement",
        "Headlight & Taillight Repair", "Wiring Diagnostics"
    ],
    "Air Conditioning (AC)": [
        "AC Gas Refill", "AC Filter Replacement", "Compressor Replacement",
        "Condenser Cleaning", "Blower Motor Repair"
    ],
    "Tyres & Wheels": [
        "Tyre Replacement", "Tyre Balancing", "Wheel Alignment",
        "Puncture Repair", "Alloy Wheel Repair"
    ],
    "Body & Paint": [
        "Dent Removal", "Full Body Paint", "Scratch Repair",
        "Bumper Replacement", "Headlight Restoration"
    ],
    "Car Detailing & Cleaning": [
        "Exterior Wash", "Interior Vacuum & Polish", "Upholstery Cleaning",
        "Ceramic Coating", "Engine Bay Cleaning"
    ],
    "Inspection & Diagnostic": [
        "Pre-Delivery Inspection (PDI)", "Vehicle Health Check",
        "Emission Testing", "Insurance Claim Inspection"
    ],
    "Emergency & On-Road Assistance": [
        "Towing Service", "Battery Jump Start", "Flat Tyre Replacement",
        "Lockout Assistance", "Fuel Delivery"
    ],
}

count = 0
for category, subtypes in data.items():
    main, _ = ServiceType.objects.get_or_create(name=category)
    for sub in subtypes:
        try:
            ServiceType.objects.get_or_create(name=sub, parent=main)
            count += 1
        except IntegrityError:
            continue

print(f"✅ Loaded {count} new service types and subtypes successfully.")
