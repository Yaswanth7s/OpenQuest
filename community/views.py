from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    ChallengeForm,
    ChallengeStatusForm,
    CommentForm,
    ReviewForm,
    SubmissionForm,
    TeamForm,
)
from .models import (
    Challenge,
    Comment,
    Review,
    Submission,
    Team,
    TeamMembership,
)


def _deadline_passed(challenge):
    return bool(
        challenge.deadline
        and challenge.deadline < timezone.localdate()
    )


def _can_review(user):
    return user.is_authenticated and (
        user.is_staff
        or user.is_superuser
        or (
            user.role == 'ORGANIZATION'
            and user.organization_status == 'APPROVED'
        )
    )


def _individual_only(request, message):
    if request.user.role == 'INDIVIDUAL':
        return None
    messages.error(request, message)
    return redirect('home')


def challenge_list(request):
    challenges = Challenge.objects.select_related('created_by').annotate(
        team_count=Count('teams', distinct=True),
        comment_count=Count('comments', distinct=True),
    )
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    challenge_type = request.GET.get('type', '')
    status = request.GET.get('status', Challenge.Status.OPEN)

    if query:
        challenges = challenges.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(location__icontains=query)
        )
    if category in Challenge.Category.values:
        challenges = challenges.filter(category=category)
    else:
        category = ''
    if challenge_type in Challenge.ChallengeType.values:
        challenges = challenges.filter(challenge_type=challenge_type)
    else:
        challenge_type = ''
    if status != 'ALL':
        if status in Challenge.Status.values:
            challenges = challenges.filter(status=status)
        else:
            status = Challenge.Status.OPEN
            challenges = challenges.filter(status=status)

    return render(
        request,
        'community/challenge_list.html',
        {
            'challenges': challenges.order_by('-created_at'),
            'query': query,
            'selected_category': category,
            'selected_type': challenge_type,
            'selected_status': status,
            'categories': Challenge.Category.choices,
            'challenge_types': Challenge.ChallengeType.choices,
            'challenge_statuses': Challenge.Status.choices,
        },
    )


def challenge_detail(request, challenge_id):
    challenge = get_object_or_404(
        Challenge.objects.select_related('created_by'),
        pk=challenge_id,
    )
    teams = challenge.teams.prefetch_related(
        'memberships__user'
    ).order_by('created_at')
    submissions = challenge.submissions.select_related(
        'team',
        'submitted_by',
    ).prefetch_related(
        'reviews__reviewer'
    ).order_by('-submitted_at')
    comments = challenge.comments.select_related(
        'author'
    ).order_by('-created_at')

    if request.user.is_authenticated:
        my_team_ids = set(
            TeamMembership.objects.filter(
                team__challenge=challenge,
                user=request.user,
            ).values_list('team_id', flat=True)
        )
    else:
        my_team_ids = set()

    can_manage = (
        request.user.is_authenticated
        and (
            request.user.is_staff
            or (
                request.user.role == 'INDIVIDUAL'
                and challenge.created_by_id == request.user.id
            )
        )
    )
    team_signup_open = (
        challenge.status == Challenge.Status.OPEN
        and not _deadline_passed(challenge)
    )
    submission_open = (
        challenge.status in (
            Challenge.Status.OPEN,
            Challenge.Status.IN_PROGRESS,
        )
        and not _deadline_passed(challenge)
    )

    return render(
        request,
        'community/challenge_detail.html',
        {
            'challenge': challenge,
            'teams': teams,
            'submissions': submissions,
            'comments': comments,
            'comment_form': CommentForm(),
            'team_form': TeamForm(),
            'team_signup_open': team_signup_open,
            'submission_open': submission_open,
            'my_team_ids': my_team_ids,
            'can_participate': (
                request.user.is_authenticated
                and request.user.role == 'INDIVIDUAL'
            ),
            'can_manage': can_manage,
            'can_review': _can_review(request.user),
            'status_form': ChallengeStatusForm(
                initial={'status': challenge.status}
            ),
        },
    )


@login_required
def create_challenge(request):
    response = _individual_only(
        request,
        'Community challenges are for individual accounts.',
    )
    if response:
        return response

    if request.method == 'POST':
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.created_by = request.user
            challenge.full_clean()
            challenge.save()
            messages.success(request, 'Your challenge is live.')
            return redirect(
                'community:challenge_detail',
                challenge_id=challenge.pk,
            )
    else:
        form = ChallengeForm()

    return render(
        request,
        'community/challenge_form.html',
        {'form': form},
    )


@login_required
@require_POST
def add_comment(request, challenge_id):
    response = _individual_only(
        request,
        'Only individual accounts can participate in community discussions.',
    )
    if response:
        return response

    challenge = get_object_or_404(Challenge, pk=challenge_id)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.challenge = challenge
        comment.author = request.user
        comment.save()
        messages.success(request, 'Your comment has been added.')
    else:
        messages.error(request, 'Please enter a comment before posting.')
    return redirect(
        'community:challenge_detail',
        challenge_id=challenge.pk,
    )


@login_required
@require_POST
def update_challenge_status(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    if not (
        request.user.is_staff
        or (
            request.user.role == 'INDIVIDUAL'
            and challenge.created_by_id == request.user.id
        )
    ):
        messages.error(request, 'Only the challenge creator can update its status.')
        return redirect(
            'community:challenge_detail',
            challenge_id=challenge.pk,
        )

    form = ChallengeStatusForm(request.POST)
    if form.is_valid():
        challenge.status = form.cleaned_data['status']
        challenge.save(update_fields=('status', 'updated_at'))
        messages.success(request, 'Challenge status updated.')
    else:
        messages.error(request, 'Choose a valid challenge status.')
    return redirect(
        'community:challenge_detail',
        challenge_id=challenge.pk,
    )


@login_required
def create_team(request, challenge_id):
    response = _individual_only(
        request,
        'Only individual accounts can start a challenge team.',
    )
    if response:
        return response

    challenge = get_object_or_404(Challenge, pk=challenge_id)
    if challenge.status != Challenge.Status.OPEN or _deadline_passed(challenge):
        messages.error(request, 'This challenge is no longer accepting teams.')
        return redirect(
            'community:challenge_detail',
            challenge_id=challenge.pk,
        )

    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.challenge = challenge
            team.leader = request.user
            try:
                with transaction.atomic():
                    team.full_clean()
                    team.save()
            except ValidationError as error:
                form.add_error(None, error)
            except IntegrityError:
                form.add_error(
                    'name',
                    'A team with this name already exists for the challenge.',
                )
            else:
                messages.success(
                    request,
                    'Your team is ready. Invite others to join the challenge.',
                )
                return redirect(
                    'community:challenge_detail',
                    challenge_id=challenge.pk,
                )
    else:
        form = TeamForm()

    return render(
        request,
        'community/team_form.html',
        {'form': form, 'challenge': challenge},
    )


@login_required
@require_POST
def join_team(request, challenge_id, team_id):
    response = _individual_only(
        request,
        'Only individual accounts can join challenge teams.',
    )
    if response:
        return response

    challenge = get_object_or_404(Challenge, pk=challenge_id)
    team = get_object_or_404(Team, pk=team_id, challenge=challenge)
    if challenge.status != Challenge.Status.OPEN or _deadline_passed(challenge):
        messages.error(request, 'This challenge is no longer accepting teammates.')
    else:
        membership, created = TeamMembership.objects.get_or_create(
            team=team,
            user=request.user,
        )
        if created:
            messages.success(request, f'You joined {team.name}.')
        else:
            messages.info(request, f'You are already a member of {team.name}.')
    return redirect(
        'community:challenge_detail',
        challenge_id=challenge.pk,
    )


@login_required
def submit_project(request, challenge_id, team_id):
    response = _individual_only(
        request,
        'Only individual accounts can submit challenge work.',
    )
    if response:
        return response

    challenge = get_object_or_404(Challenge, pk=challenge_id)
    team = get_object_or_404(Team, pk=team_id, challenge=challenge)
    is_member = TeamMembership.objects.filter(
        team=team,
        user=request.user,
    ).exists()
    accepts_submissions = (
        challenge.status in (
            Challenge.Status.OPEN,
            Challenge.Status.IN_PROGRESS,
        )
        and not _deadline_passed(challenge)
    )
    if not is_member:
        messages.error(request, 'Join the team before submitting its work.')
        return redirect(
            'community:challenge_detail',
            challenge_id=challenge.pk,
        )
    if not accepts_submissions:
        messages.error(request, 'This challenge is no longer accepting submissions.')
        return redirect(
            'community:challenge_detail',
            challenge_id=challenge.pk,
        )

    if request.method == 'POST':
        form = SubmissionForm(
            request.POST,
            request.FILES,
            challenge=challenge,
            team=team,
            submitted_by=request.user,
        )
        if form.is_valid():
            submission = form.save(commit=False)
            try:
                submission.full_clean()
                submission.save()
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(request, 'Your team submission is in.')
                return redirect(
                    'community:challenge_detail',
                    challenge_id=challenge.pk,
                )
    else:
        form = SubmissionForm(
            challenge=challenge,
            team=team,
            submitted_by=request.user,
        )

    return render(
        request,
        'community/submission_form.html',
        {'form': form, 'challenge': challenge, 'team': team},
    )


@login_required
def review_submission(request, challenge_id, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related('challenge', 'team'),
        pk=submission_id,
        challenge_id=challenge_id,
    )
    if not _can_review(request.user):
        messages.error(
            request,
            'Only approved organizations and administrators can review submissions.',
        )
        return redirect(
            'community:challenge_detail',
            challenge_id=challenge_id,
        )
    if (
        not request.user.is_staff
        and TeamMembership.objects.filter(
            team=submission.team,
            user=request.user,
        ).exists()
    ):
        messages.error(request, 'Team members cannot review their own submission.')
        return redirect(
            'community:challenge_detail',
            challenge_id=challenge_id,
        )

    review = Review.objects.filter(
        submission=submission,
        reviewer=request.user,
    ).first()
    review = review or Review(
        submission=submission,
        reviewer=request.user,
    )
    review.submission = submission
    review.reviewer = request.user
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            review = form.save(commit=False)
            try:
                review.full_clean()
                review.save()
            except ValidationError as error:
                form.add_error(None, error)
            else:
                submission.status = form.cleaned_data['decision']
                submission.save(update_fields=('status', 'updated_at'))
                messages.success(request, 'Your review has been saved.')
                return redirect(
                    'community:challenge_detail',
                    challenge_id=challenge_id,
                )
    else:
        form = ReviewForm(instance=review)

    return render(
        request,
        'community/review_form.html',
        {
            'form': form,
            'challenge': submission.challenge,
            'submission': submission,
        },
    )


@login_required
def download_submission_attachment(request, challenge_id, submission_id):
    submission = get_object_or_404(
        Submission.objects.select_related('challenge', 'team'),
        pk=submission_id,
        challenge_id=challenge_id,
    )
    is_team_member = TeamMembership.objects.filter(
        team=submission.team,
        user=request.user,
    ).exists()
    is_challenge_creator = submission.challenge.created_by_id == request.user.id
    if not (
        request.user.is_staff
        or request.user.is_superuser
        or is_team_member
        or is_challenge_creator
        or _can_review(request.user)
    ):
        raise PermissionDenied
    if not submission.attachment:
        raise Http404('This submission does not include an attachment.')
    try:
        attachment = submission.attachment.open('rb')
    except FileNotFoundError as error:
        raise Http404('The submission attachment is no longer available.') from error

    response = FileResponse(
        attachment,
        as_attachment=True,
        filename=Path(submission.attachment.name).name,
        content_type='application/octet-stream',
    )
    response.headers['Cache-Control'] = 'private, no-store'
    return response
