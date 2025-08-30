from django import forms
from .models import EnvironmentalAnalysis

class EnvironmentalAnalysisForm(forms.ModelForm):
    class Meta:
        model = EnvironmentalAnalysis
        fields = ['title', 'location', 'image', 'description']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Forest Conservation Assessment'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Amazon Rainforest, Brazil'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Provide additional details about the environmental report, observations, or concerns...'
            })
        }
