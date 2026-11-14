
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, User, OrganizationProfile


class BaseRegistrationForm(UserCreationForm):

    class Meta:
        model = User

        fields = [
            'username',
            'email',
        ]

        widgets = {
            'username': forms.TextInput(attrs={
                'placeholder': 'Choose a username',
                'class': 'form-control'
            }),

            'email': forms.EmailInput(attrs={
                'placeholder': 'Enter your email address',
                'class': 'form-control'
            }),
        }

    def save(self, commit=True):

        user = super().save(commit=False)

        if commit:
            user.save()
            self.save_m2m()

        return user


class IndividualRegistrationForm(BaseRegistrationForm):

    def save(self, commit=True):

        user = super().save(commit=False)
        user.role = User.Role.INDIVIDUAL

        if commit:
            user.save()
            self.save_m2m()

        return user


class OrganizationRegistrationForm(BaseRegistrationForm):

    def save(self, commit=True):

        user = super().save(commit=False)
        user.role = User.Role.ORGANIZATION

        if commit:
            user.save()
            self.save_m2m()

        return user


class OrganizationProfileForm(forms.ModelForm):

    class Meta:
        model = OrganizationProfile

        fields = [
            'organization_name',
            'description',
            'official_website',
            'organization_email',
            'registration_number',
            'verification_document',
        ]

        widgets = {
            'organization_name': forms.TextInput(attrs={
                'placeholder': 'Enter official organization name',
                'class': 'form-control'
            }),

            'description': forms.Textarea(attrs={
                'placeholder': 'Describe your organization',
                'rows': 5,
                'class': 'form-control'
            }),

            'official_website': forms.URLInput(attrs={
                'placeholder': 'https://example.com',
                'class': 'form-control'
            }),

            'organization_email': forms.EmailInput(attrs={
                'placeholder': 'official@example.com',
                'class': 'form-control'
            }),

            'registration_number': forms.TextInput(attrs={
                'placeholder': 'Enter registration number',
                'class': 'form-control'
            }),
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            'profile_picture',
            'bio',
            'location',
            'skills',
            'website',
        )
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'maxlength': 500,
                'placeholder': 'A little about what you care about and want to build.',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, region, or remote',
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Design, research, Python, community building…',
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://your-site.example',
            }),
        }

