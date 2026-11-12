from django.contrib import admin
from .models import Challenge, Comment, Team, TeamMembership, Submission, Review


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'challenge_type',
        'category',
        'created_by',
        'status',
        'deadline',
        'created_at'
    )

    list_filter = (
        'challenge_type',
        'category',
        'status',
        'created_at'
    )

    search_fields = (
        'title',
        'description',
        'created_by__username'
    )

    ordering = ('-created_at',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'challenge',
        'author',
        'created_at'
    )

    search_fields = (
        'content',
        'author__username',
        'challenge__title'
    )

    list_filter = ('created_at',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'name',
        'challenge',
        'leader',
        'created_at'
    )

    search_fields = (
        'name',
        'challenge__title',
        'leader__username'
    )

    list_filter = ('created_at',)


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'team',
        'user',
        'role',
        'joined_at'
    )

    search_fields = (
        'team__name',
        'user__username'
    )

    list_filter = (
        'role',
        'joined_at'
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'challenge',
        'team',
        'submitted_by',
        'status',
        'submitted_at'
    )

    search_fields = (
        'title',
        'description',
        'team__name',
        'submitted_by__username'
    )

    list_filter = (
        'status',
        'submitted_at'
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'submission',
        'reviewer',
        'decision',
        'reviewed_at'
    )

    search_fields = (
        'submission__title',
        'reviewer__username',
        'feedback'
    )

    list_filter = (
        'decision',
        'reviewed_at'
    )