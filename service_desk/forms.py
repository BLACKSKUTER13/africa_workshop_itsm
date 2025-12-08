from django import forms
from .models import Service, Incident


class PublicIncidentForm(forms.ModelForm):
    class Meta:
        model = Incident
        fields = ["service", "comment"]
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "description", "price", "is_active"]
