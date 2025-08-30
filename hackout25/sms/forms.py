from django import forms
from .models import SMSMessage
from dashboard.models import EnvironmentalAnalysis

class SMSMessageForm(forms.ModelForm):
    class Meta:
        model = SMSMessage
        fields = ['title', 'message', 'message_type', 'priority', 'phone_numbers', 'related_analysis']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter SMS title/subject'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Enter your SMS message (max 1000 characters)',
                'maxlength': '1000'
            }),
            'message_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'priority': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone_numbers': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter phone numbers separated by commas (e.g., +1234567890, +0987654321)'
            }),
            'related_analysis': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['related_analysis'].empty_label = "Select an analysis (optional)"
        self.fields['related_analysis'].queryset = EnvironmentalAnalysis.objects.all()
    
    def clean_phone_numbers(self):
        phone_numbers = self.cleaned_data.get('phone_numbers', '')
        numbers = [num.strip() for num in phone_numbers.split(',') if num.strip()]
        
        if not numbers:
            raise forms.ValidationError('Please provide at least one phone number.')
        
        # Basic phone number validation
        for number in numbers:
            if len(number) < 10:
                raise forms.ValidationError(f'Invalid phone number: {number}. Please use international format.')
        
        return phone_numbers
    
    def clean_message(self):
        message = self.cleaned_data.get('message', '')
        if len(message) > 1000:
            raise forms.ValidationError('Message is too long. SMS messages must be under 1000 characters.')
        return message
