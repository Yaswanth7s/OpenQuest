from django import forms
from django.utils import timezone

from .models import Challenge, Comment, Review, Submission, Team


class ChallengeForm(forms.ModelForm):
    class Meta:
        model = Challenge
        fields = (
            'title',
            'description',
            'challenge_type',
            'category',
            'location',
            'deadline',
        )
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Give your challenge a clear name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'What needs solving, and why does it matter?',
            }),
            'challenge_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Remote, city, or region',
            }),
            'deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.localdate():
            raise forms.ValidationError('The deadline cannot be in the past.')
        return deadline


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('content',)
        labels = {'content': 'Add to the conversation'}
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Share a question, thought, or helpful lead…',
            }),
        }


class TeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'A memorable team name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What are you hoping to build together?',
            }),
        }


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ('title', 'description', 'github_url', 'demo_url', 'attachment')
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'What did your team make?',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Describe your approach and what you learned.',
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/…',
            }),
            'demo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://…',
            }),
        }

    def __init__(
        self,
        *args,
        challenge,
        team,
        submitted_by,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.instance.challenge = challenge
        self.instance.team = team
        self.instance.submitted_by = submitted_by


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ('decision', 'feedback')
        widgets = {
            'decision': forms.Select(attrs={'class': 'form-control'}),
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Give the team useful, constructive feedback.',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['decision'].choices = [('', 'Choose a decision')] + [
            choice for choice in Review.ReviewDecision.choices
            if choice[0] != Review.ReviewDecision.PENDING
        ]


class ChallengeStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=Challenge.Status.choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
