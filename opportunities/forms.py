
from django import forms
from django.utils import timezone

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

    def clean_application_deadline(self):
        deadline = self.cleaned_data.get('application_deadline')
        if deadline and deadline < timezone.localdate():
            raise forms.ValidationError(
                'The application deadline cannot be in the past.'
            )
        return deadline


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


class ApplicationStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=(
            ('', 'Choose a status'),
            (
                Application.ApplicationStatus.UNDER_REVIEW,
                Application.ApplicationStatus.UNDER_REVIEW.label,
            ),
            (
                Application.ApplicationStatus.SHORTLISTED,
                Application.ApplicationStatus.SHORTLISTED.label,
            ),
            (
                Application.ApplicationStatus.REJECTED,
                Application.ApplicationStatus.REJECTED.label,
            ),
            (
                Application.ApplicationStatus.ACCEPTED,
                Application.ApplicationStatus.ACCEPTED.label,
            ),
        ),
        widget=forms.Select(attrs={'class': 'form-control'}),
    )

