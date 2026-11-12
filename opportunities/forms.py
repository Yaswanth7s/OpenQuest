
from django import forms
from .models import Opportunity, Application

class OpportunityForm(forms.ModelForm):

    class Meta:
        model = Opportunity

        fields = [
            'title',
            'description',
            'opportunity_type',
            'work_mode',
            'location',
            'required_skills',
            'application_url',
            'application_deadline',
            'status',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter opportunity title',
                'class': 'form-control'
            }),

            'description': forms.Textarea(attrs={
                'placeholder': 'Describe the opportunity',
                'rows': 5,
                'class': 'form-control'
            }),

            'required_skills': forms.Textarea(attrs={
                'placeholder': 'Python, Django, SQL',
                'rows': 3,
                'class': 'form-control'
            }),

            'application_deadline': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data



class ApplicationForm(forms.ModelForm):

    class Meta:
        model = Application

        fields = [
            'cover_letter',
            'resume',
        ]

        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'placeholder': 'Explain why you are suitable for this opportunity',
                'rows': 5,
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, opportunity, applicant, **kwargs):
        super().__init__(*args, **kwargs)

        self.instance.opportunity = opportunity
        self.instance.applicant = applicant

