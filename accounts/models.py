from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class User(AbstractUser):

    class Role(models.TextChoices):
        INDIVIDUAL = 'INDIVIDUAL', 'Individual'
        ORGANIZATION = 'ORGANIZATION', 'Organization'

    class OrganizationStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.INDIVIDUAL
    )

    is_email_verified = models.BooleanField(default=False)

    organization_status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.PENDING
    )

    def __str__(self):
        return self.username


    

class Profile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True
    )

    bio = models.TextField(max_length=500, blank=True)

    location = models.CharField(max_length=150, blank=True)

    skills = models.CharField(max_length=500, blank=True)

    website = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


    

class OrganizationProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='organization_profile'
    )

    organization_name = models.CharField(max_length=200)

    description = models.TextField(max_length=1000)

    official_website = models.URLField(blank=True)

    organization_email = models.EmailField()

    registration_number = models.CharField(
        max_length=100,
        unique=True
    )

    verification_document = models.FileField(
        upload_to='organization_documents/',
        blank=True,
        null=True
    )

    admin_remarks = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.user_id and self.user.role != User.Role.ORGANIZATION:
            raise ValidationError(
                "Only organization accounts can have an organization profile."
            )

    def __str__(self):
        return self.organization_name