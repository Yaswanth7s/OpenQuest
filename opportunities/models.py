from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import OrganizationProfile


class Opportunity(models.Model):

    class OpportunityType(models.TextChoices):
        INTERNSHIP = 'INTERNSHIP', 'Internship'
        FULL_TIME = 'FULL_TIME', 'Full-Time Job'
        PART_TIME = 'PART_TIME', 'Part-Time Job'
        CONTRACT = 'CONTRACT', 'Contract'

    class WorkMode(models.TextChoices):
        REMOTE = 'REMOTE', 'Remote'
        ONSITE = 'ONSITE', 'On-site'
        HYBRID = 'HYBRID', 'Hybrid'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Open'
        CLOSED = 'CLOSED', 'Closed'

    organization = models.ForeignKey(
        OrganizationProfile,
        on_delete=models.CASCADE,
        related_name='opportunities'
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    opportunity_type = models.CharField(
        max_length=20,
        choices=OpportunityType.choices
    )

    work_mode = models.CharField(
        max_length=10,
        choices=WorkMode.choices
    )

    location = models.CharField(max_length=200, blank=True)

    required_skills = models.TextField(blank=True)

    application_url = models.URLField(blank=True)

    application_deadline = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):

        if self.organization_id:
            user = self.organization.user

            if (
                user.role != 'ORGANIZATION'
                or user.organization_status != 'APPROVED'
            ):
                raise ValidationError({
                    'organization': (
                        'Only approved organizations can publish opportunities.'
                    )
                })

        if (
            self.status == self.Status.OPEN
            and self.application_deadline
            and self.application_deadline < timezone.localdate()
        ):
            raise ValidationError({
                'application_deadline': (
                    'Open opportunities cannot have a deadline in the past.'
                )
            })

    def __str__(self):
        return self.title


class Application(models.Model):

    class ApplicationStatus(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        REJECTED = 'REJECTED', 'Rejected'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'

    opportunity = models.ForeignKey(
        Opportunity,
        on_delete=models.CASCADE,
        related_name='applications'
    )

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='opportunity_applications'
    )

    cover_letter = models.TextField(
        max_length=2000,
        blank=True
    )

    resume = models.FileField(
        upload_to='applications/resumes/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.SUBMITTED
    )

    applied_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['opportunity', 'applicant'],
                name='unique_opportunity_application'
            )
        ]

    def clean(self):

        if self.applicant_id and self.applicant.role != 'INDIVIDUAL':
            raise ValidationError({
                'applicant': (
                    'Only individual accounts can apply for opportunities.'
                )
            })

        if self.opportunity_id:

            if self.opportunity.status != Opportunity.Status.OPEN:
                raise ValidationError({
                    'opportunity': (
                        'Applications are closed for this opportunity.'
                    )
                })

            if (
                self.opportunity.application_deadline
                and self.opportunity.application_deadline < timezone.localdate()
            ):
                raise ValidationError({
                    'opportunity': 'The application deadline has passed.'
                })

            if (
                self.applicant_id
                and self.opportunity.organization.user_id == self.applicant_id
            ):
                raise ValidationError({
                    'applicant': (
                        'You cannot apply to your own organization opportunity.'
                    )
                })

    def __str__(self):
        return f"{self.applicant.username} - {self.opportunity.title}"