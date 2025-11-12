from django import forms
from .models import Booking
from customers.models import Vehicle
from garage.models import ServiceType

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['garage', 'vehicle', 'service', 'appointment_date', 'delivery_option', 'remarks']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        for field in self.fields:
            if not isinstance(self.fields[field].widget, forms.RadioSelect):
                self.fields[field].widget.attrs['class'] = 'form-control'

        if user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(customer=user)
            # Group services by main category (parent)
        grouped = []
        main_categories = ServiceType.objects.filter(parent__isnull=True).order_by('name')
        for main in main_categories:
            subs = ServiceType.objects.filter(parent=main).order_by('name')
            if subs.exists():
                grouped.append((main.name, [(sub.id, sub.name) for sub in subs]))

        self.fields['service'].choices = grouped
