from django.db import models
from django.conf import settings


class Challenge(models.Model):

    class ChallengeType(models.TextChoices):
        HELP_REQUEST = 'HELP_REQUEST', 'Help Request'
        OPEN_SOURCE = 'OPEN_SOURCE', 'Open Source Project'
        COLLABORATION = 'COLLABORATION', 'Collaboration Opportunity'
        COMMUNITY = 'COMMUNITY', 'Community Problem'
        RESEARCH = 'RESEARCH', 'Research and Innovation'
        INDUSTRY = 'INDUSTRY', 'Industry Challenge'

    class Category(models.TextChoices):
        TECHNICAL = 'TECHNICAL', 'Technical'
        SOCIAL = 'SOCIAL', 'Social'
        ENVIRONMENTAL = 'ENVIRONMENTAL', 'Environmental'
        BUSINESS = 'BUSINESS', 'Business'
        EDUCATION = 'EDUCATION', 'Education'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        CLOSED = 'CLOSED', 'Closed'

    title = models.CharField(max_length=200)

    description = models.TextField()

    challenge_type = models.CharField(
        max_length=20,
        choices=ChallengeType.choices
    )

    category = models.CharField(
        max_length=20,
        choices=Category.choices
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='challenges'
    )

    location = models.CharField(max_length=200, blank=True)

    deadline = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Comment(models.Model):

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='community_comments'
    )

    content = models.TextField(max_length=1000)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.challenge.title}"


class Team(models.Model):

    name = models.CharField(max_length=100)

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='teams'
    )

    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='led_teams'
    )

    description = models.TextField(max_length=1000, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['challenge', 'name'],
                name='unique_team_name_per_challenge'
            )
        ]

    def __str__(self):
        return self.name


class TeamMembership(models.Model):

    class MembershipRole(models.TextChoices):
        LEADER = 'LEADER', 'Leader'
        MEMBER = 'MEMBER', 'Member'

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )

    role = models.CharField(
        max_length=10,
        choices=MembershipRole.choices,
        default=MembershipRole.MEMBER
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'user'],
                name='unique_team_user_membership'
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.team.name}"


class Submission(models.Model):

    class SubmissionStatus(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        REJECTED = 'REJECTED', 'Rejected'
        ACCEPTED = 'ACCEPTED', 'Accepted'

    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submissions'
    )

    title = models.CharField(max_length=200)

    description = models.TextField()

    github_url = models.URLField(blank=True)

    demo_url = models.URLField(blank=True)

    attachment = models.FileField(
        upload_to='submissions/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED
    )

    submitted_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.team and self.challenge:

            if self.team.challenge != self.challenge:
                raise ValidationError({
                    'team': 'The selected team does not belong to this challenge.'
                })

        if self.team and self.submitted_by:

            is_member = TeamMembership.objects.filter(
                team=self.team,
                user=self.submitted_by
            ).exists()

            if not is_member:
                raise ValidationError({
                    'submitted_by': 'Only team members can submit work on behalf of this team.'
                })


class Review(models.Model):

    class ReviewDecision(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_reviews'
    )

    decision = models.CharField(
        max_length=20,
        choices=ReviewDecision.choices,
        default=ReviewDecision.PENDING
    )

    feedback = models.TextField(max_length=2000, blank=True)

    reviewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['submission', 'reviewer'],
                name='unique_reviewer_per_submission'
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.reviewer:
            is_admin = self.reviewer.is_staff or self.reviewer.is_superuser

            is_approved_organization = (
                self.reviewer.role == 'ORGANIZATION'
                and self.reviewer.organization_status == 'APPROVED'
            )

            if not (is_admin or is_approved_organization):
                raise ValidationError({
                    'reviewer': 'Only approved organizations or administrators can review submissions.'
                })

    def __str__(self):
        return f"Review of {self.submission.title}"