from django import forms
from .models import Booking
from customers.models import Vehicle
from garage.models import GarageService


class BookingForm(forms.ModelForm):

    services = forms.ModelMultipleChoiceField(
        queryset=GarageService.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Select Services"
    )

    class Meta:
        model = Booking
        fields = ['garage', 'vehicle', 'services', 'appointment_date', 'delivery_option', 'remarks']
        widgets = {
            'appointment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        garage = kwargs.pop('garage', None)
        super().__init__(*args, **kwargs)

        # Add Bootstrap styling
        for field in self.fields:
            if not isinstance(self.fields[field].widget, forms.CheckboxSelectMultiple):
                self.fields[field].widget.attrs['class'] = 'form-control'

        # Filter vehicles by logged-in user
        if user:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(customer=user)

        # Load services for selected garage
        if garage:
            self.fields['services'].queryset = GarageService.objects.filter(garage=garage)
        elif 'garage' in self.data:
            try:
                garage_id = int(self.data.get('garage'))
                self.fields['services'].queryset = GarageService.objects.filter(garage_id=garage_id)
            except:
                pass
        elif self.instance.pk:
            self.fields['services'].queryset = self.instance.garage.garage_services.all()
